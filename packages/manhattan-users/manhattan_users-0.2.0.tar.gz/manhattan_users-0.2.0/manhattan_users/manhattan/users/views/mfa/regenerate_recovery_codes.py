"""
Regenerate the user's list of recovery codes.
"""

import os

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.manage.views import factories, utils
from manhattan.nav import NavItem

__all__ = ['regenerate_recovery_codes_chains']


# Define the chains
regenerate_recovery_codes_chains = ChainMgr()

# POST
regenerate_recovery_codes_chains['get'] = Chain([
    'config',
    'authenticate',
    'mfa_authenticate_scoped_session',
    'decorate',
    'render_template'
])

# POST
regenerate_recovery_codes_chains['post'] = Chain([
    'config',
    'authenticate',
    'mfa_authenticate_scoped_session',
    'regenerate_recovery_codes',
    'mfa_end_scoped_session',
    'redirect'
])

regenerate_recovery_codes_chains.set_link(factories.config())
regenerate_recovery_codes_chains.set_link(factories.authenticate())
regenerate_recovery_codes_chains.set_link(
    factories.render_template('mfa/regenerate_recovery_codes.html')
)

@regenerate_recovery_codes_chains.link
def decorate(state):
    state.decor = utils.base_decor(state.manage_config, 'mfa_recovery_codes')
    state.decor['title'] = 'Regenerate recovery codes codes'

    # Breadcrumb
    state.decor['breadcrumbs'].add(
        NavItem('Security', state.manage_config.get_endpoint('security'))
    )
    state.decor['breadcrumbs'].add(
        NavItem(
            'Recovery codes',
            state.manage_config.get_endpoint('mfa_recovery_codes')
        )
    )
    state.decor['breadcrumbs'].add(NavItem('Regenerate', ''))

@regenerate_recovery_codes_chains.link
def regenerate_recovery_codes(state):
    env = flask.current_app.jinja_env
    template_path = os.path.join(
        state.manage_config.template_path,
        'emails/mfa_recovery_codes_regenerated.html'
    )
    user_cls = state.manage_config.frame_cls
    user = getattr(flask.g, user_cls.get_g_key())

    # Generate the new recovery codes
    codes, hashes, masks = state.manage_user.generate_mfa_recovery_codes()

    # Save the new recovery codes
    state.manage_user.logged_update(
        state.manage_user,
        {
            'mfa_recovery_code_hashes': hashes,
            'mfa_recovery_code_masks': masks
        },
        'mfa_recovery_code_hashes',
        'mfa_recovery_code_masks',
        'modified'
    )
    state.retrieve_token = user_cls.stow_mfa_recovery_codes(codes)

    # Notify the user by email that their password was just changed
    flask.current_app.manage.send_email(
        [user.email],
        'Your recovery codes have been regenerated',
        template_path,
        global_vars={
            'user': user.to_json_type()
        },
        template_map={
            'password_changed': env.loader.get_source(
                env,
                'manhattan/users/emails/mfa_recovery_codes_regenerated.html'
            )[0],
            template_path: env.loader.get_source(env, template_path)[0]
        }
    )

    # Notify the user that the recovery codes have been regenerated
    flask.flash('New recovery codes generated')

@regenerate_recovery_codes_chains.link
def redirect(state):

    return flask.redirect(
        flask.url_for(
            state.manage_config.get_endpoint('mfa_recovery_codes'),
            retrieve_key=state.retrieve_token
        )
    )
