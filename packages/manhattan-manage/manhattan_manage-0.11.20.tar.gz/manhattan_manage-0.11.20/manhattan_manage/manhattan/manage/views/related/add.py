"""
Generic add related document chain.

: `form_cls`
    The form that will be used to capture and validate the details of the new
    document (required).

: `parent_config`
    The manage config class for the related document.

: `parent_field`
    The field against related documents that relates them to the document.

: `parent_projection`
    The projection used when fetching the parent document.

"""

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.formatters.text import upper_first
from manhattan.nav import Nav, NavItem

from manhattan.manage.views import factories, utils
from manhattan.manage.views.related import factories as related_factories
from manhattan.manage.views.add import add_chains

__all__ = ['add_chains']


# Define the chains
add_chains = add_chains.copy()

# GET
add_chains['get'].links = [
    'config',
    'authenticate',
    'get_parent_document',
    'init_form',
    'decorate',
    'render_template'
]

# POST
add_chains['post'].links = [
    'config',
    'authenticate',
    'get_parent_document',
    'init_form',
    'validate',
    [
        [
            'build_form_data',
            'init_document',
            'add_document',
            'store_assets',
            'redirect'
        ],
        [
            'decorate',
            'render_template'
        ]
    ]
]

# Factory overrides
add_chains.set_link(
    factories.config(
        parent_config=None,
        parent_field=None,
        parent_projection=None,
        form_cls=None
    )
)
add_chains.set_link(related_factories.get_parent_document())

# Custom overrides

@add_chains.link
def decorate(state):
    """
    Add decor information to the state (see `utils.base_decor` for further
    details on what information the `decor` dictionary consists of).

    This link adds a `decor` key to the state.
    """
    parent_document = state[state.parent_config.var_name]
    parent_field = state.parent_field or state.parent_config.var_name

    state.decor = utils.base_decor(state.manage_config, state.view_type)

    # Title
    state.decor['title'] = 'Add {0} to {1}'.format(
        state.manage_config.name,
        state.parent_config.titleize(parent_document)
    )

    # Breadcrumbs
    breadcrumbs = [
        (state.parent_config, 'list'),
        (state.parent_config, 'view', parent_document),
        (
            state.manage_config,
            'list',
            None,
            {parent_field: parent_document._id},
            upper_first(state.manage_config.name_plural)
        )
    ]

    for args in breadcrumbs:
        if Nav.exists(args[0].get_endpoint(args[1])):
            state.decor['breadcrumbs'].add(utils.create_breadcrumb(*args))

    state.decor['breadcrumbs'].add(NavItem('Add'))

@add_chains.link
def build_form_data(state):
    """
    Generate the form data that will be used to init the document.

    This link adds a `form_data` key to the the state containing the initialized
    form.
    """
    parent_document = state[state.parent_config.var_name]
    parent_field = state.parent_field or state.parent_config.var_name

    state.form_data = state.form.data
    state.form_data[parent_field] = parent_document
