from collections.abc import Callable, Iterator
from typing import TypeVar
from typing_extensions import ParamSpec

_T = TypeVar("_T")
_P = ParamSpec("_P")
_E = TypeVar("_E", bound=BaseException)

class MarkDecorator:
    def __call__(self, func: Callable[_P, _T]) -> Callable[_P, _T]: ...

class MarkGenerator:
    def blends_test_group(self, value: str) -> MarkDecorator: ...

mark: MarkGenerator

class Parser:
    def addoption(
        self,
        name: str,
        *,
        action: str | None = None,
        metavar: str | None = None,
        **kwargs: object,
    ) -> None: ...

class Config:
    def getoption(self, name: str, default: str | None = None) -> str | None: ...

class Mark:
    args: tuple[str, ...]

class Item:
    config: Config
    def iter_markers(self, name: str | None = None) -> Iterator[Mark]: ...

class Module(Item): ...

def skip(reason: str) -> None: ...

class RaisesContext:
    def __enter__(self) -> None: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> bool: ...

def raises(
    expected_exception: type[_E] | tuple[type[_E], ...],
    *,
    match: str | None = None,
) -> RaisesContext: ...
