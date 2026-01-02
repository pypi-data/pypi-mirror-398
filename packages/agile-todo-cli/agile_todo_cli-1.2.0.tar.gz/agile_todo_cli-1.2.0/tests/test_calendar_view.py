"""Tests for Story 5.8: Calendar View."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, date, timedelta
from io import StringIO
from unittest.mock import patch

from todo_cli.database import Database
from todo_cli.calendar_view import (
    CalendarView,
    CalendarDay,
    display_month_calendar,
    display_week_calendar,
    get_tasks_for_date,
    _format_calendar_day,
    _format_week_day,
)
from todo_cli.models import Priority


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
def calendar_view(temp_db):
    """Create a CalendarView instance."""
    return CalendarView(temp_db)


class TestCalendarDay:
    """Test CalendarDay dataclass."""

    def test_default_values(self):
        """Test CalendarDay default values."""
        day = CalendarDay(date=date(2025, 12, 25))
        assert day.date == date(2025, 12, 25)
        assert day.task_count == 0
        assert day.is_today is False
        assert day.is_overdue is False
        assert day.is_current_month is True

    def test_custom_values(self):
        """Test CalendarDay with custom values."""
        day = CalendarDay(
            date=date(2025, 12, 25),
            task_count=5,
            is_today=True,
            is_overdue=False,
            is_current_month=True,
        )
        assert day.task_count == 5
        assert day.is_today is True


class TestCalendarViewTaskCounts:
    """Test CalendarView.get_task_counts_by_date."""

    def test_no_tasks(self, calendar_view):
        """Test with no tasks in range."""
        start = date(2025, 12, 1)
        end = date(2025, 12, 31)
        counts = calendar_view.get_task_counts_by_date(start, end)
        assert counts == {}

    def test_tasks_in_range(self, temp_db, calendar_view):
        """Test with tasks in date range."""
        # Add tasks with due dates
        temp_db.add(task="Task 1", due_date=datetime(2025, 12, 15))
        temp_db.add(task="Task 2", due_date=datetime(2025, 12, 15))
        temp_db.add(task="Task 3", due_date=datetime(2025, 12, 20))

        start = date(2025, 12, 1)
        end = date(2025, 12, 31)
        counts = calendar_view.get_task_counts_by_date(start, end)

        assert counts[date(2025, 12, 15)] == 2
        assert counts[date(2025, 12, 20)] == 1

    def test_tasks_outside_range(self, temp_db, calendar_view):
        """Test tasks outside range are not counted."""
        temp_db.add(task="Task 1", due_date=datetime(2025, 11, 30))
        temp_db.add(task="Task 2", due_date=datetime(2026, 1, 1))

        start = date(2025, 12, 1)
        end = date(2025, 12, 31)
        counts = calendar_view.get_task_counts_by_date(start, end)

        assert counts == {}

    def test_excludes_done_by_default(self, temp_db, calendar_view):
        """Test done tasks are excluded by default."""
        task = temp_db.add(task="Done task", due_date=datetime(2025, 12, 15))
        temp_db.mark_done(task.id)

        start = date(2025, 12, 1)
        end = date(2025, 12, 31)
        counts = calendar_view.get_task_counts_by_date(start, end)

        assert counts == {}

    def test_include_done(self, temp_db, calendar_view):
        """Test including done tasks."""
        task = temp_db.add(task="Done task", due_date=datetime(2025, 12, 15))
        temp_db.mark_done(task.id)

        start = date(2025, 12, 1)
        end = date(2025, 12, 31)
        counts = calendar_view.get_task_counts_by_date(start, end, include_done=True)

        assert counts[date(2025, 12, 15)] == 1


class TestCalendarViewOverdueDates:
    """Test CalendarView.get_overdue_dates."""

    def test_no_overdue(self, calendar_view):
        """Test with no overdue tasks."""
        overdue = calendar_view.get_overdue_dates()
        assert overdue == set()

    def test_overdue_tasks(self, temp_db, calendar_view):
        """Test with overdue tasks."""
        past_date = datetime.now() - timedelta(days=5)
        temp_db.add(task="Overdue 1", due_date=past_date)
        temp_db.add(task="Overdue 2", due_date=past_date - timedelta(days=2))

        overdue = calendar_view.get_overdue_dates()

        assert past_date.date() in overdue
        assert (past_date - timedelta(days=2)).date() in overdue

    def test_future_not_overdue(self, temp_db, calendar_view):
        """Test future tasks are not overdue."""
        future_date = datetime.now() + timedelta(days=5)
        temp_db.add(task="Future task", due_date=future_date)

        overdue = calendar_view.get_overdue_dates()

        assert future_date.date() not in overdue

    def test_done_not_overdue(self, temp_db, calendar_view):
        """Test done tasks are not counted as overdue."""
        past_date = datetime.now() - timedelta(days=5)
        task = temp_db.add(task="Done overdue", due_date=past_date)
        temp_db.mark_done(task.id)

        overdue = calendar_view.get_overdue_dates()

        assert past_date.date() not in overdue


class TestBuildMonthCalendar:
    """Test CalendarView.build_month_calendar."""

    def test_returns_weeks(self, calendar_view):
        """Test returns list of weeks."""
        weeks = calendar_view.build_month_calendar(2025, 12)
        assert isinstance(weeks, list)
        assert all(isinstance(week, list) for week in weeks)
        assert all(len(week) == 7 for week in weeks)

    def test_all_days_are_calendar_days(self, calendar_view):
        """Test all items are CalendarDay objects."""
        weeks = calendar_view.build_month_calendar(2025, 12)
        for week in weeks:
            for day in week:
                assert isinstance(day, CalendarDay)

    def test_marks_current_month(self, calendar_view):
        """Test current month days are marked."""
        weeks = calendar_view.build_month_calendar(2025, 12)
        december_days = [
            day for week in weeks for day in week
            if day.date.month == 12
        ]
        for day in december_days:
            assert day.is_current_month is True

    def test_marks_other_months(self, calendar_view):
        """Test other month days are marked."""
        weeks = calendar_view.build_month_calendar(2025, 12)
        other_days = [
            day for week in weeks for day in week
            if day.date.month != 12
        ]
        for day in other_days:
            assert day.is_current_month is False

    def test_marks_today(self, calendar_view):
        """Test today is marked."""
        today = date.today()
        weeks = calendar_view.build_month_calendar(today.year, today.month)

        today_days = [
            day for week in weeks for day in week
            if day.date == today
        ]
        assert len(today_days) == 1
        assert today_days[0].is_today is True

    def test_includes_task_counts(self, temp_db, calendar_view):
        """Test task counts are included."""
        temp_db.add(task="Task 1", due_date=datetime(2025, 12, 15))
        temp_db.add(task="Task 2", due_date=datetime(2025, 12, 15))

        weeks = calendar_view.build_month_calendar(2025, 12)

        dec_15_days = [
            day for week in weeks for day in week
            if day.date == date(2025, 12, 15)
        ]
        assert len(dec_15_days) == 1
        assert dec_15_days[0].task_count == 2


class TestBuildWeekCalendar:
    """Test CalendarView.build_week_calendar."""

    def test_returns_seven_days(self, calendar_view):
        """Test returns exactly 7 days."""
        days = calendar_view.build_week_calendar()
        assert len(days) == 7

    def test_all_days_are_calendar_days(self, calendar_view):
        """Test all items are CalendarDay objects."""
        days = calendar_view.build_week_calendar()
        for day in days:
            assert isinstance(day, CalendarDay)

    def test_starts_on_monday(self, calendar_view):
        """Test week starts on Monday."""
        days = calendar_view.build_week_calendar()
        assert days[0].date.weekday() == 0  # Monday

    def test_ends_on_sunday(self, calendar_view):
        """Test week ends on Sunday."""
        days = calendar_view.build_week_calendar()
        assert days[6].date.weekday() == 6  # Sunday

    def test_custom_week_start(self, calendar_view):
        """Test custom week start date."""
        week_start = date(2025, 12, 15)  # Monday
        days = calendar_view.build_week_calendar(week_start)

        assert days[0].date == week_start
        assert days[6].date == date(2025, 12, 21)

    def test_marks_today(self, calendar_view):
        """Test today is marked in week view."""
        today = date.today()
        # Get the Monday of this week
        monday = today - timedelta(days=today.weekday())
        days = calendar_view.build_week_calendar(monday)

        today_days = [day for day in days if day.date == today]
        assert len(today_days) == 1
        assert today_days[0].is_today is True

    def test_includes_task_counts(self, temp_db, calendar_view):
        """Test task counts in week view."""
        # Add task for a specific date
        target_date = date.today() + timedelta(days=1)
        temp_db.add(task="Task", due_date=datetime.combine(target_date, datetime.min.time()))

        monday = date.today() - timedelta(days=date.today().weekday())
        days = calendar_view.build_week_calendar(monday)

        target_days = [day for day in days if day.date == target_date]
        if target_days:  # Only if target is in this week
            assert target_days[0].task_count == 1


class TestFormatCalendarDay:
    """Test _format_calendar_day function."""

    def test_regular_day(self):
        """Test formatting regular day."""
        day = CalendarDay(date=date(2025, 12, 15))
        result = _format_calendar_day(day)
        assert "15" in result.plain

    def test_today_styling(self):
        """Test today has special styling."""
        day = CalendarDay(date=date.today(), is_today=True)
        result = _format_calendar_day(day)
        assert "bold cyan reverse" in result.style or result._spans

    def test_overdue_styling(self):
        """Test overdue day has red styling."""
        day = CalendarDay(date=date(2025, 12, 15), is_overdue=True, is_current_month=True)
        result = _format_calendar_day(day)
        # Check for red styling in spans
        assert any("red" in str(span) for span in result._spans) or "red" in str(result)

    def test_other_month_dim(self):
        """Test other month days are dim."""
        day = CalendarDay(date=date(2025, 11, 30), is_current_month=False)
        result = _format_calendar_day(day)
        assert any("dim" in str(span) for span in result._spans)

    def test_shows_task_count(self):
        """Test shows task count."""
        day = CalendarDay(date=date(2025, 12, 15), task_count=3, is_current_month=True)
        result = _format_calendar_day(day)
        assert "(3)" in result.plain


class TestFormatWeekDay:
    """Test _format_week_day function."""

    def test_no_tasks(self):
        """Test day with no tasks."""
        day = CalendarDay(date=date(2025, 12, 15))
        result = _format_week_day(day)
        assert "-" in result.plain or "today" in result.plain.lower()

    def test_with_tasks(self):
        """Test day with tasks."""
        day = CalendarDay(date=date(2025, 12, 15), task_count=3)
        result = _format_week_day(day)
        assert "3" in result.plain

    def test_today_no_tasks(self):
        """Test today with no tasks shows 'today'."""
        day = CalendarDay(date=date.today(), is_today=True, task_count=0)
        result = _format_week_day(day)
        assert "today" in result.plain.lower()

    def test_overdue_styling(self):
        """Test overdue tasks have red styling."""
        day = CalendarDay(date=date(2025, 12, 15), task_count=2, is_overdue=True)
        result = _format_week_day(day)
        assert any("red" in str(span) for span in result._spans)


class TestGetTasksForDate:
    """Test get_tasks_for_date function."""

    def test_no_tasks(self, temp_db):
        """Test with no tasks for date."""
        tasks = get_tasks_for_date(temp_db, date(2025, 12, 15))
        assert tasks == []

    def test_tasks_on_date(self, temp_db):
        """Test getting tasks for specific date."""
        temp_db.add(task="Task 1", due_date=datetime(2025, 12, 15, 10, 0))
        temp_db.add(task="Task 2", due_date=datetime(2025, 12, 15, 14, 0))
        temp_db.add(task="Other", due_date=datetime(2025, 12, 16))

        tasks = get_tasks_for_date(temp_db, date(2025, 12, 15))

        assert len(tasks) == 2
        assert all(t.task in ["Task 1", "Task 2"] for t in tasks)

    def test_excludes_done_by_default(self, temp_db):
        """Test done tasks excluded by default."""
        task = temp_db.add(task="Done", due_date=datetime(2025, 12, 15))
        temp_db.mark_done(task.id)

        tasks = get_tasks_for_date(temp_db, date(2025, 12, 15))

        assert tasks == []

    def test_include_done(self, temp_db):
        """Test including done tasks."""
        task = temp_db.add(task="Done", due_date=datetime(2025, 12, 15))
        temp_db.mark_done(task.id)

        tasks = get_tasks_for_date(temp_db, date(2025, 12, 15), include_done=True)

        assert len(tasks) == 1


class TestDisplayMonthCalendar:
    """Test display_month_calendar function."""

    def test_displays_month_name(self, calendar_view):
        """Test displays month name in title."""
        weeks = calendar_view.build_month_calendar(2025, 12)

        with patch('todo_cli.calendar_view.get_console') as mock_console:
            output = StringIO()
            from rich.console import Console
            mock_console.return_value = Console(file=output, width=120, force_terminal=True)
            display_month_calendar(weeks, 2025, 12)

        output_text = output.getvalue()
        assert "December" in output_text
        assert "2025" in output_text

    def test_displays_weekday_headers(self, calendar_view):
        """Test displays weekday headers."""
        weeks = calendar_view.build_month_calendar(2025, 12)

        with patch('todo_cli.calendar_view.get_console') as mock_console:
            output = StringIO()
            from rich.console import Console
            mock_console.return_value = Console(file=output, width=120, force_terminal=True)
            display_month_calendar(weeks, 2025, 12)

        output_text = output.getvalue()
        assert "Mo" in output_text
        assert "Su" in output_text

    def test_displays_legend(self, calendar_view):
        """Test displays legend."""
        weeks = calendar_view.build_month_calendar(2025, 12)

        with patch('todo_cli.calendar_view.get_console') as mock_console:
            output = StringIO()
            from rich.console import Console
            mock_console.return_value = Console(file=output, width=120, force_terminal=True)
            display_month_calendar(weeks, 2025, 12)

        output_text = output.getvalue()
        assert "Legend" in output_text


class TestDisplayWeekCalendar:
    """Test display_week_calendar function."""

    def test_displays_week_range(self, calendar_view):
        """Test displays week date range."""
        days = calendar_view.build_week_calendar(date(2025, 12, 15))

        with patch('todo_cli.calendar_view.get_console') as mock_console:
            output = StringIO()
            from rich.console import Console
            mock_console.return_value = Console(file=output, width=120, force_terminal=True)
            display_week_calendar(days)

        output_text = output.getvalue()
        assert "Week of" in output_text
        assert "Dec" in output_text

    def test_displays_legend(self, calendar_view):
        """Test displays legend."""
        days = calendar_view.build_week_calendar()

        with patch('todo_cli.calendar_view.get_console') as mock_console:
            output = StringIO()
            from rich.console import Console
            mock_console.return_value = Console(file=output, width=120, force_terminal=True)
            display_week_calendar(days)

        output_text = output.getvalue()
        assert "Legend" in output_text


class TestCalendarConstants:
    """Test CalendarView class constants."""

    def test_weekday_names(self):
        """Test weekday names are correct."""
        assert CalendarView.WEEKDAY_NAMES == ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

    def test_month_names(self):
        """Test month names are correct."""
        assert CalendarView.MONTH_NAMES[1] == "January"
        assert CalendarView.MONTH_NAMES[12] == "December"
        assert CalendarView.MONTH_NAMES[0] == ""  # Index 0 is empty
