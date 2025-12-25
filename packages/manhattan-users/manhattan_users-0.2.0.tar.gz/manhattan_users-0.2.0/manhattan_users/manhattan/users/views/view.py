"""
View a user.
"""

from manhattan.manage.views import factories, generic
from manhattan.nav import NavItem
from mongoframes import Q, SortBy

__all__ = ['view_chains']


# Chains
view_chains = generic.view.copy()
view_chains['get'].insert_link('get_document', 'get_sessions', after=True)

# Custom overrides

@view_chains.link
def decorate(state):
    generic.view.chains['get'].get_link('decorate')(state)

    # Actions
    user_cls = state.manage_config.frame_cls
    user = state[state.manage_config.var_name]

    if not user.invite_accepted:

        # Reinvite
        state.decor['actions'].add(
            NavItem(
                'Re-invite',
                fixed_url='#resend-invite',
                data={'data-mh-submit-by-proxy': '#resend-invite-form'}
            ),
            index=0
        )

    if user_cls.is_locked_out(user.email):

        # Remove lockout
        state.decor['actions'].add(
            NavItem(
                'Remove lock',
                fixed_url='#remove-lock',
                data={'data-mh-submit-by-proxy': '#remove-lock-form'}
            ),
            index=0
        )

@view_chains.link
def get_sessions(state):
    """Get a list of sessions for the user"""

    user_cls = state.manage_config.frame_cls
    user = state[state.manage_config.var_name]

    state.user_sessions = user_cls.get_session_cls().many(
        Q.user == user,
        sort=SortBy(Q.last_accessed.desc)
    )

