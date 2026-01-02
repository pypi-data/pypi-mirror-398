"""Tests for Cycle Management & Reporting (Epic 4)."""

import json
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from todo_cli.cycles import CycleManager, CycleStatus, Cycle, CycleTask
from todo_cli.database import Database
from todo_cli.projects import ProjectManager
from todo_cli.models import Priority


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
def db(temp_db):
    """Create a Database instance."""
    return Database(temp_db)


@pytest.fixture
def cm(temp_db):
    """Create a CycleManager instance."""
    return CycleManager(temp_db)


@pytest.fixture
def pm(temp_db):
    """Create a ProjectManager instance."""
    return ProjectManager(temp_db)


@pytest.fixture
def sample_tasks(db):
    """Create sample tasks for testing."""
    tasks = []
    tasks.append(db.add(task="Task 1", priority=Priority.P0))
    tasks.append(db.add(task="Task 2", priority=Priority.P1))
    tasks.append(db.add(task="Task 3", priority=Priority.P2))
    tasks.append(db.add(task="Task 4", priority=Priority.P2))
    tasks.append(db.add(task="Task 5", priority=Priority.P3))
    return tasks


class TestCycleStatus:
    """Test CycleStatus enum."""

    def test_status_values(self):
        """Test status values."""
        assert CycleStatus.ACTIVE.value == "active"
        assert CycleStatus.CLOSED.value == "closed"


class TestCycleDataclass:
    """Test Cycle dataclass properties."""

    def test_cycle_days_remaining_active(self):
        """Test days_remaining for active cycle."""
        now = datetime.now()
        cycle = Cycle(
            id=1,
            name="Test Cycle",
            start_date=now - timedelta(days=7),
            end_date=now + timedelta(days=7),
            status=CycleStatus.ACTIVE,
            created_at=now - timedelta(days=7),
            completed_at=None,
        )
        # Should have approximately 7 days remaining
        assert 6 <= cycle.days_remaining <= 8

    def test_cycle_days_remaining_closed(self):
        """Test days_remaining for closed cycle."""
        now = datetime.now()
        cycle = Cycle(
            id=1,
            name="Test Cycle",
            start_date=now - timedelta(days=14),
            end_date=now - timedelta(days=7),
            status=CycleStatus.CLOSED,
            created_at=now - timedelta(days=14),
            completed_at=now - timedelta(days=7),
        )
        assert cycle.days_remaining == 0

    def test_cycle_is_active(self):
        """Test is_active property."""
        now = datetime.now()
        active_cycle = Cycle(
            id=1,
            name="Active",
            start_date=now,
            end_date=now + timedelta(days=14),
            status=CycleStatus.ACTIVE,
            created_at=now,
            completed_at=None,
        )
        closed_cycle = Cycle(
            id=2,
            name="Closed",
            start_date=now - timedelta(days=14),
            end_date=now,
            status=CycleStatus.CLOSED,
            created_at=now - timedelta(days=14),
            completed_at=now,
        )
        assert active_cycle.is_active is True
        assert closed_cycle.is_active is False

    def test_cycle_time_progress(self):
        """Test progress_percentage property."""
        now = datetime.now()
        # Cycle that's halfway through
        cycle = Cycle(
            id=1,
            name="Test",
            start_date=now - timedelta(days=7),
            end_date=now + timedelta(days=7),
            status=CycleStatus.ACTIVE,
            created_at=now - timedelta(days=7),
            completed_at=None,
        )
        # Should be around 50%
        assert 45 <= cycle.progress_percentage <= 55

    def test_cycle_duration_weeks(self):
        """Test duration_weeks computed property."""
        now = datetime.now()
        cycle = Cycle(
            id=1,
            name="Test",
            start_date=now,
            end_date=now + timedelta(days=14),
            status=CycleStatus.ACTIVE,
            created_at=now,
        )
        assert cycle.duration_weeks == 2


class TestCycleManagerCreate:
    """Test CycleManager.create_cycle method."""

    def test_create_cycle_success(self, cm):
        """Test successful cycle creation."""
        success, result = cm.create_cycle("Sprint 1", duration_weeks=2)

        assert success is True
        assert isinstance(result, Cycle)
        assert result.name == "Sprint 1"
        assert result.duration_weeks == 2
        assert result.status == CycleStatus.ACTIVE

    def test_create_cycle_one_week(self, cm):
        """Test 1-week cycle creation."""
        success, result = cm.create_cycle("Quick Sprint", duration_weeks=1)

        assert success is True
        delta = result.end_date - result.start_date
        assert delta.days == 7

    def test_create_cycle_four_weeks(self, cm):
        """Test 4-week cycle creation."""
        success, result = cm.create_cycle("Long Sprint", duration_weeks=4)

        assert success is True
        delta = result.end_date - result.start_date
        assert delta.days == 28

    def test_create_cycle_invalid_duration(self, cm):
        """Test cycle creation with invalid duration."""
        success, result = cm.create_cycle("Bad Sprint", duration_weeks=3)

        assert success is False
        assert "invalid" in result.lower()

    def test_create_cycle_duplicate_active(self, cm):
        """Test creating cycle when one is already active."""
        cm.create_cycle("Sprint 1")
        success, result = cm.create_cycle("Sprint 2")

        assert success is False
        assert "active cycle" in result.lower()

    def test_create_cycle_custom_start_date(self, cm):
        """Test cycle creation with custom start date."""
        start = datetime(2025, 1, 1)
        success, result = cm.create_cycle("Q1 Sprint", start_date=start)

        assert success is True
        assert result.start_date.date() == start.date()


class TestCycleManagerGet:
    """Test CycleManager get methods."""

    def test_get_cycle_exists(self, cm):
        """Test getting existing cycle."""
        _, created = cm.create_cycle("Test Cycle")
        cycle = cm.get_cycle(created.id)

        assert cycle is not None
        assert cycle.name == "Test Cycle"

    def test_get_cycle_not_found(self, cm):
        """Test getting nonexistent cycle."""
        cycle = cm.get_cycle(99999)
        assert cycle is None

    def test_get_cycle_by_name(self, cm):
        """Test getting cycle by name."""
        cm.create_cycle("My Sprint")
        cycle = cm.get_cycle_by_name("My Sprint")

        assert cycle is not None
        assert cycle.name == "My Sprint"

    def test_get_cycle_by_name_not_found(self, cm):
        """Test getting nonexistent cycle by name."""
        cycle = cm.get_cycle_by_name("Nonexistent")
        assert cycle is None

    def test_get_active_cycle(self, cm):
        """Test getting active cycle."""
        cm.create_cycle("Active Sprint")
        cycle = cm.get_active_cycle()

        assert cycle is not None
        assert cycle.status == CycleStatus.ACTIVE

    def test_get_active_cycle_none(self, cm):
        """Test getting active cycle when none exists."""
        cycle = cm.get_active_cycle()
        assert cycle is None


class TestCycleManagerList:
    """Test CycleManager.list_cycles method."""

    def test_list_cycles_empty(self, cm):
        """Test listing when no cycles exist."""
        cycles = cm.list_cycles()
        assert cycles == []

    def test_list_cycles_multiple(self, cm):
        """Test listing multiple cycles with include_closed."""
        _, c1 = cm.create_cycle("Sprint 1")
        cm.close_cycle(c1.id)
        _, c2 = cm.create_cycle("Sprint 2")
        cm.close_cycle(c2.id)
        _, c3 = cm.create_cycle("Sprint 3")

        # Without include_closed, only active cycles
        active_only = cm.list_cycles()
        assert len(active_only) == 1

        # With include_closed, all cycles
        all_cycles = cm.list_cycles(include_closed=True)
        assert len(all_cycles) == 3

    def test_list_cycles_include_closed(self, cm):
        """Test include_closed parameter."""
        _, c1 = cm.create_cycle("Sprint 1")
        cm.close_cycle(c1.id)
        cm.create_cycle("Sprint 2")

        # Default: only active
        active = cm.list_cycles()
        assert len(active) == 1
        assert active[0].status == CycleStatus.ACTIVE

        # With include_closed
        all_cycles = cm.list_cycles(include_closed=True)
        assert len(all_cycles) == 2


class TestCycleManagerTaskAssignment:
    """Test task assignment methods."""

    def test_assign_task_success(self, cm, sample_tasks):
        """Test successful task assignment."""
        _, cycle = cm.create_cycle("Sprint 1")
        task = sample_tasks[0]

        success, message = cm.assign_task(cycle.id, task.id)

        assert success is True
        assert f"#{task.id}" in message

    def test_assign_task_invalid_cycle(self, cm, sample_tasks):
        """Test assigning to invalid cycle."""
        task = sample_tasks[0]

        success, message = cm.assign_task(99999, task.id)

        assert success is False
        assert "not found" in message.lower()

    def test_assign_task_invalid_task(self, cm):
        """Test assigning invalid task."""
        _, cycle = cm.create_cycle("Sprint 1")

        success, message = cm.assign_task(cycle.id, 99999)

        assert success is False
        assert "not found" in message.lower()

    def test_assign_task_duplicate(self, cm, sample_tasks):
        """Test assigning same task twice."""
        _, cycle = cm.create_cycle("Sprint 1")
        task = sample_tasks[0]

        cm.assign_task(cycle.id, task.id)
        success, message = cm.assign_task(cycle.id, task.id)

        assert success is False
        assert "already" in message.lower()

    def test_unassign_task_success(self, cm, sample_tasks):
        """Test successful task unassignment."""
        _, cycle = cm.create_cycle("Sprint 1")
        task = sample_tasks[0]
        cm.assign_task(cycle.id, task.id)

        success, message = cm.unassign_task(cycle.id, task.id)

        assert success is True
        assert f"#{task.id}" in message

    def test_unassign_task_not_assigned(self, cm, sample_tasks):
        """Test unassigning task that's not assigned."""
        _, cycle = cm.create_cycle("Sprint 1")
        task = sample_tasks[0]

        success, message = cm.unassign_task(cycle.id, task.id)

        assert success is False
        assert "not assigned" in message.lower()


class TestCycleManagerGetTasks:
    """Test CycleManager.get_cycle_tasks method."""

    def test_get_cycle_tasks_empty(self, cm):
        """Test getting tasks from empty cycle."""
        _, cycle = cm.create_cycle("Sprint 1")
        tasks = cm.get_cycle_tasks(cycle.id)

        assert tasks == []

    def test_get_cycle_tasks_multiple(self, cm, sample_tasks):
        """Test getting multiple tasks."""
        _, cycle = cm.create_cycle("Sprint 1")
        for task in sample_tasks[:3]:
            cm.assign_task(cycle.id, task.id)

        tasks = cm.get_cycle_tasks(cycle.id)

        assert len(tasks) == 3
        assert all(isinstance(t, CycleTask) for t in tasks)

    def test_get_cycle_tasks_fields(self, cm, sample_tasks):
        """Test CycleTask field values."""
        _, cycle = cm.create_cycle("Sprint 1")
        original = sample_tasks[0]
        cm.assign_task(cycle.id, original.id)

        tasks = cm.get_cycle_tasks(cycle.id)

        assert len(tasks) == 1
        task = tasks[0]
        assert task.task_id == original.id
        assert task.task_name == original.task
        assert task.priority == original.priority.value

    def test_get_cycle_tasks_with_project(self, cm, db, pm):
        """Test tasks with project info."""
        project = pm.create_project("Test Project")
        task = db.add(task="Project Task", priority=Priority.P1, project_id=project.id)
        _, cycle = cm.create_cycle("Sprint 1")
        cm.assign_task(cycle.id, task.id)

        tasks = cm.get_cycle_tasks(cycle.id)

        assert len(tasks) == 1
        assert tasks[0].project_name == "Test Project"


class TestCycleManagerProgress:
    """Test CycleManager.get_cycle_progress method."""

    def test_progress_empty_cycle(self, cm):
        """Test progress for empty cycle."""
        _, cycle = cm.create_cycle("Sprint 1")
        progress = cm.get_cycle_progress(cycle.id)

        assert progress["total_tasks"] == 0
        assert progress["completed_tasks"] == 0
        assert progress["completion_percentage"] == 0.0

    def test_progress_with_tasks(self, cm, db, sample_tasks):
        """Test progress with assigned tasks."""
        _, cycle = cm.create_cycle("Sprint 1")
        for task in sample_tasks[:4]:
            cm.assign_task(cycle.id, task.id)

        # Mark some as done
        db.mark_done(sample_tasks[0].id)
        db.mark_done(sample_tasks[1].id)

        progress = cm.get_cycle_progress(cycle.id)

        assert progress["total_tasks"] == 4
        assert progress["completed_tasks"] == 2
        assert progress["completion_percentage"] == 50.0

    def test_progress_velocity(self, cm, db, sample_tasks):
        """Test velocity calculation."""
        _, cycle = cm.create_cycle("Sprint 1")
        for task in sample_tasks:
            cm.assign_task(cycle.id, task.id)

        # Mark all as done
        for task in sample_tasks:
            db.mark_done(task.id)

        progress = cm.get_cycle_progress(cycle.id)

        assert progress["velocity"] >= 0

    def test_progress_projected_completion(self, cm, sample_tasks):
        """Test projected completion field."""
        _, cycle = cm.create_cycle("Sprint 1")
        for task in sample_tasks:
            cm.assign_task(cycle.id, task.id)

        progress = cm.get_cycle_progress(cycle.id)

        assert "projected_completion" in progress

    def test_progress_default_active_cycle(self, cm, sample_tasks):
        """Test progress defaults to active cycle."""
        _, cycle = cm.create_cycle("Sprint 1")
        cm.assign_task(cycle.id, sample_tasks[0].id)

        progress = cm.get_cycle_progress()  # No cycle_id

        assert progress["total_tasks"] == 1


class TestCycleManagerClose:
    """Test CycleManager.close_cycle method."""

    def test_close_cycle_success(self, cm, sample_tasks):
        """Test successful cycle closing."""
        _, cycle = cm.create_cycle("Sprint 1")
        for task in sample_tasks:
            cm.assign_task(cycle.id, task.id)

        success, result = cm.close_cycle(cycle.id)

        assert success is True
        assert "closed" in result.lower()

        # Verify cycle is closed
        updated = cm.get_cycle(cycle.id)
        assert updated.status == CycleStatus.CLOSED

    def test_close_cycle_already_closed(self, cm):
        """Test closing already closed cycle."""
        _, cycle = cm.create_cycle("Sprint 1")
        cm.close_cycle(cycle.id)

        success, result = cm.close_cycle(cycle.id)

        assert success is False
        assert "already closed" in result.lower()

    def test_close_cycle_not_found(self, cm):
        """Test closing nonexistent cycle."""
        success, result = cm.close_cycle(99999)

        assert success is False
        assert "not found" in result.lower()

    def test_close_cycle_with_rollover(self, cm, db, sample_tasks):
        """Test closing with rollover to new cycle."""
        _, cycle = cm.create_cycle("Sprint 1")
        for task in sample_tasks[:3]:
            cm.assign_task(cycle.id, task.id)

        # Complete one task, leave others incomplete
        db.mark_done(sample_tasks[0].id)

        success, result = cm.close_cycle(
            cycle.id,
            rollover=True,
            new_cycle_name="Sprint 2",
            new_cycle_duration=2
        )

        assert success is True
        assert isinstance(result, dict)
        assert result["rolled_tasks"] == 2
        assert result["completed_count"] == 1

        # Verify new cycle was created with rolled tasks
        new_cycle = result["new_cycle"]
        new_tasks = cm.get_cycle_tasks(new_cycle.id)
        assert len(new_tasks) == 2

    def test_close_cycle_rollover_default_name(self, cm, sample_tasks):
        """Test rollover with default naming."""
        _, cycle = cm.create_cycle("Sprint 1")
        cm.assign_task(cycle.id, sample_tasks[0].id)

        success, result = cm.close_cycle(cycle.id, rollover=True)

        assert success is True
        new_cycle = result["new_cycle"]
        assert "continued" in new_cycle.name.lower()


class TestCycleManagerReports:
    """Test cycle reporting methods."""

    def test_generate_report_markdown(self, cm, sample_tasks):
        """Test Markdown report generation."""
        _, cycle = cm.create_cycle("Sprint 1")
        for task in sample_tasks[:3]:
            cm.assign_task(cycle.id, task.id)

        report = cm.generate_report_markdown(cycle.id)

        assert isinstance(report, str)
        assert "Sprint 1" in report
        assert "## Overview" in report
        assert "## Progress" in report
        assert "## Tasks" in report

    def test_generate_report_markdown_no_cycle(self, cm):
        """Test Markdown report when no cycle exists."""
        report = cm.generate_report_markdown()

        assert "No Cycle Data" in report or "No active cycle" in report

    def test_export_json(self, cm, sample_tasks):
        """Test JSON export."""
        _, cycle = cm.create_cycle("Sprint 1")
        for task in sample_tasks[:2]:
            cm.assign_task(cycle.id, task.id)

        json_str = cm.export_json(cycle.id)

        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert "cycle" in data
        assert "progress" in data
        assert "tasks" in data
        assert data["cycle"]["name"] == "Sprint 1"
        assert len(data["tasks"]) == 2

    def test_export_json_no_cycle(self, cm):
        """Test JSON export when no cycle exists."""
        json_str = cm.export_json()

        data = json.loads(json_str)
        assert "error" in data

    def test_export_json_fields(self, cm, sample_tasks):
        """Test JSON export field structure."""
        _, cycle = cm.create_cycle("Sprint 1")
        cm.assign_task(cycle.id, sample_tasks[0].id)

        data = json.loads(cm.export_json(cycle.id))

        # Check cycle fields
        assert "id" in data["cycle"]
        assert "name" in data["cycle"]
        assert "status" in data["cycle"]
        assert "start_date" in data["cycle"]
        assert "end_date" in data["cycle"]

        # Check progress fields
        assert "completion_percentage" in data["progress"]
        assert "velocity" in data["progress"]
        assert "projected_completion" in data["progress"]

        # Check task fields
        assert len(data["tasks"]) == 1
        task = data["tasks"][0]
        assert "id" in task
        assert "task" in task
        assert "status" in task


class TestCyclePerformance:
    """Test cycle performance requirements."""

    def test_list_cycles_100_entries(self, cm):
        """Test listing 100 cycles under 100ms."""
        import time

        # Create 100 cycles
        for i in range(100):
            _, c = cm.create_cycle(f"Sprint {i}")
            cm.close_cycle(c.id)

        start = time.time()
        cycles = cm.list_cycles(include_closed=True)
        elapsed = time.time() - start

        assert len(cycles) == 100
        assert elapsed < 0.1, f"100 cycles took {elapsed*1000:.0f}ms (>100ms)"

    def test_get_cycle_tasks_50_tasks(self, cm, db):
        """Test getting 50 tasks under 50ms."""
        import time

        _, cycle = cm.create_cycle("Sprint 1")

        # Create and assign 50 tasks
        for i in range(50):
            task = db.add(task=f"Task {i}", priority=Priority.P2)
            cm.assign_task(cycle.id, task.id)

        start = time.time()
        tasks = cm.get_cycle_tasks(cycle.id)
        elapsed = time.time() - start

        assert len(tasks) == 50
        assert elapsed < 0.05, f"50 tasks took {elapsed*1000:.0f}ms (>50ms)"

    def test_get_cycle_progress_performance(self, cm, db):
        """Test progress calculation under 50ms."""
        import time

        _, cycle = cm.create_cycle("Sprint 1")

        # Create and assign 100 tasks
        for i in range(100):
            task = db.add(task=f"Task {i}", priority=Priority.P2)
            cm.assign_task(cycle.id, task.id)
            if i % 2 == 0:
                db.mark_done(task.id)

        start = time.time()
        progress = cm.get_cycle_progress(cycle.id)
        elapsed = time.time() - start

        assert progress["total_tasks"] == 100
        assert elapsed < 0.05, f"Progress calc took {elapsed*1000:.0f}ms (>50ms)"
