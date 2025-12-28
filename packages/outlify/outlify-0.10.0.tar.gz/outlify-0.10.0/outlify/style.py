from enum import Enum
from typing import NamedTuple

from outlify._ansi import (  # noqa: F401
    AnsiBackColorsCodes,
    AnsiCodes,
    AnsiColorsCodes,
    AnsiStylesCodes,
    Back,
    Colors,
    Styles,
)


class Align(Enum):
    """Represent text alignment options."""

    left = "left"
    center = "center"
    right = "right"


class BorderStyle(NamedTuple):
    """Represent border styling."""

    lt: str
    rt: str
    lb: str
    rb: str
    headers: str
    sides: str

if __name__ == "__main__":  # pragma: no cover
    print(f"Outlify allow you {Styles.bold}styling{Styles.reset} your text")
    print(
        f"for example, you can {Colors.blue}color{Colors.reset} your text, "
        f"{Styles.underline}underline{Styles.reset} it.",
    )
