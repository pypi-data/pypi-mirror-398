import tempfile
from pathlib import Path

import pytest

from blends.content.content import (
    FileTooLargeError,
    _get_file_raw_content,
    get_content_by_path,
    get_language_by_path,
)
from blends.content.custom_parsers import custom_parsers_by_language
from blends.models import Content, Language


@pytest.mark.blends_test_group("content_unittesting")
def test_get_language_by_path() -> None:
    assert get_language_by_path(Path("mono/csharp/Service.cs")) == Language.CSHARP
    assert get_language_by_path(Path("app/csharp/logic/Middleware.CS")) == Language.CSHARP
    assert get_language_by_path(Path("lib/dartWidget/src/Widget.dart")) == Language.DART
    assert get_language_by_path(Path("mobile/dart/App.DART")) == Language.DART
    assert get_language_by_path(Path("services/user/Api.java")) == Language.JAVA
    assert get_language_by_path(Path("integration/test/TestSuite.JAVA")) == Language.JAVA
    assert get_language_by_path(Path("tools/kotlin/MyApp.kt")) == Language.KOTLIN
    assert get_language_by_path(Path("client/ui/view/Widget.jsx")) == Language.JAVASCRIPT
    assert get_language_by_path(Path("tools/scripts/Utility.JS")) == Language.JAVASCRIPT
    assert get_language_by_path(Path("frontend/components/Button.ts")) == Language.TYPESCRIPT
    assert get_language_by_path(Path("src/project/module/file.py")) == Language.PYTHON
    assert get_language_by_path(Path("some/repo/logic/BackEnd.PY")) == Language.PYTHON
    assert get_language_by_path(Path("web/assets/scripts/main.js")) == Language.JAVASCRIPT
    assert get_language_by_path(Path("cmd/tools/GoTool.GO")) == Language.GO
    assert get_language_by_path(Path("backend/go/server.go")) == Language.GO
    assert get_language_by_path(Path("cloud/hcl/main.hcl")) == Language.HCL
    assert get_language_by_path(Path("terraform/modules/config.tf")) == Language.HCL
    assert get_language_by_path(Path("database/seed/data.json")) == Language.JSON
    assert get_language_by_path(Path("resources/config/Info.JSON")) == Language.JSON
    assert get_language_by_path(Path("api/php/entry.php")) == Language.PHP
    assert get_language_by_path(Path("src/domain/Example.KT")) == Language.KOTLIN
    assert get_language_by_path(Path("legacy/src/Index.PHP")) == Language.PHP
    assert get_language_by_path(Path("web/ruby/on_rails/model.rb")) == Language.RUBY
    assert get_language_by_path(Path("scripts/util/Helper.RB")) == Language.RUBY
    assert get_language_by_path(Path("scala_project/src/main.scala")) == Language.SCALA
    assert get_language_by_path(Path("scalajs/app/Core.SCALA")) == Language.SCALA
    assert get_language_by_path(Path("ios/swift/ViewController.swift")) == Language.SWIFT
    assert get_language_by_path(Path("lib/module/Editor.tsx")) == Language.TYPESCRIPT
    assert get_language_by_path(Path("compiler/transformers/Adapter.TS")) == Language.TYPESCRIPT
    assert get_language_by_path(Path("macos/SwiftTypes/Type.SWIFT")) == Language.SWIFT
    assert get_language_by_path(Path("config/yaml/settings.yaml")) == Language.YAML
    assert get_language_by_path(Path("docker/compose/File.YML")) == Language.YAML
    assert get_language_by_path(Path("src/unknown/randomfile.unknown")) == Language.NOT_SUPPORTED
    assert get_language_by_path(Path("folder/with/no_extension")) == Language.NOT_SUPPORTED


@pytest.mark.blends_test_group("content_unittesting")
def test_get_file_raw_content_success() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        result = _get_file_raw_content(test_file)

        assert result == test_content


@pytest.mark.blends_test_group("content_unittesting")
def test_get_file_raw_content_with_size_limit() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        result = _get_file_raw_content(test_file, size=100)

        assert result == test_content


@pytest.mark.blends_test_group("content_unittesting")
def test_get_file_raw_content_file_too_large() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.txt"
        test_content = b"x" * 100
        test_file.write_bytes(test_content)

        with pytest.raises(FileTooLargeError):
            _get_file_raw_content(test_file, size=50)


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_success_python_file() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "module.py"
        test_content = "def hello():\n    print('world')"
        test_file.write_text(test_content, encoding="utf-8")

        result = get_content_by_path(test_file)

        assert result is not None
        assert isinstance(result, Content)
        assert result.content_str == test_content
        assert result.content_bytes == test_content.encode("utf-8")
        assert result.language == Language.PYTHON
        assert result.path == test_file


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_success_javascript_file() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "script.js"
        test_content = "function test() { return true; }"
        test_file.write_text(test_content, encoding="utf-8")

        result = get_content_by_path(test_file)

        assert result is not None
        assert isinstance(result, Content)
        assert result.content_str == test_content
        assert result.language == Language.JAVASCRIPT
        assert result.path == test_file


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_file_too_large() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "large.txt"
        large_content = "x" * 1000
        test_file.write_text(large_content, encoding="utf-8")

        result = get_content_by_path(test_file, max_size=100)

        assert result is None


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_file_not_found() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        non_existent_file = Path(temp_dir) / "nonexistent.py"

        result = get_content_by_path(non_existent_file)

        assert result is None


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_directory_instead_of_file() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        directory_path = Path(temp_dir)

        result = get_content_by_path(directory_path)

        assert result is None


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_custom_max_size() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.py"
        test_content = "print('test')"
        test_file.write_text(test_content, encoding="utf-8")

        result = get_content_by_path(test_file, max_size=50)

        assert result is not None
        assert result.content_str == test_content


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_not_supported_language() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "file.unknown"
        test_content = "some content"
        test_file.write_text(test_content, encoding="utf-8")

        result = get_content_by_path(test_file)

        assert result is not None
        assert isinstance(result, Content)
        assert result.language == Language.NOT_SUPPORTED
        assert result.content_str == test_content


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_json_without_helm_template() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "config.json"
        test_content = '{"key": "value"}'
        test_file.write_text(test_content, encoding="utf-8")

        result = get_content_by_path(test_file)

        assert result is not None
        assert isinstance(result, Content)
        assert result.language == Language.JSON
        assert result.content_str == test_content


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_yaml_without_helm_template() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "config.yaml"
        test_content = "key: value\nother: data"
        test_file.write_text(test_content, encoding="utf-8")

        result = get_content_by_path(test_file)

        assert result is not None
        assert isinstance(result, Content)
        assert result.language == Language.YAML
        assert result.content_str == test_content


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_json_helm_template_in_templates_directory() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        templates_dir = Path(temp_dir) / "templates"
        templates_dir.mkdir()
        test_file = templates_dir / "deployment.json"
        test_content = (
            '{"apiVersion": "v1", "kind": "Deployment", "metadata": {"name": "test"}, '
            '"spec": {"replicas": {{ .Values.replicas }}}}'
        )
        test_file.write_text(test_content, encoding="utf-8")

        result = get_content_by_path(test_file)

        assert result is not None
        assert isinstance(result, Content)
        assert result.language == Language.JSON


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_yaml_helm_template_in_templates_directory() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        templates_dir = Path(temp_dir) / "templates"
        templates_dir.mkdir()
        test_file = templates_dir / "deployment.yaml"
        test_content = (
            "apiVersion: v1\nkind: Deployment\nmetadata:\n  name: {{ .Values.name }}\n"
            "spec:\n  replicas: {{ .Values.replicas }}"
        )
        test_file.write_text(test_content, encoding="utf-8")

        result = get_content_by_path(test_file)

        assert result is not None
        assert isinstance(result, Content)
        assert result.language == Language.YAML


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_json_helm_template_not_in_templates_directory() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "deployment.json"
        test_content = (
            '{"apiVersion": "v1", "kind": "Deployment", "metadata": {"name": "test"}, '
            '"spec": {"replicas": {{ .Values.replicas }}}}'
        )
        test_file.write_text(test_content, encoding="utf-8")

        result = get_content_by_path(test_file)

        assert result is not None
        assert isinstance(result, Content)
        assert result.language == Language.JSON
        assert result.content_str == test_content


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_empty_file() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "empty.py"
        test_file.touch()

        result = get_content_by_path(test_file)

        assert result is not None
        assert isinstance(result, Content)
        assert result.content_str == ""
        assert result.content_bytes == b""
        assert result.language == Language.PYTHON


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_multiline_content() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "multiline.py"
        test_content = "line1\nline2\nline3\n"
        test_file.write_text(test_content, encoding="utf-8")

        result = get_content_by_path(test_file)

        assert result is not None
        assert result.content_str == test_content
        assert result.content_bytes == test_content.encode("utf-8")


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_special_characters() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "special.py"
        test_content = "print('ñáéíóú中文🚀')"
        test_file.write_text(test_content, encoding="utf-8")

        result = get_content_by_path(test_file)

        assert result is not None
        assert result.content_str == test_content
        assert result.content_bytes == test_content.encode("utf-8")


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_exact_max_size() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "exact.py"
        content_len = 100
        test_content = "x" * content_len
        test_file.write_text(test_content, encoding="utf-8")

        result = get_content_by_path(test_file, max_size=100)

        assert result is not None
        assert len(result.content_bytes) == content_len


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_one_byte_over_max_size() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "over.py"
        test_content = "x" * 101
        test_file.write_text(test_content, encoding="utf-8")

        result = get_content_by_path(test_file, max_size=100)

        assert result is None


@pytest.mark.blends_test_group("content_unittesting")
def test_get_content_by_path_all_supported_languages() -> None:
    language_extensions = {
        Language.PYTHON: ".py",
        Language.JAVASCRIPT: ".js",
        Language.TYPESCRIPT: ".ts",
        Language.JAVA: ".java",
        Language.KOTLIN: ".kt",
        Language.CSHARP: ".cs",
        Language.DART: ".dart",
        Language.GO: ".go",
        Language.HCL: ".hcl",
        Language.JSON: ".json",
        Language.PHP: ".php",
        Language.RUBY: ".rb",
        Language.SCALA: ".scala",
        Language.SWIFT: ".swift",
        Language.YAML: ".yaml",
        Language.NOT_SUPPORTED: ".unknown",
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        for language, extension in language_extensions.items():
            test_file = Path(temp_dir) / f"test{extension}"
            test_content = f"content for {language.value}"
            test_file.write_text(test_content, encoding="utf-8")

            result = get_content_by_path(test_file)

            assert result is not None
            assert result.language == language
            assert result.content_str == test_content


@pytest.mark.blends_test_group("content_unittesting")
def test_helm_parser_validates_and_parses_all_templates() -> None:
    templates_dir = Path(__file__).parent.parent / "data" / "helm_parser" / "templates"

    assert templates_dir.exists(), f"Templates directory not found: {templates_dir}"

    template_files = list[Path](templates_dir.iterdir())
    assert template_files, f"No template files found in {templates_dir}"

    for template_path in template_files:
        if not template_path.is_file():
            continue

        language = get_language_by_path(template_path)
        content_bytes = _get_file_raw_content(template_path)
        content_str = content_bytes.decode("utf-8", errors="ignore")
        content = Content(content_bytes, content_str, language, template_path)

        assert content is not None, f"Failed to create Content for {template_path}"

        if language_parsers := custom_parsers_by_language.get(language):
            for custom_parser in language_parsers:
                validator_result = custom_parser.validator(content)
                assert validator_result, (
                    f"Validator returned False for {template_path}. "
                    f"Expected True for helm template files."
                )

                fixed_content = custom_parser.parser(content)
                assert fixed_content is not None, (
                    f"Parser returned None for {template_path}. "
                    f"Expected a Content object after parsing."
                )
