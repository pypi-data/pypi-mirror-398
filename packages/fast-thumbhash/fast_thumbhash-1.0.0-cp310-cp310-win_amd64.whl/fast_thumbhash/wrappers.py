from pathlib import Path

try:
    from PIL import Image, ImageOps
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

from .fast_thumbhash import rgba_to_thumb_hash


def image_to_thumb_hash(fp: str | bytes | Path) -> bytes:
    """
    Opens given image file and encodes to a ThumbHash.
    Requires Pillow to be installed.
    """
    if not _HAS_PIL:
        raise ImportError("Pillow not installed, please re-install with the [pillow] extra")

    img = Image.open(fp)
    img = img.convert("RGBA")
    img.thumbnail((100, 100))
    img = ImageOps.exif_transpose(img)

    return rgba_to_thumb_hash(img.width, img.height, img.tobytes())