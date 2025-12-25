"""
Allow a user to update their profile.
"""

import os

import flask
from manhattan.assets.fields import AssetField
from manhattan.chains import Chain, ChainMgr
from manhattan.forms import BaseForm, fields, validators
from manhattan.manage.views import factories, utils
from manhattan.nav import NavItem
from mongoframes import Q

__all__ = ['update_my_profile_chains']


# Forms

class UpdateMyProfileForm(BaseForm):

    first_name = fields.StringField(
        'First name',
        [
            validators.Required(),
            validators.Length(max=20)
        ])

    last_name = fields.StringField(
        'Last name',
        [
            validators.Required(),
            validators.Length(max=20)
        ])

    email = fields.StringField(
        'Email',
        [
            validators.Required(),
            validators.Email(),
            validators.Length(max=254)
        ])

    def validate_email(form, field):
        """Validate any new email address is unique"""
        user_cls = form._user_cls

        # The email address can stay the same for the user (irrespective of
        # case).
        if field.data.lower() == form.obj.email_lower:
            return

        user = user_cls.one(
            Q.email_lower == field.data.lower(),
            projection={'_id': True}
        )
        if user:
            raise validators.ValidationError(
                'This email address is already registered.'
            )


# Chains
update_my_profile_chains = ChainMgr()

# GET
update_my_profile_chains['get'] = Chain([
    'config',
    'authenticate',
    'init_form',
    'decorate',
    'render_template'
])

# POST
update_my_profile_chains['post'] = Chain([
    'config',
    'authenticate',
    'init_form',
    'validate',
    [
        [
            'update_profile',
            'redirect'
        ], [
            'decorate',
            'render_template'
        ]
    ]
])

# Define the links
update_my_profile_chains.set_link(
    factories.config(
        form_cls=UpdateMyProfileForm,
        open_user_nav=True
    )
)
update_my_profile_chains.set_link(factories.authenticate())
update_my_profile_chains.set_link(factories.validate())
update_my_profile_chains.set_link(
    factories.render_template('update_my_profile.html'))
update_my_profile_chains.set_link(factories.redirect('update_my_profile'))

@update_my_profile_chains.link
def decorate(state):
    state.decor = utils.base_decor(state.manage_config, 'update_my_profile')
    state.decor['title'] = 'Update my profile'
    state.decor['breadcrumbs'].add(NavItem('Update my profile', ''))

@update_my_profile_chains.link
def init_form(state):
    user_cls = state.manage_config.frame_cls

    # Initialize the form
    state.form = state.form_cls(
        flask.request.form,
        obj=getattr(flask.g, user_cls.get_g_key())
    )

    # Store the user class against the form
    state.form._user_cls = user_cls

@update_my_profile_chains.link
def update_profile(state):
    user_cls = state.manage_config.frame_cls
    user = getattr(flask.g, user_cls.get_g_key())

    # Update the user's profile (capture the email before hand to determine if
    # it's been changed).
    original_email = user.email

    # Build a dictionary of form data excluding fields that contain assets as
    # these would be managed by the addition of a `store_assets` link.
    form_data = {}
    for k, v in state.form.data.items():
        if k in state.form and isinstance(state.form[k], (AssetField)):
            continue
        form_data[k] = v

    user.logged_update(user, form_data)

    if original_email.lower() != user.email.lower():

        env = flask.current_app.jinja_env
        template_path = os.path.join(
            state.manage_config.template_path,
            'emails/email_changed.html'
        )

        # The user's email address has changed email both the original and new
        # email addresses notifying the user of the change.
        flask.current_app.manage.send_email(
            [user.email, original_email],
            'Your email address has been changed',
            template_path,
            global_vars={
                'user': user.to_json_type(),
                'original_email': original_email
            },
            template_map={
                'email_changed': env.loader.get_source(
                    env,
                    'manhattan/users/emails/email_changed.html'
                )[0],
                template_path: env.loader.get_source(env, template_path)[0]
            }
        )

    # Notify the user that their profile has been updated
    flask.flash('Profile updates made.')
