"""
Revoke a user's session.
"""

import bson

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.manage.views import factories


__all__ = ['revoke_session_chains']


# Chains

revoke_session_chains = ChainMgr()

# POST
revoke_session_chains['post'] = Chain([
    'config',
    'authenticate',
    'get_session',
    'revoke_session',
    'redirect'
])

# Define the links
revoke_session_chains.set_link(factories.config())
revoke_session_chains.set_link(factories.authenticate())

@revoke_session_chains.link
def get_session(state):
    """Get the user's session"""

    user_cls = state.manage_config.frame_cls
    user_session_cls = user_cls.get_session_cls()

    # Attempt to convert the session Id to the required type
    user_session_id = flask.request.values.get('session')
    try:
        user_session_id = bson.objectid.ObjectId(user_session_id)
    except bson.errors.InvalidId:
        flask.abort(404)

    # Attempt to retrieve the document
    state.user_session = user_session_cls.by_id(user_session_id)
    if not state.user_session:
        flask.abort(404)

    # Find the user associated with the session
    user = user_cls.by_id(state.user_session.user)
    state[state.manage_config.var_name] = user

    # If the endpoint is `revoke_my_session` check that the user removing the
    # session is the one who's currently signed in.
    if flask.request.endpoint == 'revoke_my_session':
        if user != getattr(flask.g, user_cls.get_g_key()):
            flask.abort(403)

@revoke_session_chains.link
def revoke_session(state):
    """Revoke the session for the user"""

    # Remove the session
    state.user_session.delete()

    # Notify the user that the session has been revoked
    flask.flash('Session revoked')

@revoke_session_chains.link(name='redirect')
def _redirect(state):
    """Redirect the user depending on the endpoint used to call the view"""
    user = state[state.manage_config.var_name]

    if flask.request.endpoint.endswith('revoke_my_session'):
        return flask.redirect(
            flask.url_for(state.manage_config.get_endpoint('security'))
        )

    else:
        return flask.redirect(
            flask.url_for(
                state.manage_config.get_endpoint('view'),
                **{state.manage_config.var_name: user._id}
            )
        )
