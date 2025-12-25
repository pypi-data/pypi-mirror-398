"""
A set of classes and functions that help manage applications.
"""

from importlib import import_module

__all__ = [
    'get_app',
    'get_config',
    'load_blueprints'
]


def get_app(dispatcher, tag):
    """
    Return the manage app from the dispatcher.

    NOTE: The method assumes there's only one app that has a the manage
    blueprint installed against it and isn't safe to use if there are multiple
    cases.
    """
    for app in dispatcher.apps:
        if hasattr(app, '_manage') and app._manage._tag == tag:
            return app

def get_config(app, blueprint_name):
    """Return the manage config for the given blueprint."""
    if blueprint_name in app.blueprints:
        return app.blueprints[blueprint_name]._manage_config

def load_blueprints(app, app_name, blueprints):
    """
    Import and register a list of blueprints and return a map of the modules
    imported.
    """

    blueprint_modules = {}
    for blueprint in blueprints:
        # Import the blueprint module
        blueprint_module = import_module(
            'blueprints.{0}.{1}'.format(blueprint, app_name)
            )
        blueprint_modules[blueprint] = blueprint_module

        # Register the blueprint
        app.register_blueprint(blueprint_module.blueprint)

    return blueprint_modules
