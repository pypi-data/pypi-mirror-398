# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-20

### Added
- Initial release of MarkItDown YAML plugin
- Support for converting YAML files to Markdown format
- YAML 1.2 compliance (correct handling of `on`, `off`, `yes`, `no` as strings)
- Hierarchical structure preservation with Markdown headers
- Smart formatting for dictionaries, lists, and nested structures
- Support for multiple MIME types: `application/yaml`, `application/x-yaml`, `text/yaml`, `text/x-yaml`
- File extension detection for `.yaml` and `.yml` files
- Error handling for encoding issues and malformed YAML
- Comprehensive documentation and examples

### Tested With
- GitHub Actions workflows
- Kubernetes manifests
- Docker Compose files

[Unreleased]: https://github.com/YasirAlibrahem/markitdown-yaml/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/YasirAlibrahem/markitdown-yaml/releases/tag/v0.1.0
