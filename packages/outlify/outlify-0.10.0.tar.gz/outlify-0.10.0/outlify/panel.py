import re
import textwrap
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from outlify._ansi import AnsiCodes
from outlify._utils import get_reset_by_style, parse_styles, parse_title_align, resolve_width
from outlify.style import Align, BorderStyle

__all__ = ["Panel", "ParamsPanel"]


class PanelBase(ABC):
    def __init__(
            self, content: Any, *, width: int | None,
            title: str, subtitle: str,
            title_align: str | Align, subtitle_align: str | Align,
            title_style: Sequence[AnsiCodes | str] | None, subtitle_style: Sequence[AnsiCodes | str] | None,
            title_conns: str, subtitle_conns: str,
            border: str | BorderStyle,
            border_style: Sequence[AnsiCodes] | None,
    ) -> None:
        border = self._parse_border(border)
        width = resolve_width(width)

        title_style, subtitle_style = parse_styles(title_style), parse_styles(subtitle_style)
        title_reset, subtitle_reset = get_reset_by_style(title_style), get_reset_by_style(subtitle_style)

        border_style = parse_styles(border_style)
        self.border_reset = get_reset_by_style(border_style)
        self.header = self._get_header(
            title, align=parse_title_align(title_align), title_style=title_style, title_style_reset=title_reset,
            width=width, left=border.lt, char=border.headers, right=border.rt, conns=title_conns,
            border_style=border_style,
        )
        self.footer = self._get_header(
            subtitle, align=parse_title_align(subtitle_align), title_style=subtitle_style,
            title_style_reset=subtitle_reset, width=width, left=border.lb, char=border.headers,
            right=border.rb, conns=subtitle_conns, border_style=border_style,
        )
        self.content = self._get_content(content, width=width, char=border.sides, border_style=border_style)

    @abstractmethod
    def _get_content(self, content: Any, *, width: int, char: str, border_style: str) -> str:
        pass  # pragma: no cover

    @staticmethod
    def _get_inner_width(outside: int) -> int:
        """Get inner panel width.

        :param outside: outside panel width
        :return: inner panel width
        """
        minimal_width = 4
        if outside <= minimal_width:
            error = f"Invalid value for width: {outside} <= {minimal_width}"
            raise ValueError(error)
        return outside - 4

    @staticmethod
    def _parse_border(style: str) -> BorderStyle:
        if isinstance(style, BorderStyle):
            return style
        if not isinstance(style, str):
            error = f"Invalid type for border: {style} ({type(style)}) variable is not str or BorderStyle"
            raise TypeError(error)
        if len(style) not in [5, 6]:
            error = f"Invalid length for border (!= 5 or != 6): length of {style} = {len(style)}"
            raise ValueError(error)
        max_length_border = 6
        return BorderStyle(
            lt=style[0], rt=style[1],
            lb=style[2], rb=style[3],
            headers=style[4], sides=style[5] if len(style) == max_length_border else "",
        )

    def _get_header(
            self, title: str, *, width: int, align: Align, title_style: str, title_style_reset: str,
            left: str, char: str, right: str, conns: str, border_style: str,
    ) -> str:
        header = self._fill_header(
            title, width=width - 2, align=align, title_style=title_style, title_style_reset=title_style_reset,
            char=char, conns=conns, border_style=border_style,
        )
        return f"{border_style}{left}{header}{right}{self.border_reset}"

    def _fill_header(
            self, title: str, *, width: int, align: Align, title_style: str, title_style_reset: str,
            char: str, conns: str, border_style: str,
    ) -> str:
        if title != "":
            width += len(str(title_style)) + len(title_style_reset)   # title styling
            width += len(self.border_reset) + len(str(border_style))  # border styling
            title = f"{self.border_reset}{title_style}{title}{title_style_reset}{border_style}"

        lconn, rconn = self._get_connectors(conns)
        title = f"{lconn}{title}{rconn}"

        if align == Align.left:
            title = f"{char}{title}"
            return f"{title.ljust(width, char)}"
        if align == Align.right:
            title = f"{title}{char}"
            return title.rjust(width, char)
        return title.center(width, char)

    def _get_connectors(self, conns: str) -> tuple[str, str]:
        if not isinstance(conns, str):
            err = f"Expected 'conns' to be str, got {type(conns).__name__}"
            raise TypeError(err)
        if len(conns) % 2 != 0:
            err = f"Connectors pattern '{conns}' must have an even number of characters to parse it"
            raise ValueError(err)

        mid = len(conns) // 2
        return conns[:mid], conns[mid:]

    def _fill(self, line: str, *, width: int, char: str, border_style: str, indent: str = "") -> str:
        """Fill a single line.

        :param line: the content to be placed inside the panel
        :param width: total available width for the content (excluding side borders)
        :param char: border character to be placed on both sides of the line
        :param border_style: ANSI style to apply to the border. Can be a string (e.g., 'red bold') or a `Style`
                             instance. Allows customization of border color and text style (e.g., bold, underline).
        :param indent: indentation added before the content
        :return: a string representing the line wrapped with borders and padded to match the specified width
        """
        border = f"{border_style}{char}{self.border_reset}"
        return f"{border} {indent}{line.ljust(width - len(indent))} {border}"

    def __str__(self) -> str:
        return (
            f"{self.header}\n"
            f"{self.content}\n"
            f"{self.footer}"
        )

    def __repr__(self) -> str:
        content = ", ".join(f"{name}={getattr(self, name)!r}" for name in dir(self) if not name.startswith("_"))
        return f"{self.__class__.__name__}({content})"


class Panel(PanelBase):
    """Providing raw text in the panel."""

    def __init__(
            self, content: str, *, width: int | None = None,
            title: str = "", subtitle: str = "",
            title_align: str | Align = "center", subtitle_align: str | Align = "center",
            title_style: Sequence[AnsiCodes | str] | None = None,
            subtitle_style: Sequence[AnsiCodes | str] | None = None,
            title_conns: str = "", subtitle_conns: str = "",
            border: str | BorderStyle = "╭╮╰╯─│",
            border_style: Sequence[AnsiCodes | str] | None = None,
    ) -> None:
        """Create a simple panel for displaying plain text with customizable borders, title, and subtitle.

        This class inherits from `PanelBase` and provides a way to create a terminal panel with
        plain text content. It allows you to configure the panel's width, title, subtitle, alignment,
        and border style. The panel is designed to be used directly in the terminal for displaying information
        in a visually appealing way.

        :param content: the plain text content to be displayed inside the panel. It supports multi-line strings.
        :param width: total panel width (including borders)
        :param title: title displayed at the top of the panel
        :param title_align: alignment of the title. Can be a string ('left', 'center', 'right') or an Align enum/type
        :param title_style: enumeration of title styles. Any class inherited from AnsiCodes,
                            including Colors, Back and Styles
        :param title_conns: a connector pattern used to surround the title text.
            The string must have an **even number of characters**, as it will be split in half -
            the left half will appear **before** the title, and the right half **after** it.

            For example:
            - `'[]'` → produces `[Title]`
            - `'-{}-'` → produces `-{Title}-`
            - `'<<>>'` → produces `<<Title>>`

            If empty, the title is displayed without any additional connectors.
        :param subtitle: subtitle displayed below the title
        :param subtitle_align: alignment of the subtitle. Same format as title_align
        :param subtitle_style: enumeration of subtitle styles. Any class inherited from AnsiCodes,
                               including Colors, Back and Styles
        :param subtitle_conns:
            same as `title_conns`, but applied to the subtitle text instead.
            Allows creating consistent visual framing for the subtitle.
        :param border: Border character style. Can be a string representing custom border characters
                       or an instance of BorderStyle
        :param border_style: enumeration of border styles. Any class inherited from AnsiCodes,
                             including Colors, Back and Styles
        """
        super().__init__(
            content, width=width,
            title=title, subtitle=subtitle,
            title_align=title_align, subtitle_align=subtitle_align,
            title_style=title_style, subtitle_style=subtitle_style,
            title_conns=title_conns, subtitle_conns=subtitle_conns,
            border=border, border_style=border_style,
        )

    def _get_content(self, content: Any, *, width: int, char: str, border_style: str) -> str:
        """Get prepared panel content.

        :param content: multi-line string to display in the panel
        :param width: total panel width (including borders)
        :param char: character for the side borders. If empty string, disables wrapping and borders
        :param border_style: ansi escape sequences
        :return: panel with prepared content
        """
        content = str(content)
        width = self._get_inner_width(width)

        lines = []
        for line in content.splitlines():
            if char == "" or (line := line.strip()) == "":
                lines.append(line)
                continue

            wrapped = textwrap.wrap(
                line, width=width, replace_whitespace=False,
                drop_whitespace=False, break_on_hyphens=False,
            )
            lines.extend(wrapped)

        lines = [self._fill(line, width=width, char=char, border_style=border_style) for line in lines]
        return "\n".join(lines)


class ParamsPanel(PanelBase):
    """Providing parameters in the panel."""

    def __init__(
            self, content: Mapping[Any, Any], *, width: int | None = None,
            title: str = "", subtitle: str = "",
            title_align: str | Align = "center", subtitle_align: str | Align = "center",
            title_style: Sequence[AnsiCodes | str] | None = None,
            subtitle_style: Sequence[AnsiCodes | str] | None = None,
            title_conns: str = "", subtitle_conns: str = "",
            border: str | BorderStyle = "╭╮╰╯─│",
            border_style: Sequence[AnsiCodes | str] | None = None,
            hidden: Iterable[str | re.Pattern] = (".*password.*", ".*token.*"), separator: str = " = ",
            params_style: Sequence[AnsiCodes | str] | None = None,
    ) -> None:
        """Create a panel for displaying key-value parameters in a formatted layout.

        Inherits from `PanelBase` and is used to present a set of parameters, e.g. configuration settings,
        metadata, etc. in a styled, optionally bordered panel. Supports custom title, subtitle, alignment,
        and the ability to hide selected parameters.

        :param content: a mapping of keys to string values to display in the panel.
                        For example: {'learning_rate': '0.001', 'batch_size': '64'}.
        :param width: total panel width (including borders)
        :param title: title displayed at the top of the panel
        :param title_align: alignment of the title. Can be a string ('left', 'center', 'right') or an Align enum/type
        :param title_style: enumeration of title styles. Any class inherited from AnsiCodes,
                            including Colors, Back and Styles
        :param title_conns: a connector pattern used to surround the title text.
            The string must have an **even number of characters**, as it will be split in half -
            the left half will appear **before** the title, and the right half **after** it.

            For example:
            - `'[]'` → produces `[Title]`
            - `'-{}-'` → produces `-{Title}-`
            - `'<<>>'` → produces `<<Title>>`

            If empty, the title is displayed without any additional connectors.
        :param subtitle: subtitle displayed below the title
        :param subtitle_align: alignment of the subtitle. Same format as title_align
        :param subtitle_style: enumeration of subtitle styles. Any class inherited from AnsiCodes,
                               including Colors, Back and Styles
        :param subtitle_conns:
            same as `title_conns`, but applied to the subtitle text instead.
            Allows creating consistent visual framing for the subtitle.
        :param border: Border character style. Can be a string representing custom border characters
                       or an instance of BorderStyle
        :param border_style: enumeration of border styles. Any class inherited from AnsiCodes,
                             including Colors, Back and Styles
        :param hidden: Iterable of regexes for keys from `content` that should be excluded from display.
                       Useful for filtering out sensitive or irrelevant data
        :param separator: key-value separator
        :param params_style: enumeration of parameter name styles. Any class inherited from AnsiCodes,
                             including Colors, Back and Styles
        """
        self.hidden = self._compile_regexes(hidden)
        self.separator = separator
        self.params_style = parse_styles(params_style)
        self.params_reset = get_reset_by_style(self.params_style)

        # width alignment to styles
        self._additional_width = len(self.params_style) + len(self.params_reset)
        super().__init__(
            content, width=width,
            title=title, subtitle=subtitle,
            title_align=title_align, subtitle_align=subtitle_align,
            title_style=title_style, subtitle_style=subtitle_style,
            title_conns=title_conns, subtitle_conns=subtitle_conns,
            border=border, border_style=border_style,
        )

    @staticmethod
    def _compile_regexes(hidden: Iterable[str | re.Pattern[str]]) -> tuple[re.Pattern[str], ...]:
        return tuple(re.compile(pattern) if isinstance(pattern, str) else pattern for pattern in hidden)

    def _get_content(self, content: Mapping[Any, Any], *, width: int, char: str, border_style: str) -> str:
        """Get prepared panel content.

        :param content: parameters that should be in the panel
        :param width: total panel width (including borders)
        :param char: character for the side borders. If empty string, disables wrapping and borders
        :param border_style: ansi escape sequences
        :return: panel with prepared content
        """
        if not isinstance(content, Mapping):
            error = f"Invalid type for content: {type(content)} is not Mapping"
            raise TypeError(error)
        width = self._get_inner_width(width)
        params = self._prepare_params(content)

        lines = []
        max_key_length = max(len(key) for key in params)
        width_inside = width - max_key_length - len(self.separator)
        indent = " " * (max_key_length + len(self.separator))
        leveled_width = width + self._additional_width
        for key, value in params.items():
            displayed_value = self._mask_value(key, value)
            line = (
                f"{self.params_style}{key.ljust(max_key_length)}{self.params_reset}"
                f"{self.separator}{displayed_value}"
            )

            if not char:  # mode without border in sides
                lines.append(f"  {line}")
            elif len(line) <= leveled_width:  # the whole line fits in the panel
                lines.append(self._fill(line, width=leveled_width, char=char, border_style=border_style))
            else:  # it's necessary to split the string
                lines.extend(self._wrap_line(line, width, leveled_width, width_inside, char, border_style, indent))
        return "\n".join(lines)

    @staticmethod
    def _prepare_params(content: Mapping[Any, Any]) -> dict[str, str]:
        """Convert all keys and values in the mapping to strings.

        :param content: original content mapping
        :return: dictionary with stringified keys and values
        """
        return {str(key): str(value) for key, value in content.items()}

    def _mask_value(self, key: str, value: str) -> str:
        """Replace value with asterisks if the key is in the hidden list.

        :param key: parameter name
        :param value: parameter value
        :return: either the original value or a masked string
        """
        for pattern in self.hidden:
            if pattern.fullmatch(key):
                return "*****" if value else value
        return value

    def _wrap_line(
            self, line: str, width: int, leveled_width: int, width_inside: int,
            char: str, border_style: str, indent: str,
    ) -> list[str]:
        """Wrap a long line into multiple lines with proper indentation and border formatting.

        :param line: the full line to wrap
        :param width: full panel width including borders
        :param width: leveled panel width including borders (for ansi colors)
        :param width_inside: usable width after the key and separator
        :param char: border character
        :param border_style: ansi escape sequences
        :param indent: indentation for wrapped lines
        :return: list of wrapped and formatted lines
        """
        head, tail = line[:leveled_width], line[leveled_width:]
        wrapped = textwrap.wrap(
            tail, width=width_inside, replace_whitespace=False,
            drop_whitespace=False, break_on_hyphens=False,
        )
        lines = [self._fill(head, width=width, char=char, border_style=border_style)]
        lines.extend(
            self._fill(part, width=width, char=char, border_style=border_style, indent=indent) for part in wrapped
        )
        return lines


if __name__ == "__main__":  # pragma: no cover
    from outlify.style import Colors

    text = (
        "Outlify helps you render beautiful command-line panels.\n"
        "You can customize borders, alignment, etc.\n\n"
        "This is just a simple text panel."
    )
    print(Panel(
        text, title=" Welcome to Outlify ", subtitle="Text Panel Demo", title_align="left", subtitle_align="right",
    ), "", sep="\n")

    long_text = (
        "In a world where CLI tools are often boring and unstructured, "
        "Outlify brings beauty and structure to your terminal output. "
        "It allows developers to create elegant panels with customizable borders, titles, subtitles, "
        "and aligned content — all directly in the terminal.\n\n"
        "Outlify is lightweight and dependency-free — it uses only Python's standard libraries, "
        "so you can easily integrate it into any project without worrying about bloat or compatibility issues.\n\n"
        "Whether you're building debugging tools, reporting pipelines, or just want to print data in a cleaner way, "
        "Outlify helps you do it with style."
    )
    print(Panel(
        long_text, title=" Long Text Panel Example ", subtitle="using another border and border style",
        border="╔╗╚╝═║", border_style=[Colors.gray], title_conns="[]",
    ), "", sep="\n")

    text = (
        "or maybe you want to output parameters that came to your CLI input, "
        "but you do not want to output it in raw form or write a nice wrapper yourself, "
        "and the sensitive data should not be visible in the terminal, but you want to know that it is specified"
    )
    print(Panel(text, subtitle="See ↓ below", border="┌┐└┘  "), "", sep="\n")
    parameters = {
        "first name": "Vladislav",
        "last name": "Kishkin",
        "username": "k1shk1n",
        "password": "fake-password",
        "description": "This is a fake description to show you how Outlify can wrap text in the Parameters Panel",
    }
    print(ParamsPanel(parameters, title="Start Parameters"))
