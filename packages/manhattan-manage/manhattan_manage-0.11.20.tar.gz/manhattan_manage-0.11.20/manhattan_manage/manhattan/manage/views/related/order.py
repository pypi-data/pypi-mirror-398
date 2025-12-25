"""
Generic change log document chain.

: `parent_config`
    The manage config class for the related document.

: `parent_field`
    The field against related documents that relates them to the document.

: `parent_projection`
    The projection used when fetching the parent document.

: `position_field`
    The attribute that is used to set the order of the selected documents
    (defaults to 'position').

: `projection`
    The projection used when requesting documents from the database (defaults
    (to None which means the detault projection for the frame class will be
    used).

"""

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.formatters.text import upper_first
from manhattan.forms import BaseForm, fields
from manhattan.nav import Nav, NavItem
from mongoframes import ASC, Q

from manhattan.manage.views import factories, utils
from manhattan.manage.views.related import factories as related_factories
from manhattan.manage.views.order import order_chains

__all__ = ['order_chains']


# Define the chains
order_chains = order_chains.copy()
order_chains.insert_link(
    'authenticate',
    'get_parent_document',
    after=True
)

# Factory overrides
order_chains.set_link(
    factories.config(
        parent_config=None,
        parent_field=None,
        parent_projection=None,
        position_field='position',
        projection=None
    )
)
order_chains.set_link(related_factories.get_parent_document())

# Custom overrides

@order_chains.link
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
    state.decor['title'] = 'Order {0}'.format(
        state.manage_config.name_plural
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

    state.decor['breadcrumbs'].add(NavItem('Order'))

@order_chains.link
def get_documents(state):
    """
    Get the documents we want to be ordered.

    This link adds `{state.manage_config.var_name_plural}` to the state.
    """

    parent_document = state[state.parent_config.var_name]
    parent_field = state.parent_field or state.parent_config.var_name
    var_name_plural = state.manage_config.var_name_plural

    many_kw = {'sort': [(state.position_field, ASC)]}
    if state.projection:
        many_kw['projection'] = state.projection

    state[var_name_plural] = state.manage_config.frame_cls.many(
        Q[parent_field] == parent_document,
        **many_kw
    )

@order_chains.link
def redirect(state):
    """Redirect to the related listing"""

    parent_document = state[state.parent_config.var_name]
    parent_field = state.parent_field or state.parent_config.var_name

    return flask.redirect(
        flask.url_for(
            state.manage_config.get_endpoint('list'),
            **{parent_field: parent_document._id}
        )
    )