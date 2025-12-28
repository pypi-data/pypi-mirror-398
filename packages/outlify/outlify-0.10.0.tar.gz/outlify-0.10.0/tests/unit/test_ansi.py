import pytest

from outlify._ansi import Colors, Back, Styles, AnsiCodes


class IDAnsiCodes(AnsiCodes):
    pink   = [38, 5, 207]
    orange = [38, 5, 208]

class RGBAnsiCodes(AnsiCodes):
    pink   = [38, 2, 255, 192, 203]
    orange = [38, 2, 255, 128, 0]

CustomID = IDAnsiCodes()
CustomRGB = RGBAnsiCodes()

@pytest.mark.unit
@pytest.mark.parametrize(
    'color,result',
    [
        (CustomID.pink,    '\033[38;5;207m'),
        (CustomID.orange,  '\033[38;5;208m'),
        (CustomRGB.pink,   '\033[38;2;255;192;203m'),
        (CustomRGB.orange, '\033[38;2;255;128;0m'),
    ]
)
def test_custom_ansicodes(color: AnsiCodes, result: str):
    assert color == result


@pytest.mark.unit
@pytest.mark.parametrize(
    'color,result',
    [
        # standard colors
        (Colors.black,   '\033[30m'),
        (Colors.red,     '\033[31m'),
        (Colors.green,   '\033[32m'),
        (Colors.yellow,  '\033[33m'),
        (Colors.blue,    '\033[34m'),
        (Colors.magenta, '\033[35m'),
        (Colors.cyan,    '\033[36m'),
        (Colors.white,   '\033[37m'),

        # bright colors
        (Colors.gray,    '\033[90m'),
        (Colors.crimson, '\033[91m'),
        (Colors.lime,    '\033[92m'),
        (Colors.gold,    '\033[93m'),
        (Colors.skyblue, '\033[94m'),
        (Colors.violet,  '\033[95m'),
        (Colors.aqua,    '\033[96m'),
        (Colors.snow,    '\033[97m'),

        (Colors.reset, '\033[39m'),
    ]
)
def test_colors(color: AnsiCodes, result: str):
    assert color == result


@pytest.mark.unit
@pytest.mark.parametrize(
    'back,result',
    [
        # standard colors
        (Back.black,   '\033[40m'),
        (Back.red,     '\033[41m'),
        (Back.green,   '\033[42m'),
        (Back.yellow,  '\033[43m'),
        (Back.blue,    '\033[44m'),
        (Back.magenta, '\033[45m'),
        (Back.cyan,    '\033[46m'),
        (Back.white,   '\033[47m'),

        # bright colors
        (Back.gray,    '\033[100m'),
        (Back.crimson, '\033[101m'),
        (Back.lime,    '\033[102m'),
        (Back.gold,    '\033[103m'),
        (Back.skyblue, '\033[104m'),
        (Back.violet,  '\033[105m'),
        (Back.aqua,    '\033[106m'),
        (Back.snow,    '\033[107m'),

        (Back.reset, '\033[49m'),
    ]
)
def test_back(back: AnsiCodes, result: str):
    assert back == result


@pytest.mark.unit
@pytest.mark.parametrize(
    'style,result',
    [
        # styles
        (Styles.bold,        '\033[1m'),
        (Styles.dim,         '\033[2m'),
        (Styles.italic,      '\033[3m'),
        (Styles.underline,   '\033[4m'),
        (Styles.blink,       '\033[5m'),
        (Styles.inverse,     '\033[7m'),
        (Styles.hidden,      '\033[8m'),
        (Styles.crossed_out, '\033[9m'),

        # reset styles
        (Styles.reset_bold,        '\033[22m'),
        (Styles.reset_dim,         '\033[22m'),
        (Styles.reset_italic,      '\033[23m'),
        (Styles.reset_underline,   '\033[24m'),
        (Styles.reset_blink,       '\033[25m'),
        (Styles.reset_inverse,     '\033[27m'),
        (Styles.reset_hidden,      '\033[28m'),
        (Styles.reset_crossed_out, '\033[29m'),

        (Styles.reset, '\033[0m'),
    ]
)
def test_styles(style: AnsiCodes, result: str):
    assert style == result
