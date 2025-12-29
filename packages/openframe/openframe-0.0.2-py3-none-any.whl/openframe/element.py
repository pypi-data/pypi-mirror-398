from dataclasses import dataclass
from typing import Tuple
from PIL import Image, ImageDraw

from openframe.util import AnchorPoint


@dataclass(kw_only=True)
class FrameElement:
    """Base element that tracks timing and fade animations for clips."""

    start_time: float
    duration: float
    position: Tuple[int, int]
    anchor_point: AnchorPoint = AnchorPoint.TOP_LEFT
    size: Tuple[int, int] | None = None
    opacity: float = 1.0
    fade_in_duration: float = 0.0
    fade_out_duration: float = 0.0

    @property
    def end_time(self) -> float:
        """Return the time when the element stops being visible.

        Returns:
            float: End time in seconds.
        """

        return self.start_time + self.duration

    @property
    def bounding_box_size(self) -> Tuple[int, int]:
        raise NotImplementedError("FrameElement.bounding_box_size should be implemented by subclasses.")
        

    @property
    def render_position(self) -> Tuple[int, int]:
        """Translate the configured anchor-relative position into a top-left coordinate."""

        width, height = self.bounding_box_size
        base_x, base_y = self.position
        offsets = {
            AnchorPoint.TOP_LEFT: (0, 0),
            AnchorPoint.TOP_RIGHT: (-width, 0),
            AnchorPoint.BOTTOM_LEFT: (0, -height),
            AnchorPoint.BOTTOM_RIGHT: (-width, -height),
            AnchorPoint.CENTER: (-width // 2, -height // 2),
        }

        offset_x, offset_y = offsets.get(self.anchor_point, (0, 0))
        return base_x + offset_x, base_y + offset_y

    def is_visible(self, t: float) -> bool:
        """Report whether the element is visible at the requested time.

        Args:
            t: Current time in seconds.

        Returns:
            bool: True if the element should be drawn at time t.
        """

        return self.start_time <= t < self.end_time

    def opacity_at(self, t: float) -> float:
        """Compute opacity based on fade-in and fade-out durations.

        Args:
            t: Current time in seconds.

        Returns:
            float: Fractional opacity between 0.0 and 1.0.
        """

        if not self.is_visible(t):
            return 0.0

        target_opacity = max(0.0, min(1.0, self.opacity))
        if target_opacity == 0.0:
            return 0.0

        opacity = 1.0
        fade_in = min(self.fade_in_duration, self.duration)
        if fade_in > 0:
            fade_in_end = self.start_time + fade_in
            if t < fade_in_end:
                opacity *= (t - self.start_time) / fade_in

        fade_out = min(self.fade_out_duration, self.duration)
        if fade_out > 0:
            fade_out_start = self.end_time - fade_out
            if t >= fade_out_start:
                opacity *= (self.end_time - t) / fade_out

        return max(0.0, min(1.0, target_opacity * opacity))

    def render(self, canvas: Image.Image, t: float) -> None:
        """Draw the element onto the canvas with fade handled via an overlay.

        Args:
            canvas: Frame canvas to compose onto.
            t: Current time in seconds.
        """

        opacity = self.opacity_at(t)
        if opacity <= 0:
            return

        width, height = self.bounding_box_size
        overlay = Image.new('RGBA', (max(1, width), max(1, height)), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        self._render_content(overlay, overlay_draw)

        if opacity < 1.0:
            overlay = self._apply_opacity(overlay, opacity)

        canvas.paste(overlay, self.render_position, overlay)

    def _render_content(self, canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
        """Render element content onto an overlay before fade adjustments.

        Args:
            canvas: Overlay canvas matching the target frame size.
            draw: Drawing context for rendering operations.
        """

        raise NotImplementedError("FrameElement._render_content should be implemented by subclasses.")

    @staticmethod
    def _apply_opacity(image: Image.Image, opacity: float) -> Image.Image:
        """Return a copy of the image with its alpha scaled by opacity.

        Args:
            image: Source RGBA image.
            opacity: Value between 0.0 and 1.0 to scale alpha.

        Returns:
            Image.Image: Image with adjusted transparency.
        """

        if opacity >= 1.0:
            return image

        result = image.copy()
        alpha = result.getchannel('A').point(lambda value: int(value * opacity))
        result.putalpha(alpha)
        return result
