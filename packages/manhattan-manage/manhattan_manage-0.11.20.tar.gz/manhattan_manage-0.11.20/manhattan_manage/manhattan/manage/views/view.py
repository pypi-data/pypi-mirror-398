"""
Generic view document chain.

: `projection`
    The projection used when requesting the document from the database (defaults
    to None which means the detault projection for the frame class will be
    used).

"""

from manhattan.chains import Chain, ChainMgr
from manhattan.nav import Nav, NavItem

from . import factories, utils

__all__ = ['view_chains']


# Define the chains
view_chains = ChainMgr()

# GET
view_chains['get'] = Chain([
    'config',
    'authenticate',
    'get_document',
    'decorate',
    'render_template'
    ])


# Define the links
view_chains.set_link(factories.config(projection=None))
view_chains.set_link(factories.authenticate())
view_chains.set_link(factories.get_document())
view_chains.set_link(factories.render_template('view.html'))


@view_chains.link
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
    state.decor['breadcrumbs'].add(NavItem('View'))

    # Actions
    if Nav.exists(state.manage_config.get_endpoint('update')):
        state.decor['actions'].add(
            NavItem(
                'Update',
                state.manage_config.get_endpoint('update'),
                view_args={state.manage_config.var_name: document._id}
            )
        )

    if Nav.exists(state.manage_config.get_endpoint('delete')):
        state.decor['actions'].add(
            NavItem(
                'Delete',
                state.manage_config.get_endpoint('delete'),
                view_args={state.manage_config.var_name: document._id}
            )
        )

    if hasattr(document, 'url'):
        state.decor['actions'].add(
            NavItem(
                'Visit',
                fixed_url=document.url,
                data={'target': '_blank'}
            )
        )
