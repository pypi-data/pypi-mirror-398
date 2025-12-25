"""
Remove a lock from a user.
"""

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.manage.views import factories, generic

__all__ = ['remove_lock_chains']


# Chains
remove_lock_chains = ChainMgr()

# POST
remove_lock_chains['post'] = Chain([
    'config',
    'authenticate',
    'get_document',
    'remove_lockout',
    'redirect'
])

# Define the links
remove_lock_chains.set_link(factories.config(projection={'email': True}))
remove_lock_chains.set_link(factories.authenticate())
remove_lock_chains.set_link(factories.get_document())
remove_lock_chains.set_link(factories.redirect('view', include_id=True))

@remove_lock_chains.link
def remove_lockout(state):
    user_cls = state.manage_config.frame_cls
    user = state[state.manage_config.var_name]
    prefix = user_cls.get_settings_prefix()

    cache = flask.current_app.config[f'{prefix}_FAILED_SIGN_IN_CACHE']
    cache.delete(user_cls.get_sign_in_attempt_key(user.email))

    flask.flash('Lock removed')
