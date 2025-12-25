"""
Generic change log document chain.

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

: `orphans`
    The maximum number of orphan that can be merged into the last page of
    results (the orphans will form the last page) (defaults to 2).

: `per_page`
    The number of results that will appear per page (defaults to 30).

"""

import flask
from manhattan.chains import Chain, ChainMgr
from manhattan.formatters.text import upper_first
from manhattan.forms import BaseForm, fields
from manhattan.nav import Nav, NavItem

from manhattan.manage.views import factories, utils
from manhattan.manage.views.related import factories as related_factories
from manhattan.manage.views import change_log

__all__ = ['change_log_chains']


class ListForm(BaseForm):

    _info = {}

    page = fields.IntegerField('Page', default=1)


# Define the chains
change_log_chains = change_log.change_log_chains.copy()
change_log_chains.insert_link(
    'get_document',
    'get_parent_document',
    after=True
)


# Factory overrides
change_log_chains.set_link(
    factories.config(
        form_cls=ListForm,
        parent_config=None,
        parent_field=None,
        parent_projection=None,
        projection=None,
        orphans=2,
        per_page=20
    )
)
change_log_chains.set_link(related_factories.get_parent_document())


# Custom overrides

@change_log_chains.link
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

    state.decor['breadcrumbs'].add(NavItem('Change log'))
