import functools
import time
from typing import Callable, ParamSpec, Sequence, TypeVar  # noqa: UP035

from outlify._utils import get_reset_by_style, parse_styles
from outlify.style import AnsiCodes

__all__ = ["timer"]


P = ParamSpec("P")
R = TypeVar("R")


def timer(
        label: str | None = None,
        label_style: Sequence[AnsiCodes] | None = None,
        connector: str = "took",
        time_format: str = "{h:02}:{m:02}:{s:02}.{ms:03}",
        time_style: Sequence[AnsiCodes] | None = None,
        output_func: Callable[[str], None] = print,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Time the function.

    :param label: optional custom label; if not provided, defaults to "Function {function name}"
    :param label_style: enumeration of label styles. Any class inherited from AnsiCodes,
                        including Colors, Back and Styles
    :param connector: word or phrase used to connect the label and the measured duration
                      in the output message (e.g. "took", "in", "completed in").
    :param time_format: a string format specifying how the duration will be displayed.
        The following placeholders are supported:
            {h} - hours,
            {m} - minutes (0-59),
            {s} - seconds (0-59),
            {ms} - milliseconds (0-999).

        You can use any valid Python `str.format` syntax.
        Example: "{h:02}:{m:02}:{s:02}.{ms:03}" → "00:00:05.123"
        Custom example: "{m} min {s} sec" → "1 min 23 sec"
    :param time_style: enumeration of time styles. Any class inherited from AnsiCodes,
                       including Colors, Back and Styles
    :param output_func: function for outputting measurements

    :raises KeyError: used invalid key(s) of 'time_format' format-string
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = time.perf_counter()
            result = func(*args, **kwargs)
            try:
                duration = _format_duration(time.perf_counter() - start, fmt=time_format)
            except KeyError:
                error = (
                    "Unavailable key(s) in 'time_format' format-string. "
                    "Available keys: h - hours, m - minutes, s - seconds, ms - milliseconds"
                )
                raise KeyError(error) from None

            message = _get_message(
                duration, time_style, connector,
                label, label_style, funcname=repr(func.__name__),
            )
            output_func(message)
            return result
        return wrapper
    return decorator


def _format_duration(seconds: float, *, fmt: str) -> str:
    """Format the duration specified in seconds according to the specified pattern."""
    total_milliseconds = int(seconds * 1000)

    total_seconds, milliseconds = divmod(total_milliseconds, 1000)
    total_minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(total_minutes, 60)
    return fmt.format(h=hours, m=minutes, s=seconds, ms=milliseconds)


def _get_message(
        duration: str, time_style: Sequence[AnsiCodes] | None, connector: str,
        label: str | None, label_style: Sequence[AnsiCodes] | None, funcname: str,
) -> str:
    label = label if label else f"Function {funcname}"
    label = _styling_text(label, style=label_style)
    duration = _styling_text(duration, style=time_style)
    return f"{label} {connector} {duration}"


def _styling_text(text: str, style: Sequence[AnsiCodes] | None) -> str:
    style = parse_styles(style)
    reset = get_reset_by_style(style)
    return f"{style}{text}{reset}"


if __name__ == "__main__":  # pragma: no cover
    from unittest.mock import patch

    from outlify.style import Colors, Styles

    @timer()
    def dummy_func(a: int, b: int) -> int:
        return a + b

    print("""
    @timer()
    def dummy_func(a: int, b: int) -> int:
        return a + b
    """)

    with patch("outlify.decorators.time.perf_counter", side_effect=[0, 0.123]):
        dummy_func(1, 2)


    @timer(label="Dummy")
    def dummy_func_with_custom_name(a: int, b: int) -> int:
        return a + b

    print("""
    @timer(label="Dummy")
    def dummy_func_with_custom_name(a: int, b: int) -> int:
        return a + b
    """)

    with patch("outlify.decorators.time.perf_counter", side_effect=[0, 1.23]):
        dummy_func_with_custom_name(1, 2)


    @timer(label="Custom time format", time_format="{m} min {s}.{ms:03} sec")
    def dummy_func_with_custom_fmt(a: int, b: int) -> int:
        return a + b

    print("""
    @timer(label="Custom time format", time_format="{m} min {s}.{ms:03} sec")
    def dummy_func_with_custom_fmt(a: int, b: int) -> int:
        return a + b
    """)

    with patch("outlify.decorators.time.perf_counter", side_effect=[0, 123.345]):
        dummy_func_with_custom_fmt(2, 3)


    @timer(label_style=[Colors.red], time_style=[Colors.crimson, Styles.underline])
    def colored_timer(a: int, b: int) -> int:
        return a + b

    print("""
    @timer(label_style=[Colors.red], time_style=[Colors.crimson, Styles.underline])
    def colored_timer(a: int, b: int) -> int:
        return a + b
    """)

    with patch("outlify.decorators.time.perf_counter", side_effect=[0, 3723.456]):
        colored_timer(1, 2)


    @timer("Download completed", connector="in")
    def colored_timer(a: int, b: int) -> int:
        return a + b

    print("""
    @timer("Download completed", connector="in")
    def colored_timer(a: int, b: int) -> int:
        return a + b
    """)

    with patch("outlify.decorators.time.perf_counter", side_effect=[0, 3723.456]):
        colored_timer(1, 2)
