import json
import os
from ctypes import (
    c_void_p,
    cdll,
)
from pathlib import Path

import tree_sitter_c_sharp
import tree_sitter_go
import tree_sitter_hcl
import tree_sitter_java
import tree_sitter_javascript
import tree_sitter_json
import tree_sitter_kotlin
import tree_sitter_php
import tree_sitter_python
import tree_sitter_ruby
import tree_sitter_scala
import tree_sitter_swift
import tree_sitter_typescript
import tree_sitter_yaml
from tree_sitter import (
    Language,
)

from blends.ctx import (
    TREE_SITTER_PARSERS,
    TREE_SITTER_STATIC_NODE_FIELDS,
)
from blends.models import Language as BlendsLanguage


def lang_from_so(language: BlendsLanguage) -> Language:
    so_library_path = Path(TREE_SITTER_PARSERS) / f"{language.value}.so"
    lib = cdll.LoadLibrary(os.fspath(so_library_path))
    language_function = getattr(lib, f"tree_sitter_{language.value}")
    language_function.restype = c_void_p
    language_ptr = language_function()
    return Language(language_ptr)


PARSER_LANGUAGES: dict[BlendsLanguage, Language] = {
    BlendsLanguage.CSHARP: Language(tree_sitter_c_sharp.language()),
    BlendsLanguage.GO: Language(tree_sitter_go.language()),
    BlendsLanguage.HCL: Language(tree_sitter_hcl.language()),
    BlendsLanguage.JAVA: Language(tree_sitter_java.language()),
    BlendsLanguage.JAVASCRIPT: Language(tree_sitter_javascript.language()),
    BlendsLanguage.JSON: Language(tree_sitter_json.language()),
    BlendsLanguage.KOTLIN: Language(tree_sitter_kotlin.language()),
    BlendsLanguage.PHP: Language(tree_sitter_php.language_php()),
    BlendsLanguage.PYTHON: Language(tree_sitter_python.language()),
    BlendsLanguage.RUBY: Language(tree_sitter_ruby.language()),
    BlendsLanguage.SCALA: Language(tree_sitter_scala.language()),
    BlendsLanguage.SWIFT: Language(tree_sitter_swift.language()),
    BlendsLanguage.TYPESCRIPT: Language(tree_sitter_typescript.language_tsx()),
    BlendsLanguage.YAML: Language(tree_sitter_yaml.language()),
    BlendsLanguage.DART: lang_from_so(BlendsLanguage.DART),
}

FIELDS_BY_LANGUAGE: dict[BlendsLanguage, dict[str, tuple[str, ...]]] = {}


def _get_fields_by_language() -> None:
    for lang in BlendsLanguage:
        if lang == BlendsLanguage.NOT_SUPPORTED:
            continue

        path = Path(TREE_SITTER_STATIC_NODE_FIELDS) / f"{lang.value}-fields.json"

        with path.open(encoding="utf-8") as file:
            FIELDS_BY_LANGUAGE[lang] = json.load(file)


_get_fields_by_language()
