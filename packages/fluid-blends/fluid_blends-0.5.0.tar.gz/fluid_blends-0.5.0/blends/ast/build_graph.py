from collections.abc import Iterator
from itertools import (
    count,
)
from pathlib import Path

from tree_sitter import Node

from blends.content.content import get_content_by_path
from blends.models import Content, Graph, Language
from blends.tree import FIELDS_BY_LANGUAGE
from blends.tree.parse import ParsingError, get_tree
from blends.utils.logs import log_blocking, log_to_remote_blocking


def _hash_node(node: Node) -> int:
    return hash((node.end_point, node.start_point, node.type))


def _is_node_terminal(node: Node, language: Language) -> bool:
    return (
        language == Language.YAML
        and node.type
        in [
            "flow_mapping",
            "single_quote_scalar",
            "double_quote_scalar",
        ]
    ) or (language == Language.SWIFT and node.type == "bang")


def _has_content_node(node: Node, language: Language) -> bool:
    return (
        (
            language == Language.CSHARP
            and node.type
            in {
                "character_literal",
                "predefined_type",
                "string_literal",
                "verbatim_string_literal",
            }
        )
        or (
            language == Language.DART
            and node.type
            in {
                "list_literal",
                "set_or_map_literal",
                "string_literal",
            }
        )
        or (
            language == Language.GO
            and node.type
            in {
                "interpreted_string_literal",
            }
        )
        or (
            language
            in {
                Language.JAVASCRIPT,
                Language.TYPESCRIPT,
            }
            and node.type
            in {
                "template_string",
                "regex",
            }
        )
        or (
            language == Language.KOTLIN
            and node.type
            in {
                "string_literal",
            }
        )
        or (language == Language.SWIFT and node.type == "bang")
        or (
            language == Language.YAML
            and node.type
            in {
                "single_quote_scalar",
                "double_quote_scalar",
                "flow_mapping",
            }
        )
    )


def _build_ast_graph(
    content: Content,
    node: Node,
    counter: Iterator[str],
    graph: Graph,
    *,
    _edge_index: str | None = None,
    _parent: str | None = None,
    _parent_fields: dict[int, str] | None = None,
) -> Graph:
    if not isinstance(node, Node):
        raise NotImplementedError

    n_id = next(counter)
    raw_l, raw_c = node.start_point

    graph.add_node(n_id, label_l=raw_l + 1, label_c=raw_c + 1, label_type=node.type)

    if _parent is not None:
        graph.add_edge(_parent, n_id, label_ast="AST", label_index=_edge_index)

    if (field := (_parent_fields or {}).get(_hash_node(node))) and _parent is not None:
        graph.nodes[_parent][f"label_field_{field}"] = n_id

    if not node.children or _has_content_node(node, content.language):
        node_content = content.content_bytes[node.start_byte : node.end_byte]
        graph.nodes[n_id]["label_text"] = node_content.decode("latin-1")

    if node.children and not _is_node_terminal(node, content.language):
        for edge_index, child in enumerate(node.children):
            child_node: Node = child
            _build_ast_graph(
                content,
                child_node,
                counter,
                graph,
                _edge_index=str(edge_index),
                _parent=n_id,
                _parent_fields={
                    _hash_node(child): fld
                    for fld in FIELDS_BY_LANGUAGE[content.language].get(node.type, ())
                    for child in [node.child_by_field_name(fld)]
                    if child
                },
            )

    return graph


def get_ast_graph_from_path(path: Path) -> Graph | None:
    if (content := get_content_by_path(path)) is None:
        log_blocking("error", "Error extracting the content of %s", str(path))
        return None

    if content.language == Language.NOT_SUPPORTED:
        log_blocking("warning", "Unsupported language in %s", str(path))
        return None

    try:
        tree = get_tree(content)
    except ParsingError:
        msg = f"Error building the tree-sitter tree for {path!s}"
        log_blocking("error", msg)
        log_to_remote_blocking(msg=msg, severity="error")
        return None

    counter = map(str, count(1))

    try:
        return _build_ast_graph(content, tree.root_node, counter, Graph())
    except NotImplementedError:
        msg = f"Error building the ast_graph for {path!s}"
        log_blocking("error", msg)
        log_to_remote_blocking(msg=msg, severity="error")

    return None
