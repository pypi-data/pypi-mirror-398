from collections.abc import Sequence
from typing_extensions import NamedTuple

class Point(NamedTuple):
    row: int
    column: int

class Node:
    type: str
    start_byte: int
    end_byte: int
    start_point: Point
    end_point: Point
    has_error: bool
    children: Sequence[Node]

    def child_by_field_name(self, field_name: str) -> Node | None: ...
    def __hash__(self) -> int: ...

class Tree:
    root_node: Node

    def __init__(self) -> None: ...

class Language:
    def __init__(self, language_ptr: object) -> None: ...

class Parser:
    def __init__(self, language: Language | None = None) -> None: ...
    def parse(
        self, source: bytes, old_tree: Tree | None = None, encoding: str | None = None
    ) -> Tree: ...
