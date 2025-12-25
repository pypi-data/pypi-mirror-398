"""
Generic duplicate document chain.

: `duplicate_fields`
    A list of fields to duplicate (typically these include user managed fields
    that are not part represented as fields in the specified form cls
    (required).

: `form_cls`
    The form that will be used to capture and validate the details of the new
    document (required).

: `projection`
    The projection used when requesting the document from the database
    (defaults to None which means the detault projection for the frame class
    will be used).

"""

import flask
from manhattan.assets.fields import AssetField, ImageSetField
from manhattan.chains import Chain, ChainMgr
from manhattan.nav import Nav, NavItem

from . import factories, utils


# Define the chains
duplicate_chains = ChainMgr()

# GET
duplicate_chains['get'] = Chain([
    'config',
    'authenticate',
    'get_document',
    'init_form',
    'decorate',
    'render_template'
])

# POST
duplicate_chains['post'] = Chain([
    'config',
    'authenticate',
    'get_document',
    'init_form',
    'validate',
    [
        [
            'build_form_data',
            'duplicate_document',
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
duplicate_chains.set_link(
    factories.config(
        form_cls=None,
        duplicate_fields=None,
        projection=None
    )
)
duplicate_chains.set_link(factories.authenticate())
duplicate_chains.set_link(factories.get_document())
duplicate_chains.set_link(factories.init_form())
duplicate_chains.set_link(factories.validate())
duplicate_chains.set_link(factories.store_assets())
duplicate_chains.set_link(factories.render_template('duplicate.html'))
duplicate_chains.set_link(factories.redirect('view', include_id=True))


@duplicate_chains.link
def decorate(state):
    document = state[state.manage_config.var_name]
    state.decor = utils.base_decor(
        state.manage_config,
        state.view_type,
        document
    )

    # Title
    state.decor['title'] = 'Duplicate ' \
            + state.manage_config.titleize(document)

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

    state.decor['breadcrumbs'].add(NavItem('Duplicate'))

@duplicate_chains.link
def build_form_data(state):
    """
    Generate the form data that will be used to update the document.

    This link adds a `form_data` key to the the state containing the initialized
    form.
    """

    assert state.duplicate_fields != None, 'No `duplciate_fields` set'

    document = state[state.manage_config.var_name]

    # Add fields flagged for duplication to the form_data
    state.form_data = {}
    for field in state.duplicate_fields:
        state.form_data[field] = getattr(document, field)

    state.form_data.update(state.form.data)

@duplicate_chains.link
def init_form(state):
    """
    Return a function that will initialize a form for the view.

    This link adds a `form` key to the the state containing the initialized
    form.
    """

    # Initialize the form
    form_data = None
    if flask.request.method == 'POST':
        form_data = flask.request.form

    # Initialize the form
    state.form = state.form_cls(form_data)

@duplicate_chains.link
def duplicate_document(state):
    """
    Duplicate the document.

    This link adds a `source_document` key to the state containing the
    original document and replaces the `{document}` key with the new document.
    """

    # Initialize a new duplicate document
    dup_document = state.manage_config.frame_cls()

    # Populate the document from the form
    for k, v in state.form_data.items():

        if k in state.form \
                and isinstance(state.form[k], (AssetField, ImageSetField)):
            continue

        setattr(dup_document, k, v)

    # Insert the document
    state.change_log_entry = dup_document.logged_insert(state.manage_user)

    # Flash message that the document was duplicated
    flask.flash('{0} added (by duplication).'.format(dup_document))

    # Store the original source document in a new key and set the {document}
    # key to the new duplicated document.
    state.source_document = state[state.manage_config.var_name]
    state[state.manage_config.var_name] = dup_document
