import importlib
import inspect
import os

import inflection
from manhattan.formatters.text import slugify
from manhattan.nav import Nav, NavItem
from mongoframes import Frame

__all__ = [
    'ManageConfig',
    'ManageConfigMeta'
    ]


class ManageConfigMeta(type):
    """
    The `ManageConfigMeta` class implements defaults and attributes that rely on
    one or more other attributes.

    Some attributes for a `ManageConfig` class are the result of combining one
    or more of the class' attributes. Such attributes can't be combined when the
    class is defined because an overridden attribute would not change any other
    attribute that is based on it.

    To resolve this issue the `ManageConfigMeta` class is used to define
    attribute that are based on other attributes.
    """

    def __new__(meta, name, bases, dct):

        cls = super(ManageConfigMeta, meta).__new__(meta, name, bases, dct)

        # No set up required for the base ManageConfig class
        if name == 'ManageConfig' and not bases:
            return cls

        assert cls.frame_cls is not None, \
                '`frame_cls` not defined for `{0}` class'.format(name)

        # Add lazy attributes
        meta.add_lazy_defaults(cls, name, bases, dct)
        meta.add_lazy_attributes(cls, name, bases, dct)

        # Associate the config with the blueprint
        cls.blueprint._manage_config = cls

        return cls

    @classmethod
    def add_lazy_attributes(meta, cls, name, bases, dct):
        """
        Add attributes that are not set directly and rely on other settable
        attributes.
        """

    @classmethod
    def add_lazy_defaults(meta, cls, name, bases,  dct):
        """
        Add default values that use other attributes to determine the default.
        """
        frame_cls = dct['frame_cls']
        filepath = os.path.relpath(inspect.getfile(cls))
        path = os.path.split(filepath)[0]

        # Name
        cls.name = cls.name or \
                inflection.underscore(frame_cls.__name__).replace('_', ' ')
        cls.name_plural = cls.name_plural or inflection.pluralize(cls.name)

        # Var name
        cls.var_name = cls.var_name or cls.name.replace(' ', '_')
        cls.var_name_plural = cls.var_name_plural or \
                cls.name_plural.replace(' ', '_')

        # Blueprint
        assert cls.blueprint, 'No blueprint set against the config: ' + cls.name
        if cls.endpoint_prefix is None:
            if path.split('/')[-1] == 'manage':
                cls.endpoint_prefix = ''
            else:
                cls.endpoint_prefix = cls.var_name_plural + '__'

        # Template path
        if not cls.template_path:
            parts = path.split('/')
            if len(parts) == 3:
                cls.template_path = parts[1]
            else:
                cls.template_path = '/'.join(parts[3:])

        # Asset analyzers and variations
        if cls.asset_analyzers is None:
            cls.asset_analyzers = {}

        if cls.asset_variations is None:
            cls.asset_variations = {}


class ManageConfig(metaclass=ManageConfigMeta):
    """
    `ManageConfig` classes provide configuration options for views that manage
    database documents (via `Frame`s). The `manhattan_manage` package provides
    a set of generic manage views (list, view, add, update, delete, ...) which
    rely on a `ManageConfig` class.
    """

    # The `Frame` class being managed
    frame_cls = None

    # The name of the document type being managed in singular and plural form
    name = None
    name_plural = None

    # The name of the document as it would appear as a variable
    var_name = None
    var_name_plural = None

    # The function used to convert a document to a human friendly title
    titleize = str

    # Blueprint
    blueprint = None
    endpoint_prefix = None

    # Templates
    template_path = None

    # Asset analyzers and variations
    asset_analyzers = None
    asset_variations = None

    @classmethod
    def add_view_rule(cls, rule, view_type, chain_mgr, initial_state=None):
        """Add a rule for the given view type"""
        initial_state = initial_state or {}
        cls.blueprint.add_url_rule(
            rule,
            endpoint=cls.endpoint_prefix + view_type,
            view_func=chain_mgr.flask_view(
                manage_config=cls,
                view_type=view_type,
                **initial_state
                ),
            methods=[m.upper() for m in chain_mgr.chains.keys()]
            )

    @classmethod
    def get_endpoint(cls, view_type):
        """Return the endpoint for a given view"""
        return '{blueprint_name}.{endpoint_prefix}{view_type}'.format(
            blueprint_name=cls.blueprint.name,
            endpoint_prefix=cls.endpoint_prefix,
            view_type=view_type
            )

    @classmethod
    def tabs(cls, view_type, document=None):
        """Return a nav menu containing the tabs for the given view type"""
        return Nav.local_menu()
