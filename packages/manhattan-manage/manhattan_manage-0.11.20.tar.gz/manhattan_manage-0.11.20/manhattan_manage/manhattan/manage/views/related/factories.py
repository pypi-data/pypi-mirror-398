"""
A set of factories to simplify creating manage chains that relate to a parent
document.
"""

import bson
import flask
import inflection
from manhattan.formatters.text import upper_first
from manhattan.nav import Nav, NavItem
from manhattan.manage.views import utils
from mongoframes.queries import to_refs

__all__ = [
    'decorate',
    'get_parent_document'
]


def decorate(view_type, title=None, last_breadcrumb=None):
    """
    Return a function that will add decor information to the state for the
    named view. Unlike the standard `decorate` factory this function places
    the UI at the root of the parent documents `view` or `update` UI.

    This function requires `state.parent_config` to be set.
    """

    def decorate(state):
        parent_document = state[state.parent_config.var_name]
        parent_field = state.parent_field or state.parent_config.var_name
        document = state[state.manage_config.var_name]

        # Base
        state.decor = utils.base_decor(
            state.manage_config,
            state.view_type,
            document
        )

        # Title
        state.decor['title'] = '{0} {1}'.format(
            inflection.humanize(view_type),
            state.manage_config.titleize(document)
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

        # Add view to the breadcrumb, or update if view doesn't exist
        if Nav.exists(state.manage_config.get_endpoint('view')):
            state.decor['breadcrumbs'].add(
                utils.create_breadcrumb(
                    state.manage_config,
                    'view',
                    document
                )
            )

        elif Nav.exists(state.manage_config.get_endpoint('update')):
            state.decor['breadcrumbs'].add(
                utils.create_breadcrumb(
                    state.manage_config,
                    'update',
                    document,
                    label=upper_first(state.manage_config.name) + ' details'
                )
            )

        state.decor['breadcrumbs'].add(
            NavItem(inflection.humanize(view_type))
        )

    return decorate

def get_parent_document(projection=None):
    """
    Return a function that will attempt to retreive a parent document from the
    database by `_id` using the `state.parent_config.var_name`, or if
    specified `state.parent_field` name, to find the documents Id against
    either the request params or current document.

    This link adds a `{state.parent_config.var_name}` key to the the state
    containing the parent document retreived.

    This function requires that `state.parent_config` is specified in the
    state.

    Optionally a projection to use when getting the parent document can be
    specified, if no projection is specified then the function will look for a
    projection against the state (e.g state.[parent_projection).

    The `get_parent_document` link should be inserted after any `get_document`
    link within the chain.
    """

    def get_parent_document(state):

        document = state.get(state.manage_config.var_name)

        # Get the Id of the document passed in the request
        parent_field = state.parent_field or state.parent_config.var_name
        if document:
            parent_document_id = to_refs(document[parent_field])
        else:
            parent_document_id = flask.request.values.get(parent_field)

        # Attempt to convert the Id to the required type
        try:
            parent_document_id = bson.objectid.ObjectId(parent_document_id)
        except bson.errors.InvalidId:
            flask.abort(404)

        # Attempt to retrieve the document
        by_id_kw = {}
        if projection or state.parent_projection:
            by_id_kw['projection'] = projection or state.parent_projection

        parent_document = state.parent_config.frame_cls.by_id(
            parent_document_id,
            **by_id_kw
        )

        if not parent_document:
            flask.abort(404)

        # Set the document against the state
        state[state.parent_config.var_name] = parent_document

    return get_parent_document
