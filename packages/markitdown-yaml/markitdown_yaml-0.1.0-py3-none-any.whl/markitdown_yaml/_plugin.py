# SPDX-FileCopyrightText: 2025-present Yasir Alibrahem <alibrahem.yasir@gmail.com>
#
# SPDX-License-Identifier: MIT

from typing import Any, BinaryIO

from markitdown import (
    DocumentConverter,
    DocumentConverterResult,
    FileConversionException,
    MarkItDown,
    StreamInfo,
)
from ruamel.yaml import YAML, YAMLError

__plugin_interface_version__ = 1

ACCEPTED_FILE_EXTENSIONS = [".yaml", ".yml"]

ACCEPTED_MIME_TYPE_PREFIXES = [
    "application/yaml",
    "application/x-yaml",
    "text/yaml",
    "text/x-yaml",
]


def register_converters(markitdown: MarkItDown, **kwargs):
    """
    Called during construction of MarkItDown instances to register converters provided by plugins.

    Args:
        markitdown: The MarkItDown instance to register converters with
        **kwargs: Additional keyword arguments (unused but required by plugin interface)
    """
    markitdown.register_converter(YamlConverter())


class YamlConverter(DocumentConverter):
    """
    Converts YAML files to structured Markdown.
    """

    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        """
        Determines if this converter can handle the given file.
        """
        mimetype = (stream_info.mimetype or "").lower()
        extension = (stream_info.extension or "").lower()

        if extension in ACCEPTED_FILE_EXTENSIONS:
            return True

        return any(mimetype.startswith(prefix) for prefix in ACCEPTED_MIME_TYPE_PREFIXES)

    def convert(
        self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any
    ) -> DocumentConverterResult:
        """
        Converts a YAML file to Markdown.

        Args:
            file_stream: Binary file stream to convert
            stream_info: Metadata about the file (mimetype, extension, charset)
            **kwargs: Additional conversion parameters

        Returns:
            DocumentConverterResult containing the Markdown representation

        Raises:
            FileConversionException: If YAML parsing fails
        """
        # Read file content
        encoding = stream_info.charset or "utf-8"
        try:
            content = file_stream.read().decode(encoding)
        except UnicodeDecodeError as e:
            raise FileConversionException(
                f"Unable to decode file with '{encoding}' encoding: {str(e)}"
            ) from e

        # Handle empty files
        if not content or not content.strip():
            return DocumentConverterResult(markdown="Empty YAML file")

        # Parse YAML using YAML 1.2 (prevents YAML 1.1 on/off/yes/no boolean conversion)
        yaml_parser = YAML()
        yaml_parser.preserve_quotes = False  # We don't need to preserve formatting
        try:
            data = yaml_parser.load(content)
        except YAMLError as e:
            raise FileConversionException(f"Error parsing YAML file: {str(e)}") from e

        # Convert to markdown
        markdown = self._structure_to_markdown(data)

        return DocumentConverterResult(markdown=markdown)

    def _structure_to_markdown(self, data: Any, level: int = 1) -> str:
        """
        Recursively converts YAML data structures to Markdown.
        Returns a Markdown string representation.

        Args:
            data: YAML data (dict, list, or scalar)
            level: Current heading level for nested structures
        """

        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                # Create header for this key
                header = "#" * min(level, 6)  # Max 6 levels in Markdown
                lines.append(f"{header} {key}")

                # Recursively process the value at deeper nesting level
                nested_result = self._structure_to_markdown(value, level + 1)
                if nested_result:  # Only add non-empty results to prevent excessive blank lines
                    lines.append(nested_result)

            return "\n".join(lines)

        if isinstance(data, list):
            lines = []
            for i, item in enumerate(data, 1):
                # Check if item is a scalar (simple value)
                if item is None:
                    lines.append("- null")
                elif isinstance(item, (str, int, float, bool)):
                    lines.append(f"- {item}")
                elif isinstance(item, dict):
                    # Handle empty dictionaries
                    if not item:
                        lines.append(f"{i}. {{}}")
                        continue

                    # Format dictionaries as key-value pairs
                    pairs = []
                    for key, value in item.items():
                        # Check if value is complex (dict/list), common in Kubernetes manifests
                        if isinstance(value, (dict, list)):
                            nested = self._structure_to_markdown(value, level + 1)
                            if nested:  # Only process non-empty nested results
                                # Indent the nested content to align with parent
                                parent_indent = " " * (len(str(i)) + 2)
                                nested_indented = "\n".join(
                                    f"{parent_indent}{line}" if line.strip() else ""
                                    for line in nested.split("\n")
                                )
                                pairs.append(f"**{key}**\n{nested_indented}")
                            else:
                                # For None or empty values, show explicit representation
                                pairs.append(f"**{key}**: null")
                        else:
                            pairs.append(f"**{key}**: {value}")
                    # Join with line breaks and indent continuation lines
                    lines.append(f"{i}. {pairs[0]}")
                    # indentation to account for single- and multi-digit numbering
                    indent = " " * (len(str(i)) + 2)  # length of i + ". "
                    for pair in pairs[1:]:
                        lines.append(f"{indent}{pair}")  # Indent continuation
                else:
                    # Complex nested structure
                    nested_md = self._structure_to_markdown(item, level)
                    if nested_md:
                        lines.append(f"{i}. {nested_md}")

            return "\n".join(lines)

        return str(data)
