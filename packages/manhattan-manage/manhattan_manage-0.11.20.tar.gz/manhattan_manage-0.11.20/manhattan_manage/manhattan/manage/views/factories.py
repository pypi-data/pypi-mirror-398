"""
Link factories for manhattan views.
"""


import bson
import json
import os
import urllib.parse as urlparse
from urllib.parse import urlencode

import flask
import inflection
from manhattan import secure
from manhattan.nav import Nav, NavItem
from manhattan.manage.views import utils

# Optional imports
try:
    from manhattan.assets import Asset, ImageSet
    from manhattan.assets.fields import AssetField, ImageSetField
    from manhattan.assets.transforms.base import BaseTransform
    from manhattan.assets.transforms.images import Fit, Output
    __assets_supported__ = True

except ImportError as e:
    __assets_supported__ = False

__all__ = [
    'authenticate',
    'config',
    'decorate',
    'get_document',
    'init_form',
    'mfa_authenticate',
    'mfa_end_scoped_session',
    'mfa_authenticate_scoped_session',
    'redirect',
    'render_template',
    'store_assets',
    'validate'
]


def authenticate(
    user_g_key='user',
    sign_in_endpoint='manage_users.sign_in',
    sign_out_endpoint='manage_users.sign_out',
    mfa_required=None,
    mfa_authorize_endpoint='manage_users.mfa_auth',
    mfa_authorized_attr='mfa_authorized',
    mfa_enable_endpoint='manage_users.mfa_enable',
    mfa_enabled_attr='mfa_enabled'
):
    """
    Authenticate the caller has permission to call the view.

    This link adds a `user` key to the the state containing the currently
    signed in user.
    """

    def authenticate(state):
        # Get the signed in user
        state.manage_user = flask.g.get(user_g_key)

        # Extract the full path (we use this approach to cater for the
        # dispatcher potentially modifying the URL root value).
        parts = urlparse.urlparse(flask.request.url)
        full_path = flask.request.url.split(parts[1], 1)[1]

        # We're not allowed to access this view point so determine if that's
        # because we're not sign-in or because we don't have permission.
        if not state.manage_user:
            # We need to sign-in to view this endpoint

            # Forward the user to the sign-in page with the requested URL as
            # the `next` parameter.
            redirect_url = flask.url_for(
                sign_in_endpoint,
                next=secure.safe_redirect_url(
                    full_path,
                    [flask.url_for(sign_out_endpoint)]
                )
            )
            return flask.redirect(redirect_url)

        # Check that any user with multi-factor authentication (MFA) enabled
        # has authorized their session using MFA.
        if getattr(state.manage_user, mfa_enabled_attr, None):
            if not getattr(state.manage_user, mfa_authorized_attr, None):

                # The user needs to MFA authorize their session to view this
                # endpoint.

                # Forward the user to the MFA auth page with the requested URL
                # as the `caller` parameter.
                redirect_url = flask.url_for(
                    mfa_authorize_endpoint,
                    caller_url=full_path
                )

                return flask.redirect(redirect_url)

        # Check if the application requires multi-factor authentication (MFA)
        # to be enabled for users. If so and a user doesn't have MFA enabled
        # then we redirect them to enable MFA.
        _mfa_required = mfa_required
        if _mfa_required is None:
            _mfa_required = flask.current_app.config.get('USER_MFA_REQUIRED')

        if _mfa_required:
            if not getattr(state.manage_user, mfa_enabled_attr, None):
                return flask.redirect(flask.url_for(mfa_enable_endpoint))

        # Check if we're allowed to access this requested endpoint
        if not Nav.allowed(flask.request.endpoint, **flask.request.view_args):

            # We don't have permission to view this endpoint
            flask.abort(403, 'Permission denied')

    return authenticate

def config(**defaults):
    """
    Return a function will configure a view's state adding defaults where no
    existing value currently exists in the state.

    This function is designed to be included as the first link in a chain and
    to set the initial state so that chains can be configured on a per copy
    basis.
    """

    def config(state):
        # Apply defaults
        for key, value in defaults.items():

            # First check if a value is already set against the state
            if key in state:
                continue

            # If not then set the default
            state[key] = value

    return config

def decorate(view_type, title=None, last_breadcrumb=None):
    """
    Return a function that will add decor information to the state for the
    named view.
    """

    def decorate(state):
        document = state.get(state.manage_config.var_name)
        state.decor = utils.base_decor(state.manage_config, state.view_type)

        # Title
        if document:
            state.decor['title'] = '{action} {target}'.format(
                action=inflection.humanize(view_type),
                target=state.manage_config.titleize(document)
            )
        else:
            state.decor['title'] = inflection.humanize(view_type)

        # Breadcrumbs
        if Nav.exists(state.manage_config.get_endpoint('list')):
            state.decor['breadcrumbs'].add(
                utils.create_breadcrumb(state.manage_config, 'list')
            )
        if Nav.exists(state.manage_config.get_endpoint('view')) and document:
            state.decor['breadcrumbs'].add(
                utils.create_breadcrumb(state.manage_config, 'view', document)
            )
        state.decor['breadcrumbs'].add(NavItem('Update'))

    return decorate

def get_document(projection=None):
    """
    Return a function that will attempt to retreive a document from the
    database by `_id` using the `var_name` named parameter in the request.

    This link adds a `{state.manage_config.var_name}` key to the the state
    containing the document retreived.

    Optionally a projection to use when getting the document can be specified,
    if no projection is specified then the function will look for a projection
    against the state (e.g state.projection).
    """

    def get_document(state):
        # Get the Id of the document passed in the request
        document_id = flask.request.values.get(state.manage_config.var_name)

        # Attempt to convert the Id to the required type
        try:
            document_id = bson.objectid.ObjectId(document_id)
        except bson.errors.InvalidId:
            flask.abort(404)

        # Attempt to retrieve the document
        by_id_kw = {}
        if projection or state.projection:
            by_id_kw['projection'] = projection or state.projection

        document = state.manage_config.frame_cls.by_id(
            document_id,
            **by_id_kw
        )

        if not document:
            flask.abort(404)

        # Set the document against the state
        state[state.manage_config.var_name] = document

    return get_document

def init_form(populate_on=None):
    """
    Return a function that will initialize a form for the named generic view
    (e.g list, add, update, etc.) or the given form class.

    This link adds a `form` key to the the state containing the initialized
    form.
    """

    # If populate_on is not specified then we default to `POST`
    if populate_on is None:
        populate_on = ['POST']

    def init_form(state):
        # Get the form class
        assert state.form_cls, 'No form class `form_cls` defined'

        # Initialize the form
        form_data = None
        if flask.request.method in populate_on:
            if flask.request.method in ['POST', 'PUT']:
                form_data = flask.request.form
            else:
                form_data = flask.request.args

        # If a document is assign to the state then this is sent as the first
        # argument when initializing the form.
        obj = None
        if state.manage_config.var_name in state:
            obj = state[state.manage_config.var_name]

        # Initialize the form
        state.form = state.form_cls(form_data or None, obj=obj)

    return init_form

def mfa_authenticate_scoped_session(
    authorize_endpoint='manage_users.mfa_auth',
    enabled_attr='mfa_enabled',
    get_cache=None
):
    """
    Return a function that creates an authorized 2-factor authenticated
    session.

    This link should be added after the `authenticate` link.
    """

    if get_cache is None:
        get_cache = lambda s: \
                flask.current_app.config[(
                    f'{s.manage_config.frame_cls.get_settings_prefix()}'
                    '_MFA_SCOPED_SESSION_CACHE'
                )]

    def mfa_authenticate_scoped_session(state):

        if getattr(state.manage_user, enabled_attr, None):

            # Generate the caller URL

            # Extract the full path (we use this approach to cater for the
            # dispatcher potentially modifying the URL root value).
            parts = urlparse.urlparse(flask.request.url)
            full_path = flask.request.url.split(parts[1], 1)[1]

            # Parse URL
            caller_url_parts = list(urlparse.urlparse(full_path))

            # Remove 'mfa_scoped_session_token' from the query parameters
            query = dict(urlparse.parse_qsl(caller_url_parts[4]))
            query.pop('mfa_scoped_session_token', None)
            caller_url_parts[4] = urlencode(query)

            # Rebuild the URL
            caller_url = urlparse.urlunparse(caller_url_parts)

            # Check if a scoped session has been authorized using MFA
            session_token \
                    = flask.request.values.get('mfa_scoped_session_token')

            if session_token:

                # Verify the scoped session
                verified = secure.mfa.verify_scoped_session(
                    get_cache(state),
                    session_token,
                    (str(state.manage_user._id), caller_url)
                )
                if verified:
                    return

                # Notify the user that their session likely expired
                flask.flash('2FA session expired', 'error')

            # Redirect the user to verify the session
            return flask.redirect(
                flask.url_for(
                    authorize_endpoint,
                    caller_url=caller_url,
                    scoped=True
                )
            )

    return mfa_authenticate_scoped_session

def mfa_end_scoped_session(
    authorize_endpoint='manage_users.mfa_auth',
    enabled_attr='mfa_enabled',
    get_cache=None
):
    """
    Return a function that will clear a scoped session.

    This link should be added as the penultimate link, e.g before `redirect`
    or `render_template`.
    """

    if get_cache is None:
        get_cache = lambda s: \
                flask.current_app.config[(
                    f'{s.manage_config.frame_cls.get_settings_prefix()}'
                    '_MFA_FAILED_AUTH_CACHE'
                )]

    def mfa_end_scoped_session(state):
        secure.mfa.delete_scoped_session(
            get_cache(state),
            flask.request.values.get('mfa_scoped_session_token')
        )

    return mfa_end_scoped_session

def redirect(endpoint, include_id=False):
    """
    Return a function that will trigger a redirect to the given endpoint.

    Optionally an Id for the current document in the state can be added to the
    URL, e.g `url_for('view.user', user=user._id)` by passing `include_id` as
    True.
    """

    def redirect(state):
        # Build the URL arguments
        url_args = {}
        if include_id:
            url_args[state.manage_config.var_name] = \
                    state[state.manage_config.var_name]._id

        # Get the URL for the endpoint
        prefix = state.manage_config.endpoint_prefix
        if state.manage_config.endpoint_prefix:
            url = flask.url_for('.' + prefix + endpoint, **url_args)
        else:
            url = flask.url_for('.' + endpoint, **url_args)

        # Return the redirect response
        return flask.redirect(url)

    return redirect

def render_template(template_path):
    """
    Return a function that will render the named template. The state object is
    used as template arguments.
    """

    def render_template(state):
        # Build the template filepath
        full_template_path = os.path.join(
            state.manage_config.template_path,
            template_path
        )

        # Render the template
        return flask.render_template(full_template_path, **state)

    return render_template

def store_assets():
    """
    Return a function that will store changes to assets.
    """

    def store_assets(state):

        if not getattr(flask.current_app, 'asset_mgr', None):
            return

        # Identify asset fields within the form
        document = state[state.manage_config.var_name]
        asset_fields = []
        image_set_fields = []

        for field in document.get_fields():

            form_field = getattr(state.form, field, None)

            if isinstance(form_field, AssetField):
                asset_fields.append(field)

            if isinstance(form_field, ImageSetField):
                image_set_fields.append(field)

        # Build a list of assets to make permanent (persist), to generate new
        # variations for (transform) and to remove.
        assets_to_persist = []
        assets_to_transform = []
        assets_to_remove = []

        # Asset fields
        for field in asset_fields:

            asset = state.form_data.get(field)

            if asset:

                if asset.temporary:
                    assets_to_persist.append(asset)

                    if document.get(field):
                        assets_to_remove.append(document[field])

                    if not asset.base_transforms:
                        continue

                elif not state.form[field].base_transform_modified:
                    continue

            else:

                if document.get(field):
                    assets_to_remove.append(document[field])

                continue

            # Build the transform instructions required to regenerate
            # variations for the asset.

            # Get variations defined for the field against the manage config.
            variations = state.manage_config.asset_variations.get(field, {})

            # Copy the variations structure
            variations = {k: [i for i in v] for k, v in variations.items()}

            if '--thumb--' in asset.variations:

                # Cater for regenerating the thumbnail.
                variations['--thumb--'] = flask.current_app.config.get(
                    'ASSET_THUMB_VARIATION',
                    [
                        Fit(480),
                        Output('jpg', 75)
                    ]
                )

            if asset.variations:

                # Check for local transforms against the asset which are added
                # to and may override variations defined for the field.
                for variation_name, variation_asset \
                        in asset.variations.items():

                    if variation_name in variations:

                        # Don't use the local transforms if there's
                        # transforms defined the variation.
                        continue

                    if not isinstance(variation_asset, Asset):
                        variation_asset = Asset(variation_asset)

                    variations[variation_name] = [
                        BaseTransform.from_json_type(t)
                        for t in variation_asset.local_transforms
                    ]

            # Ensure the system set '--draft--' variation is never updated
            variations.pop('--draft--', None)

            if variations:

                # Add the tranform information for the asset (the asset,
                # variations and base transforms).
                assets_to_transform.append((
                    asset,
                    variations,
                    [
                        BaseTransform.from_json_type(t)
                        for t in asset.base_transforms
                    ]
                ))

        # Image set fields
        for field in image_set_fields:

            image_set = state.form_data.get(field)

            if image_set:
                current_image_set = document.get(field)

                images_to_regenerate = {}

                for version, asset in image_set.images.items():

                    if asset.temporary:

                        # This a new asset so persist it
                        assets_to_persist.append(asset)
                        images_to_regenerate[version] = asset

                        if current_image_set \
                                and current_image_set.images.get(version):

                            # There's an old version of this asset so remove
                            # it.
                            assets_to_remove.append(
                                current_image_set.images[version]
                            )

                    else:

                        # Determine if we need to generate variations of this
                        # asset.
                        modified = state.form[field].modified_base_transforms

                        if version == image_set.base_version:
                            for v in asset.variations.keys():

                                if v == image_set.base_version \
                                        and v in modified:
                                    images_to_regenerate[version] = asset
                                    break

                                if v not in image_set.images and v in modified:
                                    images_to_regenerate[version] = asset
                                    break

                        else:
                            if version in modified:
                                images_to_regenerate[version] = asset

                if current_image_set:
                    for version, asset in current_image_set.images.items():
                        if not image_set.images.get(version):

                            # The new image set doesn't contain this version
                            # so we need to remove the associated image asset.
                            assets_to_remove.append(asset)

                # Build the transform instructions required to regenerate
                # variations for the assets in the image set.

                # Get variations defined for the field against the manage
                # config.
                field_variations = state.manage_config.asset_variations.get(
                    field,
                    {}
                )

                for version, asset in images_to_regenerate.items():

                    # Copy the field variations structure
                    variations = {
                        k: [i for i in v]
                        for k, v in field_variations.items()
                    }

                    # If this isn't the base version of the image set remove
                    # any variations not related to the verison.
                    if version != image_set.base_version:
                        if version in variations:
                            variations = {version: variations[version]}
                        else:
                            variations = {}

                    if '--thumb--' in asset.variations:

                        # Cater for regenerating the thumbnail.
                        variations['--thumb--'] = flask.current_app.config.get(
                            'ASSET_THUMB_VARIATION',
                            [
                                Fit(480),
                                Output('jpg', 75)
                            ]
                        )

                        if version in image_set.base_transforms:
                            variations['--thumb--'] = [
                                BaseTransform.from_json_type(t)
                                for t in image_set.base_transforms[version]
                            ] + variations['--thumb--']

                    # Ensure the system set '--draft--' variation is never
                    # updated.
                    variations.pop('--draft--', None)

                    if variations:

                        # Build the local transforms for the asset using the
                        # base transforms and defined transforms. Unlike with
                        # standard assets, assets in image sets don't have
                        # separate base transforms (these are stored directly
                        # against the image set instead).

                        for k, v in variations.items():

                            base_transforms = []

                            if k in image_set.base_transforms:

                                base_transforms = [
                                    BaseTransform.from_json_type(t)
                                    for t in image_set.base_transforms[k]
                                ]

                            variations[k] = base_transforms + v

                        # Add the tranform information for the asset (the asset,
                        # variations and base transforms).
                        assets_to_transform.append((asset, variations, []))

            else:
                if document.get(field):

                    # Image set has been removed so remove all image assets
                    # associated with it.
                    for image in document[field].images.values():
                        assets_to_remove.append(image)

        # Store assets permanently
        asset_mgr = flask.current_app.asset_mgr
        asset_mgr.persist_many(assets_to_persist)

        # Generate variations
        asset_mgr.generate_variations_for_many(
            [a[0] for a in assets_to_transform],
            {a[0].key: a[1] for a in assets_to_transform},
            {a[0].key: a[2] for a in assets_to_transform}
        )

        if asset_fields or image_set_fields:

            update_fields = asset_fields + image_set_fields

            # Update the document
            if hasattr(document, 'logged_update'):
                document.logged_update(
                    state.manage_user,
                    {
                        field: state.form_data.get(field) or None
                        for field in update_fields
                    },
                    *update_fields
                )

            else:
                for field in update_fields:
                    setattr(
                        document,
                        field,
                        state.form_data.get(field) or None
                    )

                document.update(*update_fields)

        if state.remove_assets:

            # Remove assets
            asset_mgr.remove_many(assets_to_remove)

    return store_assets

def validate(error_msg='Please review your submission'):
    """
    Return a function that will call validate against `state.form`. If the form
    is valid the function will return `True` or `False` if not.

    Optionally an `error_msg` can be passed, if the form fails to validate this
    will be flashed to the user.
    """

    def validate(state):
        assert state.form, 'No form to validate against'

        if state.form.validate():
            return True

        flask.flash(error_msg, 'error')
        return False

    return validate
