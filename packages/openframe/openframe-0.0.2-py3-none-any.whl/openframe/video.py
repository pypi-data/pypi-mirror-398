from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List, Tuple

import av
from PIL import Image, ImageDraw

from openframe.element import FrameElement
from openframe.util import ContentMode, _compute_scaled_size


def _scale_frame(
    frame: Image.Image,
    target_size: Tuple[int, int],
    mode: ContentMode,
) -> Image.Image:
    """Resize the frame according to the requested content mode.

    Args:
        frame: Source image to adjust.
        target_size: Desired width and height.
        mode: Content mode that controls scaling behavior.

    Returns:
        Image.Image: Adjusted frame image.
    """

    width = max(1, target_size[0])
    height = max(1, target_size[1])
    scaled = _compute_scaled_size(frame.size, (width, height), mode)
    resized = frame.resize(scaled, Image.Resampling.LANCZOS)

    if mode == ContentMode.FILL:
        left = (resized.width - width) // 2
        top = (resized.height - height) // 2
        right = left + width
        bottom = top + height
        return resized.crop((left, top, right, bottom))

    return resized


@lru_cache(maxsize=4)
def _decode_raw_frames(path: str) -> Tuple[Tuple[Image.Image, ...], Tuple[float, ...]]:
    """Decode a video source freeing its frames and timestamps.

    Args:
        path: File path to the video asset.

    Returns:
        Tuple[Tuple[Image.Image, ...], Tuple[float, ...]]: Decoded frames and their timestamps.
    """

    container = av.open(path)
    stream = container.streams.video[0]
    frames: List[Image.Image] = []
    timestamps: List[float] = []
    time_base = float(stream.time_base or 0.0)
    estimated_rate = float(stream.average_rate or 30.0)
    index = 0

    for frame in container.decode(stream):
        if frame.pts is not None:
            timestamp = float(frame.pts * time_base)
        elif frame.time is not None:
            timestamp = float(frame.time)
        else:
            timestamp = index / estimated_rate

        frames.append(frame.to_image().convert('RGBA'))
        timestamps.append(timestamp)
        index += 1

    container.close()

    if not frames:
        raise ValueError("Video source contains no frames.")

    return tuple(frames), tuple(timestamps)


def _prepare_frames(
    path: str,
    size: Tuple[int, int] | None,
    content_mode: ContentMode,
) -> Tuple[List[Image.Image], Tuple[float, ...]]:
    """Prepare processed frames for the requested configuration.

    Args:
        path: Video source path.
        size: Optional target size for scaling.
        content_mode: Determines how the frame is resized.

    Returns:
        Tuple[List[Image.Image], Tuple[float, ...]]: Frames ready for rendering and their timestamps.
    """

    raw_frames, timestamps = _decode_raw_frames(path)
    if size is None or content_mode == ContentMode.NONE:
        return list(raw_frames), timestamps

    scaled_frames = [
        _scale_frame(frame, size, content_mode) for frame in raw_frames
    ]
    return scaled_frames, timestamps


@dataclass(kw_only=True)
class VideoClip(FrameElement):
    """Render a series of video frames as a frame element.

    Looping can be enabled so the clip repeats whenever the requested duration exceeds the source length.
    """

    source_path: str
    source_start: float = 0.0
    source_end: float | None = None
    content_mode: ContentMode = ContentMode.NONE
    loop_enable: bool = False
    _frames: List[Image.Image] = field(init=False)
    _frame_offsets: List[float] = field(init=False)
    _visible_duration: float = field(init=False)
    _source_duration: float = field(init=False)
    _current_frame: Image.Image | None = field(init=False, default=None)

    def __post_init__(self) -> None:
        """Load and slice frames that match the requested source range.

        Returns:
            None
        """

        frames, timestamps = _prepare_frames(
            self.source_path,
            self.size,
            self.content_mode,
        )

        start_time = max(0.0, self.source_start)
        end_time = self.source_end
        start_index = bisect_left(timestamps, start_time)
        end_index = len(timestamps) if end_time is None else bisect_right(timestamps, end_time)

        if start_index >= end_index:
            raise ValueError("No frames available within the requested source range.")

        selected_frames = frames[start_index:end_index]
        selected_timestamps = timestamps[start_index:end_index]
        base = selected_timestamps[0]

        self._frames = selected_frames
        self._frame_offsets = [ts - base for ts in selected_timestamps]
        self._source_duration = self._compute_source_duration(selected_timestamps)
        if self.loop_enable:
            self._visible_duration = self.duration
        else:
            self._visible_duration = min(self.duration, self._source_duration)

    def is_visible(self, t: float) -> bool:
        """Report whether the clip should still draw its frames.

        Args:
            t: Current timeline time in seconds.

        Returns:
            bool: True while the source has remaining frames.
        """

        if not super().is_visible(t):
            return False

        return t < self.start_time + self._visible_duration

    def render(self, canvas: Image.Image, t: float) -> None:
        """Select the correct frame before delegating to the base renderer.

        Args:
            canvas: Frame canvas to render onto.
            t: Timeline time in seconds.

        Returns:
            None
        """

        self._current_frame = self._frame_for_time(t)
        try:
            super().render(canvas, t)
        finally:
            self._current_frame = None

    def _frame_for_time(self, t: float) -> Image.Image:
        """Pick the frame that most closely matches the requested timeline.

        Args:
            t: Timeline time in seconds.

        Returns:
            Image.Image: Frame that should be drawn.
        """

        elapsed_base = max(0.0, t - self.start_time)
        if self.loop_enable and self._source_duration > 0:
            elapsed = elapsed_base % self._source_duration
        else:
            elapsed = min(elapsed_base, self._visible_duration)
        index = bisect_right(self._frame_offsets, elapsed) - 1
        if index < 0:
            index = 0
        if index >= len(self._frames):
            index = len(self._frames) - 1
        return self._frames[index]

    def _render_content(self, canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
        """Paint the current frame onto the overlay canvas.

        Args:
            canvas: Overlay canvas matching the clip bounds.
            draw: Drawing helper (unused).

        Returns:
            None
        """

        if self._current_frame is None:
            return
        canvas.paste(self._current_frame, (0, 0), self._current_frame)

    def _compute_source_duration(self, timestamps: List[float]) -> float:
        """Estimate how long the decoded source actually plays.

        Args:
            timestamps: Timeline timestamps of the decoded frames.

        Returns:
            float: Estimated duration of the source clip.
        """

        if len(timestamps) <= 1:
            return self.duration

        last_offset = timestamps[-1] - timestamps[0]
        last_interval = timestamps[-1] - timestamps[-2]
        frame_gap = max(last_interval, 1 / 30)
        return last_offset + frame_gap

    @property
    def bounding_box_size(self) -> Tuple[int, int]:
        """Return the size that will be used when creating overlays.

        Returns:
            Tuple[int, int]: Width and height of the clip.
        """

        if self.size is not None:
            return (max(1, self.size[0]), max(1, self.size[1]))

        return self._frames[0].size
