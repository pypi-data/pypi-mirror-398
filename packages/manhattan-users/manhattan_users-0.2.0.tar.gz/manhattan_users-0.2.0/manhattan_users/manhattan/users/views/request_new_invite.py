"""
Allow users to request a new invite.
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

__all__ = ['request_new_invite_chains']


# Forms

class RequestNewInviteForm(BaseForm):

    email = fields.StringField(
        'Email',
        [
            validators.Required(),
            validators.Email(),
            validators.Length(max=254)
        ]
    )


# Chains
request_new_invite_chains = ChainMgr()

# GET
request_new_invite_chains['get'] = Chain([
    'config',
    'init_form',
    'decorate',
    'render_template'
    ])

# POST
request_new_invite_chains['post'] = Chain([
    'config',
    'init_form',
    'validate',
    [
        [
            'get_user',
            'limit_rate',
            'send_new_invite',
            'redirect'
        ], [
            'decorate',
            'render_template'
        ]
    ]
])

# Define the links
request_new_invite_chains.set_link(
    factories.config(form_cls=RequestNewInviteForm)
)
request_new_invite_chains.set_link(factories.validate())
request_new_invite_chains.set_link(
    factories.render_template('request_new_invite.html')
)
request_new_invite_chains.set_link(factories.redirect('request_new_invite'))

@request_new_invite_chains.link
def decorate(state):
    state.decor = utils.base_decor(state.manage_config, 'request_new_invite')
    state.decor['title'] = 'Request new invite'

@request_new_invite_chains.link
def init_form(state):
    # Initialize the form
    state.form = state.form_cls(flask.request.form)

    # Store the user class against the form
    state.form._user_cls = state.manage_config.frame_cls

@request_new_invite_chains.link
def get_user(state):
    """Get the user to send a new invite to"""
    user_cls = state.manage_config.frame_cls
    user = user_cls.one(Q.email_lower == state.form.data['email'].lower())
    state[state.manage_config.var_name] = user

    if not user or user.invite_accepted:
        # If we couldn't find a user based on the email address the user gave
        # then we don't indicate this to the user as this can be exploited to
        # determine registered email addresses.
        flask.flash('A new invite has been emailed to you.')

        # Redirect the user back to the request new invite page
        return flask.redirect(
            flask.url_for(
                state.manage_config.get_endpoint('request_new_invite')
            )
        )

@request_new_invite_chains.link
def limit_rate(state):
    """Limit the number of reset requests a user can make to once a minute"""
    user = state[state.manage_config.var_name]

    if user.invited is None:
        # User doesn't have an invite pending no need to rate limit
        return

    if (datetime.utcnow() - user.invited).total_seconds() < 60:

        # Let the user know an email has been sent to them but don't send one
        # as we did only 60 seconds ago.
        #
        # NOTE: We used to flag to users that they should wait but this can be
        # exploited to determine registered email addresses and so we no
        # longer provide this feedback.
        #
        flask.flash('A new invite has been emailed to you.')

        # Redirect the user back to the request new invite page
        return flask.redirect(
            flask.url_for(
                state.manage_config.get_endpoint('request_new_invite')
            )
        )

@request_new_invite_chains.link
def send_new_invite(state):
    """Send the user a new invite"""

    env = flask.current_app.jinja_env
    template_path = os.path.join(
        state.manage_config.template_path,
        'emails/invite.html'
    )
    user = state[state.manage_config.var_name]

    # Assign the user an invite token
    user.invited = datetime.utcnow()
    user.invite_token = random_token()
    user.update('invited', 'invite_token')

    # Send the user an invite by email
    flask.current_app.manage.send_email(
        [user.email],
        'Your invite',
        template_path,
        global_vars={
            'user': user.to_json_type(),
            'invite_link': path_to_url(
                flask.url_for(
                    state.manage_config.get_endpoint('accept_invite'),
                    invite_token=user.invite_token
                )
            )
        },
        template_map={
            'invite': env.loader.get_source(
                env,
                'manhattan/users/emails/invite.html'
            )[0],
            template_path: env.loader.get_source(env, template_path)[0]
        }
    )

    # Let the user know to expect an email containing their reset password
    # instructions.
    flask.flash('A new invite has been emailed to you.')
