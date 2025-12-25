from collections import namedtuple

from .add import add_chains
from .change_log import change_log_chains
from .delete import delete_chains
from .duplicate import duplicate_chains
from .list import list_chains
from .order import order_chains
from .typeahead import typeahead_chains
from .update import update_chains
from .view import view_chains

__all__ = ['generic']


# We name space generic views using a named tuple to provide a slightly nicer
# way to access them, e.g:
#
#     from manhattan.manage.views import generic
#
#     view = generic.add
#
# And to make it easy to iterate through the list of generic views to make
# changes, e.g:
#
#     def authenticate(state):
#         """A custom authenticator for my site"""
#
#         ...
#
#     for view in generic:
#         view.set_link(authenticate)

# Define the named tuple (preventing the list of generic views being altered)
Generic = namedtuple(
    'Generic',
    [
        'add',
        'change_log',
        'delete',
        'duplicate',
        'list',
        'order',
        'typeahead',
        'update',
        'view'
    ]
)

# Create an instance of Generic containing all the generic views
generic = Generic(
    add=add_chains,
    change_log=change_log_chains,
    delete=delete_chains,
    duplicate=duplicate_chains,
    list=list_chains,
    order=order_chains,
    typeahead=typeahead_chains,
    update=update_chains,
    view=view_chains,
)
