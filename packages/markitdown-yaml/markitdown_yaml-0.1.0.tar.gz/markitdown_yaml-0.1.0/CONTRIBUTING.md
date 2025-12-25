# Contributing to MarkItDown YAML Plugin
Thank you for your interest in contributing to the MarkItDown YAML plugin! This document provides guidelines and instructions for contributing.

## Getting Started
### Prerequisites
- Python 3.10 or higher
- Git
- Familiarity with YAML and Markdown formats

### Development Setup
1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/markitdown-yaml.git
   cd markitdown-yaml
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e .
   ```

4. **Install development dependencies**
   ```bash
   pip install -e ".[test]"
   ```

## How to Contribute

### Reporting Bugs
If you find a bug, please create an issue with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs. actual behavior
- Sample YAML file that demonstrates the issue (if applicable)
- Your Python version and OS

### Suggesting Enhancements
For feature requests:
- Describe the feature and its use case
- Explain why it would be useful
- Provide examples of how it would work

### Pull Requests
1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clear, documented code
   - Follow the existing code style
   - Add or update tests if applicable
   - Update documentation as needed

3. **Test your changes**
   ```bash
   pytest  # Run tests
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add feature description"
   ```

5. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style
- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Write clear docstrings for public functions and classes
- Keep functions focused and concise
- Add comments for complex logic

### Testing Guidelines
Testing is **required** for all code changes:

1. **Write tests first**
2. **Run the test suite** before committing:
   ```bash
   pytest tests/ -v
   ```
3. **Check code coverage**:
   ```bash
   pytest tests/ --cov=markitdown_yaml --cov-report=term
   ```
   - Target: 90%+ coverage for new code

4. **Add test files** to `tests/test_files/` for new YAML formats
5. **Test edge cases**:
   - Empty files
   - Invalid YAML
   - Encoding issues
   - Deeply nested structures

6. **Test both converter and integration**:
   - Direct converter tests (unit tests)
   - MarkItDown integration tests (end-to-end)

#### Test Categories
- **Conversion tests**: Verify correct Markdown output
- **Acceptance tests**: File type detection
- **Edge case tests**: Error handling and unusual inputs
- **Integration tests**: Plugin system compatibility

## Development Priorities
Current areas where contributions are especially welcome:

1. **Specialized YAML Format Support**: Format-specific optimizations for:
   - GitHub Actions
   - OpenAPI/Swagger specifications
   - Helm charts

2. **Enhanced Formatting**: 
   - Improved rendering of deeply nested structures
   - Table formatting for certain YAML structures
   - Code block formatting for embedded scripts

3. **Performance Improvements**:
   - Optimization for large YAML files
   - Streaming support for very large files

4. **Additional Features**:
   - Custom formatting options via kwargs
   - Configuration file support
   - Validation of converted output

## Questions?
Feel free to open an issue for questions or discussions about:
- Implementation approaches
- Design decisions
- Feature ideas
- Anything else related to the project

## Code of Conduct
Be respectful, inclusive, and considerate in all interactions. We're all here to learn and improve the project together.

## License
By contributing, you agree that your contributions will be licensed under the MIT License.