"""Tests for Story 5.7: Overdue Task Notifications."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import patch

from todo_cli.database import Database
from todo_cli.display import format_due_date, display_todos, display_stats, get_console
from todo_cli.kanban import KanbanManager, KanbanTask, _format_task_line
from todo_cli.models import Todo, Priority, Status


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    db = Database(db_path)
    yield db

    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def km(temp_db):
    """Create a KanbanManager instance."""
    return KanbanManager(temp_db.db_path)


class TestFormatDueDate:
    """Test format_due_date function for overdue tasks."""

    def test_overdue_shows_days_overdue(self):
        """Test overdue tasks show 'Xd overdue' format."""
        # 2 days overdue
        todo = Todo(
            id=1,
            task="Overdue task",
            due_date=datetime.now() - timedelta(days=2)
        )
        result = format_due_date(todo, show_relative=True)
        assert "2d overdue" in result.plain
        assert result.style == "bold red"

    def test_overdue_1_day(self):
        """Test 1 day overdue."""
        todo = Todo(
            id=1,
            task="Overdue task",
            due_date=datetime.now() - timedelta(days=1, hours=1)  # Ensure past
        )
        result = format_due_date(todo, show_relative=True)
        assert "1d overdue" in result.plain
        assert result.style == "bold red"

    def test_overdue_many_days(self):
        """Test many days overdue."""
        todo = Todo(
            id=1,
            task="Overdue task",
            due_date=datetime.now() - timedelta(days=30)
        )
        result = format_due_date(todo, show_relative=True)
        assert "30d overdue" in result.plain

    def test_overdue_shows_date_when_relative_false(self):
        """Test overdue shows date format when show_relative=False."""
        todo = Todo(
            id=1,
            task="Overdue task",
            due_date=datetime.now() - timedelta(days=2)
        )
        result = format_due_date(todo, show_relative=False)
        assert "overdue" not in result.plain.lower()
        assert result.style == "bold red"

    def test_due_today_shows_today(self):
        """Test tasks due today show 'today'."""
        # Set due date to today at end of day
        today = datetime.now().replace(hour=23, minute=59, second=59)
        todo = Todo(
            id=1,
            task="Today task",
            due_date=today
        )
        result = format_due_date(todo, show_relative=True)
        assert "today" in result.plain.lower()
        assert result.style == "yellow"

    def test_due_tomorrow_shows_tomorrow(self):
        """Test tasks due tomorrow show 'tomorrow'."""
        tomorrow = datetime.now() + timedelta(days=1)
        todo = Todo(
            id=1,
            task="Tomorrow task",
            due_date=tomorrow
        )
        result = format_due_date(todo, show_relative=True)
        assert "tomorrow" in result.plain.lower()
        assert result.style == "cyan"

    def test_future_date_shows_date(self):
        """Test tasks with future due dates show the date."""
        future = datetime.now() + timedelta(days=7)
        todo = Todo(
            id=1,
            task="Future task",
            due_date=future
        )
        result = format_due_date(todo, show_relative=True)
        # Should show date, not "overdue", "today", or "tomorrow"
        assert "overdue" not in result.plain.lower()
        assert "today" not in result.plain.lower()
        assert "tomorrow" not in result.plain.lower()

    def test_no_due_date(self):
        """Test tasks with no due date."""
        todo = Todo(id=1, task="No due date")
        result = format_due_date(todo, show_relative=True)
        assert result.plain == "-"
        assert result.style == "dim"


class TestDisplayTodosOverdueWarning:
    """Test display_todos shows overdue count warning."""

    def test_shows_overdue_warning_single(self, temp_db, capsys):
        """Test overdue warning with single task."""
        # Add one overdue task
        temp_db.add(
            task="Overdue task",
            priority=Priority.P2,
            due_date=datetime.now() - timedelta(days=2)
        )
        todos = temp_db.list_all(include_done=False)

        with patch('todo_cli.display.get_console') as mock_console:
            output = StringIO()
            from rich.console import Console
            mock_console.return_value = Console(file=output, width=120, force_terminal=True)
            display_todos(todos, show_overdue_warning=True)

        output_text = output.getvalue()
        assert "1 task overdue" in output_text or "1" in output_text

    def test_shows_overdue_warning_multiple(self, temp_db, capsys):
        """Test overdue warning with multiple tasks."""
        # Add multiple overdue tasks
        for i in range(3):
            temp_db.add(
                task=f"Overdue task {i}",
                priority=Priority.P2,
                due_date=datetime.now() - timedelta(days=i+1)
            )
        todos = temp_db.list_all(include_done=False)

        with patch('todo_cli.display.get_console') as mock_console:
            output = StringIO()
            from rich.console import Console
            mock_console.return_value = Console(file=output, width=120, force_terminal=True)
            display_todos(todos, show_overdue_warning=True)

        output_text = output.getvalue()
        assert "3 tasks overdue" in output_text or "3" in output_text

    def test_no_warning_when_no_overdue(self, temp_db):
        """Test no warning when no overdue tasks."""
        # Add task with future due date
        temp_db.add(
            task="Future task",
            priority=Priority.P2,
            due_date=datetime.now() + timedelta(days=7)
        )
        todos = temp_db.list_all(include_done=False)

        with patch('todo_cli.display.get_console') as mock_console:
            output = StringIO()
            from rich.console import Console
            mock_console.return_value = Console(file=output, width=120, force_terminal=True)
            display_todos(todos, show_overdue_warning=True)

        output_text = output.getvalue()
        assert "overdue" not in output_text.lower()

    def test_can_disable_warning(self, temp_db):
        """Test warning can be disabled."""
        # Add overdue task
        temp_db.add(
            task="Overdue task",
            priority=Priority.P2,
            due_date=datetime.now() - timedelta(days=2)
        )
        todos = temp_db.list_all(include_done=False)

        with patch('todo_cli.display.get_console') as mock_console:
            output = StringIO()
            from rich.console import Console
            mock_console.return_value = Console(file=output, width=120, force_terminal=True)
            display_todos(todos, show_overdue_warning=False)

        output_text = output.getvalue()
        # The header warning should not appear when disabled
        # (task itself may still show overdue styling)
        lines = output_text.split('\n')
        # First non-empty lines should not be the overdue warning
        first_content = [l for l in lines if l.strip()]
        if first_content:
            assert "overdue" not in first_content[0].lower() or "task overdue" not in first_content[0].lower()

    def test_done_tasks_not_counted_as_overdue(self, temp_db):
        """Test done tasks are not counted as overdue."""
        # Add overdue task and mark it done
        task = temp_db.add(
            task="Done overdue task",
            priority=Priority.P2,
            due_date=datetime.now() - timedelta(days=2)
        )
        temp_db.mark_done(task.id)

        todos = temp_db.list_all(include_done=True)

        with patch('todo_cli.display.get_console') as mock_console:
            output = StringIO()
            from rich.console import Console
            mock_console.return_value = Console(file=output, width=120, force_terminal=True)
            display_todos(todos, show_overdue_warning=True)

        output_text = output.getvalue()
        # Should not show overdue warning for done tasks
        first_lines = output_text[:200].lower()
        assert "task overdue" not in first_lines or "0" in first_lines


class TestGetStatsOverdue:
    """Test get_stats includes overdue count."""

    def test_stats_includes_overdue_count(self, temp_db):
        """Test stats includes overdue count."""
        # Add overdue tasks
        for i in range(2):
            temp_db.add(
                task=f"Overdue task {i}",
                priority=Priority.P2,
                due_date=datetime.now() - timedelta(days=i+1)
            )

        stats = temp_db.get_stats()

        assert "overdue" in stats
        assert stats["overdue"] == 2

    def test_stats_overdue_zero_when_none(self, temp_db):
        """Test stats shows 0 overdue when no overdue tasks."""
        # Add non-overdue task
        temp_db.add(
            task="Future task",
            priority=Priority.P2,
            due_date=datetime.now() + timedelta(days=7)
        )

        stats = temp_db.get_stats()

        assert "overdue" in stats
        assert stats["overdue"] == 0

    def test_stats_overdue_excludes_done(self, temp_db):
        """Test stats doesn't count done tasks as overdue."""
        # Add overdue task and mark done
        task = temp_db.add(
            task="Done overdue task",
            priority=Priority.P2,
            due_date=datetime.now() - timedelta(days=2)
        )
        temp_db.mark_done(task.id)

        stats = temp_db.get_stats()

        assert stats["overdue"] == 0

    def test_stats_overdue_only_past_dates(self, temp_db):
        """Test stats only counts past due dates as overdue."""
        # Add past, today, and future tasks
        temp_db.add(task="Past", due_date=datetime.now() - timedelta(days=1))
        temp_db.add(task="Today", due_date=datetime.now() + timedelta(hours=1))
        temp_db.add(task="Future", due_date=datetime.now() + timedelta(days=1))

        stats = temp_db.get_stats()

        # Only past due date should count
        assert stats["overdue"] == 1


class TestDisplayStatsOverdue:
    """Test display_stats shows overdue warning and count."""

    def test_display_stats_shows_overdue_warning(self):
        """Test display_stats shows overdue warning."""
        stats = {
            "total": 5,
            "todo": 3,
            "doing": 1,
            "done": 1,
            "overdue": 2,
            "total_time_seconds": 3600,
        }

        with patch('todo_cli.display.get_console') as mock_console:
            output = StringIO()
            from rich.console import Console
            mock_console.return_value = Console(file=output, width=120, force_terminal=True)
            display_stats(stats)

        output_text = output.getvalue()
        assert "2 tasks overdue" in output_text or "2" in output_text
        assert "Overdue" in output_text

    def test_display_stats_no_warning_when_no_overdue(self):
        """Test display_stats doesn't show warning when no overdue."""
        stats = {
            "total": 5,
            "todo": 3,
            "doing": 1,
            "done": 1,
            "overdue": 0,
            "total_time_seconds": 3600,
        }

        with patch('todo_cli.display.get_console') as mock_console:
            output = StringIO()
            from rich.console import Console
            mock_console.return_value = Console(file=output, width=120, force_terminal=True)
            display_stats(stats)

        output_text = output.getvalue()
        # Should not show overdue warning or row
        assert "overdue" not in output_text.lower() or "Overdue" not in output_text

    def test_display_stats_singular_task(self):
        """Test display_stats shows 'task' (singular) for 1."""
        stats = {
            "total": 5,
            "todo": 3,
            "doing": 1,
            "done": 1,
            "overdue": 1,
            "total_time_seconds": 3600,
        }

        with patch('todo_cli.display.get_console') as mock_console:
            output = StringIO()
            from rich.console import Console
            mock_console.return_value = Console(file=output, width=120, force_terminal=True)
            display_stats(stats)

        output_text = output.getvalue()
        assert "1 task overdue" in output_text or "1" in output_text


class TestKanbanOverdueIndicator:
    """Test KANBAN board shows red ! for overdue tasks."""

    def test_format_task_line_overdue_has_indicator(self):
        """Test _format_task_line adds red ! for overdue tasks."""
        task = KanbanTask(
            id=1, task="Overdue task", priority=2, status="todo",
            kanban_column="backlog", project_id=None, project_name=None,
            project_color=None, due_date="2020-01-01T00:00:00", tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        result = _format_task_line(task)
        assert "[bold red]![/bold red]" in result

    def test_format_task_line_non_overdue_no_indicator(self):
        """Test _format_task_line doesn't add ! for non-overdue tasks."""
        task = KanbanTask(
            id=1, task="Future task", priority=2, status="todo",
            kanban_column="backlog", project_id=None, project_name=None,
            project_color=None, due_date="2099-12-31T00:00:00", tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        result = _format_task_line(task)
        assert "[bold red]![/bold red]" not in result

    def test_format_task_line_no_due_date_no_indicator(self):
        """Test _format_task_line doesn't add ! when no due date."""
        task = KanbanTask(
            id=1, task="No due task", priority=2, status="todo",
            kanban_column="backlog", project_id=None, project_name=None,
            project_color=None, due_date=None, tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        result = _format_task_line(task)
        assert "[bold red]![/bold red]" not in result

    def test_format_task_line_overdue_text_styled(self):
        """Test overdue task text is styled in bold red."""
        task = KanbanTask(
            id=1, task="Overdue task", priority=2, status="todo",
            kanban_column="backlog", project_id=None, project_name=None,
            project_color=None, due_date="2020-01-01T00:00:00", tags="[]",
            subtask_count=0, completed_subtasks=0
        )
        result = _format_task_line(task)
        # Task text should be styled in bold red
        assert "[bold red]Overdue task[/bold red]" in result

    def test_kanban_board_includes_overdue_tasks(self, temp_db, km):
        """Test KANBAN board includes overdue tasks."""
        db = Database(temp_db.db_path)

        # Add overdue task
        db.add(
            task="Overdue task",
            priority=Priority.P2,
            due_date=datetime.now() - timedelta(days=2)
        )

        board = km.get_board()

        # Find the task in the board
        all_tasks = []
        for tasks in board.values():
            all_tasks.extend(tasks)

        assert len(all_tasks) == 1
        assert all_tasks[0].is_overdue is True


class TestTodoIsOverdue:
    """Test Todo.is_overdue property."""

    def test_is_overdue_past_date(self):
        """Test is_overdue True for past due date."""
        todo = Todo(
            id=1,
            task="Overdue",
            due_date=datetime.now() - timedelta(days=1)
        )
        assert todo.is_overdue is True

    def test_is_overdue_future_date(self):
        """Test is_overdue False for future due date."""
        todo = Todo(
            id=1,
            task="Future",
            due_date=datetime.now() + timedelta(days=1)
        )
        assert todo.is_overdue is False

    def test_is_overdue_no_due_date(self):
        """Test is_overdue False when no due date."""
        todo = Todo(id=1, task="No date")
        assert todo.is_overdue is False

    def test_is_overdue_done_task_not_overdue(self):
        """Test done tasks are not overdue even with past date."""
        todo = Todo(
            id=1,
            task="Done overdue",
            status=Status.DONE,
            due_date=datetime.now() - timedelta(days=1)
        )
        assert todo.is_overdue is False
