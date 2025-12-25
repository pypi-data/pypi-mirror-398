"""
View the user's recovery codes.
"""

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.manage.views import factories, utils
from manhattan.nav import NavItem

__all__ = ['recovery_codes_chains']


# Chains
recovery_codes_chains = ChainMgr()

# POST
recovery_codes_chains['get'] = Chain([
    'config',
    'authenticate',
    'get_recovery_codes',
    'decorate',
    'render_template'
])

# Define the links
recovery_codes_chains.set_link(factories.config(open_user_nav=True))
recovery_codes_chains.set_link(factories.authenticate())
recovery_codes_chains.set_link(
    factories.render_template('mfa/recovery_codes.html')
)

@recovery_codes_chains.link
def decorate(state):
    state.decor = utils.base_decor(state.manage_config, 'mfa_recovery_codes')
    state.decor['title'] = 'Recovery codes'

    # Breadcrumb
    state.decor['breadcrumbs'].add(
        NavItem('Security', state.manage_config.get_endpoint('security'))
    )
    state.decor['breadcrumbs'].add(NavItem('Recovery codes', ''))

    # Actions

    if state.masked:

        state.decor['actions'].add(
            NavItem(
                'Regenerate',
                fixed_url='#regenerate-recovery-codes',
                data={
                    'data-mh-submit-by-proxy': '#regenerate-recovery-codes-form'
                }
            )
        )

    else:

        state.decor['actions'].add(
            NavItem(
                'Copy',
                fixed_url='#copy-recovery-codes',
                data={'data-mh-copy-to-clipboard': '[data-mh-recovery-codes]'}
            )
        )

@recovery_codes_chains.link
def get_recovery_codes(state):
    # Add the recovery codes to the state
    user_cls = state.manage_config.frame_cls
    user = getattr(flask.g, user_cls.get_g_key())

    retreieve_key = flask.request.args.get('retrieve_key')
    if retreieve_key:

        state.masked = False
        state.mfa_recovery_codes \
                = user_cls.retrieve_mfa_recovery_codes(retreieve_key)

    if not state.mfa_recovery_codes:
        state.mfa_recovery_codes = user.mfa_recovery_code_masks
        state.masked = True
