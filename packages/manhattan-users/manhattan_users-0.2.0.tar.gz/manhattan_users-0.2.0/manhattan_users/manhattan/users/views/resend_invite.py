"""
Resend an invite to a user.
"""

from datetime import datetime
import os

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.formatters.flask import path_to_url
from manhattan.manage.views import factories
from manhattan.secure import random_token

__all__ = ['resend_invite_chains']


# Chains

resend_invite_chains = ChainMgr()

# POST
resend_invite_chains['post'] = Chain([
    'authenticate',
    'get_document',
    'resend_invite',
    'redirect'
])

# Define the links
resend_invite_chains.set_link(factories.authenticate())
resend_invite_chains.set_link(factories.get_document())
resend_invite_chains.set_link(factories.redirect('view', include_id=True))

@resend_invite_chains.link
def resend_invite(state):
    """Resend the user an invite"""
    env = flask.current_app.jinja_env
    template_path = os.path.join(
        state.manage_config.template_path,
        'emails/invite.html'
    )
    user = state[state.manage_config.var_name]

    # Generate the invite for the user
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

    # Notify the user that a new invite has been sent
    flask.flash('New invite sent.')
