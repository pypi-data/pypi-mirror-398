import os
from io import BytesIO

import pytest
from markitdown import FileConversionException, MarkItDown, StreamInfo

from markitdown_yaml import YamlConverter

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")

ACTIONS_TEST_STRINGS = {
    "# name",
    "GitHub Actions Workflow",
    "# on",
    "- push",
    "- pull_request",
    "# jobs",
    "## test",
}

KUBERNETES_TEST_STRINGS = {
    "# apiVersion",
    "apps/v1",
    "# kind",
    "Deployment",
    "# metadata",
    "## name",
    "nginx-deployment",
}

DOCKER_COMPOSE_TEST_STRINGS = {
    "# version",
    "3.8",
    "# services",
    "## web",
    "### image",
    "nginx:latest",
    "### ports",
}


def test_converter_actions() -> None:
    """
    Tests the YAML converter with a GitHub Actions workflow.
    """
    with open(os.path.join(TEST_FILES_DIR, "test_actions.yaml"), "rb") as file_stream:
        converter = YamlConverter()
        result = converter.convert(
            file_stream=file_stream,
            stream_info=StreamInfo(
                mimetype="application/yaml",
                extension=".yaml",
                filename="test_actions.yaml",
            ),
        )

    for test_string in ACTIONS_TEST_STRINGS:
        assert test_string in result.text_content


def test_converter_kubernetes() -> None:
    """
    Tests the YAML converter with a Kubernetes manifest file.
    """
    with open(os.path.join(TEST_FILES_DIR, "test_kubernetes.yaml"), "rb") as file_stream:
        converter = YamlConverter()
        result = converter.convert(
            file_stream=file_stream,
            stream_info=StreamInfo(
                mimetype="application/yaml",
                extension=".yaml",
                filename="test_kubernetes.yaml",
            ),
        )

    for test_string in KUBERNETES_TEST_STRINGS:
        assert test_string in result.text_content


def test_converter_docker_compose() -> None:
    """
    Tests the YAML converter with a Docker Compose file.
    """
    with open(os.path.join(TEST_FILES_DIR, "test_docker_compose.yaml"), "rb") as file_stream:
        converter = YamlConverter()
        result = converter.convert(
            file_stream=file_stream,
            stream_info=StreamInfo(
                mimetype="application/yaml",
                extension=".yaml",
                filename="test_docker_compose.yaml",
            ),
        )

    for test_string in DOCKER_COMPOSE_TEST_STRINGS:
        assert test_string in result.text_content


def test_accepts_yaml_extension() -> None:
    """
    Tests that converter accepts .yaml and .yml extensions.
    """
    converter = YamlConverter()
    dummy_stream = BytesIO(b"test: some_value")

    assert converter.accepts(
        dummy_stream, StreamInfo(extension=".yaml", mimetype=None, filename="test.yaml")
    )

    assert converter.accepts(
        dummy_stream, StreamInfo(extension=".yml", mimetype=None, filename="test.yml")
    )


def test_accepts_yaml_mimetype() -> None:
    """
    Tests that converter accepts YAML MIME types.
    """
    converter = YamlConverter()
    dummy_stream = BytesIO(b"test: some_value")

    assert converter.accepts(
        dummy_stream,
        StreamInfo(mimetype="application/yaml", extension=None, filename="test"),
    )

    assert converter.accepts(
        dummy_stream,
        StreamInfo(mimetype="application/x-yaml", extension=None, filename="test"),
    )

    assert converter.accepts(
        dummy_stream, StreamInfo(mimetype="text/yaml", extension=None, filename="test")
    )

    assert converter.accepts(
        dummy_stream,
        StreamInfo(mimetype="text/x-yaml", extension=None, filename="test"),
    )


def test_rejects_non_yaml() -> None:
    """
    Tests that converter rejects non-YAML files.
    """
    converter = YamlConverter()
    dummy_stream = BytesIO(b"test: some_value")

    assert not converter.accepts(
        dummy_stream, StreamInfo(extension=".txt", mimetype=None, filename="test.txt")
    )

    assert not converter.accepts(
        dummy_stream, StreamInfo(extension=".json", mimetype=None, filename="test.json")
    )

    assert not converter.accepts(
        dummy_stream, StreamInfo(extension=None, mimetype="text/plain", filename="test")
    )

    assert not converter.accepts(
        dummy_stream,
        StreamInfo(extension=None, mimetype="application/json", filename="test"),
    )


def test_empty_yaml() -> None:
    """
    Tests handling of empty YAML files.
    """
    converter = YamlConverter()
    empty_stream = BytesIO(b"")

    result = converter.convert(
        empty_stream, StreamInfo(extension=".yaml", mimetype="application/yaml")
    )

    assert "Empty YAML file" in result.text_content


def test_invalid_yaml() -> None:
    """Tests that invalid YAML raises appropriate exception."""
    converter = YamlConverter()

    # Invalid YAML - unclosed bracket
    invalid_yaml = BytesIO(b"key: [unclosed")

    with pytest.raises(FileConversionException, match="Error parsing YAML"):
        converter.convert(invalid_yaml, StreamInfo(extension=".yaml", mimetype="application/yaml"))


def test_invalid_encoding() -> None:
    """Tests handling of files with wrong encoding."""
    converter = YamlConverter()

    # Create UTF-16 encoded content but claim it's UTF-8
    content = "key: value with 🎉".encode("utf-16")
    stream = BytesIO(content)

    with pytest.raises(FileConversionException, match="Unable to decode file"):
        converter.convert(stream, StreamInfo(extension=".yaml", charset="utf-8"))


def test_markitdown_integration() -> None:
    """
    Tests that MarkItDown correctly loads the plugin.
    """
    md = MarkItDown(enable_plugins=True)

    # Test plugin loads and works with a YAML file
    result = md.convert(os.path.join(TEST_FILES_DIR, "test_actions.yaml"))

    for test_string in ACTIONS_TEST_STRINGS:
        assert test_string in result.text_content
