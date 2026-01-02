"""Calendar view for Todo CLI.

Renders a calendar with task counts for each day.
"""

import calendar
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .display import get_console


@dataclass
class CalendarDay:
    """Represents a day in the calendar view."""
    date: date
    task_count: int = 0
    is_today: bool = False
    is_overdue: bool = False
    is_current_month: bool = True


class CalendarView:
    """Renders calendar views with task data."""

    WEEKDAY_NAMES = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    MONTH_NAMES = [
        "", "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    def __init__(self, db):
        """Initialize calendar view.

        Args:
            db: Database instance
        """
        self.db = db

    def get_task_counts_by_date(
        self,
        start_date: date,
        end_date: date,
        include_done: bool = False
    ) -> dict[date, int]:
        """Get task counts grouped by due date.

        Args:
            start_date: Start of date range
            end_date: End of date range
            include_done: Include completed tasks

        Returns:
            Dict mapping dates to task counts
        """
        todos = self.db.list_all(include_done=include_done)
        counts = defaultdict(int)

        for todo in todos:
            if todo.due_date:
                due_date = todo.due_date.date() if isinstance(todo.due_date, datetime) else todo.due_date
                if start_date <= due_date <= end_date:
                    counts[due_date] += 1

        return dict(counts)

    def get_overdue_dates(self) -> set[date]:
        """Get set of dates with overdue tasks.

        Returns:
            Set of dates that have overdue tasks
        """
        todos = self.db.list_all(include_done=False)
        today = date.today()
        overdue_dates = set()

        for todo in todos:
            if todo.due_date:
                due_date = todo.due_date.date() if isinstance(todo.due_date, datetime) else todo.due_date
                if due_date < today:
                    overdue_dates.add(due_date)

        return overdue_dates

    def build_month_calendar(
        self,
        year: int,
        month: int
    ) -> list[list[CalendarDay]]:
        """Build calendar data for a month.

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            List of weeks, each containing 7 CalendarDay objects
        """
        cal = calendar.Calendar(firstweekday=0)  # Monday = 0
        today = date.today()

        # Get date range for the month (including padding days)
        month_days = list(cal.itermonthdates(year, month))
        start_date = month_days[0]
        end_date = month_days[-1]

        # Get task counts and overdue dates
        task_counts = self.get_task_counts_by_date(start_date, end_date)
        overdue_dates = self.get_overdue_dates()

        # Build calendar grid
        weeks = []
        current_week = []

        for day_date in month_days:
            is_current_month = day_date.month == month
            day = CalendarDay(
                date=day_date,
                task_count=task_counts.get(day_date, 0),
                is_today=(day_date == today),
                is_overdue=(day_date in overdue_dates),
                is_current_month=is_current_month,
            )
            current_week.append(day)

            if len(current_week) == 7:
                weeks.append(current_week)
                current_week = []

        if current_week:
            weeks.append(current_week)

        return weeks

    def build_week_calendar(
        self,
        week_start: Optional[date] = None
    ) -> list[CalendarDay]:
        """Build calendar data for a week.

        Args:
            week_start: Start date of week (defaults to current week's Monday)

        Returns:
            List of 7 CalendarDay objects
        """
        today = date.today()

        if week_start is None:
            # Get Monday of current week
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)

        # Get task counts and overdue dates
        task_counts = self.get_task_counts_by_date(week_start, week_end)
        overdue_dates = self.get_overdue_dates()

        # Build week
        days = []
        for i in range(7):
            day_date = week_start + timedelta(days=i)
            day = CalendarDay(
                date=day_date,
                task_count=task_counts.get(day_date, 0),
                is_today=(day_date == today),
                is_overdue=(day_date in overdue_dates),
                is_current_month=True,
            )
            days.append(day)

        return days


def display_month_calendar(
    calendar_data: list[list[CalendarDay]],
    year: int,
    month: int,
    console: Optional[Console] = None,
):
    """Display a month calendar.

    Args:
        calendar_data: List of weeks from build_month_calendar
        year: Year for title
        month: Month for title
        console: Optional Rich console
    """
    if console is None:
        console = get_console()

    month_name = CalendarView.MONTH_NAMES[month]
    title = f"{month_name} {year}"

    # Create table
    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
        box=None,
        padding=(0, 1),
    )

    # Add columns for each day
    for name in CalendarView.WEEKDAY_NAMES:
        table.add_column(name, justify="center", width=6)

    # Add rows for each week
    for week in calendar_data:
        row = []
        for day in week:
            cell = _format_calendar_day(day)
            row.append(cell)
        table.add_row(*row)

    # Add legend
    console.print()
    console.print(table)
    console.print()
    console.print("[dim]Legend: [/dim][bold cyan][TODAY][/bold cyan] = today, "
                  "[bold red][OVERDUE][/bold red] = overdue tasks, "
                  "[dim](n)[/dim] = task count")


def display_week_calendar(
    calendar_data: list[CalendarDay],
    console: Optional[Console] = None,
):
    """Display a week calendar.

    Args:
        calendar_data: List of 7 CalendarDay objects
        console: Optional Rich console
    """
    if console is None:
        console = get_console()

    # Determine week range for title
    start = calendar_data[0].date
    end = calendar_data[-1].date
    title = f"Week of {start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}"

    # Create table
    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
        box=None,
        padding=(0, 2),
    )

    # Add columns for each day
    for day in calendar_data:
        col_name = f"{CalendarView.WEEKDAY_NAMES[day.date.weekday()]}\n{day.date.day}"
        table.add_column(col_name, justify="center", width=8)

    # Add single row with task counts
    row = []
    for day in calendar_data:
        cell = _format_week_day(day)
        row.append(cell)
    table.add_row(*row)

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]Legend: [/dim][bold cyan][TODAY][/bold cyan] = today, "
                  "[bold red][n][/bold red] = overdue, "
                  "[dim](n)[/dim] = task count")


def _format_calendar_day(day: CalendarDay) -> Text:
    """Format a calendar day cell for month view.

    Args:
        day: CalendarDay to format

    Returns:
        Rich Text object
    """
    text = Text()

    # Day number
    day_str = str(day.date.day).rjust(2)

    if not day.is_current_month:
        # Dim days from other months
        text.append(day_str, style="dim")
    elif day.is_today:
        # Highlight today
        text.append(day_str, style="bold cyan reverse")
    elif day.is_overdue:
        # Red for overdue
        text.append(day_str, style="bold red")
    else:
        text.append(day_str)

    # Task count indicator
    if day.task_count > 0 and day.is_current_month:
        count_style = "bold red" if day.is_overdue else "dim"
        text.append(f"\n({day.task_count})", style=count_style)
    else:
        text.append("\n   ")

    return text


def _format_week_day(day: CalendarDay) -> Text:
    """Format a calendar day cell for week view.

    Args:
        day: CalendarDay to format

    Returns:
        Rich Text object
    """
    text = Text()

    if day.task_count > 0:
        if day.is_overdue:
            text.append(f"[{day.task_count}]", style="bold red")
        elif day.is_today:
            text.append(f"[{day.task_count}]", style="bold cyan")
        else:
            text.append(f"({day.task_count})", style="dim")
    else:
        if day.is_today:
            text.append("today", style="bold cyan")
        else:
            text.append("-", style="dim")

    return text


def get_tasks_for_date(db, target_date: date, include_done: bool = False):
    """Get tasks due on a specific date.

    Args:
        db: Database instance
        target_date: Date to get tasks for
        include_done: Include completed tasks

    Returns:
        List of Todo objects due on the target date
    """
    todos = db.list_all(include_done=include_done)
    tasks = []

    for todo in todos:
        if todo.due_date:
            due_date = todo.due_date.date() if isinstance(todo.due_date, datetime) else todo.due_date
            if due_date == target_date:
                tasks.append(todo)

    return tasks
