from typing import Type
from unittest.mock import Mock, patch

import pytest

from outlify.decorators import timer


@pytest.mark.unit
@pytest.mark.parametrize(
    'label,connector,timefmt,start,end,result',
    [
        (None, None, "{h:02}:{m:02}:{s:02}.{ms:03}", 1.0, 1.1, "Function 'dummy_func' took 00:00:00.100"),
        ("TestFunc", None, "{h:02}:{m:02}:{s:02}.{ms:03}", 1.0, 1.5, "TestFunc took 00:00:00.500"),

        ("test connector", "in", "{h:02}:{m:02}",  0.0, 3661.0, "test connector in 01:01"),

        ("test calculate", None, "{h:02}:{m:02}:{s:02}.{ms:03}", 0.0, 1.0, "test calculate took 00:00:01.000"),
        ("test calculate", None, "{h:02}:{m:02}:{s:02}.{ms:03}",  0.0, 1.123, "test calculate took 00:00:01.123"),
        ("test calculate", None, "{h:02}:{m:02}:{s:02}.{ms:03}",  0.0, 60.0, "test calculate took 00:01:00.000"),
        ("test calculate", None, "{h:02}:{m:02}:{s:02}.{ms:03}",  0.0, 61.0, "test calculate took 00:01:01.000"),
        ("test calculate", None, "{h:02}:{m:02}:{s:02}.{ms:03}",  0.0, 3600.0, "test calculate took 01:00:00.000"),
        ("test calculate", None, "{h:02}:{m:02}:{s:02}.{ms:03}",  0.0, 3601.0, "test calculate took 01:00:01.000"),
        ("test calculate", None, "{h:02}:{m:02}:{s:02}.{ms:03}",  0.0, 3660.0, "test calculate took 01:01:00.000"),
        ("test calculate", None, "{h:02}:{m:02}:{s:02}.{ms:03}",  0.0, 3661.0, "test calculate took 01:01:01.000"),

        ("test format", None, "{h:02}:{m:02}",  0.0, 3661.0, "test format took 01:01"),
        ("test format", None, "{m} min {s} sec",  0.0, 3661.0, "test format took 1 min 1 sec"),
        ("test format extra names", None, "{mm}",  0.0, 1.0, KeyError),
    ]
)
def test_timer_decorator_outputs_timing(label: str, connector: str, timefmt: str, start: float, end: float, result: str | Type[BaseException]):
    output_mock = Mock()

    params = {"time_format": timefmt, "output_func": output_mock}
    if label is not None:
        params["label"] = label
    if connector is not None:
        params["connector"] = connector

    @timer(**params)
    def dummy_func(x, y):
        return x + y
    def run():
        with patch("outlify.decorators.time.perf_counter", side_effect=[start, end]):
            dummy_func(2, 3)

    if isinstance(result, type) and issubclass(result, BaseException):
        with pytest.raises(result):
            run()
        return
    run()

    output_mock.assert_called_once()
    message = output_mock.call_args[0][0]
    assert message == result
