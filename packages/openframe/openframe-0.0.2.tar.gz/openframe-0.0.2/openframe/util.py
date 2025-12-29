from enum import Enum
from typing import Tuple


class ContentMode(Enum):
    FILL = "fill"
    FIT = "fit"
    NONE = "none"

class Layer(Enum):
    TOP = "top"
    BOTTOM = "bottom"
    
class AnchorPoint(Enum):
    TOP_RIGHT = "top-right"
    TOP_LEFT = "top-left"
    BOTTOM_RIGHT = "bottom-right"
    BOTTOM_LEFT = "bottom-right"
    CENTER = "center"

class TextAlign(Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"

def _compute_scaled_size(
    original_size: Tuple[int, int],
    target_size: Tuple[int, int],
    mode: ContentMode,
) -> Tuple[int, int]:
    """Return dimensions computed by the requested content mode.

    Args:
        original_size: Width and height of the source image.
        target_size: Bounding width and height that the clip must respect.
        mode: Behavior that controls how the image is scaled.

    Returns:
        Tuple[int, int]: Width and height to use when resizing.
    """

    if mode == ContentMode.NONE:
        return original_size

    orig_width, orig_height = original_size
    target_width, target_height = target_size

    width_ratio = target_width / orig_width
    height_ratio = target_height / orig_height
    scale = (
        max(width_ratio, height_ratio)
        if mode == ContentMode.FILL
        else min(width_ratio, height_ratio)
    )

    scaled_width = max(1, round(orig_width * scale))
    scaled_height = max(1, round(orig_height * scale))

    if mode == ContentMode.FILL:
        return (
            max(target_width, scaled_width),
            max(target_height, scaled_height),
        )

    return (
        min(target_width, scaled_width),
        min(target_height, scaled_height),
    )
