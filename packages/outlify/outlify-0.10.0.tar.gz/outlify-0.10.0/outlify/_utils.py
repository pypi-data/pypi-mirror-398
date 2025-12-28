import shutil
from collections.abc import Sequence
from typing import Any

from outlify.style import Align, Styles


def resolve_width(width: int | None) -> int:
    if isinstance(width, int):
        return width
    if width is not None:
        error = f"Invalid type for width: {width} is not int"
        raise TypeError(error)

    try:
        return shutil.get_terminal_size().columns
    except (AttributeError, OSError):
        return 80  # Fallback width


def parse_title_align(align: str | Align) -> Align:
    return _parse_class(align, Align)


def _parse_class(element: str | Any, cls: Any) -> Any:
    if isinstance(element, cls):
        return element
    return cls(element)


def parse_styles(codes: Sequence | None) -> str:
    return "".join(codes) if codes is not None else ""


def get_reset_by_style(style: str) -> str:
    """Return the appropriate reset code for the given style.

    If the style is empty, returns an empty reset.
    Otherwise, returns the standard reset
    """
    return Styles.reset if style != "" else ""
