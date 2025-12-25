# 🛠️ Development Guide

## Setting Up Development Environment

### Prerequisites

- Python 3.10+
- pipx (for global CLI installation)
- Git

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/makeplane/compose.git
cd compose

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (if configured)
pre-commit install
```

### Project Structure

```
compose/
├── src/
│   └── planecompose/
│       ├── cli/              # CLI commands
│       ├── backend/          # Backend implementations
│       ├── core/             # Domain models
│       ├── config/           # Configuration
│       ├── parser/           # YAML parsers
│       ├── sync/             # Sync logic
│       ├── diff/             # Diff calculation
│       ├── validation/       # Validation rules
│       └── utils/            # Utilities
├── tests/                    # Test suite
├── docs/                     # Documentation
├── pyproject.toml            # Project metadata
└── README.md
```

## Running Tests

### All Tests

```bash
# Run full test suite
pytest

# With coverage
pytest --cov=planecompose --cov-report=html

# Verbose output
pytest -v

# Run specific test file
pytest tests/test_models.py

# Run specific test
pytest tests/test_models.py::test_work_item_basic
```

### Test Coverage Goals

- **Target**: 80%+ coverage
- **Critical modules**: 90%+ (models, backend, sync)
- **CLI modules**: 70%+ (harder to test)

### Writing Tests

Use the fixtures from `tests/conftest.py`:

```python
@pytest.mark.asyncio
async def test_push_work_items(mock_backend, temp_project):
    """Test pushing work items."""
    # Given
    item = WorkItem(title="Test", type="task")
    
    # When
    item_id = await mock_backend.create_work_item(item)
    
    # Then
    assert item_id.startswith("item-")
```

## Code Style

### Guidelines

1. **PEP 8**: Follow Python style guide
2. **Type Hints**: Use on all functions
3. **Docstrings**: Document all public APIs
4. **Max Line Length**: 100 characters
5. **Imports**: Organized (stdlib, third-party, local)

### Example

```python
"""Module description."""
from pathlib import Path
from typing import AsyncIterator

from rich.console import Console
from pydantic import BaseModel

from planecompose.core.models import WorkItem
from planecompose.exceptions import ValidationError


async def process_work_items(
    items: list[WorkItem],
    validate: bool = True,
) -> AsyncIterator[str]:
    """
    Process work items and yield IDs.
    
    Args:
        items: List of work items to process
        validate: Whether to validate items before processing
    
    Yields:
        Work item IDs as they are processed
    
    Raises:
        ValidationError: If validation fails
    
    Example:
        >>> items = [WorkItem(title="Test", type="task")]
        >>> async for item_id in process_work_items(items):
        ...     print(item_id)
    """
    for item in items:
        if validate:
            # Validation logic
            pass
        
        yield f"item-{item.title}"
```

### Linting

```bash
# Run ruff (fast linter)
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Type checking with mypy
mypy src/planecompose/

# Format code with black
black src/ tests/
```

## Debugging

### Enable Debug Logging

```bash
# Via CLI flag
plane --debug push

# Via environment variable
export PLANE_DEBUG=true
plane push

# View log file
tail -f ~/.config/plane-cli/plane.log
```

### Debugging with pdb

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

### VS Code Configuration

`.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Plane CLI",
      "type": "python",
      "request": "launch",
      "module": "planecompose.main",
      "args": ["push", "--verbose"],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

## Testing Locally

### Manual Testing

```bash
# Install locally
pip install -e .

# Test commands
plane init my-test-project
cd my-test-project
plane --help
plane status

# Test with mock project
cd tests/fixtures/sample-project
plane push --force
```

### Integration Testing

Test against real Plane instance:

```bash
# Set API key
export PLANE_API_KEY=your_key_here

# Run integration tests (not in default suite)
pytest tests/integration/ --integration
```

## Common Development Tasks

### Adding a New Command

1. Create file in `src/planecompose/cli/`:

```python
# src/planecompose/cli/export.py
import typer
from rich.console import Console

app = typer.Typer(help="Export data from Plane")
console = Console()

@app.command()
def json():
    """Export work items to JSON."""
    console.print("[green]Exporting...[/green]")
```

2. Register in `cli/root.py`:

```python
from planecompose.cli import export

app.add_typer(export.app, name="export")
```

3. Add tests:

```python
# tests/test_export.py
def test_export_json():
    """Test JSON export."""
    # Test implementation
    pass
```

### Adding a New Model

1. Define in `core/models.py`:

```python
class Milestone(BaseModel):
    """Project milestone model."""
    name: str
    description: str | None = None
    due_date: str | None = None
    target_date: str | None = None
```

2. Add parser if needed:

```python
# parser/milestones_yaml.py
def parse_milestones(yaml_path: Path) -> list[Milestone]:
    """Parse milestones from YAML."""
    # Implementation
    pass
```

3. Add tests:

```python
# tests/test_models.py
def test_milestone_model():
    """Test milestone model."""
    milestone = Milestone(name="v1.0", due_date="2025-12-31")
    assert milestone.name == "v1.0"
```

### Adding Custom Exceptions

1. Define in `exceptions.py`:

```python
class ImportError(PlaneComposeError):
    """Raised when import operations fail."""
    pass
```

2. Use in code:

```python
from planecompose.exceptions import ImportError

raise ImportError("Failed to import data", details={"source": "jira"})
```

3. Handle in CLI:

```python
try:
    import_data()
except ImportError as e:
    console.print(f"[red]Import failed: {e}[/red]")
    raise typer.Exit(1)
```

## Release Process

### Version Bumping

1. Update `pyproject.toml`:

```toml
[project]
version = "0.2.0"
```

2. Update `CHANGELOG.md`:

```markdown
## [0.2.0] - 2025-11-26

### Added
- New export command
- Rate limiting statistics

### Fixed
- Bug in state synchronization
```

3. Commit and tag:

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.2.0"
git tag v0.2.0
git push origin main --tags
```

### Publishing to PyPI

```bash
# Build distribution
python -m build

# Upload to PyPI (test)
twine upload --repository testpypi dist/*

# Upload to PyPI (production)
twine upload dist/*
```

### Creating GitHub Release

1. Go to GitHub Releases
2. Click "Draft a new release"
3. Select tag `v0.2.0`
4. Copy changelog content
5. Attach distribution files
6. Publish

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Solution: Reinstall in editable mode
pip install -e .
```

#### Test Failures

```bash
# Run with verbose output
pytest -vv --tb=long

# Run specific failing test
pytest tests/test_models.py::test_work_item_basic -vv
```

#### Rate Limit Errors

```bash
# Reset rate limit stats
plane rate reset

# Reduce rate limit for testing
export PLANE_RATE_LIMIT_PER_MINUTE=10
```

## Getting Help

- **Documentation**: `docs/`
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Discord**: [Join our Discord](#)

## Contributing Guidelines

### Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### PR Requirements

- [ ] Tests pass (`pytest`)
- [ ] Code is formatted (`black`, `ruff`)
- [ ] Types check (`mypy`)
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Tests added for new features

### Code Review

- All PRs require review from maintainers
- Address feedback within 2 weeks
- Squash commits before merging

## Resources

- [Plane API Docs](https://docs.plane.so/api)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Rich Documentation](https://rich.readthedocs.io/)

