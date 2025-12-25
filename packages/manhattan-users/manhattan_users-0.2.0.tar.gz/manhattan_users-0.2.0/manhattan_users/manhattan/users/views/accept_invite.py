"""
Allow users to accept an invite to join the application.
"""

from datetime import datetime

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.comparable.change_log import ChangeLogEntry
from manhattan.forms import BaseForm, fields, validators
from manhattan.manage.views import factories, utils
from manhattan.users.utils import apply_password_rules, password_validator
from mongoframes import Q

__all__ = ['accept_invite_chains']


# Forms

class AcceptInviteForm(BaseForm):

    token = fields.HiddenField()

    email = fields.StringField(
        'Email',
        render_kw={'autocomplete': 'username'}
    )

    password = fields.PasswordField(
        'Password',
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

    def validate_password(form, field):

        if form.obj.email.lower() in field.data.lower():
            raise validators.ValidationError(
                'Your password cannot contain your email address.'
            )


# Chains
accept_invite_chains = ChainMgr()

# GET
accept_invite_chains['get'] = Chain([
    'config',
    'get_user',
    'init_form',
    'apply_password_rules',
    'decorate',
    'render_template'
])

# POST
accept_invite_chains['post'] = Chain([
    'config',
    'get_user',
    'init_form',
    'apply_password_rules',
    'validate',
    [
        [
            'accept_invite',
            'sign_in',
            'redirect'
        ], [
            'decorate',
            'render_template'
        ]
    ]
])

# Define the links
accept_invite_chains.set_link(factories.config(form_cls=AcceptInviteForm))
accept_invite_chains.set_link(factories.init_form())
accept_invite_chains.set_link(apply_password_rules())
accept_invite_chains.set_link(factories.validate())
accept_invite_chains.set_link(factories.render_template('accept_invite.html'))
accept_invite_chains.set_link(factories.redirect('dashboard'))

@accept_invite_chains.link
def decorate(state):
    state.decor = utils.base_decor(state.manage_config, 'accept_invite')
    state.decor['title'] = 'Accept invite'

@accept_invite_chains.link
def get_user(state):
    """Get the user who is accepting an invite base on the token"""
    user_cls = state.manage_config.frame_cls
    prefix = user_cls.get_settings_prefix()

    request_new_invite_url = flask.url_for(
        state.manage_config.get_endpoint('request_new_invite')
    )

    invite_token = flask.request.values.get('invite_token', '').strip()
    if not invite_token:

        # The token was provided, notify the user and redirect them to request
        # a new invite.
        flask.flash(
            'Not a valid invite link, no invite token provided.',
            'warning'
        )
        return flask.redirect(request_new_invite_url)

    # Get the user by their invite token
    user = user_cls.one(Q.invite_token == invite_token)
    state[state.manage_config.var_name] = user

    if not user:

        # No user found for the invite token, notify the user and redirect
        # them to request a new invite.
        flask.flash(
            'Not a valid invite link, the invite token does not exist.',
            'warning'
        )
        return flask.redirect(request_new_invite_url)

    ellapsed = datetime.utcnow() - user.invited
    if ellapsed > flask.current_app.config.get(f'{prefix}_INVITE_LIFESPAN'):

        # The invite has expired, notify the user and redirect them to request
        # a new invite.
        flask.flash(
            'It appears this invite has expired please request a new one.',
            'warning'
        )
        return flask.redirect(request_new_invite_url)

    if user_cls.is_locked_out(user.email):

        # The user is currently locked out for too many failed attempts to
        # sign-in, notify the user and redirect them to the accept invite page.
        lockout = flask.current_app.config[f'{prefix}_FAILED_SIGN_IN_LOCKOUT']
        minutes = round(lockout.total_seconds() / 60)
        flask.flash(
            'Your account is locked out due to too many failed sign '
            f'in attempts, please try again in {minutes} minutes.',
            'error'
        )
        return flask.redirect(flask.request.full_path)

@accept_invite_chains.link
def init_form(state):
    user = state[state.manage_config.var_name]

    # Initialize the form
    state.form = state.form_cls(flask.request.form, obj=user)

@accept_invite_chains.link
def accept_invite(state):
    """Accept an invite for a user"""
    user = state[state.manage_config.var_name]

    # Set the user's password
    user.password = state.form.data['password']
    user.update(
        'invite_accepted',
        'invited',
        'modified',
        'password_hash',
        'password_salt'
    )

    # Log the change
    entry = ChangeLogEntry({
        'type': 'NOTE',
        'documents': [user],
        'user': user
    })
    entry.add_note('Accepted invite')
    entry.insert()

    # Clear the invite token so the invite can't be used again
    state.manage_config.frame_cls.get_collection().update_one(
        {'_id': user._id},
        {'$unset': {'invite_token': ''}}
    )

@accept_invite_chains.link
def sign_in(state):
    """Sign the user in after they have accepted their invite"""
    user_cls = state.manage_config.frame_cls
    user = state[state.manage_config.var_name]

    if user_cls.is_locked_out(user.email):

        # If the user is currently locked out remove the lock so we can sign
        # them in.
        prefix = user_cls.get_settings_prefix()
        cache = flask.current_app.config[f'{prefix}_FAILED_SIGN_IN_CACHE']
        cache.delete(user_cls.get_sign_in_attempt_key(user.email))

    user.sign_in()
    flask.session[user_cls.get_session_token_key()] = user.session_token
