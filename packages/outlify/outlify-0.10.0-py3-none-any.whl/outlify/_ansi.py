from collections.abc import Sequence

__all__ = [
    "AnsiBackColorsCodes",
    "AnsiCodes",
    "AnsiColorsCodes",
    "AnsiStylesCodes",
    "Back",
    "Colors",
    "Styles",
]


CSI = "\033["  # Control Sequence Introducer
SGR = "m"      # Select Graphic Rendition suffix


def code_to_ansi(*codes: int) -> str:
    return f"{CSI}{';'.join(map(str, codes))}{SGR}"


class AnsiCodes:
    def __init__(self) -> None:
        for name in (name for name in dir(self) if not name.startswith("_")):
            value = getattr(self, name)
            if isinstance(value, Sequence):
                setattr(self, name, code_to_ansi(*value))
            else:
                setattr(self, name, code_to_ansi(value))


class AnsiColorsCodes(AnsiCodes):
    # standard colors
    black   : str = 30
    red     : str = 31
    green   : str = 32
    yellow  : str = 33
    blue    : str = 34
    magenta : str = 35
    cyan    : str = 36
    white   : str = 37

    # bright colors
    gray    : str = 90
    crimson : str = 91
    lime    : str = 92
    gold    : str = 93
    skyblue : str = 94
    violet  : str = 95
    aqua    : str = 96
    snow    : str = 97

    # reset all colors
    reset   : str = 39


class AnsiBackColorsCodes(AnsiCodes):
    # standard colors
    black   : str = 40
    red     : str = 41
    green   : str = 42
    yellow  : str = 43
    blue    : str = 44
    magenta : str = 45
    cyan    : str = 46
    white   : str = 47

    # bright colors
    gray    : str = 100
    crimson : str = 101
    lime    : str = 102
    gold    : str = 103
    skyblue : str = 104
    violet  : str = 105
    aqua    : str = 106
    snow    : str = 107

    # reset all colors
    reset   : str = 49


class AnsiStylesCodes(AnsiCodes):
    bold              : str = 1
    dim               : str = 2
    italic            : str = 3
    underline         : str = 4
    blink             : str = 5
    inverse           : str = 7
    hidden            : str = 8
    crossed_out       : str = 9

    reset_bold        : str = 22
    reset_dim         : str = 22
    reset_italic      : str = 23
    reset_underline   : str = 24
    reset_blink       : str = 25
    reset_inverse     : str = 27
    reset_hidden      : str = 28
    reset_crossed_out : str = 29

    # reset all styles include colors/styles
    reset             : str = 0


Colors = AnsiColorsCodes()
Back = AnsiBackColorsCodes()
Styles = AnsiStylesCodes()
