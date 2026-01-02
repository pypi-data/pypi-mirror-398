"""Tests for project management."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from todo_cli.projects import ProjectManager, Project
from todo_cli.database import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    # Initialize database with migrations
    db = Database(db_path)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def pm(temp_db):
    """Create a ProjectManager instance."""
    return ProjectManager(temp_db)


@pytest.fixture
def db(temp_db):
    """Create a Database instance."""
    return Database(temp_db)


class TestProjectCreate:
    """Test project creation."""

    def test_create_basic_project(self, pm):
        """Test creating a basic project."""
        project = pm.create_project("Test Project")

        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description is None
        assert project.color is None
        assert project.archived is False
        assert project.created_at is not None
        assert project.updated_at is not None

    def test_create_project_with_description(self, pm):
        """Test creating a project with description."""
        project = pm.create_project(
            "Test Project",
            description="This is a test project"
        )

        assert project.description == "This is a test project"

    def test_create_project_with_color(self, pm):
        """Test creating a project with color."""
        project = pm.create_project("Test Project", color="blue")

        assert project.color == "blue"

    def test_create_project_strips_whitespace(self, pm):
        """Test that project name is trimmed."""
        project = pm.create_project("  Test Project  ")

        assert project.name == "Test Project"

    def test_create_project_empty_name_fails(self, pm):
        """Test that empty project name fails."""
        with pytest.raises(ValueError, match="cannot be empty"):
            pm.create_project("")

        with pytest.raises(ValueError, match="cannot be empty"):
            pm.create_project("   ")

    def test_create_duplicate_project_fails(self, pm):
        """Test that duplicate project names fail."""
        pm.create_project("Test Project")

        with pytest.raises(ValueError, match="already exists"):
            pm.create_project("Test Project")

    def test_create_duplicate_project_case_insensitive(self, pm):
        """Test that duplicate check is case-insensitive."""
        pm.create_project("Test Project")

        with pytest.raises(ValueError, match="already exists"):
            pm.create_project("test project")

        with pytest.raises(ValueError, match="already exists"):
            pm.create_project("TEST PROJECT")


class TestProjectRetrieval:
    """Test project retrieval."""

    def test_get_project_by_id(self, pm):
        """Test getting project by ID."""
        created = pm.create_project("Test Project")
        retrieved = pm.get_project(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_project_nonexistent(self, pm):
        """Test getting nonexistent project returns None."""
        result = pm.get_project(999)

        assert result is None

    def test_get_project_by_name(self, pm):
        """Test getting project by name."""
        pm.create_project("Test Project")
        retrieved = pm.get_project_by_name("Test Project")

        assert retrieved is not None
        assert retrieved.name == "Test Project"

    def test_get_project_by_name_case_insensitive(self, pm):
        """Test that name lookup is case-insensitive."""
        pm.create_project("Test Project")

        assert pm.get_project_by_name("test project") is not None
        assert pm.get_project_by_name("TEST PROJECT") is not None
        assert pm.get_project_by_name("TeSt PrOjEcT") is not None

    def test_get_project_by_name_nonexistent(self, pm):
        """Test getting nonexistent project by name returns None."""
        result = pm.get_project_by_name("Nonexistent")

        assert result is None


class TestProjectList:
    """Test listing projects."""

    def test_list_projects_empty(self, pm):
        """Test listing projects when none exist."""
        projects = pm.list_projects()

        assert projects == []

    def test_list_projects(self, pm):
        """Test listing multiple projects."""
        pm.create_project("Project A")
        pm.create_project("Project B")
        pm.create_project("Project C")

        projects = pm.list_projects()

        assert len(projects) == 3
        # Should be sorted by name
        assert projects[0].name == "Project A"
        assert projects[1].name == "Project B"
        assert projects[2].name == "Project C"

    def test_list_projects_excludes_archived(self, pm):
        """Test that archived projects are excluded by default."""
        p1 = pm.create_project("Active Project")
        p2 = pm.create_project("Archived Project")

        pm.archive_project(p2.id)

        projects = pm.list_projects(archived=False)

        assert len(projects) == 1
        assert projects[0].name == "Active Project"

    def test_list_archived_projects(self, pm):
        """Test listing only archived projects."""
        p1 = pm.create_project("Active Project")
        p2 = pm.create_project("Archived Project")

        pm.archive_project(p2.id)

        projects = pm.list_projects(archived=True)

        assert len(projects) == 1
        assert projects[0].name == "Archived Project"


class TestProjectUpdate:
    """Test updating projects."""

    def test_update_project_name(self, pm):
        """Test updating project name."""
        project = pm.create_project("Old Name")
        updated = pm.update_project(project.id, name="New Name")

        assert updated is not None
        assert updated.name == "New Name"

    def test_update_project_description(self, pm):
        """Test updating project description."""
        project = pm.create_project("Test Project")
        updated = pm.update_project(project.id, description="New description")

        assert updated is not None
        assert updated.description == "New description"

    def test_update_project_color(self, pm):
        """Test updating project color."""
        project = pm.create_project("Test Project")
        updated = pm.update_project(project.id, color="red")

        assert updated is not None
        assert updated.color == "red"

    def test_update_project_duplicate_name_fails(self, pm):
        """Test that updating to existing name fails."""
        pm.create_project("Project A")
        project_b = pm.create_project("Project B")

        with pytest.raises(ValueError, match="already exists"):
            pm.update_project(project_b.id, name="Project A")

    def test_update_project_same_name_succeeds(self, pm):
        """Test that updating to same name (different case) succeeds."""
        project = pm.create_project("Test Project")
        updated = pm.update_project(project.id, name="test project")

        assert updated is not None

    def test_update_nonexistent_project(self, pm):
        """Test updating nonexistent project returns None."""
        result = pm.update_project(999, name="New Name")

        assert result is None


class TestProjectDelete:
    """Test deleting projects."""

    def test_delete_project(self, pm):
        """Test deleting a project."""
        project = pm.create_project("Test Project")

        success = pm.delete_project(project.id)

        assert success is True
        assert pm.get_project(project.id) is None

    def test_delete_nonexistent_project(self, pm):
        """Test deleting nonexistent project returns False."""
        success = pm.delete_project(999)

        assert success is False

    def test_delete_project_tasks_persist(self, pm, db):
        """Test that deleting a project keeps tasks."""
        # Create project
        project = pm.create_project("Test Project")

        # Add tasks to project
        task1 = db.add("Task 1")
        task2 = db.add("Task 2")

        # Manually set project_id (since we haven't added CLI support yet)
        with db._get_conn() as conn:
            conn.execute("UPDATE todos SET project_id = ? WHERE id = ?",
                        (project.id, task1.id))
            conn.execute("UPDATE todos SET project_id = ? WHERE id = ?",
                        (project.id, task2.id))
            conn.commit()

        # Delete project
        pm.delete_project(project.id)

        # Verify tasks still exist
        assert db.get(task1.id) is not None
        assert db.get(task2.id) is not None

        # Verify project_id is NULL
        with db._get_conn() as conn:
            row = conn.execute("SELECT project_id FROM todos WHERE id = ?",
                             (task1.id,)).fetchone()
            assert row['project_id'] is None


class TestProjectArchive:
    """Test archiving projects."""

    def test_archive_project(self, pm):
        """Test archiving a project."""
        project = pm.create_project("Test Project")

        archived = pm.archive_project(project.id)

        assert archived is not None
        assert archived.archived is True

    def test_unarchive_project(self, pm):
        """Test unarchiving a project."""
        project = pm.create_project("Test Project")
        pm.archive_project(project.id)

        unarchived = pm.unarchive_project(project.id)

        assert unarchived is not None
        assert unarchived.archived is False

    def test_archive_nonexistent_project(self, pm):
        """Test archiving nonexistent project."""
        result = pm.archive_project(999)

        # Should return None (no rows updated)
        # But get_project will return None
        assert result is None


class TestProjectStats:
    """Test project statistics."""

    def test_project_stats_no_tasks(self, pm):
        """Test stats for project with no tasks."""
        project = pm.create_project("Test Project")

        stats = pm.get_project_stats(project.id)

        assert stats is not None
        assert stats['total_tasks'] == 0
        assert stats['completed_tasks'] == 0
        assert stats['active_tasks'] == 0
        assert stats['completion_rate'] == 0
        assert stats['total_time_seconds'] == 0

    def test_project_stats_with_tasks(self, pm, db):
        """Test stats for project with tasks."""
        project = pm.create_project("Test Project")

        # Add tasks
        task1 = db.add("Task 1")
        task2 = db.add("Task 2")
        task3 = db.add("Task 3")

        # Assign to project and mark one done
        with db._get_conn() as conn:
            conn.execute("UPDATE todos SET project_id = ? WHERE id IN (?, ?, ?)",
                        (project.id, task1.id, task2.id, task3.id))
            conn.commit()

        db.mark_done(task1.id)

        stats = pm.get_project_stats(project.id)

        assert stats['total_tasks'] == 3
        assert stats['completed_tasks'] == 1
        assert stats['active_tasks'] == 2
        assert stats['completion_rate'] == pytest.approx(33.33, rel=0.1)

    def test_project_stats_priority_breakdown(self, pm, db):
        """Test priority breakdown in stats."""
        project = pm.create_project("Test Project")

        # Add tasks with different priorities
        from todo_cli.models import Priority

        task1 = db.add("Task 1", priority=Priority.P0)
        task2 = db.add("Task 2", priority=Priority.P1)
        task3 = db.add("Task 3", priority=Priority.P1)

        # Assign to project
        with db._get_conn() as conn:
            conn.execute("UPDATE todos SET project_id = ? WHERE id IN (?, ?, ?)",
                        (project.id, task1.id, task2.id, task3.id))
            conn.commit()

        stats = pm.get_project_stats(project.id)

        assert stats['priority_breakdown'][0] == 1  # P0
        assert stats['priority_breakdown'][1] == 2  # P1

    def test_project_stats_nonexistent(self, pm):
        """Test stats for nonexistent project."""
        stats = pm.get_project_stats(999)

        assert stats is None


class TestProjectStatsWithDB:
    """Test project statistics populate correctly when querying."""

    def test_get_project_includes_stats(self, pm, db):
        """Test that get_project includes task statistics."""
        project = pm.create_project("Test Project")

        # Add some tasks
        task1 = db.add("Task 1")
        task2 = db.add("Task 2")

        with db._get_conn() as conn:
            conn.execute("UPDATE todos SET project_id = ? WHERE id IN (?, ?)",
                        (project.id, task1.id, task2.id))
            conn.commit()

        db.mark_done(task1.id)

        # Get project should include stats
        retrieved = pm.get_project(project.id)

        assert retrieved.total_tasks == 2
        assert retrieved.completed_tasks == 1
        assert retrieved.active_tasks == 1

    def test_list_projects_includes_stats(self, pm, db):
        """Test that list_projects includes task statistics."""
        project = pm.create_project("Test Project")

        # Add some tasks
        task1 = db.add("Task 1")
        task2 = db.add("Task 2")

        with db._get_conn() as conn:
            conn.execute("UPDATE todos SET project_id = ? WHERE id IN (?, ?)",
                        (project.id, task1.id, task2.id))
            conn.commit()

        db.mark_done(task1.id)

        # List projects should include stats
        projects = pm.list_projects()

        assert len(projects) == 1
        assert projects[0].total_tasks == 2
        assert projects[0].completed_tasks == 1
        assert projects[0].active_tasks == 1
