"""
Generic add document chain.

: `form_cls`
    The form that will be used to capture and validate the details of the new
    document (required).

"""

import flask
from manhattan.assets.fields import AssetField, ImageSetField
from manhattan.chains import Chain, ChainMgr
from manhattan.nav import Nav, NavItem

from . import factories, utils

__all__ = ['add_chains']


# Define the chains
add_chains = ChainMgr()

# GET
add_chains['get'] = Chain([
    'config',
    'authenticate',
    'init_form',
    'decorate',
    'render_template'
])

# POST
add_chains['post'] = Chain([
    'config',
    'authenticate',
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
])


# Define the links
add_chains.set_link(factories.config(form_cls=None))
add_chains.set_link(factories.authenticate())
add_chains.set_link(factories.init_form())
add_chains.set_link(factories.validate())
add_chains.set_link(factories.store_assets())
add_chains.set_link(factories.render_template('add.html'))
add_chains.set_link(factories.redirect('view', include_id=True))


@add_chains.link
def decorate(state):
    """
    Add decor information to the state (see `utils.base_decor` for further
    details on what information the `decor` dictionary consists of).

    This link adds a `decor` key to the state.
    """
    state.decor = utils.base_decor(state.manage_config, state.view_type)

    # Title
    state.decor['title'] = 'Add ' + state.manage_config.name

    # Breadcrumbs
    if Nav.exists(state.manage_config.get_endpoint('list')):
        state.decor['breadcrumbs'].add(
            utils.create_breadcrumb(state.manage_config, 'list')
        )
    state.decor['breadcrumbs'].add(NavItem('Add'))

@add_chains.link
def build_form_data(state):
    """
    Generate the form data that will be used to init the document.

    This link adds a `form_data` key to the the state containing the initialized
    form.
    """
    state.form_data = state.form.data

@add_chains.link
def init_document(state):
    """
    Initialize a new document and populates it using the submitted form data.

    This link adds a `{state.manage_config.var_name}` key to the the state
    containing the initialized document.
    """

    # Initialize a new document
    document = state.manage_config.frame_cls()

    # Populate the document from the form
    for k, v in state.form_data.items():

        if k in state.form \
                and isinstance(state.form[k], (AssetField, ImageSetField)):
            continue

        setattr(document, k, v)

    # Set the document against the state
    state[state.manage_config.var_name] = document

@add_chains.link
def add_document(state):
    """Add a document"""

    # Get the initialized document
    document = state[state.manage_config.var_name]

    assert document, \
            'No `{0}` set in state'.format(state.manage_config.var_name)

    # Check to see if the frame class supports `logged_insert`s and if so
    if hasattr(state.manage_config.frame_cls, 'logged_insert'):
        # Supports `logged_insert`
        state.change_log_entry = document.logged_insert(state.manage_user)

    else:
        # Doesn't support `logged_insert`
        document.insert()

    # Flash message that the document was added
    flask.flash('{document} added.'.format(document=document))
