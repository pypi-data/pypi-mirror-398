"""
Allow a user to change their password, view, enable and disable their
multi-factor authentication and
"""

import os

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.forms import BaseForm, fields, validators
from manhattan.manage.views import factories
from manhattan.nav import Nav, NavItem
from manhattan.users.utils import apply_password_rules, password_validator
from mongoframes import Q, SortBy

__all__ = ['security_chains']


# Forms

class ChangeMyPasswordForm(BaseForm):

    email = fields.StringField(
        'Email',
        render_kw={'autocomplete': 'username'}
    )

    current_password = fields.PasswordField(
        'Current password',
        [validators.Required()],
        render_kw={'autocomplete': 'current-password'}
    )

    new_password = fields.PasswordField(
        'New password',
        [
            validators.Required(),
            validators.EqualTo('confirm_password', "Passwords don't match."),
            password_validator
        ],
        render_kw={'autocomplete': 'new-password'}
    )

    confirm_password = fields.PasswordField(
        'Confirm password',
        render_kw={'autocomplete': 'new-password'}
    )

    def validate_new_password(form, field):

        if form.confirm_password.data != field.data:

            # Prevent the user from attempting gain access to previous
            # passwords.
            return

        if form.obj.email.lower() in field.data.lower():
            raise validators.ValidationError(
                'Your password cannot contain your email address.'
            )

        if form.obj.is_previous_password(field.data):
            raise validators.ValidationError(
                "You can't reuse a password you've used before."
            )

    def validate_current_password(form, field):
        """
        The user must specify their existing password to change their existing
        one.
        """
        user_cls = form._user_cls
        user = getattr(flask.g, user_cls.get_g_key())

        if not field.data:
            return

        if not user.password_eq(field.data):
            raise validators.ValidationError('Password is incorrect.')


# Chains
security_chains = ChainMgr()

# GET
security_chains['get'] = Chain([
    'config',
    'authenticate',
    'init_form',
    'apply_password_rules',
    'get_sessions',
    'decorate',
    'render_template'
])

# POST
security_chains['post'] = Chain([
    'config',
    'authenticate',
    'init_form',
    'apply_password_rules',
    'validate',
    [
        [
            'change_password',
            'redirect'
        ], [
            'log_failed_attempts',
            'get_sessions',
            'decorate',
            'render_template'
        ]
    ]
])

# Define the links
security_chains.set_link(
    factories.config(
        form_cls=ChangeMyPasswordForm,
        open_user_nav=True
    )
)
security_chains.set_link(factories.authenticate())
security_chains.set_link(apply_password_rules())
security_chains.set_link(factories.validate())
security_chains.set_link(factories.render_template('security.html'))
security_chains.set_link(factories.redirect('security'))

@security_chains.link
def decorate(state):
    factories.decorate('security')(state)

    # Modify the breadcrumb
    state.decor['breadcrumbs'] = Nav.local_menu()
    state.decor['breadcrumbs'].add(NavItem('Security', ''))

@security_chains.link
def init_form(state):
    user_cls = state.manage_config.frame_cls
    user = getattr(flask.g, user_cls.get_g_key())

    # Initialize the form
    state.form = state.form_cls(flask.request.form, obj=user)

    # Store the user class against the form
    state.form._user_cls = state.manage_config.frame_cls

@security_chains.link
def log_failed_attempts(state):
    """Log failed attempts"""
    user_cls = state.manage_config.frame_cls
    user = getattr(flask.g, user_cls.get_g_key())
    prefix = user_cls.get_settings_prefix()

    if 'current_password' not in state.form.errors:
        # We only log an attempt as failed if the current password is invalid
        return

    # Log the failed attempt
    cache = flask.current_app.config[f'{prefix}_FAILED_SIGN_IN_CACHE']
    attempt_key = user_cls.get_sign_in_attempt_key(state.form.email.data)
    attempts = cache.get(attempt_key) or 0

    # Record the failed attempt
    cache.set(
        attempt_key,
        attempts + 1,
        flask.current_app.config[f'{prefix}_FAILED_SIGN_IN_LOCKOUT']
    )

    if user_cls.is_locked_out(state.form.email.data):

        # Clear the user's session token
        if user:
            user_cls.get_collection().update_one(
                {'_id': user._id},
                {'$unset': {'session_token': ''}}
            )

        # Clear the session token from the the flask session
        if user_cls.get_session_token_key() in flask.session:
            flask.session.pop(user_cls.get_session_token_key())

        # Notify the user that their account is locked out
        flask.session['_flashes'] = []

        lockout = flask.current_app.config[f'{prefix}_FAILED_SIGN_IN_LOCKOUT']
        minutes = round(lockout.total_seconds() / 60)

        flask.flash(
            'Your account is locked due to too many failed attempts to change '
            f'your password, please try again in {minutes} minutes.',
            'error'
        )

        return flask.redirect(
            flask.url_for(state.manage_config.get_endpoint('sign_in'))
        )

@security_chains.link
def change_password(state):
    """Change the current user's password"""
    env = flask.current_app.jinja_env
    template_path = os.path.join(
        state.manage_config.template_path,
        'emails/password_changed.html'
    )
    user_cls = state.manage_config.frame_cls
    user = getattr(flask.g, user_cls.get_g_key())

    # Change the password
    user.logged_update(
        user,
        {'password': state.form.data['new_password']}
    )

    # Force a change of session token
    user.sign_in(force_new_token=True)
    flask.session[user_cls.get_session_token_key()] = user.session_token

    # Notify the user by email that their password was just changed
    flask.current_app.manage.send_email(
        [user.email],
        'Your password has been changed',
        template_path,
        global_vars={
            'user': user.to_json_type()
        },
        template_map={
            'password_changed': env.loader.get_source(
                env,
                'manhattan/users/emails/password_changed.html'
            )[0],
            template_path: env.loader.get_source(env, template_path)[0]
        }
    )

    # Notify the user that their new password has been set
    flask.flash('New password set.')

@security_chains.link
def get_sessions(state):
    """Get a list of the current user's sessions"""
    user_cls = state.manage_config.frame_cls
    user = getattr(flask.g, user_cls.get_g_key())

    state.user_sessions = user_cls.get_session_cls().many(
        Q.user == user,
        sort=SortBy(Q.last_accessed.desc)
    )
