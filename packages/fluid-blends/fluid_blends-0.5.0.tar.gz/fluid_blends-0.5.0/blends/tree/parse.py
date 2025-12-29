from tree_sitter import (
    Parser,
    Tree,
)

from blends.models import Content
from blends.tree import PARSER_LANGUAGES


class ParsingError(Exception):
    pass


def get_tree(content: Content) -> Tree:
    parser_language = PARSER_LANGUAGES[content.language]
    parser = Parser(parser_language)

    tree = parser.parse(content.content_bytes)

    if tree.root_node.has_error:
        raise ParsingError

    return tree
