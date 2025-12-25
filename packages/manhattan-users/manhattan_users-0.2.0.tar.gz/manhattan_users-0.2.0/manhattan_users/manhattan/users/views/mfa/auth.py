"""
Authorize the user using a secondary mechanism.
"""

from datetime import datetime
import io
import os
import urllib.parse as urlparse
from urllib.parse import urlencode

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.forms import BaseForm, fields, validators
from manhattan.manage.views import factories, utils
from manhattan.nav import NavItem
from manhattan import secure
import pyotp

__all__ = ['auth_chains']


# Utils

def is_blocked(user):
    """
    Return true if the user is temporarily blocked from authorizing due to too
    many failed attempts.
    """
    prefix = user.get_settings_prefix()
    cache = flask.current_app.config[f'{prefix}_MFA_FAILED_AUTH_CACHE']
    key = f'mfa_failed_auth:{user._id}'

    max_attempts = flask\
        .current_app\
        .config[f'{prefix}_MFA_MAX_FAILED_AUTH_ATTEMPTS']

    return (cache.get(key) or 0) >= max_attempts


# Forms

class AuthForm(BaseForm):

    totp = fields.StringField(
        'Your six-digit code',
        [validators.Required()],
        render_kw={
            'autocomplete': 'one-time-code',
            'autofocus': True
        }
    )

    def validate_totp(form, field):
        if not field.data:
            return

        # Check that the user has not been blocked due to too many failed
        # attempts.
        if is_blocked(form.obj):
            raise validators.ValidationError('To many failed attempts.')

        # Check that the code given is valid
        verified = False

        # First check the TOTP...
        totp = field.data.replace(' ', '')
        if pyotp.TOTP(form.obj.mfa_otp_secret).verify(totp):
            verified = True

        else:

            # ...then check the recovery codes for the user
            for mfa_recovery_code_hash in form.obj.mfa_recovery_code_hashes:
                if secure.verify_password(mfa_recovery_code_hash, totp):
                    verified = True
                    break

        if not verified:
            raise validators.ValidationError('Not a valid code')


# Chains
auth_chains = ChainMgr()

# POST
auth_chains['get'] = Chain([
    'config',
    'authenticate',
    'init_form',
    'decorate',
    'render_template'
])

# POST
auth_chains['post'] = Chain([
    'config',
    'authenticate',
    'init_form',
    'validate',
    [
        ['authorize'],
        [
            'log_failed_attempts',
            'decorate',
            'render_template'
        ]
    ]
])

# Define the links
auth_chains.set_link(
    factories.config(
        form_cls=AuthForm,
        open_user_nav=True
    )
)
auth_chains.set_link(factories.validate())
auth_chains.set_link(factories.render_template('mfa/auth.html'))

@auth_chains.link
def authenticate(state):
    """Ensure there's a signed in user"""
    user_cls = state.manage_config.frame_cls
    user = getattr(flask.g, user_cls.get_g_key(), None)

    if user:

        if not user.mfa_enabled:
            return flask.redirect(
                flask.url_for(state.manage_config.get_endpoint('dashboard'))
            )

        current_session = user.current_session

        if (
            current_session
            and getattr(current_session, 'mfa_authorized')
            and 'scoped' not in flask.request.args
        ):

            # Verify the caller URL is safe
            caller_url = flask.request.args.get('caller_url')
            caller_url = secure.safe_redirect_url(caller_url) \
                    if caller_url else None

            if caller_url is None:
                flask.flash('Invalid caller URL', 'error')
                return flask.redirect(
                    flask.url_for(state.manage_config.get_endpoint('dashboard'))
                )

            # Return the user to the caller
            return flask.redirect(caller_url)

    else:
        return flask.redirect(
            flask.url_for(state.manage_config.get_endpoint('sign_in'))
        )

@auth_chains.link
def decorate(state):
    user_cls = state.manage_config.frame_cls
    prefix = user_cls.get_settings_prefix()

    state.decor = utils.base_decor(state.manage_config, 'mfa_auth')
    state.decor['title'] = 'Two factor authentication'
    state.decor['breadcrumbs'].add(NavItem('Two factor authentication', ''))

    state.mfa_issuer = flask.current_app.config[f'{prefix}_MFA_ISSUER']

@auth_chains.link
def init_form(state):
    user_cls = state.manage_config.frame_cls

    # Initialize the form
    state.form = state.form_cls(
        flask.request.form,
        obj=getattr(flask.g, user_cls.get_g_key())
    )

    # Store the user class against the form
    state.form._user_cls = user_cls

@auth_chains.link
def log_failed_attempts(state):
    """Log a failed attempt to authorize using MFA"""

    if not state.form.totp.data:
        # Don't log failed attempts if no password (totp) was provided
        return

    user_cls = state.manage_config.frame_cls
    prefix = user_cls.get_settings_prefix()
    user = getattr(flask.g, user_cls.get_g_key())
    cache = flask.current_app.config[f'{prefix}_MFA_FAILED_AUTH_CACHE']
    attempt_key = f'mfa_failed_auth:{user._id}'
    attempts = cache.get(attempt_key) or 0
    lockout = flask.current_app.config[f'{prefix}_MFA_FAILED_AUTH_LOCKOUT']

    # Record the failed attempt
    cache.set(attempt_key, attempts + 1, lockout)

    if is_blocked(user):

        # Notify the user that they are temporarily blocked from
        # authorizing.
        flask.session['_flashes'] = []
        seconds = round(lockout.total_seconds())
        flask.flash(
            f'To too many failed attempts. Please wait {seconds} seconds '
            'before trying again.',
            'error'
        )

@auth_chains.link
def authorize(state):
    """
    Create a session key which can be used by the caller to authorize the
    request and return the user to the caller with the key.
    """
    user_cls = state.manage_config.frame_cls
    user = getattr(flask.g, user_cls.get_g_key())

    # Check if a recovery code was used
    totp = state.form.data['totp']

    used_recovert_code_hash = None
    for mfa_recovery_code_hash in user.mfa_recovery_code_hashes:
        if secure.verify_password(mfa_recovery_code_hash, totp):
            used_recovert_code_hash = mfa_recovery_code_hash
            break

    if used_recovert_code_hash:

        # Remove the recovery code for the user
        index = user.mfa_recovery_code_hashes.index(used_recovert_code_hash)

        user_cls.get_collection().update_one(
            {'_id': user._id},
            {
                '$pull': {'mfa_recovery_code_hashes': used_recovert_code_hash},
                '$unset': {f'mfa_recovery_code_masks.{index}': 1}
            }
        )

        user_cls.get_collection().update_one(
            {'_id': user._id},
            {'$pull': {'mfa_recovery_code_masks': None}}
        )

        # Email the user to let them know a recovery code was used
        env = flask.current_app.jinja_env
        template_path = os.path.join(
            state.manage_config.template_path,
            'emails/recovery_code_used.html'
        )

        flask.current_app.manage.send_email(
            [user.email],
            'Recovery code used',
            template_path,
            global_vars={'user': user.to_json_type()},
            template_map={
                'recovery_code_used': env.loader.get_source(
                    env,
                    'manhattan/users/emails/recovery_code_used.html'
                )[0],
                template_path: env.loader.get_source(env, template_path)[0]
            }
        )

    # Verify the caller URL is safe
    caller_url = flask.request.args.get('caller_url')
    caller_url = secure.safe_redirect_url(caller_url) if caller_url else None

    if caller_url is None:
        flask.flash('Invalid caller URL', 'error')
        return flask.redirect(
            flask.url_for(state.manage_config.get_endpoint('dashboard'))
        )

    # Update the user's sessions MFA authorized date/time
    flask.current_session = user.current_session
    flask.current_session.mfa_authorized = datetime.utcnow()
    flask.current_session.update('mfa_authorized')

    # Check to see if the caller is requesting a scoped session
    if 'scoped' in flask.request.args:

        # Generate the scoped session key
        prefix = user_cls.get_settings_prefix()
        session_token = secure.mfa.create_scoped_session(
            flask.current_app.config[f'{prefix}_MFA_SCOPED_SESSION_CACHE'],
            (str(user._id), caller_url),
            flask.current_app.config[f'{prefix}_MFA_SCOPED_SESSION_LIFESPAN']
        )

        # Add the scoped session key to the caller URL

        # Parse the URL
        caller_url_parts = list(urlparse.urlparse(caller_url))

        # Update the query parameters
        query = dict(urlparse.parse_qsl(caller_url_parts[4]))
        query['mfa_scoped_session_token'] = session_token
        caller_url_parts[4] = urlencode(query)

        # Rebuild the URL
        caller_url = urlparse.urlunparse(caller_url_parts)

    # Return the user to the caller
    return flask.redirect(caller_url)
