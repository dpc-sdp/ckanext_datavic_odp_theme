import logging
import mimetypes
from typing import Optional

import requests

import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)


def datavic_organization_upload(key, data, errors, context):
    """Process image upload or URL for an organization.

    HACK: we're adding an error under the `Logo` key, because client want to
    rename the field, but changing the field machine name will throw away uploaded
    previously files"""
    image_upload = tk.request.files.get("image_upload")
    errors[("Logo",)] = []

    if image_upload:
        mimetype = image_upload.mimetype
    else:
        image_url = data.get(("image_url",))
        if not image_url.startswith("http"):
            return
        if not image_url:
            return
        try:
            mimetype = _get_mimetype_from_url(image_url)
        except ValueError as e:
            errors[("Logo",)].append(str(e))
            return

    if not mimetype:
        return

    if not _is_valid_image_extension(mimetype):
        errors[("Logo",)].append(
            (
                "Image format is not supported. "
                "Select an image in one of the following formats: "
                "JPG, JPEG, GIF, PNG, BMP, SVG."
            )
        )


def _is_valid_image_extension(mimetype: str) -> bool:
    """Check if the mimetype corresponds to a valid image extension."""
    valid_extensions = ["jpg", "png", "jpeg", "gif", "bmp", "svg"]
    extension = mimetypes.guess_extension(mimetype)
    return extension and extension.strip(".").lower() in valid_extensions


def _get_mimetype_from_url(image_url: str) -> Optional[str]:
    """Attempt to get the mimetype of an image given its URL."""
    try:
        response = requests.head(image_url, allow_redirects=True, timeout=5)
        response.raise_for_status()
        return response.headers.get("Content-Type")
    except requests.RequestException as e:
        raise ValueError(f"Error fetching image: {e}")
