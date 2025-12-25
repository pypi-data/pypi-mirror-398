"""
Placeholder dashboard view.
"""

from manhattan.chains import Chain, ChainMgr
from manhattan.manage.views import factories, utils
from manhattan.nav import Nav, NavItem

__all__ = ['dashboard_chains']


# Chains
dashboard_chains = ChainMgr()

# GET
dashboard_chains['get'] = Chain([
    'authenticate',
    'decorate',
    'render_template'
])

# Define the links
dashboard_chains.set_link(factories.authenticate())
dashboard_chains.set_link(factories.render_template('dashboard.html'))

@dashboard_chains.link
def decorate(state):
    state.decor = utils.base_decor(state.manage_config, 'dashboard')
    state.decor['title'] = 'Dashboard'
    state.decor['breadcrumbs'].add(NavItem('Dashboard', ''))
