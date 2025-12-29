import re

from blends.models import Content, CustomParser
from blends.tree.parse import ParsingError, get_tree
from blends.utils.logs import log_blocking, log_to_remote_blocking

HELM_EXPR_PATTERN = re.compile(r"\{\{\-?\s*[^{}]*?\s*\-?\}\}")
KV_PATTERN = re.compile(r"^(?P<indent>\s*)(?P<dash>- )?(?P<key>[^:]+:\s*)(?P<value>.*)$")
BLOCK_HELM_COMMENT_PATTERN = re.compile(r"\{\{\s*-?\s*/\*([\s\S]*?)\*/\s*-?\s*\}\}")


def _validate_helm_required_keys(content: str) -> bool:
    config_required_keys = ["apiVersion", "kind", "metadata"]
    return all(key in content for key in config_required_keys)


def _convert_block_helm_comment(content: str) -> str:
    def _replacer(match: re.Match[str]) -> str:
        block = match.group(0)
        lines = block.splitlines()
        return "\n".join("# " + line for line in lines)

    return BLOCK_HELM_COMMENT_PATTERN.sub(_replacer, content)


def _normalize_helm_expression(value: str) -> str:
    return re.sub(r"\{\{\-?\s*(.*?)\s*\-?\}\}", r"{{ \1 }}", value)


def _is_full_helm_expression(value: str) -> bool:
    return bool(re.fullmatch(r"\{\{\s*[^{}]+\s*\}\}", value.strip()))


def _has_helm_expression_in_key(key: str) -> bool:
    return bool(HELM_EXPR_PATTERN.search(key))


def _fix_inner_quotes_in_helm(value: str) -> str:
    def _replacer(match: re.Match[str]) -> str:
        expr = match.group(0)
        inner = expr[2:-2]
        fixed_inner = re.sub(r'(?<!\\)"([^"]*?)"', r"'\1'", inner)
        return "{{" + fixed_inner + "}}"

    return HELM_EXPR_PATTERN.sub(_replacer, value)


def _process_key_value_line(line: str) -> str:
    match = KV_PATTERN.match(line)
    if not match:
        return line

    indent = match.group("indent")
    dash = match.group("dash") or ""
    key_part = match.group("key")
    value = match.group("value").strip()

    key_name = key_part.rstrip(": ").strip()

    if _has_helm_expression_in_key(key_name):
        key_name = _normalize_helm_expression(key_name)
        key_part = f"'{key_name}': "
    else:
        key_part = f"{key_name}: "

    if value == "":
        return f"{indent}{dash}{key_part}"

    if HELM_EXPR_PATTERN.search(value):
        value = _fix_inner_quotes_in_helm(value)
        value = _normalize_helm_expression(value)
        min_helm_expressions_in_value = 2
        if (
            ":" in value
            and value.count("{{") >= min_helm_expressions_in_value
            and not (value.startswith('"') and value.endswith('"'))
            and not (value.startswith("'") and value.endswith("'"))
        ):
            value = f'"{value}"'

        if value.startswith('"') and value.endswith('"'):
            return f"{indent}{dash}{key_part}{value}"
        if '"' in value:
            return f"{indent}{dash}{key_part}'{value}'"
        return f'{indent}{dash}{key_part}"{value}"'

    return f"{indent}{dash}{key_part}{value}"


def _process_full_helm_line(line: str) -> str:
    expr = _normalize_helm_expression(line.strip())
    if _is_full_helm_expression(expr):
        indent = len(line) - len(line.lstrip())
        return f"{' ' * indent}# {expr}"
    return line


def _preprocess_helm_templates(content: Content) -> Content | None:
    try:
        content_str = _convert_block_helm_comment(content.content_str)
        lines = content_str.splitlines()
        processed_lines = []

        for line in lines:
            if re.match(r"^\s*-?\s*[\w\-_.\/{}$]+\s*:", line):
                processed_lines.append(_process_key_value_line(line))

            elif _is_full_helm_expression(line.strip()):
                processed_lines.append(_process_full_helm_line(line))

            elif HELM_EXPR_PATTERN.search(line):
                processed_lines.append(
                    f"{_get_indent(line)}# {_normalize_helm_expression(line.strip())}"
                )
            else:
                processed_lines.append(line)
        fixed_content = "\n".join(processed_lines).strip()

        content_bytes = fixed_content.encode("utf-8")
    except Exception as exc:  # noqa: BLE001
        msg = f"Content fix logic got {exc} error when parsing {content.path}"
        log_blocking("error", msg)
        log_to_remote_blocking(msg=msg, severity="error")
        return None

    return Content(content_bytes, fixed_content, content.language, content.path)


def _get_indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def validator(content: Content) -> bool:
    valid_extensions = {".json", ".yml", ".yaml"}
    return (
        "templates" in str(content.path)
        and any(str(content.path).lower().endswith(ext) for ext in valid_extensions)
        and _validate_helm_required_keys(content.content_str)
    )


def parser(
    content: Content,
) -> Content | None:
    if not HELM_EXPR_PATTERN.search(content.content_str):
        return content

    try:
        get_tree(content)
    except ParsingError:
        fixed_content = _preprocess_helm_templates(content)
    else:
        return content

    if fixed_content is not None:
        try:
            get_tree(fixed_content)
        except ParsingError:
            msg = (
                f"HELM template still not parseable by tree-sitter after custom fix: {content.path}"
            )
            log_blocking("error", msg)
            log_to_remote_blocking(msg=msg, severity="error")
        else:
            return fixed_content

    return None


helm_parser = CustomParser(validator=validator, parser=parser)
