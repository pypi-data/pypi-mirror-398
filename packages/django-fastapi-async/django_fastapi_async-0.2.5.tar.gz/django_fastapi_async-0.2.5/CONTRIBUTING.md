# Contributing to FastDjango

Thank you for your interest in contributing to FastDjango! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/TWFBusiness/fastdjango/issues)
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the bug
   - Expected behavior
   - Actual behavior
   - Python version and OS
   - Relevant code snippets

### Suggesting Features

1. Check existing issues and discussions
2. Create a new issue with:
   - Clear description of the feature
   - Use case / motivation
   - Proposed implementation (if any)

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Write/update tests
5. Ensure all tests pass: `pytest`
6. Format code: `black . && ruff check --fix .`
7. Commit with a clear message: `git commit -m "Add: feature description"`
8. Push to your fork: `git push origin feature/my-feature`
9. Create a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/TWFBusiness/fastdjango.git
cd fastdjango

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check --fix .

# Type checking
mypy fastdjango
```

## Project Structure

```
fastdjango/
├── fastdjango/           # Main package
│   ├── app.py           # FastDjango application
│   ├── conf/            # Settings
│   ├── core/            # Core utilities, exceptions, signals
│   ├── db/              # ORM (models, fields, queryset)
│   ├── contrib/         # Contrib apps (admin, auth, sessions)
│   ├── middleware/      # Middleware classes
│   ├── routing/         # Router and WebSocket
│   ├── templates/       # Template engine
│   ├── forms/           # Forms and schemas
│   └── utils/           # Utilities
├── tests/               # Test suite
├── docs/                # Documentation
└── example/             # Example project
```

## Coding Standards

### Style

- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints
- Write docstrings for public functions/classes

### Commit Messages

Use conventional commits:
- `Add:` New feature
- `Fix:` Bug fix
- `Docs:` Documentation changes
- `Test:` Test additions/changes
- `Refactor:` Code refactoring
- `Style:` Formatting, no code change
- `Chore:` Maintenance tasks

### Testing

- Write tests for new features
- Maintain test coverage
- Use pytest and pytest-asyncio
- Test both success and error cases

Example test:
```python
import pytest
from fastdjango.db.models import Model
from fastdjango.db import fields

class TestModel(Model):
    name = fields.CharField(max_length=100)

    class Meta:
        table = "test_model"

@pytest.mark.asyncio
async def test_model_create():
    obj = await TestModel.objects.create(name="test")
    assert obj.pk is not None
    assert obj.name == "test"
```

## Areas for Contribution

### High Priority
- [ ] Improve Admin interface
- [ ] Add more comprehensive tests
- [ ] Better documentation
- [ ] Aerich integration for migrations

### Medium Priority
- [ ] Cache framework
- [ ] Email backend
- [ ] File uploads/storage
- [ ] Pagination utilities

### Good First Issues
- Add more template filters
- Improve error messages
- Add type hints to missing functions
- Write documentation examples

## Questions?

Feel free to open an issue for questions or join our discussions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
