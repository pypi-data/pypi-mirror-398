# Contributing to Todo CLI

Thank you for your interest in contributing to Todo CLI! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Test Fixtures](#test-fixtures)
- [Code Coverage](#code-coverage)
- [Performance Testing](#performance-testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip or uv for package management
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/AgileInnov8tor/todo-cli.git
cd todo-cli
```

2. Install in development mode:
```bash
pip install -e ".[dev]"
```

This installs the package in editable mode with all development dependencies (pytest, pytest-cov).

## Running Tests

### Quick Test Run

Run all tests:
```bash
pytest
```

Run tests with output:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_database.py
```

Run specific test:
```bash
pytest tests/test_database.py::TestDatabase::test_add
```

### Test Coverage

Run tests with coverage report:
```bash
pytest --cov=todo_cli --cov-report=term-missing
```

Generate HTML coverage report:
```bash
pytest --cov=todo_cli --cov-report=html
open htmlcov/index.html
```

**Coverage Requirements:**
- Minimum coverage: 80%
- Current coverage: 87%
- CI will fail if coverage drops below 80%

### Performance Tests

Performance regression tests are in `tests/test_performance.py`. These tests ensure queries remain fast:

```bash
# Run performance tests (uses 1k dataset for speed)
pytest tests/test_performance.py -v

# Run with full 10k dataset (local only)
# Edit benchmark_db fixture in test_performance.py first
pytest tests/test_performance.py -v -s
```

**Performance Targets:**
- `todo list`: <100ms
- `todo list --project`: <100ms
- `todo project list`: <200ms

## Test Fixtures

The project provides comprehensive test fixtures in `tests/conftest.py`:

### Basic Fixtures

- `runner`: CLI test runner (Typer CliRunner)
- `temp_dir`: Temporary directory for test files
- `temp_db`: Temporary database instance
- `temp_config`: Temporary config file path

### Sample Data Fixtures

- `sample_project`: Single project with sample data
- `sample_projects`: List of 3 projects (Alpha, Beta, Gamma)
- `sample_task`: Single task with sample data
- `sample_tasks`: List of 5 tasks with varying properties:
  - High priority task with project
  - Overdue bug task
  - Low priority documentation task
  - In-progress code review task
  - Completed deployment task

### Composite Fixtures

- `db_with_data`: Database pre-populated with projects and tasks

### Using Fixtures

```python
def test_project_stats(sample_project, sample_tasks):
    """Test using pre-populated sample data."""
    pm = ProjectManager(sample_project.db_path)
    stats = pm.get_project_stats(sample_project.id)

    assert stats['total_tasks'] == 3  # 3 tasks assigned to sample_project
    assert stats['completion_rate'] > 0
```

### Creating Custom Fixtures

Add new fixtures to `tests/conftest.py`:

```python
@pytest.fixture
def custom_fixture(temp_db):
    """Your custom fixture description."""
    # Setup
    data = create_test_data(temp_db)

    yield data

    # Teardown (optional)
    cleanup(data)
```

## Test Organization

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_cli_commands.py     # CLI command tests
├── test_database.py         # Database operations
├── test_projects.py         # Project management
├── test_migrations.py       # Database migrations
├── test_performance.py      # Performance benchmarks
├── test_config.py           # Configuration
├── test_export.py           # Export functionality
├── test_interactive.py      # Interactive mode
└── test_reports.py          # Reporting features
```

### Test Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test<Feature>`
- Test methods: `test_<scenario>`

Example:
```python
class TestProjectFiltering:
    def test_list_with_project_filter(self, runner, cli_env):
        """Test filtering todos by project name."""
        # Test implementation
```

### Test Documentation

Every test should have a clear docstring explaining:
- What is being tested
- Expected behavior
- Any special setup or conditions

```python
def test_combined_filters_project_and_status(self, runner, cli_env):
    """Test combining --project with --status filter.

    Ensures that multiple filters work correctly when combined,
    and that results properly intersect the filter criteria.
    """
    # Test implementation
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints for function parameters and return values
- Maximum line length: 100 characters
- Use docstrings for all public functions and classes

### Running Linters

```bash
# Install linters
pip install ruff mypy

# Run ruff (fast linter)
ruff check todo_cli/ tests/

# Run type checker
mypy todo_cli/
```

### Code Formatting

```bash
# Auto-format code
ruff format todo_cli/ tests/
```

## Continuous Integration

Tests run automatically on GitHub Actions for:
- Python 3.10, 3.11, 3.12, 3.13
- All tests must pass
- Coverage must be ≥80%
- Performance benchmarks must pass

### CI Workflow

The CI pipeline runs:
1. **Unit Tests**: All test files except performance
2. **Performance Tests**: Regression benchmarks
3. **Coverage**: Report uploaded to Codecov
4. **Linting**: Code quality checks

## Submitting Changes

### Pull Request Process

1. **Create a branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Make changes**:
- Write code
- Add tests
- Update documentation

3. **Run tests locally**:
```bash
pytest --cov=todo_cli --cov-report=term-missing
```

4. **Ensure coverage**:
- New code should have >80% coverage
- Don't decrease overall coverage

5. **Commit changes**:
```bash
git add .
git commit -m "feat: add new feature"
```

6. **Push and create PR**:
```bash
git push origin feature/your-feature-name
```

### Commit Message Format

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or modifications
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

Example:
```
feat: add project filtering to list command

- Add --project flag to filter todos by project
- Update database queries to support project_id
- Add tests for project filtering
- Update documentation

Closes #123
```

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] All tests pass locally
- [ ] New code has tests
- [ ] Coverage is ≥80%
- [ ] Performance tests pass
- [ ] Documentation updated
- [ ] Commit messages follow format
- [ ] No merge conflicts
- [ ] Code follows style guide

## Database Migrations

When modifying the database schema:

1. Create a new migration in `todo_cli/migrations.py`
2. Increment `CURRENT_VERSION`
3. Add migration function
4. Test migration path from all previous versions
5. Document migration in comments

Example:
```python
def migrate_v2_to_v3(self, conn) -> bool:
    """Add new column to todos table.

    Changes:
    - Add 'column_name' to todos table
    """
    # Migration implementation
```

## Testing Best Practices

1. **Test Independence**: Each test should be independent and not rely on other tests
2. **Use Fixtures**: Leverage existing fixtures instead of duplicating setup code
3. **Clear Assertions**: Use descriptive assertion messages
4. **Edge Cases**: Test boundary conditions and error cases
5. **Performance**: Keep tests fast (<30 seconds for full suite excluding benchmarks)

### Example Test

```python
def test_project_stats_calculation(sample_project, temp_db):
    """Test that project statistics are calculated correctly.

    Verifies that completion rate, task counts, and time tracking
    are accurately computed for a project with mixed task statuses.
    """
    # Arrange
    pm = ProjectManager(temp_db.db_path)

    # Add tasks with different statuses
    temp_db.add("Task 1", project_id=sample_project.id)
    task2 = temp_db.add("Task 2", project_id=sample_project.id)
    temp_db.mark_done(task2.id)

    # Act
    stats = pm.get_project_stats(sample_project.id)

    # Assert
    assert stats['total_tasks'] == 2, "Should count all tasks"
    assert stats['completed_tasks'] == 1, "Should count completed tasks"
    assert stats['completion_rate'] == 50.0, "Should calculate correct percentage"
```

## Getting Help

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Review existing issues and PRs
- Check documentation in `docs/`

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).
