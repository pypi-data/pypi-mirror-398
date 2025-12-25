"""
Disable multi-factor authentication (MFA) for the user.
"""

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.forms import BaseForm, fields, validators
from manhattan.manage.views import factories, utils
from manhattan.nav import NavItem

__all__ = ['disable_chains']


# Utils

def is_blocked(user):
    """
    Return true if the user is temporarily blocked from authorizing due to too
    many failed attempts.
    """
    prefix = user.get_settings_prefix()
    cache = flask.current_app.config[f'{prefix}_MFA_FAILED_AUTH_CACHE']
    key = f'mfa_failed_disable:{user._id}'

    max_attempts = flask\
        .current_app\
        .config[f'{prefix}_MFA_MAX_FAILED_AUTH_ATTEMPTS']

    return (cache.get(key) or 0) >= max_attempts


# Forms

class DisableForm(BaseForm):

    current_password = fields.PasswordField(
        'Password',
        [validators.Required()]
    )

    def validate_current_password(form, field):
        """
        The user must specify their existing password to disable multi-factor
        authentication.
        """

        if not field.data:
            return

        # Check that the user has not been blocked due to too many failed
        # attempts.
        if is_blocked(form.obj):
            raise validators.ValidationError('To many failed attempts.')

        if not form.obj.password_eq(field.data):
            raise validators.ValidationError('Password is incorrect.')


# Chains
disable_chains = ChainMgr()

# GET
disable_chains['get'] = Chain([
    'config',
    'authenticate',
    'mfa_authenticate_scoped_session',
    'init_form',
    'decorate',
    'render_template'
])

# POST
disable_chains['post'] = Chain([
    'config',
    'authenticate',
    'mfa_authenticate_scoped_session',
    'init_form',
    'validate',
    [
        [
            'disable_mfa',
            'mfa_end_scoped_session',
            'redirect'
        ], [
            'log_failed_attempts',
            'decorate',
            'render_template'
        ]
    ]
])

# Define the links
disable_chains.set_link(
    factories.config(
        form_cls=DisableForm,
        open_user_nav=True
    )
)
disable_chains.set_link(factories.authenticate())
disable_chains.set_link(factories.mfa_authenticate_scoped_session())
disable_chains.set_link(factories.mfa_end_scoped_session())
disable_chains.set_link(factories.validate())
disable_chains.set_link(factories.redirect('security'))
disable_chains.set_link(factories.render_template('mfa/disable.html'))

@disable_chains.link
def decorate(state):
    state.decor = utils.base_decor(state.manage_config, 'mfa_disable')
    state.decor['title'] = 'Disable two factor authentication'

    state.decor['breadcrumbs'].add(
        NavItem('Security', state.manage_config.get_endpoint('security'))
    )
    state.decor['breadcrumbs'].add(
        NavItem('Disable twp factor authentication', '')
    )

@disable_chains.link
def init_form(state):
    user_cls = state.manage_config.frame_cls

    # Initialize the form
    state.form = state.form_cls(
        flask.request.form,
        obj=getattr(flask.g, user_cls.get_g_key())
    )

    # Store the user class against the form
    state.form._user_cls = user_cls

@disable_chains.link
def log_failed_attempts(state):
    """Log a failed attempt to disable MFA"""

    if not state.form.current_password.data:
        # Don't log failed attempts if no password was provided
        return

    user_cls = state.manage_config.frame_cls
    prefix = user_cls.get_settings_prefix()
    user = getattr(flask.g, user_cls.get_g_key())
    cache = flask.current_app.config[f'{prefix}_MFA_FAILED_AUTH_CACHE']
    attempt_key = f'mfa_failed_disable:{user._id}'
    attempts = cache.get(attempt_key) or 0
    lockout = flask.current_app.config[f'{prefix}_FAILED_SIGN_IN_LOCKOUT']

    # Record the failed attempt
    cache.set(attempt_key, attempts + 1, lockout)

    if is_blocked(user):

        # Notify the user that they are temporarily blocked from
        # authorizing.
        flask.session['_flashes'] = []
        minutes = round(lockout.total_seconds() / 60)

        flask.flash(
            f'To too many failed attempts. Please wait {minutes} minutes '
            'before trying again.',
            'error'
        )

@disable_chains.link
def disable_mfa(state):
    """Disable multi-factor authentication for the user"""
    user_cls = state.manage_config.frame_cls
    user = getattr(flask.g, user_cls.get_g_key())

    # Disable MFA for the user
    user.logged_update(
        user,
        {
            'mfa_enabled': False,
            'mfa_otp_secret': None,
            'mfa_recovery_codes': None
        },
        'mfa_enabled',
        'mfa_otp_secret',
        'mfa_recovery_codes',
        'modified'
    )

    current_session = user.current_session
    current_session.mfa_authorized = None
    current_session.update('mfa_authorized')

    # Notify the user the MFA has been disabled
    flask.flash('Two factor authentication disabled')
