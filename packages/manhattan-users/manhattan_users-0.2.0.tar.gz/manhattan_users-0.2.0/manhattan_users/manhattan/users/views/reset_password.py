"""
Allow users to request a link to reset their password with.
"""

from datetime import datetime
import os

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.formatters.flask import path_to_url
from manhattan.forms import BaseForm, fields, validators
from manhattan.manage.views import factories, utils
from manhattan.secure import random_token
from mongoframes import Q

__all__ = ['reset_password_chains']


# Forms

class ResetPasswordForm(BaseForm):

    email = fields.StringField(
        'Email',
        [validators.Required(), validators.Email()]
    )


# Chains
reset_password_chains = ChainMgr()

# GET
reset_password_chains['get'] = Chain([
    'config',
    'init_form',
    'decorate',
    'render_template'
])

# POST
reset_password_chains['post'] = Chain([
    'config',
    'init_form',
    'validate',
    [
        [
            'get_user',
            'limit_rate',
            'send_reset_link',
            'redirect'
        ],
        [
            'decorate',
            'render_template'
        ]
    ]
])

# Define the links
reset_password_chains.set_link(factories.config(form_cls=ResetPasswordForm))
reset_password_chains.set_link(factories.validate())
reset_password_chains.set_link(
    factories.render_template('reset_password.html')
)
reset_password_chains.set_link(factories.redirect('reset_password'))

@reset_password_chains.link
def decorate(state):
    state.decor = utils.base_decor(state.manage_config, 'reset_password')
    state.decor['title'] = 'Reset password'

@reset_password_chains.link
def init_form(state):
    # Initialize the form
    state.form = state.form_cls(flask.request.form)

    # Store the user class against the form
    state.form._user_cls = state.manage_config.frame_cls

@reset_password_chains.link
def get_user(state):
    """Get the user to send a reset link to"""
    user_cls = state.manage_config.frame_cls
    user = user_cls.one(Q.email_lower == state.form.data['email'].lower())
    state[state.manage_config.var_name] = user

    if not user:
        # If we couldn't find a user based on the email address the user gave
        # then we don't indicate this to the user as this can be exploited to
        # determine registered email addresses.
        flask.flash(
            'Instructions on resetting your password have been emailed to you.'
        )

        # Redirect the user back to the reset password page
        return flask.redirect(
            flask.url_for(state.manage_config.get_endpoint('reset_password'))
        )

@reset_password_chains.link
def limit_rate(state):
    """Limit the number of reset requests a user can make to once a minute"""
    user = state[state.manage_config.var_name]

    if user.password_reset_requested is None:
        # No reset token set for the user no need to rate limit
        return

    last_request = user.password_reset_requested
    if (datetime.utcnow() - last_request).total_seconds() < 60:

        # Let the user know an email has been sent to them but don't send one
        # as we did only 60 seconds ago.
        #
        # NOTE: We used to flag to users that they should wait but this can be
        # exploited to determine registered email addresses and so we no
        # longer provide this feedback.
        #
        flask.flash(
            'Instructions on resetting your password have been emailed to you.'
        )

        # Redirect the user back to the reset password page
        return flask.redirect(
            flask.url_for(state.manage_config.get_endpoint('reset_password'))
        )

@reset_password_chains.link
def send_reset_link(state):
    """Send the user a reset password link"""

    env = flask.current_app.jinja_env
    template_path = os.path.join(
        state.manage_config.template_path,
        'emails/reset_password.html'
    )
    user = state[state.manage_config.var_name]

    # Generate the password reset token for the user
    user.password_reset_requested = datetime.utcnow()
    user.password_reset_token = random_token()
    user.update('password_reset_requested', 'password_reset_token')

    # Send the user a reset password link by email
    flask.current_app.manage.send_email(
        [user.email],
        'How to reset your password',
        template_path,
        global_vars={
            'user': user.to_json_type(),
            'reset_link':
                path_to_url(
                    flask.url_for(
                        state.manage_config.get_endpoint('set_new_password'),
                        reset_token=user.password_reset_token
                    )
                )
        },
        template_map={
            'reset_password': env.loader.get_source(
                env,
                'manhattan/users/emails/reset_password.html'
            )[0],
            template_path: env.loader.get_source(env, template_path)[0]
        }
    )

    # Let the user know to expect an email containing their reset password
    # instructions.
    flask.flash(
        'Instructions on resetting your password have been emailed to you.'
    )
