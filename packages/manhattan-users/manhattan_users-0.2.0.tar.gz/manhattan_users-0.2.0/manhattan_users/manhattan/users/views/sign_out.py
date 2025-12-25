"""
Sign the current user out.
"""

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.manage.views import factories

__all__ = ['sign_out_chains']


# Chains
sign_out_chains = ChainMgr()

# GET
sign_out_chains['get'] = Chain([
    'config',
    'sign_out',
    'redirect'
])

# Define the links
sign_out_chains.set_link(factories.config())
sign_out_chains.set_link(factories.redirect('sign_in'))

@sign_out_chains.link
def sign_out(state):
    user_cls = state.manage_config.frame_cls
    user = getattr(flask.g, user_cls.get_g_key(), None)

    # Clear the user's session token
    if user:
        user_cls.get_collection().update_one(
            {'_id': user._id},
            {'$unset': {'session_token': ''}}
        )

    # Clear the session token from the the flask session
    if user_cls.get_session_token_key() in flask.session:
        flask.session.pop(user_cls.get_session_token_key())
