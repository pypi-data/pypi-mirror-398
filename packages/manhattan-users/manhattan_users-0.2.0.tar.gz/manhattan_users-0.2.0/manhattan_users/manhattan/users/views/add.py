"""
Add a user.
"""

from datetime import datetime
import os

import flask
from manhattan.formatters.flask import path_to_url
from manhattan.forms import BaseForm, fields, validators
from manhattan.manage.views import factories, generic
from manhattan.secure import random_token
from mongoframes import Q

__all__ = ['add_chains']


# Forms

class AddForm(BaseForm):

    first_name = fields.StringField(
        'First name',
        validators=[
            validators.Required(),
            validators.Length(max=20)
            ]
        )

    last_name = fields.StringField(
        'Last name',
        validators=[
            validators.Required(),
            validators.Length(max=20)
            ]
        )

    email = fields.StringField(
        'Email',
        validators=[
            validators.Required(),
            validators.Email(),
            validators.Length(max=80)
            ]
        )

    def validate_email(form, field):
        """Validate email is unique"""
        user_cls = form._user_cls
        user = user_cls.one(
            Q.email_lower == field.data.lower(),
            projection={'_id': True}
        )

        if user:
            raise validators.ValidationError(
                'This email address is already registered.'
            )


# Chains
add_chains = generic.add.copy()
add_chains['post'].insert_link('add_document', 'invite', after=True)

# Factory overrides
add_chains.set_link(factories.config(form_cls=AddForm))

# Custom overrides

@add_chains.link
def init_form(state):
    generic.add['get'].super(state)

    # Store the user class against the form
    state.form._user_cls = state.manage_config.frame_cls

@add_chains.link
def invite(state):
    """
    Create an invite link for the user and send them an email containing the
    link.
    """

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
