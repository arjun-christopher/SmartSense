# Contributing to SmartSense

Thank you for considering contributing to SmartSense! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect different viewpoints and experiences

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title**: Descriptive summary of the issue
- **Description**: Detailed explanation of the problem
- **Steps to reproduce**: How to recreate the issue
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, SmartSense version
- **Logs**: Relevant log files from `logs/` directory

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. Include:

- **Clear title**: Concise description of the enhancement
- **Use case**: Why this enhancement would be useful
- **Proposed solution**: How you envision it working
- **Alternatives**: Other solutions you've considered

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/AmazingFeature`
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages**: `git commit -m 'Add some AmazingFeature'`
6. **Push to branch**: `git push origin feature/AmazingFeature`
7. **Open a Pull Request**

## Development Setup

### 1. Clone and Setup

```bash
git clone https://github.com/arjun-christopher/SmartSense.git
cd SmartSense
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Install Development Dependencies

```bash
pip install pytest pytest-asyncio black flake8 mypy
```

### 3. Run Tests

```bash
pytest tests/
```

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use meaningful variable names

### Code Formatting

```bash
# Format code with black
black .

# Check style with flake8
flake8 .

# Type checking with mypy
mypy .
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: Description of when this is raised
    """
    pass
```

### Testing

- Write unit tests for new features
- Maintain test coverage above 80%
- Use pytest for testing
- Test async code with pytest-asyncio

Example test:

```python
import pytest
from core.nlp import NLPProcessor

@pytest.mark.asyncio
async def test_nlp_processor():
    """Test NLP processor initialization"""
    processor = NLPProcessor("test", None)
    processor._initialized = True
    result = await processor._analyze_text("Hello world")
    assert result.intent is not None
```

## Project Structure

Understanding the codebase:

```
SmartSense/
├── core/           # Core AI components
│   ├── base.py            # Base classes
│   ├── nlp.py            # NLP processor
│   ├── vision_processor.py  # Vision processor
│   └── ...
├── models/         # Data models
│   ├── events.py         # Event definitions
│   ├── config.py         # Configuration models
│   └── ...
├── utils/          # Utilities
│   ├── logger.py         # Logging utilities
│   ├── lifecycle.py      # Lifecycle manager
│   └── ...
├── actions/        # Action handlers
├── ui/             # User interface
└── examples/       # Example scripts
```

## Component Development

### Creating a New Component

1. **Inherit from base class**:
```python
from core.base import BaseProcessor

class MyProcessor(BaseProcessor):
    async def initialize(self) -> bool:
        # Initialization code
        pass
    
    async def shutdown(self) -> None:
        # Cleanup code
        pass
    
    async def process_event(self, event: Event) -> Optional[Event]:
        # Event processing logic
        pass
```

2. **Register in lifecycle**:
Add to `utils/lifecycle.py` in `_register_components()`

3. **Add event subscriptions**:
Use `subscribe_to_event()` in `initialize()`

4. **Publish results**:
Use `publish_event()` to send results

### Adding Event Types

1. Add to `models/events.py`:
```python
class EventType(str, Enum):
    MY_NEW_EVENT = "my_new_event"
```

2. Create data model:
```python
class MyEventData(BaseModel):
    field1: str
    field2: int
```

## Git Commit Messages

Format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Example:
```
feat(nlp): add sentiment analysis

Implement sentiment analysis using VADER sentiment analyzer.
Supports positive, negative, and neutral sentiment detection.

Closes #123
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public methods
- Update QUICKSTART.md if setup process changes
- Create examples for new features

## Review Process

Pull requests are reviewed for:

1. **Functionality**: Does it work as intended?
2. **Code quality**: Is it well-written and maintainable?
3. **Tests**: Are there adequate tests?
4. **Documentation**: Is it properly documented?
5. **Style**: Does it follow coding standards?

## Release Process

1. Update version in `setup.py`
2. Update CHANGELOG.md
3. Tag release: `git tag v1.x.x`
4. Push tag: `git push origin v1.x.x`
5. Create GitHub release with notes

## Getting Help

- **Questions**: Open a GitHub discussion
- **Chat**: Join our community chat (if available)
- **Email**: Contact maintainers directly

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to SmartSense! 🎉
