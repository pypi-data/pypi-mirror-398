"""
Generic update document chain.

: `form_cls`
    The form that will be used to capture and validate the updated details of
    the document (required).

: `parent_config`
    The manage config class for the related document.

: `parent_field`
    The field against related documents that relates them to the document.

: `parent_projection`
    The projection used when fetching the parent document.

: `projection`
    The projection used when requesting the document from the database (
    defaults to None which means the detault projection for the frame class
    will be used).

: `update_fields`
    A subset of fields to update (by default all fields in the document will
    are updated).

"""

import flask
from manhattan.assets.fields import AssetField
from manhattan.chains import Chain, ChainMgr
from manhattan.formatters.text import upper_first
from manhattan.nav import Nav, NavItem

from manhattan.manage.views import factories, utils
from manhattan.manage.views.related import factories as related_factories
from manhattan.manage.views.update import update_chains

__all__ = ['update_chains']


# Define the chains
update_chains = update_chains.copy()
update_chains.insert_link('get_document', 'get_parent_document', after=True)

# Factory overrides
update_chains.set_link(factories.config(
    form_cls=None,
    parent_config=None,
    parent_field=None,
    parent_projection=None,
    projection=None,
    remove_assets=False,
    update_fields=None
))
update_chains.set_link(related_factories.get_parent_document())

@update_chains.link
def decorate(state):
    """
    Add decor information to the state (see `utils.base_decor` for further
    details on what information the `decor` dictionary consists of).

    This link adds a `decor` key to the state.
    """
    parent_document = state[state.parent_config.var_name]
    parent_field = state.parent_field or state.parent_config.var_name
    document = state[state.manage_config.var_name]

    state.decor = utils.base_decor(
        state.manage_config,
        state.view_type,
        document
    )

    # Title
    state.decor['title'] = 'Update ' + state.manage_config.titleize(document)

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
        ),
        (state.manage_config, 'view', document)
    ]

    for args in breadcrumbs:
        if Nav.exists(args[0].get_endpoint(args[1])):
            state.decor['breadcrumbs'].add(utils.create_breadcrumb(*args))

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
