"""Time tracking reports for Todo CLI."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .database import Database
from .models import Todo, Status


console = Console()


def format_duration(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_week_range(date: datetime) -> tuple[datetime, datetime]:
    """Get start and end of the week for a given date."""
    start = date - timedelta(days=date.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return start, end


def daily_report(db: Database, date: Optional[datetime] = None):
    """Generate daily time tracking report."""
    if date is None:
        date = datetime.now()

    day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Get all todos that have time tracking
    all_todos = db.list_all(include_done=True)

    # Filter to todos completed today or with time spent
    daily_todos = []
    for todo in all_todos:
        if todo.time_spent.total_seconds() > 0:
            # Include if completed today
            if todo.completed_at and day_start <= todo.completed_at <= day_end:
                daily_todos.append(todo)
            # Or if created today and has time
            elif day_start <= todo.created_at <= day_end:
                daily_todos.append(todo)
            # Or if actively tracking today
            elif todo.timer_started and day_start <= todo.timer_started <= day_end:
                daily_todos.append(todo)

    date_str = date.strftime("%Y-%m-%d (%A)")

    if not daily_todos:
        console.print(f"[dim]No time tracked for {date_str}[/dim]")
        return

    table = Table(title=f"Daily Report: {date_str}", show_header=True)
    table.add_column("Task", min_width=30)
    table.add_column("Project", width=15)
    table.add_column("Status", width=10)
    table.add_column("Time", width=10, justify="right")

    total_seconds = 0
    project_totals = defaultdict(float)

    for todo in daily_todos:
        time_seconds = todo.total_time.total_seconds()
        total_seconds += time_seconds

        project = todo.project or "(No project)"
        project_totals[project] += time_seconds

        table.add_row(
            todo.task,
            todo.project or "-",
            todo.status.value,
            format_duration(time_seconds),
        )

    console.print(table)
    console.print()

    # Project breakdown
    if len(project_totals) > 1:
        breakdown = Table(title="By Project", show_header=True)
        breakdown.add_column("Project", min_width=20)
        breakdown.add_column("Time", width=10, justify="right")
        breakdown.add_column("%", width=6, justify="right")

        for project, seconds in sorted(project_totals.items(), key=lambda x: -x[1]):
            pct = (seconds / total_seconds * 100) if total_seconds > 0 else 0
            breakdown.add_row(project, format_duration(seconds), f"{pct:.0f}%")

        console.print(breakdown)
        console.print()

    console.print(f"[bold]Total time:[/bold] {format_duration(total_seconds)}")


def weekly_report(db: Database, date: Optional[datetime] = None):
    """Generate weekly time tracking report."""
    if date is None:
        date = datetime.now()

    week_start, week_end = get_week_range(date)

    # Get all todos with time
    all_todos = db.list_all(include_done=True)

    # Group by day
    daily_totals = defaultdict(float)
    project_totals = defaultdict(float)
    task_times = []

    for todo in all_todos:
        if todo.time_spent.total_seconds() > 0:
            time_seconds = todo.total_time.total_seconds()

            # Attribute to completed date or created date
            todo_date = todo.completed_at or todo.created_at

            if week_start <= todo_date <= week_end:
                day_key = todo_date.strftime("%Y-%m-%d")
                daily_totals[day_key] += time_seconds
                project_totals[todo.project or "(No project)"] += time_seconds
                task_times.append((todo, time_seconds))

    week_str = f"{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"

    if not task_times:
        console.print(f"[dim]No time tracked for week of {week_str}[/dim]")
        return

    console.print(Panel(f"[bold]Weekly Report: {week_str}[/bold]", border_style="cyan"))
    console.print()

    # Daily breakdown
    day_table = Table(title="Daily Breakdown", show_header=True)
    day_table.add_column("Day", width=15)
    day_table.add_column("Date", width=12)
    day_table.add_column("Time", width=10, justify="right")

    total_seconds = sum(daily_totals.values())

    # Fill in all days of the week
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_key = day.strftime("%Y-%m-%d")
        day_name = day.strftime("%A")
        time = daily_totals.get(day_key, 0)

        style = "dim" if time == 0 else ""
        day_table.add_row(day_name, day_key, format_duration(time), style=style)

    console.print(day_table)
    console.print()

    # Project breakdown
    project_table = Table(title="By Project", show_header=True)
    project_table.add_column("Project", min_width=20)
    project_table.add_column("Time", width=10, justify="right")
    project_table.add_column("%", width=6, justify="right")

    for project, seconds in sorted(project_totals.items(), key=lambda x: -x[1]):
        pct = (seconds / total_seconds * 100) if total_seconds > 0 else 0
        project_table.add_row(project, format_duration(seconds), f"{pct:.0f}%")

    console.print(project_table)
    console.print()

    # Top tasks
    task_table = Table(title="Top Tasks", show_header=True)
    task_table.add_column("Task", min_width=30)
    task_table.add_column("Project", width=15)
    task_table.add_column("Time", width=10, justify="right")

    for todo, seconds in sorted(task_times, key=lambda x: -x[1])[:10]:
        task_table.add_row(todo.task, todo.project or "-", format_duration(seconds))

    console.print(task_table)
    console.print()

    console.print(f"[bold]Total time this week:[/bold] {format_duration(total_seconds)}")
    avg_per_day = total_seconds / 7
    console.print(f"[dim]Average per day: {format_duration(avg_per_day)}[/dim]")


def project_report(db: Database, project: Optional[str] = None):
    """Generate project time report."""
    all_todos = db.list_all(include_done=True)

    if project:
        # Single project report
        project_todos = [t for t in all_todos if t.project == project]

        if not project_todos:
            console.print(f"[dim]No todos found for project: {project}[/dim]")
            return

        table = Table(title=f"Project: {project}", show_header=True)
        table.add_column("Task", min_width=30)
        table.add_column("Status", width=10)
        table.add_column("Priority", width=8)
        table.add_column("Time", width=10, justify="right")

        total_seconds = 0
        done_count = 0

        for todo in project_todos:
            time_seconds = todo.total_time.total_seconds()
            total_seconds += time_seconds

            if todo.status == Status.DONE:
                done_count += 1

            table.add_row(
                todo.task,
                todo.status.value,
                str(todo.priority),
                format_duration(time_seconds),
            )

        console.print(table)
        console.print()
        console.print(f"[bold]Total tasks:[/bold] {len(project_todos)}")
        console.print(f"[bold]Completed:[/bold] {done_count}")
        console.print(f"[bold]Total time:[/bold] {format_duration(total_seconds)}")

    else:
        # All projects summary
        project_data = defaultdict(lambda: {"time": 0, "total": 0, "done": 0})

        for todo in all_todos:
            proj = todo.project or "(No project)"
            project_data[proj]["time"] += todo.total_time.total_seconds()
            project_data[proj]["total"] += 1
            if todo.status == Status.DONE:
                project_data[proj]["done"] += 1

        if not project_data:
            console.print("[dim]No projects found[/dim]")
            return

        table = Table(title="All Projects", show_header=True)
        table.add_column("Project", min_width=20)
        table.add_column("Tasks", width=8, justify="right")
        table.add_column("Done", width=8, justify="right")
        table.add_column("Progress", width=10)
        table.add_column("Time", width=10, justify="right")

        for project, data in sorted(project_data.items(), key=lambda x: -x[1]["time"]):
            progress = (data["done"] / data["total"] * 100) if data["total"] > 0 else 0
            progress_bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))

            table.add_row(
                project,
                str(data["total"]),
                str(data["done"]),
                f"{progress_bar} {progress:.0f}%",
                format_duration(data["time"]),
            )

        console.print(table)
