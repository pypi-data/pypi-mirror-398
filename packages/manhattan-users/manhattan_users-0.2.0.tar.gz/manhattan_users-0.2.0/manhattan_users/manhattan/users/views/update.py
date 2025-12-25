"""
Update a user.
"""

import flask
from manhattan.forms import fields, validators
from manhattan.manage.views import factories, generic
from manhattan.users.utils import apply_password_rules, password_validator
from manhattan.users.views.add import AddForm
from mongoframes import Q

__all__ = ['update_chains']


# Forms

class UpdateForm(AddForm):

    new_password = fields.PasswordField(
        'Password',
        validators=[
            password_validator,
            validators.EqualTo('confirm_password', "Passwords don't match")
        ]
    )

    confirm_password = fields.PasswordField('Confirm password')

    def validate_email(form, field):
        """Validate email is unique"""
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
update_chains = generic.update.copy()
update_chains.insert_link('init_form', 'apply_password_rules', after=True)

# Factory overrides
update_chains.set_link(
    factories.config(
        form_cls=UpdateForm,
        projection=None
    )
)
update_chains.set_link(apply_password_rules())

# Custom overrides

@update_chains.link
def init_form(state):
    # Initialize the form
    state.form = state.form_cls(
        flask.request.form,
        obj=state[state.manage_config.var_name]
    )

    # Store the user class against the form
    state.form._user_cls = state.manage_config.frame_cls

@update_chains.link
def build_form_data(state):
    # Switch the `new_password` field with password
    state.form_data = state.form.data
    state.form_data['password'] = state.form_data.pop('new_password')

@update_chains.link
def update_document(state):
    generic.update['get'].super(state)

    # If a new password has been set for the user sign them out
    if state.form_data.get('password'):
        state.manage_config.frame_cls.get_collection().update_one(
            {'_id': state[state.manage_config.var_name]._id},
            {'$unset': {'session_token': ''}}
        )
