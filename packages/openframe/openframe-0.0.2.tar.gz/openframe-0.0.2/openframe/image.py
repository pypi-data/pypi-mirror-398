from dataclasses import dataclass, field
from functools import lru_cache
from typing import Tuple
from PIL import Image, ImageDraw

from openframe.element import FrameElement
from openframe.util import ContentMode, _compute_scaled_size

@lru_cache(maxsize=256)
def _load_image(path: str) -> Image.Image:
    """Load an image from disk and return it as RGBA.

    Args:
        path: File path for the image asset.

    Returns:
        Image.Image: Loaded RGBA image.
    """

    with Image.open(path) as source:
        return source.convert('RGBA')


@lru_cache(maxsize=512)
def _load_resized_image(
    path: str,
    size: Tuple[int, int],
    content_mode: ContentMode,
) -> Image.Image:
    """Load, resize, and crop an image based on the content mode.

    Args:
        path: File path for the image asset.
        size: Target size for rendering.
        content_mode: Scaling mode.

    Returns:
        Image.Image: Processed RGBA image ready for rendering.
    """

    loaded = _load_image(path)
    scaled = _compute_scaled_size(loaded.size, size, content_mode)
    resized = loaded.resize(scaled, Image.Resampling.LANCZOS)

    if content_mode == ContentMode.FILL:
        target_width, target_height = size
        left = (resized.width - target_width) // 2
        top = (resized.height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        return resized.crop((left, top, right, bottom))

    return resized

@dataclass
class ImageClip(FrameElement):
    """Represents an image overlay with timing, size, and placement."""

    path: str
    image: Image.Image = field(init=False)
    content_mode: ContentMode = ContentMode.NONE

    def __post_init__(self) -> None:
        """Load and cache the RGBA image, resizing when needed."""

        if self.size is None or self.content_mode == ContentMode.NONE:
            self.image = _load_image(self.path)
            return

        self.image = _load_resized_image(self.path, self.size, self.content_mode)

    def _render_content(self, canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
        """Paste the clip's image onto the overlay canvas using its alpha channel.

        Args:
            canvas: Overlay canvas that matches the target frame size.
            draw: Drawing helper (unused) that keeps signature consistent.
        """

        canvas.paste(self.image, (0, 0), self.image)

    @property
    def bounding_box_size(self) -> Tuple[int, int]:
        """Return the dimensions of the image that will be drawn."""

        return self.image.size
