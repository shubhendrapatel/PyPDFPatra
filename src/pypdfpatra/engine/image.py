"""
pypdfpatra.engine.image
~~~~~~~~~~~~~~~~~~~~~~~
Handles fetching, caching, and determining the intrinsic dimensions of images.
Supports local file paths and HTTP/HTTPS URLs.
"""

from __future__ import annotations
import os
import io
from urllib.request import urlopen
from urllib.error import URLError
from PIL import Image

# Simple cache so we don't fetch/parse the same image multiple times during layout & render
_IMAGE_CACHE = {}


def get_image_info(src: str, base_url: str = "") -> dict | None:
    """
    Given an image source URL or file path, fetches the image (or reads from cache)
    and returns its intrinsic pixel dimensions.

    Args:
        src: The image URL or local file path.
        base_url: The base directory/URL if `src` is relative.

    Returns:
        A dictionary `{"width": float, "height": float, "path": str, "is_url": bool}`,
        or None if the image could not be loaded.
    """
    if not src:
        return None

    is_url = src.startswith("http://") or src.startswith("https://")

    # Resolve relative local paths using base_url if applicable
    full_path = src
    if not is_url:
        if base_url and not os.path.isabs(src):
            full_path = os.path.join(base_url, src)

        full_path = os.path.normpath(full_path)

    cache_key = full_path

    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    try:
        if is_url:
            with urlopen(full_path) as response:
                image_data = response.read()
                img = Image.open(io.BytesIO(image_data))
                width, height = img.size

                # We need to save remote images locally to a temp file because fpdf.image
                # usually takes a filepath (or PIL object, but for simplicity we can cache locally).
                # Actually, fpdf2 CAN sometimes take a URL, but caching locally avoids network latency during render.
                # Let's keep it simple and just cache the dimensions and raw URL for now.
        else:
            if not os.path.exists(full_path):
                print(f"pypdfpatra - WARNING - Image not found: {full_path}")
                _IMAGE_CACHE[cache_key] = None
                return None

            img = Image.open(full_path)
            width, height = img.size

        info = {
            "width": float(width),
            "height": float(height),
            "src": full_path,
        }

        _IMAGE_CACHE[cache_key] = info
        return info

    except Exception as e:
        print(f"pypdfpatra - WARNING - Failed to load image {full_path}: {e}")
        _IMAGE_CACHE[cache_key] = None
        return None
