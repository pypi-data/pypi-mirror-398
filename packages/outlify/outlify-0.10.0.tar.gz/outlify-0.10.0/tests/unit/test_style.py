import pytest

from outlify.style import Align


@pytest.mark.unit
@pytest.mark.parametrize(
    'align,result',
    [
        ('left', Align.left),
        ('center', Align.center),
        ('right', Align.right),
    ]
)
def test_align(align: str, result: Align):
    assert Align(align) == result
