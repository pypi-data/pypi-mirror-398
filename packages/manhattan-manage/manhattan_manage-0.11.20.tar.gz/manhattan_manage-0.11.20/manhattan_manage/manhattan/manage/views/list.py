"""
Generic list document chain.

: `collation`
    The collation to use when querying for results.

: `form_cls`
    The form that will be used to control pagination and filtering of results
    (required).

: `hint`
    A hint to use when querying for results.

: `projection`
    The projection used when requesting results from the database (defaults to
    None which means the detault projection for the frame class will be used).

: `search_fields`
    A list of fields searched when matching the results (defaults to None which
    means no results are searched).

: `orphans`
    The maximum number of orphan that can be merged into the last page of
    results (the orphans will form the last page) (defaults to 2).

: `per_page`
    The number of results that will appear per page (defaults to 30).

"""

import re
from urllib.parse import urlencode

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.formatters.text import remove_accents, upper_first
from manhattan.nav import Nav, NavItem
from mongoframes import ASC, DESC, And, In, InvalidPage, Or, Paginator, Q

from . import factories, utils

__all__ = ['list_chains']


# Define the chains
list_chains = ChainMgr()

# GET
list_chains['get'] = Chain([
    'config',
    'authenticate',
    'init_form',
    'validate',
    'search',
    'filter',
    'sort',
    'paginate',
    'form_info',
    'decorate',
    'render_template'
])


# Define the links
list_chains.set_link(factories.config(
    collation=None,
    form_class=None,
    hint=None,
    projection=None,
    search_fields=None,
    orphans=2,
    per_page=20,
    max_per_page=100
))
list_chains.set_link(factories.authenticate())
list_chains.set_link(factories.init_form(populate_on=['GET']))
list_chains.set_link(factories.decorate('list'))
list_chains.set_link(factories.render_template('list.html'))


def results_action(config):
    """
    Return a function that will generate a link for a result in the listing
    (e.g if someone clicks on a result).
    """

    def results_action(document):

        # See if there's a view link...
        if Nav.exists(config.get_endpoint('view')):
            return Nav.query(
                config.get_endpoint('view'),
                **{config.var_name: document._id}
            )

        # ...else see if there's an update link...
        elif Nav.exists(config.get_endpoint('update')):
            return Nav.query(
                config.get_endpoint('update'),
                **{config.var_name: document._id}
            )

    return results_action

@list_chains.link
def decorate(state):
    """
    Add decor information to the state (see `utils.base_decor` for further
    details on what information the `decor` dictionary consists of).

    This link adds a `decor` key to the state.
    """
    state.decor = utils.base_decor(state.manage_config, state.view_type)

    # Title
    state.decor['title'] = upper_first(state.manage_config.name_plural)

    # Breadcrumbs
    state.decor['breadcrumbs'].add(NavItem(state.decor['title']))

    # Actions
    if Nav.exists(state.manage_config.get_endpoint('add')):
        state.decor['actions'].add(
            NavItem('Add', state.manage_config.get_endpoint('add'))
        )

    if Nav.exists(state.manage_config.get_endpoint('order')):
        state.decor['actions'].add(
            NavItem('Order', state.manage_config.get_endpoint('order'))
        )

    # Results action
    state.decor['results_action'] = results_action(state.manage_config)

@list_chains.link
def filter(state):
    """
    Apply any filters to the query.
    """

    # Check that there are filters to apply
    if not hasattr(state.form, 'filters'):
        return

    filter_conditions = []

    for filter_field in state.form.filters:

        # Get the name of the filter field against excluding the prefix
        based_field_name = filter_field.name.split('filters-', 1)[1]

        # Check for a custom filter handler
        custom_func_name = 'filter_' + based_field_name
        if hasattr(state.form.filters, custom_func_name):
            # Custom filter function exists so call it
            custom_func = getattr(state.form.filters, custom_func_name)
            condition = custom_func(state.form, filter_field)
            if condition:
                filter_conditions.append(condition)

        else:
            # No custom filter apply the default filter
            filter_value = filter_field.data

            # Build the conditions
            if filter_value is not None and filter_value != '':
                if isinstance(filter_value, list):
                    filter_conditions.append(
                            In(Q[based_field_name], filter_value))

                else:
                    filter_conditions.append(
                            Q[based_field_name] == filter_value)

    # Apply the filter conditions to the query
    if filter_conditions:
        if state.query:
            state.query = And(state.query, *filter_conditions)
        else:
            state.query = And(*filter_conditions)

@list_chains.link
def form_info(state):
    """
    This link adds information about the form to the `state.form` instance
    (against `_info`, e.g `state.form._info`):

    - `filters_applied` flags that at least one field in the filters form has
      been applied.
    - `paging_query_string` a URL that can be used to retain the form's state
      when navigating between pages.
    - `show_search_button` flags if there are any visible search fields in the
      form (excluding fields in the filters field form).

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

    # Check to see if any fields in the `filters` field form have been set
    form_info['filters_applied'] = False
    if hasattr(state.form, 'filters'):
        for field in state.form.filters:
            if field.data:
                form_info['filters_applied'] = True
                break

    # Generate a paging URL for the form
    paging_fields = [f for f in state.form if f.name not in {'filters', 'page'}]
    if hasattr(state.form, 'filters'):
        paging_fields += list(state.form.filters)

    # Check if any filter arguments have been submitted
    filters_applied = [
        f.name for f in paging_fields if f.name in flask.request.args
    ]
    if len(filters_applied):

        # Build params based on the request
        params = {f.name: f.raw_data for f in paging_fields if f.raw_data}

    else:

        # Build params based on the form defaults
        params = {f.name: f.default for f in paging_fields if f.default}

    form_info['paging_params'] = params
    form_info['paging_query_string'] = urlencode(params, True)

    # Determine if there are any visible fields in the form that are not part
    # of pagination, sorting of the (advanced) filter field.
    form_info['show_search_button'] = False
    none_search_fields = {'filters', 'page', 'per_page', 'sort_by'}
    for field in state.form:
        if field.type != 'HiddenField' and field.name not in none_search_fields:
            form_info['show_search_button'] = True
            break

    # Predefined form information overrides information defined by the link
    if getattr(state.form, '_info', None):
        form_info.update(state.form._info)

    # Add the form information to the form
    state.form._info = form_info

@list_chains.link
def validate(state):
    """Validate the filter form"""
    if not state.form.validate():
        flask.flash('Invalid page or search request', 'error')

@list_chains.link
def paginate(state):
    """
    Select a paginated list of documents from the database.

    This link adds `page` and `paginator` keys to the state containing the
    the paged results and the document paginator.
    """

    # Select the documents in paginated form
    per_page = min(
        state.form.data.get('per_page', '') or state.per_page,
        state.max_per_page or 100
    )
    if state.form.errors:
        per_page = state.per_page

    paginator_kw = {
        'per_page': per_page,
        'orphans': state.orphans
    }

    if state.projection :
        paginator_kw['projection'] = state.projection

    if state.sort_by:
        paginator_kw['sort'] = state.sort_by

    if state.collation:
        paginator_kw['collation'] = state.collation

    if state.hint:
        paginator_kw['hint'] = state.hint

    state.paginator = Paginator(
        state.manage_config.frame_cls,
        state.query or {},
        **paginator_kw
    )

    # Select the requested page
    try:
        state.page = state.paginator[state.form.data.get('page', 1)]
    except InvalidPage:
        return flask.abort(404, 'Page does not exists')

@list_chains.link
def search(state):
    """
    Build a database query based on the `q` parameter within the request to
    filter the paginated documents.

    This link adds the `query` key to the state containing the database query.
    """
    if 'query' not in state:
        state.query = None

    # If no query was provided then skip this step
    if 'q' not in state.form.data or not state.form.data['q']:
        return

    # Replace accented characters in the string with closest matching
    # equivalent non-accented characters.
    q = remove_accents(state.form.data['q'])

    # Make the query safe for regular expressions
    q = re.escape(q)

    # Build the query to search
    assert state.search_fields, 'No search fields defined'

    q_match = re.compile(q, re.I)
    conditions = []
    for field in state.search_fields:
        conditions.append(Q[field] == q_match)

    state.query = Or(*conditions)

@list_chains.link
def sort(state):
    """
    Build the sort operation to order the paginated documents.

    This link adds the `sort_by` key to the state containing the sort operation.
    """

    # If no sort field/direction was provided then skip this step
    if 'sort_by' not in state.form.data or not state.form.data['sort_by']:
        return

    # Build a sort operation from the form data
    state.sort_by = [(
        state.form.data['sort_by'].lstrip('-'),
        DESC if state.form.data['sort_by'].startswith('-') else ASC
    )]
