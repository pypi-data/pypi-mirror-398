"""
Generic change log document chain.

: `projection`
    The projection used when requesting the document from the database (defaults
    to None which means the detault projection for the frame class will be
    used).

: `orphans`
    The maximum number of orphan that can be merged into the last page of
    results (the orphans will form the last page) (defaults to 2).

: `per_page`
    The number of results that will appear per page (defaults to 30).

"""

import bson
from urllib.parse import urlencode

import flask
from manhattan.chains import Chain, ChainMgr
from mongoframes import And, InvalidPage, Paginator, Q, SortBy
from manhattan.forms import BaseForm, fields
from manhattan.nav import Nav, NavItem

from . import factories, utils

__all__ = ['change_log_chains']


class ListForm(BaseForm):

    _info = {}

    page = fields.IntegerField('Page', default=1)


# Define the chains
change_log_chains = ChainMgr()

# GET
change_log_chains['get'] = Chain([
    'config',
    'authenticate',
    'get_document',
    'init_form',
    'validate',
    'related_filter',
    'paginate',
    'form_info',
    'decorate',
    'render_template'
    ])


# Define the links
change_log_chains.set_link(
    factories.config(
        form_cls=ListForm,
        orphans=2,
        per_page=20,
        projection=None
    )
)
change_log_chains.set_link(factories.authenticate())
change_log_chains.set_link(factories.get_document())
change_log_chains.set_link(factories.render_template('change_log.html'))


@change_log_chains.link
def decorate(state):
    """
    Add decor information to the state (see `utils.base_decor` for further
    details on what information the `decor` dictionary consists of).

    This link adds a `decor` key to the state.
    """
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

    else:
        if Nav.exists(state.manage_config.get_endpoint('update')):
            state.decor['breadcrumbs'].add(
                utils.create_breadcrumb(
                    state.manage_config,
                    'update',
                    document
                )
            )

    state.decor['breadcrumbs'].add(NavItem('Change log'))

@change_log_chains.link
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

@change_log_chains.link
def related_filter(state):
    """
    Apply a query that filters the results to show changes to the given
    document.

    This link adds `query` to the state.
    """

    # Get the document
    document = state[state.manage_config.var_name]

    # Apply the query
    if state.query:
        state.query = And(state.query, Q.documents == document._id)
    else:
        state.query = Q.documents == document._id

@change_log_chains.link
def form_info(state):
    """
    This link adds information about the form to the `state.form` instance
    (against `_info`, e.g `state.form._info`):

    - `paging_query_string` a URL that can be used to retain the form's state
      when navigating between pages.

    NOTE: We store information against `_info` (prefixing wth the an underscore)
    because it prevents potential name clashes with fields that might be defined
    against the form, further for the most part filter forms are generated using
    a template macro which is aware of/expects this attribute and so we
    typcially don't expect developers to interact with this information
    directly.
    """

    if not state.form:
        return

    # Build the form information
    form_info = {}

    # Generate a paging URL for the form
    document = state[state.manage_config.var_name]
    params = {state.manage_config.var_name: [document._id]}
    form_info['paging_params'] = params
    form_info['paging_query_string'] = urlencode(params, True)

    # Predefined form information overrides information defined by the link
    if getattr(state.form, '_info', None):
        form_info.update(state.form._info)

    # Add the form information to the form
    state.form._info = form_info

@change_log_chains.link
def paginate(state):
    """
    Select a paginated list of change log entries from the database.

    This link adds `page` and `paginator` keys to the state containing the
    the paged results and the document paginator.
    """

    assert hasattr(state.manage_config.frame_cls, '_change_log_cls'), \
            'The target class does not support a change log'

    # Select the documents in paginated form
    per_page = min(
        state.form.data.get('per_page', '') or state.per_page,
        state.max_per_page or 100
    )
    if state.form.errors:
        per_page = state.per_page

    # Select the documents in paginated form
    paginator_kw = {
        'per_page': per_page,
        'orphans': state.orphans,
        'sort': SortBy(Q.created.desc)
    }

    if state.projection :
        paginator_kw['projection'] = state.projection

    if state.sort_by:
        paginator_kw['sort'] = state.sort_by

    # Select the documents in paginated form
    state.paginator = Paginator(
        state.manage_config.frame_cls._change_log_cls,
        state.query or {},
        **paginator_kw
        )

    # Select the requested page
    try:
        state.page = state.paginator[state.form.data.get('page', 1)]
    except InvalidPage:
        return flask.redirect(flask.url_for(flask.request.url_rule.endpoint))

@change_log_chains.link
def validate(state):
    """Validate the filter form"""
    if not state.form.validate():
        flask.flash('Invalid page or search request', 'error')
