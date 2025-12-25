"""
Generic delete document chain.

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

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.nav import Nav, NavItem

from manhattan.manage.views import factories, utils
from manhattan.manage.views.related import factories as related_factories
from manhattan.manage.views.delete import delete_chains

__all__ = ['delete_chains']


# Define the chains
delete_chains = delete_chains.copy()
delete_chains.insert_link('get_document', 'get_parent_document', after=True)

# Factory overrides
delete_chains.set_link(
    factories.config(
        parent_config=None,
        parent_field=None,
        parent_projection=None,
        projection=None,
        remove_assets=False
    )
)
delete_chains.set_link(related_factories.get_parent_document())
delete_chains.set_link(related_factories.decorate('delete'))

# Custom overrides

@delete_chains.link
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
