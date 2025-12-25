"""
Allow users to sign-in.
"""

import os

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.forms import BaseForm, fields, validators
from manhattan.manage.views import factories, utils
from manhattan.secure import safe_redirect_url
from mongoframes import Q

__all__ = ['sign_in_chains']


# Forms

class SignInForm(BaseForm):

    next = fields.HiddenField()

    email = fields.StringField(
        'Email',
        [validators.Required()],
        render_kw={'autocomplete': 'username'}
    )

    password = fields.PasswordField(
        'Password',
        [validators.Required()],
        render_kw={'autocomplete': 'current-password'}
    )

    remember_me = fields.BooleanField('Remember me')

    def validate_email(form, field):
        """Validate the login details"""

        user_cls = form._user_cls

        if not field.data:
            return

        if not form.password.data:
            return

        # Check that the email has not been locked out for too many failed
        # attempts.
        if user_cls.is_locked_out(field.data):
            raise validators.ValidationError('To many failed attempts.')

        # Validate we can find the user
        user = user_cls.one(
            Q.email_lower == form.email.data.lower(),
            projection={
                'password_hash': True,
                'password_salt': True
            }
        )
        if not user:
            raise validators.ValidationError('Invalid email or password.')

        # Check the user has set a password
        if not user.password_hash:
            raise validators.ValidationError('Invalid email or password.')

        # Check the password matches
        if not user.password_eq(form.password.data):
            raise validators.ValidationError('Invalid email or password.')


# Chains

sign_in_chains = ChainMgr()

# GET
sign_in_chains['get'] = Chain([
    'config',
    'authenticate',
    'init_form',
    'decorate',
    'render_template'
])

# POST
sign_in_chains['post'] = Chain([
    'config',
    'authenticate',
    'init_form',
    'validate',
    [
        [
            'sign_in',
            'notify',
            'redirect'
        ],
        [
            'log_failed_attempts',
            'decorate',
            'render_template'
        ]
    ]
])

# Define the links
sign_in_chains.set_link(factories.config(form_cls=SignInForm))
sign_in_chains.set_link(factories.validate())
sign_in_chains.set_link(factories.render_template('sign_in.html'))

@sign_in_chains.link
def authenticate(state):
    user_cls = state.manage_config.frame_cls

    if flask.g.get(user_cls.get_g_key()) \
            and user_cls.get_session_token_key() in flask.session:

        # User is already logged in redirect them to the dashboard
        return flask.redirect(
            flask.url_for(state.manage_config.get_endpoint('dashboard'))
        )

@sign_in_chains.link
def decorate(state):
    state.decor = utils.base_decor(state.manage_config, 'sign_in')
    state.decor['title'] = 'Sign-in'

@sign_in_chains.link
def init_form(state):
    # Initialize the form
    state.form = state.form_cls(
        flask.request.form,
        next=flask.request.args.get('next', '')
    )

    # Store the user class against the form
    state.form._user_cls = state.manage_config.frame_cls

@sign_in_chains.link
def log_failed_attempts(state):
    """Log failed attempts"""
    user_cls = state.manage_config.frame_cls
    prefix = user_cls.get_settings_prefix()

    if not (state.form.email.data and state.form.password.data):
        # We only log an attempt as failed if both an email and password were
        # entered.
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

        # Notify the user that their account is locked out
        flask.session['_flashes'] = []

        lockout = flask.current_app.config[f'{prefix}_FAILED_SIGN_IN_LOCKOUT']
        minutes = round(lockout.total_seconds() / 60)

        flask.flash(
            'Your account is locked due to too many failed sign in '
            f'attempts, please try again in {minutes} minutes.',
            'error'
        )

        return flask.redirect(
            flask.url_for(state.manage_config.get_endpoint('sign_in'))
        )

@sign_in_chains.link
def sign_in(state):
    """
    Sign a user into the application.

    This link adds `user_session` (an instance of the users current session)
    and `new_session` (a flag indicating if the current session represents a
    new session (device)) to the state.
    """
    user_cls = state.manage_config.frame_cls

    # Sign the user in
    user = user_cls.one(
        Q.email_lower == state.form.data['email'].lower()
    )
    state[state.manage_config.var_name] = user
    user_session, new_session = user.sign_in()
    state.session = user_session
    state.new_session = new_session

    # Set the session token as a secure cookie
    flask.session[user_cls.get_session_token_key()] = user.session_token

    # If the user ticked the `remember_me` option then set the secure cookie
    # to be permenant (e.g to remain once the user closes their browser
    # client).
    if state.form.data['remember_me']:
        flask.session.permanent = True

@sign_in_chains.link
def notify(state):
    """
    Nofity the user if a new session (device) was registered when signing them
    in.
    """

    if state.new_session:

        env = flask.current_app.jinja_env
        template_path = os.path.join(
            state.manage_config.template_path,
            'emails/new_device.html'
        )
        user = state[state.manage_config.var_name]

        flask.current_app.manage.send_email(
            [user.email],
            'A new device was used to sign-in',
            template_path,
            global_vars={
                'user': user.to_json_type(),
                'user_session': state.session.to_json_type()
            },
            template_map={
                'new_device': env.loader.get_source(
                    env,
                    'manhattan/users/emails/new_device.html'
                )[0],
                template_path: env.loader.get_source(
                    env,
                    template_path
                )[0]
            }
        )

@sign_in_chains.link
def redirect(state):
    # Redirect the user to either the URL they were trying to get to or the
    # dashboard.

    next_url = safe_redirect_url(state.form.data['next'] or '')

    if not next_url:
        # If no valid next URL is provided redirect the user to the dashboard
        next_url = flask.url_for(
            state.manage_config.get_endpoint('dashboard')
        )

    return flask.redirect(next_url)
