"""Tests for KANBAN board functionality."""

import pytest
import tempfile
from pathlib import Path

from todo_cli.kanban import KanbanManager, KanbanColumn, KanbanTask
from todo_cli.database import Database
from todo_cli.projects import ProjectManager
from todo_cli.models import Priority, Status


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
def km(temp_db):
    """Create a KanbanManager instance."""
    return KanbanManager(temp_db)


@pytest.fixture
def pm(temp_db):
    """Create a ProjectManager instance."""
    return ProjectManager(temp_db)


@pytest.fixture
def sample_tasks(db):
    """Create sample tasks for testing."""
    tasks = []
    tasks.append(db.add(task="Backlog task 1", priority=Priority.P2))
    tasks.append(db.add(task="Backlog task 2", priority=Priority.P1))
    tasks.append(db.add(task="Todo task", priority=Priority.P0))
    tasks.append(db.add(task="In progress task", priority=Priority.P1))
    tasks.append(db.add(task="Review task", priority=Priority.P2))
    return tasks


class TestKanbanColumn:
    """Test KanbanColumn enum."""

    def test_from_string_valid(self):
        """Test valid column names."""
        assert KanbanColumn.from_string("backlog") == KanbanColumn.BACKLOG
        assert KanbanColumn.from_string("todo") == KanbanColumn.TODO
        assert KanbanColumn.from_string("in-progress") == KanbanColumn.IN_PROGRESS
        assert KanbanColumn.from_string("review") == KanbanColumn.REVIEW
        assert KanbanColumn.from_string("done") == KanbanColumn.DONE

    def test_from_string_aliases(self):
        """Test column name aliases."""
        assert KanbanColumn.from_string("doing") == KanbanColumn.IN_PROGRESS
        assert KanbanColumn.from_string("inprogress") == KanbanColumn.IN_PROGRESS
        assert KanbanColumn.from_string("in_progress") == KanbanColumn.IN_PROGRESS
        assert KanbanColumn.from_string("progress") == KanbanColumn.IN_PROGRESS
        assert KanbanColumn.from_string("complete") == KanbanColumn.DONE
        assert KanbanColumn.from_string("completed") == KanbanColumn.DONE

    def test_from_string_case_insensitive(self):
        """Test case insensitivity."""
        assert KanbanColumn.from_string("BACKLOG") == KanbanColumn.BACKLOG
        assert KanbanColumn.from_string("Todo") == KanbanColumn.TODO
        assert KanbanColumn.from_string("IN-PROGRESS") == KanbanColumn.IN_PROGRESS

    def test_from_string_invalid(self):
        """Test invalid column names."""
        assert KanbanColumn.from_string("invalid") is None
        assert KanbanColumn.from_string("") is None
        assert KanbanColumn.from_string("xyz") is None

    def test_display_name(self):
        """Test display names."""
        assert KanbanColumn.BACKLOG.display_name == "Backlog"
        assert KanbanColumn.TODO.display_name == "Todo"
        assert KanbanColumn.IN_PROGRESS.display_name == "In Progress"
        assert KanbanColumn.REVIEW.display_name == "Review"
        assert KanbanColumn.DONE.display_name == "Done"

    def test_color(self):
        """Test column colors."""
        assert KanbanColumn.BACKLOG.color == "dim"
        assert KanbanColumn.TODO.color == "blue"
        assert KanbanColumn.IN_PROGRESS.color == "yellow"
        assert KanbanColumn.REVIEW.color == "magenta"
        assert KanbanColumn.DONE.color == "green"


class TestKanbanManagerGetBoard:
    """Test KanbanManager.get_board method."""

    def test_get_board_empty(self, km):
        """Test getting empty board."""
        board = km.get_board()

        assert "backlog" in board
        assert "todo" in board
        assert "in-progress" in board
        assert "review" in board
        assert "done" not in board  # Hidden by default

    def test_get_board_with_tasks(self, km, sample_tasks):
        """Test getting board with tasks."""
        board = km.get_board()

        # All tasks should be in backlog initially (default column)
        assert len(board["backlog"]) == 5

    def test_get_board_include_done(self, km, db, sample_tasks):
        """Test including done column."""
        # Mark one task as done
        db.mark_done(sample_tasks[0].id)

        board = km.get_board(include_done=True)

        assert "done" in board

    def test_get_board_exclude_done(self, km, db, sample_tasks):
        """Test excluding done column (default)."""
        db.mark_done(sample_tasks[0].id)

        board = km.get_board(include_done=False)

        assert "done" not in board


class TestKanbanManagerMoveTask:
    """Test KanbanManager.move_task method."""

    def test_move_task_success(self, km, db):
        """Test successfully moving a task."""
        task = db.add(task="Test task", priority=Priority.P2)

        success, message = km.move_task(task.id, "todo")

        assert success is True
        assert f"#{task.id}" in message
        assert "todo" in message

    def test_move_task_to_in_progress(self, km, db):
        """Test moving to in-progress updates status."""
        task = db.add(task="Test task", priority=Priority.P2)

        km.move_task(task.id, "in-progress")

        # Verify column changed
        column = km.get_task_column(task.id)
        assert column == "in-progress"

        # Verify status changed to doing
        updated = db.get(task.id)
        assert updated.status == Status.DOING

    def test_move_task_to_done_auto_completes(self, km, db):
        """Test moving to done automatically completes the task."""
        task = db.add(task="Test task", priority=Priority.P2)

        success, message = km.move_task(task.id, "done")

        assert success is True
        assert "auto-completed" in message.lower()

        # Verify task is done
        updated = db.get(task.id)
        assert updated.status == Status.DONE
        assert updated.completed_at is not None

    def test_move_task_invalid_column(self, km, db):
        """Test moving to invalid column fails."""
        task = db.add(task="Test task", priority=Priority.P2)

        success, message = km.move_task(task.id, "invalid")

        assert success is False
        assert "invalid column" in message.lower()

    def test_move_task_not_found(self, km):
        """Test moving nonexistent task fails."""
        success, message = km.move_task(99999, "todo")

        assert success is False
        assert "not found" in message.lower()

    def test_move_task_using_alias(self, km, db):
        """Test moving using column alias."""
        task = db.add(task="Test task", priority=Priority.P2)

        success, message = km.move_task(task.id, "doing")

        assert success is True
        column = km.get_task_column(task.id)
        assert column == "in-progress"


class TestKanbanManagerFiltering:
    """Test KANBAN board filtering."""

    def test_filter_by_project(self, km, db, pm):
        """Test filtering by project."""
        # Create project and tasks
        project = pm.create_project("Test Project")
        task1 = db.add(task="Project task", priority=Priority.P2, project_id=project.id)
        task2 = db.add(task="No project task", priority=Priority.P2)

        board = km.get_board(project_id=project.id)

        # Only project task should be included
        all_tasks = []
        for tasks in board.values():
            all_tasks.extend(tasks)

        assert len(all_tasks) == 1
        assert all_tasks[0].id == task1.id

    def test_filter_by_priority(self, km, db):
        """Test filtering by priority."""
        task_p0 = db.add(task="P0 task", priority=Priority.P0)
        task_p2 = db.add(task="P2 task", priority=Priority.P2)

        board = km.get_board(priority=0)

        all_tasks = []
        for tasks in board.values():
            all_tasks.extend(tasks)

        assert len(all_tasks) == 1
        assert all_tasks[0].id == task_p0.id

    def test_filter_by_tags(self, km, db):
        """Test filtering by tags."""
        task1 = db.add(task="Tagged task", priority=Priority.P2, tags=["urgent"])
        task2 = db.add(task="Untagged task", priority=Priority.P2)

        board = km.get_board(tags=["urgent"])

        all_tasks = []
        for tasks in board.values():
            all_tasks.extend(tasks)

        assert len(all_tasks) == 1
        assert all_tasks[0].id == task1.id

    def test_filter_multiple_tags(self, km, db):
        """Test filtering by multiple tags (OR logic)."""
        task1 = db.add(task="Task 1", priority=Priority.P2, tags=["urgent"])
        task2 = db.add(task="Task 2", priority=Priority.P2, tags=["bug"])
        task3 = db.add(task="Task 3", priority=Priority.P2, tags=["other"])

        board = km.get_board(tags=["urgent", "bug"])

        all_tasks = []
        for tasks in board.values():
            all_tasks.extend(tasks)

        assert len(all_tasks) == 2
        task_ids = {t.id for t in all_tasks}
        assert task1.id in task_ids
        assert task2.id in task_ids


class TestKanbanManagerColumnCounts:
    """Test column count functionality."""

    def test_get_column_counts_empty(self, km):
        """Test column counts with no tasks."""
        counts = km.get_column_counts()

        assert counts["backlog"] == 0
        assert counts["todo"] == 0
        assert counts["in-progress"] == 0
        assert counts["review"] == 0

    def test_get_column_counts_with_tasks(self, km, db):
        """Test column counts with tasks."""
        # Add tasks to different columns
        task1 = db.add(task="Task 1", priority=Priority.P2)
        task2 = db.add(task="Task 2", priority=Priority.P2)
        task3 = db.add(task="Task 3", priority=Priority.P2)

        km.move_task(task1.id, "todo")
        km.move_task(task2.id, "in-progress")
        # task3 stays in backlog

        counts = km.get_column_counts()

        assert counts["backlog"] == 1
        assert counts["todo"] == 1
        assert counts["in-progress"] == 1
        assert counts["review"] == 0


class TestKanbanTask:
    """Test KanbanTask dataclass."""

    def test_priority_icon(self):
        """Test priority icons."""
        task = KanbanTask(
            id=1, task="Test", priority=0, status="todo",
            kanban_column="backlog", project_id=None, project_name=None,
            project_color=None, due_date=None, tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        assert task.priority_icon == "🔴"

        task.priority = 1
        assert task.priority_icon == "🟡"

        task.priority = 2
        assert task.priority_icon == "🔵"

        task.priority = 3
        assert task.priority_icon == "⚪"

    def test_is_overdue_no_date(self):
        """Test is_overdue with no due date."""
        task = KanbanTask(
            id=1, task="Test", priority=2, status="todo",
            kanban_column="backlog", project_id=None, project_name=None,
            project_color=None, due_date=None, tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        assert task.is_overdue is False

    def test_is_overdue_past_date(self):
        """Test is_overdue with past due date."""
        task = KanbanTask(
            id=1, task="Test", priority=2, status="todo",
            kanban_column="backlog", project_id=None, project_name=None,
            project_color=None, due_date="2020-01-01T00:00:00", tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        assert task.is_overdue is True

    def test_is_overdue_future_date(self):
        """Test is_overdue with future due date."""
        task = KanbanTask(
            id=1, task="Test", priority=2, status="todo",
            kanban_column="backlog", project_id=None, project_name=None,
            project_color=None, due_date="2099-12-31T00:00:00", tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        assert task.is_overdue is False


class TestKanbanPerformance:
    """Test KANBAN performance requirements."""

    def test_get_board_100_tasks(self, km, db):
        """Test board retrieval with 100 tasks under 100ms."""
        import time

        # Create 100 tasks
        for i in range(100):
            db.add(task=f"Task {i}", priority=Priority.P2)

        start = time.time()
        board = km.get_board()
        elapsed = time.time() - start

        # Should complete in under 100ms
        assert elapsed < 0.1, f"100 tasks took {elapsed*1000:.0f}ms (>100ms)"

        # Verify all tasks retrieved
        total = sum(len(tasks) for tasks in board.values())
        assert total == 100

    def test_get_board_1000_tasks(self, km, db):
        """Test board retrieval with 1000 tasks under 500ms."""
        import time

        # Create 1000 tasks in batches for efficiency
        with km._get_conn() as conn:
            for i in range(1000):
                conn.execute(
                    "INSERT INTO todos (task, priority, status, kanban_column, created_at, tags) VALUES (?, ?, ?, ?, datetime('now'), '[]')",
                    (f"Task {i}", 2, "todo", "backlog")
                )
            conn.commit()

        start = time.time()
        board = km.get_board()
        elapsed = time.time() - start

        # Should complete in under 500ms
        assert elapsed < 0.5, f"1000 tasks took {elapsed*1000:.0f}ms (>500ms)"

        # Verify all tasks retrieved
        total = sum(len(tasks) for tasks in board.values())
        assert total == 1000

    def test_move_task_performance(self, km, db):
        """Test task movement under 50ms."""
        import time

        task = db.add(task="Test task", priority=Priority.P2)

        start = time.time()
        km.move_task(task.id, "in-progress")
        elapsed = time.time() - start

        # Should complete in under 50ms
        assert elapsed < 0.05, f"Move took {elapsed*1000:.0f}ms (>50ms)"


class TestKanbanWithSubtasks:
    """Test KANBAN with subtask integration."""

    def test_board_shows_subtask_count(self, km, db, temp_db):
        """Test that board includes subtask counts."""
        from todo_cli.subtasks import SubtaskManager
        sm = SubtaskManager(temp_db)

        # Create parent and children
        parent = db.add(task="Parent task", priority=Priority.P1)
        child1 = db.add(task="Child 1", priority=Priority.P2)
        child2 = db.add(task="Child 2", priority=Priority.P2)

        sm.add_subtask(parent.id, child1.id)
        sm.add_subtask(parent.id, child2.id)

        board = km.get_board()

        # Find parent task in board
        parent_task = None
        for tasks in board.values():
            for task in tasks:
                if task.id == parent.id:
                    parent_task = task
                    break

        assert parent_task is not None
        assert parent_task.subtask_count == 2
        assert parent_task.completed_subtasks == 0

    def test_board_shows_completed_subtasks(self, km, db, temp_db):
        """Test that board shows completed subtask count."""
        from todo_cli.subtasks import SubtaskManager
        sm = SubtaskManager(temp_db)

        # Create parent and children
        parent = db.add(task="Parent task", priority=Priority.P1)
        child1 = db.add(task="Child 1", priority=Priority.P2)
        child2 = db.add(task="Child 2", priority=Priority.P2)

        sm.add_subtask(parent.id, child1.id)
        sm.add_subtask(parent.id, child2.id)

        # Complete one child
        db.mark_done(child1.id)

        board = km.get_board()

        # Find parent task in board
        parent_task = None
        for tasks in board.values():
            for task in tasks:
                if task.id == parent.id:
                    parent_task = task
                    break

        assert parent_task is not None
        assert parent_task.subtask_count == 2
        assert parent_task.completed_subtasks == 1
