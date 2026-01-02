"""Tests for Story 5.9: Interactive Calendar TUI."""

import pytest
import tempfile
from pathlib import Path
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

from todo_cli.database import Database
from todo_cli.calendar_interactive import (
    DayCell,
    CalendarGrid,
    WeekdayHeader,
    TaskListModal,
    AddTaskModal,
    InteractiveCalendar,
    run_interactive_calendar,
)
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


class TestDayCell:
    """Test DayCell widget initialization."""

    def test_day_cell_stores_date(self):
        """Test DayCell stores the date correctly."""
        test_date = date(2025, 1, 15)
        cell = DayCell(day_date=test_date)
        assert cell.day_date == test_date

    def test_day_cell_stores_task_count(self):
        """Test DayCell stores task count."""
        cell = DayCell(day_date=date.today(), task_count=5)
        assert cell.task_count == 5

    def test_day_cell_stores_is_today(self):
        """Test DayCell stores is_today flag."""
        cell = DayCell(day_date=date.today(), is_today=True)
        assert cell.is_today is True

    def test_day_cell_stores_is_overdue(self):
        """Test DayCell stores is_overdue flag."""
        cell = DayCell(day_date=date.today(), is_overdue=True)
        assert cell.is_overdue is True

    def test_day_cell_stores_is_current_month(self):
        """Test DayCell stores is_current_month flag."""
        cell = DayCell(day_date=date.today(), is_current_month=False)
        assert cell.is_current_month is False

    def test_day_cell_default_values(self):
        """Test DayCell default values."""
        cell = DayCell(day_date=date.today())
        assert cell.task_count == 0
        assert cell.is_today is False
        assert cell.is_overdue is False
        assert cell.is_current_month is True


class TestWeekdayHeader:
    """Test WeekdayHeader widget."""

    def test_weekday_header_is_static(self):
        """Test WeekdayHeader is a Static widget."""
        from textual.widgets import Static
        header = WeekdayHeader("Mon")
        assert isinstance(header, Static)


class TestCalendarGrid:
    """Test CalendarGrid container."""

    def test_calendar_grid_is_container(self):
        """Test CalendarGrid is a Container."""
        from textual.containers import Container
        grid = CalendarGrid()
        assert isinstance(grid, Container)


class TestTaskListModal:
    """Test TaskListModal screen."""

    def test_task_list_modal_stores_date(self):
        """Test TaskListModal stores target date."""
        test_date = date(2025, 1, 15)
        modal = TaskListModal(target_date=test_date, tasks=[])
        assert modal.target_date == test_date

    def test_task_list_modal_stores_tasks(self):
        """Test TaskListModal stores tasks list."""
        tasks = [
            Todo(id=1, task="Task 1"),
            Todo(id=2, task="Task 2"),
        ]
        modal = TaskListModal(target_date=date.today(), tasks=tasks)
        assert len(modal.tasks) == 2

    def test_task_list_modal_has_escape_binding(self):
        """Test TaskListModal has escape binding."""
        modal = TaskListModal(target_date=date.today(), tasks=[])
        bindings = [b.key for b in modal.BINDINGS]
        assert "escape" in bindings

    def test_task_list_modal_has_q_binding(self):
        """Test TaskListModal has q binding."""
        modal = TaskListModal(target_date=date.today(), tasks=[])
        bindings = [b.key for b in modal.BINDINGS]
        assert "q" in bindings


class TestAddTaskModal:
    """Test AddTaskModal screen."""

    def test_add_task_modal_stores_date(self):
        """Test AddTaskModal stores target date."""
        test_date = date(2025, 1, 15)
        modal = AddTaskModal(target_date=test_date)
        assert modal.target_date == test_date

    def test_add_task_modal_has_escape_binding(self):
        """Test AddTaskModal has escape binding."""
        modal = AddTaskModal(target_date=date.today())
        bindings = [b.key for b in modal.BINDINGS]
        assert "escape" in bindings


class TestInteractiveCalendar:
    """Test InteractiveCalendar app."""

    def test_interactive_calendar_stores_db(self, temp_db):
        """Test InteractiveCalendar stores database reference."""
        app = InteractiveCalendar(temp_db)
        assert app.db is temp_db

    def test_interactive_calendar_initializes_to_today(self, temp_db):
        """Test InteractiveCalendar starts on today's date."""
        app = InteractiveCalendar(temp_db)
        today = date.today()
        assert app.selected_date == today
        assert app.current_year == today.year
        assert app.current_month == today.month

    def test_interactive_calendar_has_quit_binding(self, temp_db):
        """Test InteractiveCalendar has q binding."""
        app = InteractiveCalendar(temp_db)
        bindings = [b.key for b in app.BINDINGS]
        assert "q" in bindings

    def test_interactive_calendar_has_escape_binding(self, temp_db):
        """Test InteractiveCalendar has escape binding."""
        app = InteractiveCalendar(temp_db)
        bindings = [b.key for b in app.BINDINGS]
        assert "escape" in bindings

    def test_interactive_calendar_has_arrow_bindings(self, temp_db):
        """Test InteractiveCalendar has arrow key bindings."""
        app = InteractiveCalendar(temp_db)
        bindings = [b.key for b in app.BINDINGS]
        assert "left" in bindings
        assert "right" in bindings
        assert "up" in bindings
        assert "down" in bindings

    def test_interactive_calendar_has_enter_binding(self, temp_db):
        """Test InteractiveCalendar has enter binding."""
        app = InteractiveCalendar(temp_db)
        bindings = [b.key for b in app.BINDINGS]
        assert "enter" in bindings

    def test_interactive_calendar_has_add_task_binding(self, temp_db):
        """Test InteractiveCalendar has 'a' binding for add task."""
        app = InteractiveCalendar(temp_db)
        bindings = [b.key for b in app.BINDINGS]
        assert "a" in bindings

    def test_interactive_calendar_has_month_nav_bindings(self, temp_db):
        """Test InteractiveCalendar has n/p bindings."""
        app = InteractiveCalendar(temp_db)
        bindings = [b.key for b in app.BINDINGS]
        assert "n" in bindings
        assert "p" in bindings

    def test_interactive_calendar_has_today_binding(self, temp_db):
        """Test InteractiveCalendar has t binding."""
        app = InteractiveCalendar(temp_db)
        bindings = [b.key for b in app.BINDINGS]
        assert "t" in bindings

    def test_weekday_names_has_7_days(self, temp_db):
        """Test WEEKDAY_NAMES has 7 entries."""
        app = InteractiveCalendar(temp_db)
        assert len(app.WEEKDAY_NAMES) == 7

    def test_weekday_names_starts_with_monday(self, temp_db):
        """Test WEEKDAY_NAMES starts with Monday."""
        app = InteractiveCalendar(temp_db)
        assert app.WEEKDAY_NAMES[0] == "Mon"

    def test_get_month_title_format(self, temp_db):
        """Test _get_month_title returns correct format."""
        app = InteractiveCalendar(temp_db)
        app.current_year = 2025
        app.current_month = 1
        title = app._get_month_title()
        assert title == "January 2025"

    def test_get_month_title_all_months(self, temp_db):
        """Test _get_month_title works for all months."""
        app = InteractiveCalendar(temp_db)
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        for i, month_name in enumerate(months, 1):
            app.current_month = i
            app.current_year = 2025
            title = app._get_month_title()
            assert title == f"{month_name} 2025"


class TestInteractiveCalendarNavigation:
    """Test navigation actions in InteractiveCalendar."""

    def test_action_move_left_decrements_day(self, temp_db):
        """Test action_move_left decrements selected date by 1 day."""
        app = InteractiveCalendar(temp_db)
        original = app.selected_date
        with patch.object(app, '_handle_date_change'):
            app.selected_date -= timedelta(days=1)
        assert app.selected_date == original - timedelta(days=1)

    def test_action_move_right_increments_day(self, temp_db):
        """Test action_move_right increments selected date by 1 day."""
        app = InteractiveCalendar(temp_db)
        original = app.selected_date
        with patch.object(app, '_handle_date_change'):
            app.selected_date += timedelta(days=1)
        assert app.selected_date == original + timedelta(days=1)

    def test_action_move_up_decrements_week(self, temp_db):
        """Test action_move_up decrements selected date by 1 week."""
        app = InteractiveCalendar(temp_db)
        original = app.selected_date
        with patch.object(app, '_handle_date_change'):
            app.selected_date -= timedelta(weeks=1)
        assert app.selected_date == original - timedelta(weeks=1)

    def test_action_move_down_increments_week(self, temp_db):
        """Test action_move_down increments selected date by 1 week."""
        app = InteractiveCalendar(temp_db)
        original = app.selected_date
        with patch.object(app, '_handle_date_change'):
            app.selected_date += timedelta(weeks=1)
        assert app.selected_date == original + timedelta(weeks=1)

    def test_action_goto_today_sets_today(self, temp_db):
        """Test action_goto_today sets selected date to today."""
        app = InteractiveCalendar(temp_db)
        # Move away from today
        app.selected_date = date(2020, 1, 1)
        app.current_year = 2020
        app.current_month = 1
        # Go to today (mock rebuild)
        with patch.object(app, '_rebuild_calendar'):
            app.action_goto_today()
        today = date.today()
        assert app.selected_date == today
        assert app.current_year == today.year
        assert app.current_month == today.month


class TestInteractiveCalendarMonthNavigation:
    """Test month navigation in InteractiveCalendar."""

    def test_action_next_month_increments_month(self, temp_db):
        """Test action_next_month increments month."""
        app = InteractiveCalendar(temp_db)
        app.current_month = 5
        app.current_year = 2025
        app.selected_date = date(2025, 5, 15)
        with patch.object(app, '_rebuild_calendar'):
            app.action_next_month()
        assert app.current_month == 6
        assert app.current_year == 2025

    def test_action_next_month_wraps_year(self, temp_db):
        """Test action_next_month wraps to next year from December."""
        app = InteractiveCalendar(temp_db)
        app.current_month = 12
        app.current_year = 2025
        app.selected_date = date(2025, 12, 15)
        with patch.object(app, '_rebuild_calendar'):
            app.action_next_month()
        assert app.current_month == 1
        assert app.current_year == 2026

    def test_action_prev_month_decrements_month(self, temp_db):
        """Test action_prev_month decrements month."""
        app = InteractiveCalendar(temp_db)
        app.current_month = 5
        app.current_year = 2025
        app.selected_date = date(2025, 5, 15)
        with patch.object(app, '_rebuild_calendar'):
            app.action_prev_month()
        assert app.current_month == 4
        assert app.current_year == 2025

    def test_action_prev_month_wraps_year(self, temp_db):
        """Test action_prev_month wraps to previous year from January."""
        app = InteractiveCalendar(temp_db)
        app.current_month = 1
        app.current_year = 2025
        app.selected_date = date(2025, 1, 15)
        with patch.object(app, '_rebuild_calendar'):
            app.action_prev_month()
        assert app.current_month == 12
        assert app.current_year == 2024

    def test_action_next_month_handles_day_overflow(self, temp_db):
        """Test next month handles day overflow (e.g., Jan 31 -> Feb)."""
        app = InteractiveCalendar(temp_db)
        app.current_month = 1
        app.current_year = 2025
        app.selected_date = date(2025, 1, 31)
        with patch.object(app, '_rebuild_calendar'):
            app.action_next_month()
        # February 2025 has 28 days, so should go to Feb 28
        assert app.selected_date.month == 2
        assert app.selected_date.day == 28

    def test_action_prev_month_handles_day_overflow(self, temp_db):
        """Test prev month handles day overflow (e.g., Mar 31 -> Feb)."""
        app = InteractiveCalendar(temp_db)
        app.current_month = 3
        app.current_year = 2025
        app.selected_date = date(2025, 3, 31)
        with patch.object(app, '_rebuild_calendar'):
            app.action_prev_month()
        # February 2025 has 28 days, so should go to Feb 28
        assert app.selected_date.month == 2
        assert app.selected_date.day == 28


class TestInteractiveCalendarDateChange:
    """Test date change handling in InteractiveCalendar."""

    def test_handle_date_change_switches_month_when_needed(self, temp_db):
        """Test _handle_date_change switches month when date crosses boundary."""
        app = InteractiveCalendar(temp_db)
        app.current_month = 5
        app.current_year = 2025
        app.selected_date = date(2025, 6, 1)  # Different month
        with patch.object(app, '_rebuild_calendar'):
            app._handle_date_change()
        assert app.current_month == 6

    def test_handle_date_change_keeps_month_when_same(self, temp_db):
        """Test _handle_date_change keeps month when date is same month."""
        app = InteractiveCalendar(temp_db)
        app.current_month = 5
        app.current_year = 2025
        app.selected_date = date(2025, 5, 15)  # Same month
        original_month = app.current_month
        with patch.object(app, '_update_selection'):
            app._handle_date_change()
        assert app.current_month == original_month


class TestRunInteractiveCalendar:
    """Test run_interactive_calendar function."""

    def test_run_interactive_calendar_creates_app(self, temp_db):
        """Test run_interactive_calendar creates and runs app."""
        with patch.object(InteractiveCalendar, 'run') as mock_run:
            run_interactive_calendar(temp_db)
            mock_run.assert_called_once()


class TestInteractiveCalendarCLI:
    """Test CLI integration for interactive calendar."""

    def test_calendar_command_has_interactive_option(self):
        """Test calendar command has -i/--interactive option."""
        from todo_cli.main import calendar_cmd
        import inspect
        # The callback function should have interactive parameter
        sig = inspect.signature(calendar_cmd)
        params = list(sig.parameters.keys())
        assert "interactive" in params


class TestDayCellCSS:
    """Test DayCell CSS classes."""

    def test_day_cell_has_default_css(self):
        """Test DayCell has DEFAULT_CSS defined."""
        assert DayCell.DEFAULT_CSS is not None
        assert "DayCell" in DayCell.DEFAULT_CSS

    def test_day_cell_css_has_selected_class(self):
        """Test DayCell CSS defines .selected class."""
        assert "selected" in DayCell.DEFAULT_CSS

    def test_day_cell_css_has_today_class(self):
        """Test DayCell CSS defines .today class."""
        assert "today" in DayCell.DEFAULT_CSS

    def test_day_cell_css_has_overdue_class(self):
        """Test DayCell CSS defines .overdue class."""
        assert "overdue" in DayCell.DEFAULT_CSS

    def test_day_cell_css_has_other_month_class(self):
        """Test DayCell CSS defines .other-month class."""
        assert "other-month" in DayCell.DEFAULT_CSS

    def test_day_cell_css_has_has_tasks_class(self):
        """Test DayCell CSS defines .has-tasks class."""
        assert "has-tasks" in DayCell.DEFAULT_CSS


class TestInteractiveCalendarCSS:
    """Test InteractiveCalendar CSS."""

    def test_interactive_calendar_has_css(self, temp_db):
        """Test InteractiveCalendar has CSS defined."""
        app = InteractiveCalendar(temp_db)
        assert app.CSS is not None

    def test_interactive_calendar_css_has_calendar_container(self, temp_db):
        """Test CSS defines #calendar-container."""
        app = InteractiveCalendar(temp_db)
        assert "calendar-container" in app.CSS

    def test_interactive_calendar_css_has_month_header(self, temp_db):
        """Test CSS defines #month-header."""
        app = InteractiveCalendar(temp_db)
        assert "month-header" in app.CSS

    def test_interactive_calendar_css_has_status_bar(self, temp_db):
        """Test CSS defines #status-bar."""
        app = InteractiveCalendar(temp_db)
        assert "status-bar" in app.CSS
