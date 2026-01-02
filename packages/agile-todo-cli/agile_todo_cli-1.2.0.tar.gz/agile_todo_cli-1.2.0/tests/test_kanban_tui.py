"""Tests for KANBAN interactive TUI mode."""

import pytest
import tempfile
from pathlib import Path

from todo_cli.kanban_tui import (
    KanbanApp,
    TaskItem,
    KanbanColumnWidget,
    MoveTaskScreen,
    HelpScreen,
    run_kanban_interactive,
)
from todo_cli.kanban import KanbanManager, KanbanColumn, KanbanTask
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
def km(temp_db):
    """Create a KanbanManager instance."""
    return KanbanManager(temp_db)


@pytest.fixture
def sample_tasks(db):
    """Create sample tasks for testing."""
    tasks = []
    tasks.append(db.add(task="Task 1 - Backlog", priority=Priority.P1))
    tasks.append(db.add(task="Task 2 - Backlog", priority=Priority.P2))
    tasks.append(db.add(task="Task 3 - Backlog", priority=Priority.P0))
    return tasks


class TestTaskItem:
    """Test TaskItem widget."""

    def test_task_item_creation(self):
        """Test TaskItem can be created with a KanbanTask."""
        task = KanbanTask(
            id=1, task="Test task", priority=1, status="todo",
            kanban_column="backlog", project_id=None, project_name=None,
            project_color=None, due_date=None, tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        item = TaskItem(task)
        assert item.kanban_task == task
        assert item.kanban_task.id == 1
        assert item.kanban_task.task == "Test task"

    def test_task_item_with_subtasks(self):
        """Test TaskItem with subtask count."""
        task = KanbanTask(
            id=2, task="Parent task", priority=0, status="todo",
            kanban_column="todo", project_id=None, project_name=None,
            project_color=None, due_date=None, tags="[]",
            subtask_count=3, completed_subtasks=1
        )
        item = TaskItem(task)
        assert item.kanban_task.subtask_count == 3
        assert item.kanban_task.completed_subtasks == 1

    def test_task_item_overdue(self):
        """Test TaskItem with overdue task."""
        task = KanbanTask(
            id=3, task="Overdue task", priority=1, status="todo",
            kanban_column="todo", project_id=None, project_name=None,
            project_color=None, due_date="2020-01-01T00:00:00", tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        item = TaskItem(task)
        assert item.kanban_task.is_overdue is True


class TestKanbanColumnWidget:
    """Test KanbanColumnWidget."""

    def test_column_widget_creation(self):
        """Test KanbanColumnWidget can be created."""
        column = KanbanColumn.BACKLOG
        tasks = [
            KanbanTask(
                id=1, task="Task 1", priority=1, status="todo",
                kanban_column="backlog", project_id=None, project_name=None,
                project_color=None, due_date=None, tags="[]",
                subtask_count=0, completed_subtasks=0
            )
        ]
        widget = KanbanColumnWidget(column, tasks)
        assert widget.column == column
        assert len(widget.tasks) == 1

    def test_column_widget_empty(self):
        """Test KanbanColumnWidget with no tasks."""
        column = KanbanColumn.TODO
        widget = KanbanColumnWidget(column, [])
        assert widget.column == column
        assert len(widget.tasks) == 0


class TestKanbanApp:
    """Test KanbanApp main application."""

    def test_app_creation(self, temp_db):
        """Test KanbanApp can be instantiated."""
        app = KanbanApp(db_path=temp_db)
        assert app.km is not None
        assert app.project_id is None
        assert app.priority is None
        assert app.tags is None

    def test_app_with_filters(self, temp_db):
        """Test KanbanApp with filter parameters."""
        app = KanbanApp(
            db_path=temp_db,
            project_id=1,
            priority=0,
            tags=["urgent", "bug"],
        )
        assert app.project_id == 1
        assert app.priority == 0
        assert app.tags == ["urgent", "bug"]

    def test_app_bindings(self, temp_db):
        """Test that app has expected bindings."""
        app = KanbanApp(db_path=temp_db)

        # Check key bindings exist
        binding_keys = [b.key for b in app.BINDINGS]

        assert "q" in binding_keys
        assert "escape" in binding_keys
        assert "?" in binding_keys
        assert "r" in binding_keys
        assert "d" in binding_keys
        assert "h" in binding_keys
        assert "l" in binding_keys
        assert "j" in binding_keys
        assert "k" in binding_keys
        assert "enter" in binding_keys
        assert "m" in binding_keys

    def test_app_initial_state(self, temp_db):
        """Test app initial reactive state."""
        app = KanbanApp(db_path=temp_db)
        assert app.current_column_idx == 0
        assert app.show_done is False

    def test_app_css(self, temp_db):
        """Test app has CSS defined."""
        app = KanbanApp(db_path=temp_db)
        assert app.CSS is not None
        assert "board-container" in app.CSS


class TestHelpScreen:
    """Test HelpScreen modal."""

    def test_help_screen_bindings(self):
        """Test HelpScreen has expected bindings."""
        screen = HelpScreen()
        binding_keys = [b.key for b in screen.BINDINGS]

        assert "escape" in binding_keys
        assert "q" in binding_keys

    def test_help_screen_css(self):
        """Test HelpScreen has CSS defined."""
        screen = HelpScreen()
        assert screen.DEFAULT_CSS is not None


class TestMoveTaskScreen:
    """Test MoveTaskScreen modal."""

    def test_move_screen_creation(self):
        """Test MoveTaskScreen can be created."""
        task = KanbanTask(
            id=1, task="Test task", priority=1, status="todo",
            kanban_column="backlog", project_id=None, project_name=None,
            project_color=None, due_date=None, tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        screen = MoveTaskScreen(task)
        assert screen.task == task

    def test_move_screen_bindings(self):
        """Test MoveTaskScreen has escape binding."""
        task = KanbanTask(
            id=1, task="Test task", priority=1, status="todo",
            kanban_column="backlog", project_id=None, project_name=None,
            project_color=None, due_date=None, tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        screen = MoveTaskScreen(task)
        binding_keys = [b.key for b in screen.BINDINGS]

        assert "escape" in binding_keys

    def test_move_screen_css(self):
        """Test MoveTaskScreen has CSS defined."""
        task = KanbanTask(
            id=1, task="Test task", priority=1, status="todo",
            kanban_column="backlog", project_id=None, project_name=None,
            project_color=None, due_date=None, tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        screen = MoveTaskScreen(task)
        assert screen.DEFAULT_CSS is not None


class TestRunKanbanInteractive:
    """Test the run_kanban_interactive entry point."""

    def test_function_exists(self):
        """Test that run_kanban_interactive function exists."""
        assert callable(run_kanban_interactive)

    def test_function_signature(self):
        """Test function accepts expected parameters."""
        import inspect
        sig = inspect.signature(run_kanban_interactive)
        params = list(sig.parameters.keys())

        assert "db_path" in params
        assert "project_id" in params
        assert "priority" in params
        assert "tags" in params


class TestKanbanAppIntegrationSync:
    """Synchronous integration tests for KanbanApp with database."""

    def test_kanban_manager_integration(self, temp_db, db, sample_tasks):
        """Test that KanbanApp uses KanbanManager correctly."""
        app = KanbanApp(db_path=temp_db)

        # Get board through the manager
        board = app.km.get_board()

        # Should have the sample tasks
        assert len(board.get("backlog", [])) == 3

    def test_kanban_app_with_priority_filter(self, temp_db, db):
        """Test that priority filter is passed correctly."""
        # Create tasks with different priorities
        db.add(task="P0 task", priority=Priority.P0)
        db.add(task="P1 task", priority=Priority.P1)
        db.add(task="P2 task", priority=Priority.P2)

        app = KanbanApp(db_path=temp_db, priority=0)

        # Priority should be set
        assert app.priority == 0

    def test_kanban_app_with_project_filter(self, temp_db, db):
        """Test that project filter is passed correctly."""
        app = KanbanApp(db_path=temp_db, project_id=123)
        assert app.project_id == 123

    def test_kanban_app_with_tag_filter(self, temp_db, db):
        """Test that tag filter is passed correctly."""
        app = KanbanApp(db_path=temp_db, tags=["urgent", "bug"])
        assert app.tags == ["urgent", "bug"]


class TestKanbanColumnWidgetIntegration:
    """Integration tests for KanbanColumnWidget."""

    def test_column_widget_with_many_tasks(self):
        """Test column widget with many tasks."""
        column = KanbanColumn.BACKLOG
        tasks = [
            KanbanTask(
                id=i, task=f"Task {i}", priority=i % 4, status="todo",
                kanban_column="backlog", project_id=None, project_name=None,
                project_color=None, due_date=None, tags="[]",
                subtask_count=0, completed_subtasks=0
            )
            for i in range(50)
        ]
        widget = KanbanColumnWidget(column, tasks)
        assert len(widget.tasks) == 50

    def test_column_widget_refresh(self):
        """Test column widget can refresh tasks."""
        column = KanbanColumn.TODO
        initial_tasks = [
            KanbanTask(
                id=1, task="Task 1", priority=1, status="todo",
                kanban_column="todo", project_id=None, project_name=None,
                project_color=None, due_date=None, tags="[]",
                subtask_count=0, completed_subtasks=0
            )
        ]
        widget = KanbanColumnWidget(column, initial_tasks)
        assert len(widget.tasks) == 1

        # Note: refresh_tasks can't be tested without mounting


class TestKanbanTask:
    """Test KanbanTask dataclass used by TUI."""

    def test_kanban_task_priority_icons(self):
        """Test priority icons for all priorities."""
        icons = {
            0: "🔴",
            1: "🟡",
            2: "🔵",
            3: "⚪",
        }
        for priority, expected_icon in icons.items():
            task = KanbanTask(
                id=1, task="Test", priority=priority, status="todo",
                kanban_column="backlog", project_id=None, project_name=None,
                project_color=None, due_date=None, tags="[]",
                subtask_count=0, completed_subtasks=0
            )
            assert task.priority_icon == expected_icon

    def test_kanban_task_with_project(self):
        """Test KanbanTask with project info."""
        task = KanbanTask(
            id=1, task="Project task", priority=1, status="todo",
            kanban_column="backlog", project_id=5, project_name="My Project",
            project_color="blue", due_date=None, tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        assert task.project_id == 5
        assert task.project_name == "My Project"
        assert task.project_color == "blue"


class TestCLIIntegration:
    """Test CLI integration with kanban TUI."""

    def test_cli_command_imports(self):
        """Test that CLI can import the TUI function."""
        from todo_cli.main import kanban
        assert callable(kanban)

    def test_cli_has_interactive_option(self):
        """Test that kanban command has --interactive option."""
        from todo_cli.main import kanban
        import inspect

        # Check by importing the function and verifying signature
        sig = inspect.signature(kanban)
        param_names = list(sig.parameters.keys())

        assert "interactive" in param_names


class TestKanbanAppPerformance:
    """Performance tests for KanbanApp initialization."""

    def test_app_init_performance(self, temp_db, km):
        """Test app initializes quickly even with many tasks."""
        import time

        # Create 100 tasks
        with km._get_conn() as conn:
            for i in range(100):
                conn.execute(
                    "INSERT INTO todos (task, priority, status, kanban_column, created_at, tags) VALUES (?, ?, ?, ?, datetime('now'), '[]')",
                    (f"Task {i}", 2, "todo", "backlog")
                )
            conn.commit()

        start = time.time()
        app = KanbanApp(db_path=temp_db)
        elapsed = time.time() - start

        # App should initialize in under 100ms
        assert elapsed < 0.1, f"App init took {elapsed*1000:.0f}ms (>100ms)"

    def test_board_retrieval_performance(self, temp_db, km):
        """Test board retrieval is fast with many tasks."""
        import time

        # Create 500 tasks
        with km._get_conn() as conn:
            for i in range(500):
                conn.execute(
                    "INSERT INTO todos (task, priority, status, kanban_column, created_at, tags) VALUES (?, ?, ?, ?, datetime('now'), '[]')",
                    (f"Task {i}", i % 4, "todo", ["backlog", "todo", "in-progress", "review"][i % 4])
                )
            conn.commit()

        app = KanbanApp(db_path=temp_db)

        start = time.time()
        board = app.km.get_board()
        elapsed = time.time() - start

        # Should complete in under 200ms
        assert elapsed < 0.2, f"Board retrieval took {elapsed*1000:.0f}ms (>200ms)"

        # Verify tasks distributed across columns
        total = sum(len(tasks) for tasks in board.values())
        assert total == 500
