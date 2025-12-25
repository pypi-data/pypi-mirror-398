"""
Utilities functions for manhattan views.
"""

import flask
import inflection
from manhattan.formatters.text import upper_first
from manhattan.nav import Nav, NavItem

__all__ = [
    'base_decor',
    'create_breadcrumb',
    'json_fail',
    'json_success'
    ]


def base_decor(config, view_type, document=None):
    """
    Return a dictionary that contains the base information required for
    decorating a manage UI. The dictionary will contain the following base
    values:

    - `actions`
    - `breadcrumb`
    - `tabs`
    - `title`
    """

    return {
        'actions': Nav.local_menu(),
        'breadcrumbs': Nav.local_menu(),
        'tabs': config.tabs(view_type, document),
        'title': '-- NOT SET --'
    }

def create_breadcrumb(
    config,
    view_type,
    document=None,
    view_args=None,
    label=None
):
    """Short-cut for creating a breadcrumb for the manage UI"""

    # Create a label (if not supplied)
    if label is None:
        if view_type == 'list':
            label = upper_first(config.name_plural)

        elif view_type == 'view':
            label = upper_first(config.name) + ' details'

        else:
            label = inflection.humanize(view_type)

    # Build the view args
    view_args = view_args or {}

    # Create the breadcrumb
    if document:
        view_args.update({config.var_name: document._id})

    return NavItem(
        label,
        config.get_endpoint(view_type),
        view_args=view_args or None
    )

def json_fail(reason, errors=None):
    """Return a fail response"""
    response = {'status': 'fail', 'payload': {'reason': reason}}
    if errors:
        response['payload']['errors'] = errors
    return flask.jsonify(response)

def json_success(payload=None):
    """Return a success response"""
    response = {'status': 'success'}
    if payload:
        response['payload'] = payload
    return flask.jsonify(response)
