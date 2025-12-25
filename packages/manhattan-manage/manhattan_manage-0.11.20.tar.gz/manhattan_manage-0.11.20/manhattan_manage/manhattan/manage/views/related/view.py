"""
Generic view document chain.

: `parent_config`
    The manage config class for the related document.

: `parent_field`
    The field against related documents that relates them to the document.

: `parent_projection`
    The projection used when fetching the parent document.

: `projection`
    The projection used when requesting the document from the database (defaults
    to None which means the detault projection for the frame class will be
    used).

"""

from manhattan.chains import Chain, ChainMgr
from manhattan.formatters.text import upper_first
from manhattan.nav import Nav, NavItem

from manhattan.manage.views import factories, utils
from manhattan.manage.views.related import factories as related_factories
from manhattan.manage.views.view import view_chains

__all__ = ['view_chains']


# Define the chains
view_chains = view_chains.copy()
view_chains.insert_link('get_document', 'get_parent_document', after=True)

# Factory overrides
view_chains.set_link(
    factories.config(
        parent_config=None,
        parent_field=None,
        parent_projection=None,
        projection=None
    )
)
view_chains.set_link(related_factories.get_parent_document())


# Custom overrides

@view_chains.link
def decorate(state):
    """
    Add decor information to the state (see `utils.base_decor` for further
    details on what information the `decor` dictionary consists of).

    This link adds a `decor` key to the state.
    """
    document = state[state.manage_config.var_name]
    parent_document = state[state.parent_config.var_name]
    parent_field = state.parent_field or state.parent_config.var_name

    state.decor = utils.base_decor(
        state.manage_config,
        state.view_type,
        document
    )

    # Title
    state.decor['title'] = state.manage_config.titleize(document)

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
