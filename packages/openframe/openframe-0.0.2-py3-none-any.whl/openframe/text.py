from dataclasses import dataclass, field
from functools import lru_cache
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont

from openframe.element import FrameElement
from openframe.util import TextAlign

DEFAULT_FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"

@lru_cache(maxsize=256)
def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font from disk and cache it by path and size.

    Args:
        path: File path for the font.
        size: Font size in points.

    Returns:
        ImageFont.FreeTypeFont: Loaded font instance.
    """

    return ImageFont.truetype(path, size)


@dataclass
class TextClip(FrameElement):
    """Represents a text overlay with timing, styling, and position.

    Attributes:
        text: The text string to render.
        start_time: Seconds at which the clip appears.
        duration: Seconds the clip stays on-screen.
        position: (x, y) pixel coordinates for placement.
        size: Optional bounding box size for alignment.
        font_size: Point size used for rendering text.
        color: RGBA tuple used to draw the text.
        font: Loaded FreeType font instance for rendering.
        text_align: Horizontal alignment when positioning the text.
    """
    
    text: str
    font_size: int
    color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    font: str = DEFAULT_FONT_PATH
    text_align: TextAlign = TextAlign.LEFT
    image: Image.Image = field(init=False)
    _text_size: Tuple[int, int] = field(init=False)
    _bbox_size: Tuple[int, int] = field(init=False)

    def __post_init__(self) -> None:
        """Pre-render text into an RGBA image for fast compositing."""

        font = self.load_font()
        probe = Image.new('RGBA', (1, 1))
        probe_draw = ImageDraw.Draw(probe)
        left, top, right, bottom = probe_draw.multiline_textbbox((0, 0), self.text, font=font)
        width = max(1, right - left)
        height = max(1, bottom - top)
        self._text_size = (width, height)
        if self.size is None:
            self._bbox_size = self._text_size
        else:
            box_width = max(1, self.size[0])
            box_height = max(1, self.size[1])
            self._bbox_size = (box_width, box_height)

        self.image = Image.new('RGBA', self._bbox_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(self.image)
        box_width = self._bbox_size[0]
        text_width = self._text_size[0]
        x_pos = {
            TextAlign.LEFT: 0,
            TextAlign.CENTER: (box_width - text_width) // 2,
            TextAlign.RIGHT: box_width - text_width,
        }.get(self.text_align, 0)
        draw.multiline_text(
            (x_pos - left, -top),
            self.text,
            font=font,
            fill=self.color,
            align=self.text_align.value,
        )

    def load_font(self) -> ImageFont.FreeTypeFont:
        """Load the configured font at the clip's size.

        Returns:
            ImageFont.FreeTypeFont: The font ready for rendering text.
        """

        return _load_font(self.font, self.font_size)

    def _render_content(self, canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
        """Draw the text clip on the provided overlay context.

        Args:
            canvas: Overlay canvas matching the target frame size.
            draw: Drawing helper for text rendering.
        """

        canvas.paste(self.image, (0, 0), self.image)

    @property
    def bounding_box_size(self) -> Tuple[int, int]:
        """Compute the pixel area required to render the clip's text."""

        return self._bbox_size
