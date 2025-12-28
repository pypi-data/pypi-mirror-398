from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from outlify._utils import get_reset_by_style, parse_styles, resolve_width
from outlify.style import AnsiCodes

__all__ = ["TitledList"]


class ListBase(ABC):
    def __init__(
            self, content: Sequence[Any], *, width: int | None,
            title: str, title_separator: str, title_style: Sequence[AnsiCodes] | None,
    ) -> None:
        self.width = resolve_width(width)
        title_style = parse_styles(title_style)
        title_reset = get_reset_by_style(title_style)
        self.title = self._get_title(title, count=len(content), style=title_style, reset=title_reset)
        self.title_separator = title_separator

        content = self._prepare_content(content)
        self.content = self._get_content(content, width=self.width)

    @abstractmethod
    def _get_content(self, content: list[Any], *, width: int) -> str:
        pass  # pragma: no cover

    @staticmethod
    def _get_title(title: str, *, count: int, style: str, reset: str) -> str:
        return f"{style}{title} ({count}){reset}"

    @staticmethod
    def _prepare_content(content: Sequence[Any]) -> list[str]:
        return [str(elem) for elem in content]

    def __str__(self) -> str:
        if len(self.content) == 0:
            return self.title
        return self.title_separator.join((self.title, self.content))

    def __repr__(self) -> str:
        content = ", ".join(f"{name}={getattr(self, name)!r}" for name in dir(self) if not name.startswith("_"))
        return f"{self.__class__.__name__}({content})"


class TitledList(ListBase):
    """Titled list with length."""

    def __init__(
            self, content: Sequence[Any], *,
            title: str = "Content", title_style: Sequence[AnsiCodes] | None = None,
            title_separator: str = ": ",
            separator: str = "  ",
    ) -> None:
        """Create a simple list for displaying elements with customizable title.

        Can be used to list installed packages, processed files, etc.

        :param content: element enumeration
        :param title: title displayed before elements
        :param title_style: enumeration of title styles. Any class inherited from AnsiCodes,
                            including Colors, Back and Styles
        :param title_separator: separator between title and first item in list (content)
        :param separator: separator between title and elements
        """
        self.separator = separator
        super().__init__(
            content, width=None, title=title,
            title_separator=title_separator,
            title_style=title_style,
        )

    def _get_content(self, content: list[str], *, width: int) -> str:  # noqa: ARG002
        return self.separator.join(content)


if __name__ == "__main__":  # pragma: no cover
    from outlify.style import Styles
    print(
        "Outlify helps you create list output in a beautiful format\n",
        "The first one is the simplest: a titled list", sep="\n",
    )
    print(TitledList([
        "ruff@1.0.0", "pytest@1.2.3", "mkdocs@3.2.1", "mike@0.0.1",
    ], title="Packages"))

    print("\nor you can output the elements line by line")
    print(TitledList(
        ["first", "second", "third", "fourth", "fifth"], title="Elements",
        title_style=[Styles.bold], title_separator=":\n- ", separator="\n- ",
    ))
