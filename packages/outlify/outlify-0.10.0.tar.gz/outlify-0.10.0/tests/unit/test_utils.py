from typing import Union
from unittest.mock import patch

import pytest

from outlify.style import Align
from outlify._utils import parse_title_align, resolve_width


@pytest.mark.unit
@pytest.mark.parametrize(
    'align,result',
    [
        ('left', Align.left),
        ('center', Align.center),
        ('right', Align.right),
        (Align.left, Align.left),
        (Align.center, Align.center),
        (Align.right, Align.right),
    ]
)
def test_resolve_title_align(align: Union[str, Align], result: Align):
    assert parse_title_align(align) == result


@pytest.mark.unit
@pytest.mark.parametrize(
    'width,error,result',
    [
        (1, None, 1),
        ({}, TypeError, None),
        ([], TypeError, None),
        ((), TypeError, None),
    ]
)
def test_resolve_width_errors(width: int, error, result: int):
    if error is None:
        assert resolve_width(width) == result
        return
    with pytest.raises(error):
        resolve_width(width)


@pytest.mark.unit
@pytest.mark.parametrize("exception", [AttributeError("test"), OSError("test")])
def test_resolve_width_terminal_fallback(exception):
    with patch("shutil.get_terminal_size", side_effect=exception):
        assert resolve_width(None) == 80
