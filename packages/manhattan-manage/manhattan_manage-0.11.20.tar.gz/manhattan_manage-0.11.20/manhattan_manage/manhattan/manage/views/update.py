"""
Generic update document chain.

: `form_cls`
    The form that will be used to capture and validate the updated details of
    the document (required).

: `projection`
    The projection used when requesting the document from the database (
    defaults to None which means the detault projection for the frame class
    will be used).

: `remove_assets`
    If True then assets associated with the document will be removed when they
    are removed from document.

: `update_fields`
    A subset of fields to update (by default all fields in the document will
    are updated).

"""

import flask
from manhattan.assets.fields import AssetField, ImageSetField
from manhattan.chains import Chain, ChainMgr
from manhattan.nav import Nav, NavItem

from . import factories, utils

__all__ = ['update_chains']


# Define the chains
update_chains = ChainMgr()

# GET
update_chains['get'] = Chain([
    'config',
    'authenticate',
    'get_document',
    'init_form',
    'decorate',
    'render_template'
])

# POST
update_chains['post'] = Chain([
    'config',
    'authenticate',
    'get_document',
    'init_form',
    'validate',
    [
        [
            'build_form_data',
            'update_document',
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
update_chains.set_link(factories.config(
    form_cls=None,
    projection=None,
    remove_assets=False,
    update_fields=None
))
update_chains.set_link(factories.authenticate())
update_chains.set_link(factories.get_document())
update_chains.set_link(factories.init_form())
update_chains.set_link(factories.validate())
update_chains.set_link(factories.store_assets())
update_chains.set_link(factories.render_template('update.html'))
update_chains.set_link(factories.redirect('view', include_id=True))


@update_chains.link
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
    state.decor['title'] = 'Update ' + state.manage_config.titleize(document)

    # Breadcrumbs
    if Nav.exists(state.manage_config.get_endpoint('list')):
        state.decor['breadcrumbs'].add(
            utils.create_breadcrumb(state.manage_config, 'list')
        )
    if Nav.exists(state.manage_config.get_endpoint('view')):
        state.decor['breadcrumbs'].add(
            utils.create_breadcrumb(state.manage_config, 'view', document)
        )
    state.decor['breadcrumbs'].add(NavItem('Update'))

    # Actions
    if not Nav.exists(state.manage_config.get_endpoint('view')):
        if Nav.exists(state.manage_config.get_endpoint('delete')):
            state.decor['actions'].add(
                NavItem(
                    'Delete',
                    state.manage_config.get_endpoint('delete'),
                    view_args={state.manage_config.var_name: document._id}
                )
            )

@update_chains.link
def build_form_data(state):
    """
    Generate the form data that will be used to update the document.

    This link adds a `form_data` key to the the state containing the initialized
    form.
    """
    state.form_data = state.form.data

@update_chains.link
def update_document(state):
    """Update a document"""

    # Get the initialized document
    document = state[state.manage_config.var_name]

    assert document, \
            'No `{0}` set in state'.format(state.manage_config.var_name)

    # Build a dictionary of form data excluding fields that contain assets as
    # these are managed by the `store_assets` link.
    form_data = {}
    for k, v in state.form_data.items():

        if k in state.form \
                and isinstance(state.form[k], (AssetField, ImageSetField)):
            continue

        form_data[k] = v

    # Check to see if the frame class supports `logged_update`s and if so..
    update_fields = state.update_fields or []

    if hasattr(state.manage_config.frame_cls, 'logged_update'):

        # Supports `logged_update`
        state.change_log_entry = document.logged_update(
            state.manage_user,
            form_data,
            *update_fields
        )

    else:

        # Doesn't support `logged_update`
        for k, v in form_data.items():
            setattr(document, k, v)
        document.update(*update_fields)

    # Flash message that the document was updated
    flask.flash('{document} updated.'.format(document=document))
