"""
View a user's activity log (the change log entries they are responsible for).
"""

from datetime import datetime, time
from urllib.parse import urlencode

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.comparable.change_log import ChangeLogEntry
from manhattan.forms import BaseForm, fields, validators
from manhattan.manage.views import factories, generic, utils
from manhattan.nav import Nav, NavItem
from mongoframes import And, InvalidPage, Paginator, Q, SortBy

__all__ = ['activity_log_chains']


# Forms


class Filters(BaseForm):

    _inline = True

    from_date = fields.DateField(
        'From',
        render_kw={
            'data-mh-date-picker': True,
            'placeholder': '1 Jan 2000'
        }
    )

    to_date = fields.DateField(
        'To',
        render_kw={
            'data-mh-date-picker': True,
            'placeholder': '1 Jan 2000'
        }
    )

    def filter_from_date(filter_form, form, field):
        if field.data:
            return Q.created >= datetime.combine(field.data, time.min)

    def filter_to_date(filter_form, form, field):
        if field.data:
            return Q.created <= datetime.combine(field.data, time.max)


class ListForm(BaseForm):

    _info = {'show_search_button': True}

    page = fields.IntegerField('Page', default=1)

    filters = fields.FormField(Filters)


# Chains
activity_log_chains = ChainMgr()

# GET
activity_log_chains['get'] = Chain([
    'config',
    'authenticate',
    'get_document',
    'init_form',
    'validate',
    'filter',
    'related_filter',
    'paginate',
    'form_info',
    'decorate',
    'render_template'
])

# Define the links
activity_log_chains.set_link(
    factories.config(
        change_log_cls=ChangeLogEntry,
        collation=None,
        form_cls=ListForm,
        hint=None,
        orphans=2,
        per_page=20,
        projection=None
    )
)
activity_log_chains.set_link(factories.authenticate())
activity_log_chains.set_link(factories.get_document())
activity_log_chains.set_link(generic.list['get'].get_link('validate'))
activity_log_chains.set_link(generic.list['get'].get_link('filter'))
activity_log_chains.set_link(generic.list['get'].get_link('form_info'))
activity_log_chains.set_link(factories.render_template('activity_log.html'))

@activity_log_chains.link
def decorate(state):

    document = state[state.manage_config.var_name]

    state.decor = utils.base_decor(
        state.manage_config,
        state.view_type,
        document
    )

    # Title
    state.decor['title'] = state.manage_config.titleize(document)

    # Breadcrumbs
    if Nav.exists(state.manage_config.get_endpoint('list')):
        state.decor['breadcrumbs'].add(
            utils.create_breadcrumb(state.manage_config, 'list')
        )

    if Nav.exists(state.manage_config.get_endpoint('view')):
        state.decor['breadcrumbs'].add(
            utils.create_breadcrumb(state.manage_config, 'view', document)
        )

    state.decor['breadcrumbs'].add(NavItem('Activity log'))

@activity_log_chains.link
def init_form(state):
    # Ensure the form class has a hidden field to indicate which document the
    # change log should relate to.

    if hasattr(state.form_cls, state.manage_config.var_name):
        form_cls = state.form_cls

    else:
        class form_cls(state.form_cls):
            pass

        setattr(form_cls, state.manage_config.var_name, fields.HiddenField())

    # Initialize the form
    state.form = form_cls(
        flask.request.args or None
    )

@activity_log_chains.link
def related_filter(state):
    document = state[state.manage_config.var_name]

    # Filter the results by which user made the change
    if state.query:
        state.query = And(state.query, Q.user == document._id)
    else:
        state.query = Q.user == document._id

@activity_log_chains.link
def paginate(state):

    # Select the documents in paginated form
    paginator_kw = {
        'per_page': state.per_page,
        'orphans': state.orphans,
        'sort': SortBy(Q.created.desc)
    }

    if state.projection :
        paginator_kw['projection'] = state.projection

    if state.collation:
        paginator_kw['collation'] = state.collation

    if state.hint:
        paginator_kw['hint'] = state.hint

    # Select the documents in paginated form
    state.paginator = Paginator(
        state.change_log_cls,
        state.query or {},
        **paginator_kw
        )

    # Select the requested page
    try:
        state.page = state.paginator[state.form.data.get('page', 1)]
    except InvalidPage:
        return flask.redirect(flask.url_for(flask.request.url_rule.endpoint))
