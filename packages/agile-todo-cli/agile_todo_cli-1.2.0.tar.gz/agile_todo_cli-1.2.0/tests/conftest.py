"""Pytest fixtures for todo-cli tests."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typer.testing import CliRunner

from todo_cli.config import Config, reload_config
from todo_cli.database import Database
from todo_cli.projects import ProjectManager
from todo_cli.models import Priority, Status
from todo_cli.main import app


@pytest.fixture
def runner():
    """CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_config(temp_dir):
    """Create a temporary config file."""
    config_path = temp_dir / "config.yaml"
    return config_path


@pytest.fixture
def temp_db(temp_dir):
    """Create a temporary database."""
    db_path = temp_dir / "test.db"
    return Database(db_path)


@pytest.fixture
def config_with_defaults():
    """Config with default values."""
    return Config()


@pytest.fixture
def sample_config():
    """Config with sample non-default values."""
    return Config(
        default_priority="p1",
        date_format="MM/DD/YYYY",
        time_format="12h",
        color_scheme="none",
        confirm_delete=False,
        auto_start_on_add=True,
        show_completed_in_list=True,
    )


@pytest.fixture(autouse=True)
def reset_config():
    """Reset global config before each test."""
    import todo_cli.config as config_module
    config_module._config = None
    yield
    config_module._config = None


@pytest.fixture
def sample_project(temp_db):
    """Create a sample project for testing.

    Args:
        temp_db: Temporary database fixture

    Returns:
        Project object with sample data
    """
    pm = ProjectManager(temp_db.db_path)
    return pm.create_project(
        name="Sample Project",
        description="A test project for unit tests",
        color="cyan"
    )


@pytest.fixture
def sample_projects(temp_db):
    """Create multiple sample projects for testing.

    Args:
        temp_db: Temporary database fixture

    Returns:
        List of 3 Project objects
    """
    pm = ProjectManager(temp_db.db_path)
    projects = [
        pm.create_project("Project Alpha", "First test project", "cyan"),
        pm.create_project("Project Beta", "Second test project", "green"),
        pm.create_project("Project Gamma", "Third test project", "yellow"),
    ]
    return projects


@pytest.fixture
def sample_task(temp_db):
    """Create a sample task for testing.

    Args:
        temp_db: Temporary database fixture

    Returns:
        Todo object with sample data
    """
    return temp_db.add(
        task="Sample task for testing",
        priority=Priority.P2,
        tags=["test", "sample"],
        due_date=datetime.now() + timedelta(days=7)
    )


@pytest.fixture
def sample_tasks(temp_db, sample_project):
    """Create multiple sample tasks for testing.

    Args:
        temp_db: Temporary database fixture
        sample_project: Sample project fixture

    Returns:
        List of 5 Todo objects with varying properties
    """
    tasks = []

    # Task 1: High priority, assigned to project, with tags
    tasks.append(temp_db.add(
        task="Implement feature X",
        priority=Priority.P0,
        project_id=sample_project.id,
        tags=["feature", "urgent"],
        due_date=datetime.now() + timedelta(days=1)
    ))

    # Task 2: Normal priority, no project, overdue
    tasks.append(temp_db.add(
        task="Fix bug in authentication",
        priority=Priority.P2,
        tags=["bug"],
        due_date=datetime.now() - timedelta(days=2)
    ))

    # Task 3: Low priority, assigned to project, no due date
    tasks.append(temp_db.add(
        task="Update documentation",
        priority=Priority.P3,
        project_id=sample_project.id,
        tags=["docs"]
    ))

    # Task 4: High priority, in progress with time tracked
    task4 = temp_db.add(
        task="Code review PR #123",
        priority=Priority.P1,
        tags=["review"]
    )
    task4.status = Status.DOING
    task4.time_spent = timedelta(hours=2, minutes=30)
    temp_db.update(task4)
    tasks.append(task4)

    # Task 5: Completed task
    task5 = temp_db.add(
        task="Deploy to staging",
        priority=Priority.P2,
        project_id=sample_project.id,
        tags=["deployment"]
    )
    temp_db.mark_done(task5.id)
    tasks.append(temp_db.get(task5.id))

    return tasks


@pytest.fixture
def db_with_data(temp_db, sample_projects, sample_tasks):
    """Database pre-populated with sample projects and tasks.

    Args:
        temp_db: Temporary database fixture
        sample_projects: Sample projects fixture
        sample_tasks: Sample tasks fixture

    Returns:
        Tuple of (Database, list of projects, list of tasks)
    """
    return (temp_db, sample_projects, sample_tasks)
