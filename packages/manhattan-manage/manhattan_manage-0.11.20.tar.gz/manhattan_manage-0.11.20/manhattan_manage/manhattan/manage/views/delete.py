"""
Generic delete document chain.

: `projection`
    The projection used when requesting the document from the database
    (defaults to None which means the detault projection for the frame class
    will be used).

: `remove_assets`
    If True then assets associated with the document will be removed when it
    is deleted. Asset values must be projected as `Asset` instances, the
    chain supports deleting asset from a value or a list of values (other
    structures are not supported and must be added manually).

"""

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.formatters.text import upper_first
from manhattan.nav import Nav, NavItem

# Optional imports
try:
    from manhattan.assets import Asset, ImageSet
    __assets_supported__ = True

except ImportError as e:
    __assets_supported__ = False

from . import factories, utils

__all__ = ['delete_chains']


# Define the chains
delete_chains = ChainMgr()

# GET
delete_chains['get'] = Chain([
    'config',
    'authenticate',
    'get_document',
    'decorate',
    'render_template'
])

# POST
delete_chains['post'] = Chain([
    'config',
    'authenticate',
    'get_document',
    'delete_document',
    'redirect'
])


# Define the links
delete_chains.set_link(
    factories.config(
        projection=None,
        remove_assets=False
    )
)
delete_chains.set_link(factories.authenticate())
delete_chains.set_link(factories.get_document())
delete_chains.set_link(factories.render_template('delete.html'))
delete_chains.set_link(factories.redirect('list'))


@delete_chains.link
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
    state.decor['title'] = 'Delete ' + state.manage_config.titleize(document)

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
                    document,
                    label=upper_first(state.manage_config.name) + ' details'
                )
            )

    state.decor['breadcrumbs'].add(NavItem('Delete'))

@delete_chains.link
def delete_document(state):
    """Delete a document"""

    # Get the document
    document = state[state.manage_config.var_name]

    assert document, \
            'No `{0}` set in state'.format(state.manage_config.var_name)

    # Check to see if the frame class supports `logged_delete`s and if so
    if hasattr(state.manage_config.frame_cls, 'logged_delete'):
        # Supports `logged_delete`
        state.change_log_entry = document.logged_delete(state.manage_user)

    else:
        # Doesn't support `logged_delete`
        document.delete()

    if state.remove_assets:

        assert __assets_supported__, \
            'This link requires manhattan-assets to be installed'

        asset_mgr = flask.current_app.asset_mgr

        # Attempt to delete any assets associated with the document
        assets_to_remove = []
        for field in document.get_fields():

            value = document.get(field)
            if not value:
                continue

            if isinstance(value, Asset):
                assets_to_remove.append(value)

            if isinstance(value, list) and isinstance(value[0], Asset):
                for a in value:
                    if isinstance(a, Asset):
                        assets_to_remove.append(a)

            if isinstance(value, ImageSet):
                for image in value.images.values():
                    assets_to_remove.append(image)

        asset_mgr.remove_many(assets_to_remove)

    # Flash message that the document was deleted
    flask.flash('{document} deleted.'.format(document=document))
