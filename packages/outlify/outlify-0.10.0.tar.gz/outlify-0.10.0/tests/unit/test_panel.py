import re
from typing import Union, Optional, Any, Sequence

import pytest

from outlify.panel import PanelBase, Panel, ParamsPanel
from outlify.style import Align, BorderStyle, AnsiCodes


class ReleasedPanelBase(PanelBase):
    def __init__(
            self, content: str = 'test', *, width: Optional[int] = None,
            title: str = '', title_align: Union[str, Align] = 'center',
            title_style: Optional[Sequence[Union[AnsiCodes, str]]] = None,
            subtitle: str = '', subtitle_align: Union[str, Align] = 'center',
            subtitle_style: Optional[Sequence[Union[AnsiCodes, str]]] = None,
            title_conns: str = "", subtitle_conns: str = "",
            border: Union[str | BorderStyle] = '╭╮╰╯─│',
            border_style: Optional[Sequence[Union[AnsiCodes, str]]] = None,
    ):
        super().__init__(
            content, width=width,
            title=title, title_align=title_align, title_style=title_style,
            subtitle=subtitle, subtitle_align=subtitle_align, subtitle_style=subtitle_style,
            title_conns=title_conns, subtitle_conns=subtitle_conns,
            border=border, border_style=border_style
        )

    def _get_content(self, content: str, *, width: int, char: str, border_style: str) -> str:
        return ''


@pytest.mark.unit
@pytest.mark.parametrize(
    'width,result',
    [
        (10, 6),     # small size
        (80, 76),    # default size
        (160, 156),  # big size
        (4, None),
        (0, None),
    ]
)
def test_get_inner_width(width: int, result: int):
    base = ReleasedPanelBase()
    if result is not None:
        assert base._get_inner_width(width) == result
        return

    with pytest.raises(ValueError):
        base._get_inner_width(width)


@pytest.mark.unit
@pytest.mark.parametrize(
    'style,error,result',
    [
        ('╭╮╰╯─│', None, BorderStyle('╭', '╮', '╰', '╯', '─', '│')),
        ('╭╮╰╯─', None, BorderStyle('╭', '╮', '╰', '╯', '─', '')),
        ('123456', None, BorderStyle('1', '2', '3', '4', '5', '6')),
        ('12345', None, BorderStyle('1', '2', '3', '4', '5', '')),
        (123, TypeError, None),
        ('╭╮', ValueError, None),
        ('╭╮╰╯─│{', ValueError, None),
        (BorderStyle('╭', '╮', '╰', '╯', '─', '│'), None, BorderStyle('╭', '╮', '╰', '╯', '─', '│')),
        (BorderStyle('1', '2', '3', '4', '5', '6'), None, BorderStyle('1', '2', '3', '4', '5', '6')),
    ],
)
def test_parse_border_style(
        style: Union[str, BorderStyle], error, result: BorderStyle
):
    base = ReleasedPanelBase()
    if error is None:
        assert base._parse_border(style) == result
        return

    with pytest.raises(error):
        base._parse_border(style)


@pytest.mark.unit
@pytest.mark.parametrize(
    'title,align,char,conns,result',
    [
        ('TITLE', Align.left, '-', '', '-TITLE--------'),
        ('TITLE', Align.right, '-', '[]', '------[TITLE]-'),
        ('TITLE', Align.center, '-', '>-{}-<', '->-{TITLE}-<--'),
    ]
)
def test_get_connectors(title: str, align: Align, char: str, conns: str, result: str):
    print('nned', result)
    assert ReleasedPanelBase()._fill_header(
        title, align=align, width=14, char=char, title_style='', title_style_reset='', border_style='', 
        conns=conns,
    ) == result


@pytest.mark.unit
@pytest.mark.parametrize(
    'conns,error,result',
    [
        ('', None, ('', '')),
        ('[]', None, ('[', ']')),
        ('>-{}-<', None, ('>-{', '}-<')),
        (None, TypeError, None),
        ((), TypeError, None),
        ('[', ValueError, None),
    ]
)
def test_fill_header(conns: str, error, result: str):
    if error is None:
        assert ReleasedPanelBase()._get_connectors(conns) == result
        return
    
    with pytest.raises(error):
        ReleasedPanelBase()._get_connectors(conns)


@pytest.mark.unit
@pytest.mark.parametrize(
    'title,align,left,char,right,result',
    [
        ('TITLE', Align.left, '╭', '-', '╮', '╭-TITLE----╮'),
        ('TITLE', Align.center, '╭', '-', '╮', '╭--TITLE---╮'),
        ('TITLE', Align.right, '╭', '-', '╮', '╭----TITLE-╮'),
        ('fake', Align.center, '╭', '-', '╮', '╭---fake---╮'),
        ('fake', Align.center, '+', ' ', '+', '+   fake   +'),
    ]
)
def test_get_header(title: str, align: Align, left: str, char: str, right: str, result: str):
    base = ReleasedPanelBase()
    assert base._get_header(
        title, align=align, title_style='', title_style_reset='', width=12,
        left=left, char=char, right=right, border_style='', conns=''
    ) == result


@pytest.mark.unit
@pytest.mark.parametrize(
    'line,width,char,indent,result',
    [
        ('test', 6, '|', '', '| test   |'),
        ('test', 6, '|', ' ', '|  test  |'),
        ('test', 6, '|', '-', '| -test  |'),
        ('test', 6, '1', '-', '1 -test  1'),
        ('test', 10, '|', ' ', '|  test      |'),
    ]
)
def test_fill(line: str, width: int, char: str, indent: str, result: str):
    assert ReleasedPanelBase()._fill(
        line, width=width, char=char, indent=indent, border_style=''
    ) == result


@pytest.mark.unit
@pytest.mark.parametrize(
    'text,title,title_align,subtitle,subtitle_align,border,result',
    [
        (
            'test', '', 'center', '', 'center', '╭╮╰╯─│',
            '╭──────────────────╮\n'
            '│ test             │\n'
            '╰──────────────────╯'
        ),
        (
            'test looooong text', '', 'center', '', 'center', '╭╮╰╯─│',
            '╭──────────────────╮\n'
            '│ test looooong    │\n'
            '│ text             │\n'
            '╰──────────────────╯'
        ),
        (
            'test looooonooooooooog', '', 'center', '', 'center', '╭╮╰╯─│',
            '╭──────────────────╮\n'
            '│ test looooonoooo │\n'
            '│ ooooog           │\n'
            '╰──────────────────╯'
        ),

        (
            'test', 'title1', 'left', 'title2', 'left', '╭╮╰╯─│',
            '╭─title1───────────╮\n'
            '│ test             │\n'
            '╰─title2───────────╯'
        ),
        (
            'test', 'title1', 'center', 'title2', 'center', '╭╮╰╯─│',
            '╭──────title1──────╮\n'
            '│ test             │\n'
            '╰──────title2──────╯'
        ),

        (
            'test', 'title1', 'right', 'title2', 'right', '╭╮╰╯─│',
            '╭───────────title1─╮\n'
            '│ test             │\n'
            '╰───────────title2─╯'
        ),
        (
            'test', 'title1', 'left', 'title2', 'center', '╭╮╰╯─│',
            '╭─title1───────────╮\n'
            '│ test             │\n'
            '╰──────title2──────╯'
        ),
        (
            'test', 'title1', 'left', 'title2', 'right', '╭╮╰╯─│',
            '╭─title1───────────╮\n'
            '│ test             │\n'
            '╰───────────title2─╯'
        ),

        (
            'test', 'title1', 'center', 'title2', 'left', '╭╮╰╯─│',
            '╭──────title1──────╮\n'
            '│ test             │\n'
            '╰─title2───────────╯'
        ),
        (
            'test', 'title1', 'center', 'title2', 'right', '╭╮╰╯─│',
            '╭──────title1──────╮\n'
            '│ test             │\n'
            '╰───────────title2─╯'
        ),

        (
            'test', 'title1', 'right', 'title2', 'left', '╭╮╰╯─│',
            '╭───────────title1─╮\n'
            '│ test             │\n'
            '╰─title2───────────╯'
        ),
        (
            'test', 'title1', 'right', 'title2', 'center', '╭╮╰╯─│',
            '╭───────────title1─╮\n'
            '│ test             │\n'
            '╰──────title2──────╯'
        ),

        (
            'test', '', 'center', '', 'center', '╭╮╰╯─',
            '╭──────────────────╮\n'
            ' test             \n'
            '╰──────────────────╯'
        ),
    ]
)
def test_panel(text: str, title: str, title_align: str, subtitle: str, subtitle_align: str, border: str, result: str):
    panel = Panel(
        text, width=20, title=title, subtitle=subtitle,
        title_align=title_align, title_style='',
        subtitle_align=subtitle_align, subtitle_style='',
        border=border, border_style=''
    )
    assert str(panel) == result


@pytest.mark.unit
@pytest.mark.parametrize(
    'params,title,title_align,subtitle,subtitle_align,border,hidden,result',
    [
        (
            {'x': 10, 'y': 20}, '', 'center', '', 'center', '╭╮╰╯─│', None,
            '╭──────────────────╮\n'
            '│ x = 10           │\n'
            '│ y = 20           │\n'
            '╰──────────────────╯'
        ),
        (
            {'x': 10000000000000}, '', 'center', '', 'center', '╭╮╰╯─│', None,
            '╭──────────────────╮\n'
            '│ x = 100000000000 │\n'
            '│     00           │\n'
            '╰──────────────────╯'
        ),

        (
            {'x': 10}, 'title1', 'left', 'title2', 'left', '╭╮╰╯─│', None,
            '╭─title1───────────╮\n'
            '│ x = 10           │\n'
            '╰─title2───────────╯'
        ),
        (
            {'x': 10}, 'title1', 'center', 'title2', 'center', '╭╮╰╯─│', None,
            '╭──────title1──────╮\n'
            '│ x = 10           │\n'
            '╰──────title2──────╯'
        ),
        (
            {'x': 10}, 'title1', 'right', 'title2', 'right', '╭╮╰╯─│', None,
            '╭───────────title1─╮\n'
            '│ x = 10           │\n'
            '╰───────────title2─╯'
        ),

        (
            {'x': 10}, 'title1', 'left', 'title2', 'center', '╭╮╰╯─│', None,
            '╭─title1───────────╮\n'
            '│ x = 10           │\n'
            '╰──────title2──────╯'
        ),
        (
            {'x': 10}, 'title1', 'left', 'title2', 'right', '╭╮╰╯─│', None,
            '╭─title1───────────╮\n'
            '│ x = 10           │\n'
            '╰───────────title2─╯'
        ),

        (
            {'x': 10}, 'title1', 'center', 'title2', 'left', '╭╮╰╯─│', None,
            '╭──────title1──────╮\n'
            '│ x = 10           │\n'
            '╰─title2───────────╯'
        ),
        (
            {'x': 10}, 'title1', 'center', 'title2', 'right', '╭╮╰╯─│', None,
            '╭──────title1──────╮\n'
            '│ x = 10           │\n'
            '╰───────────title2─╯'
        ),

        (
            {'x': 10}, 'title1', 'right', 'title2', 'left', '╭╮╰╯─│', None,
            '╭───────────title1─╮\n'
            '│ x = 10           │\n'
            '╰─title2───────────╯'
        ),
        (
            {'x': 10}, 'title1', 'right', 'title2', 'center', '╭╮╰╯─│', None,
            '╭───────────title1─╮\n'
            '│ x = 10           │\n'
            '╰──────title2──────╯'
        ),

        (
            {'x': 10}, '', 'center', '', 'center', '╭╮╰╯─', None,
            '╭──────────────────╮\n'
            '  x = 10\n'
            '╰──────────────────╯'
        ),

        ## Test hiding parameters
        # default hidden
        (
            {'password': 10}, '', 'center', '', 'center', '╭╮╰╯─', None,
            '╭──────────────────╮\n'
            '  password = *****\n'
            '╰──────────────────╯'
        ),
        (
            {'password': 10, 'x': 20}, '', 'center', '', 'center', '╭╮╰╯─', None,
            '╭──────────────────╮\n'
            '  password = *****\n'
            '  x        = 20\n'
            '╰──────────────────╯'
        ),
        # set empty hidden
        (
            {'password': 10, 'x': 20}, '', 'center', '', 'center', '╭╮╰╯─', [],
            '╭──────────────────╮\n'
            '  password = 10\n'
            '  x        = 20\n'
            '╰──────────────────╯'
        ),
        # set other patterns
        (
            {'password': 10, 'x': 20}, '', 'center', '', 'center', '╭╮╰╯─', ['.*x.*'],
            '╭──────────────────╮\n'
            '  password = 10\n'
            '  x        = *****\n'
            '╰──────────────────╯'
        ),
        # set additionally patterns
        (
            {'password': 10, 'x': 20}, '', 'center', '', 'center', '╭╮╰╯─', ['.*password.*', '.*x.*'],
            '╭──────────────────╮\n'
            '  password = *****\n'
            '  x        = *****\n'
            '╰──────────────────╯'
        ),
        # set different pattern types: string, regex string, regex pattern
        (
            {'word': 10, 'another': 20, 'one-more': 30}, '', 'center', '', 'center', '╭╮╰╯─',
            ['word', '.*other', re.compile('(one|two)?-more.*')],
            '╭──────────────────╮\n'
            '  word     = *****\n'
            '  another  = *****\n'
            '  one-more = *****\n'
            '╰──────────────────╯'
        ),
    ]
)
def test_params_panel(
        params: dict[Any, Any], title: str, title_align: str, subtitle: str, subtitle_align: str,
        border, hidden: list[str],
        result: str
):
    additionally = {}
    if hidden is not None:
        additionally['hidden'] = hidden
    panel = ParamsPanel(
        params, width=20, title=title, subtitle=subtitle,
        title_align=title_align, title_style='',
        subtitle_align=subtitle_align, subtitle_style='',
        border=border, border_style='', params_style='',
        **additionally
    )
    assert str(panel) == result


@pytest.mark.unit
@pytest.mark.parametrize(
    'content',
    [
        (1,),
        ('test',),
        ((1, 2),),
    ]
)
def test_params_panel_invalid_content(content):
    with pytest.raises(TypeError):
        ParamsPanel(content)


@pytest.mark.unit
@pytest.mark.parametrize(
    'panel,result',
    [
        (
            Panel('text', width=10),
            "Panel(border_reset='', content='│ text   │', footer='╰────────╯', header='╭────────╮')",
        ),
        (
            ParamsPanel({'x': 10}, width=10),
            "ParamsPanel(border_reset='', content='│ x = 10 │', footer='╰────────╯', header='╭────────╮', "
            "hidden=(re.compile('.*password.*'), re.compile('.*token.*')), params_reset='', params_style='', "
            "separator=' = ')",
        ),
    ]
)
def test_repr(panel: Panel | ParamsPanel, result: str):
    assert repr(panel) == result
