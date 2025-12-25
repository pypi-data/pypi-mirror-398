
import click
from flask import Flask
from flask.cli import AppGroup
from manhattan.publishing import PublishableFrame
from mongoframes import Frame

__all__ = ['add_command']


# Create a group for all fixture commands
manage_cli = AppGroup('manage')
def add_commands(app):
    app.cli.add_command(manage_cli)


@manage_cli.command('build-indexes')
@click.argument('collections', nargs=-1)
def build_indexes(collections=None):
    """Find and (re)build indexes defined against models"""

    # Find a list of frames that need indexes built against them
    frames = []
    sub_classes = Frame.__subclasses__()
    while len(sub_classes) > 0:
        sub_class = sub_classes.pop()
        if len(sub_class.__subclasses__()):
            sub_classes += sub_class.__subclasses__()
        else:
            if hasattr(sub_class, '_indexes'):
                frames.append(sub_class)

    for frame in frames:

        # If a collection has been named skip all other collections
        if len(collections) > 0 and frame.__name__ not in collections:
            continue

        print('Building indexes for', frame.__name__)

        if issubclass(frame, PublishableFrame):

            # Rebuild the indexes

            with frame._context_manager.draft():
                frame.get_collection().drop_indexes()
                frame.get_collection().create_indexes(frame._indexes)

            with frame._context_manager.published():
                frame.get_collection().drop_indexes()
                frame.get_collection().create_indexes(frame._indexes)

        else:
            # Rebuild the indexes
            frame.get_collection().drop_indexes()
            frame.get_collection().create_indexes(frame._indexes)

    print('Indexes built')