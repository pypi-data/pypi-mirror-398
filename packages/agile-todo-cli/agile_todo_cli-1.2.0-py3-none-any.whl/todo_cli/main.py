"""Main CLI entry point for Todo CLI."""

from datetime import datetime
from typing import Optional

import typer
from rich.console import Console

from . import __version__
from .database import Database
from .projects import ProjectManager
from .subtasks import SubtaskManager
from .display import (
    display_todos,
    display_todos_tree,
    display_todo_detail,
    display_stats,
    display_projects,
    display_project_detail,
    success,
    error,
    warning,
    info,
)
from .models import Priority, Status
from .reports import daily_report, weekly_report, project_report
from .export import export_todos
from .kanban import KanbanManager, KanbanColumn, display_kanban_board, display_kanban_compact
from .recurrence import RecurrenceManager
from .kanban_tui import run_kanban_interactive
from .calendar_view import CalendarView, display_month_calendar, display_week_calendar
from .cycles import CycleManager, CycleStatus
from .config import (
    get_config, get_config_warnings, save_config, Config, DEFAULT_CONFIG_PATH,
    VALID_PRIORITIES, VALID_DATE_FORMATS, VALID_TIME_FORMATS, VALID_COLOR_SCHEMES,
)

app = typer.Typer(
    name="todo",
    help="A CLI todo manager with time tracking.",
    no_args_is_help=True,
)
console = Console()

# Project subcommands
project_app = typer.Typer(
    name="project",
    help="Manage projects.",
    no_args_is_help=True,
)
app.add_typer(project_app, name="project")

# Cycle subcommands
cycle_app = typer.Typer(
    name="cycle",
    help="Manage development cycles (sprints).",
    no_args_is_help=True,
)
app.add_typer(cycle_app, name="cycle")

# Recurrence subcommands
recur_app = typer.Typer(
    name="recur",
    help="Manage recurring tasks.",
    no_args_is_help=True,
)
app.add_typer(recur_app, name="recur")


def get_db() -> Database:
    """Get database instance."""
    return Database()


def get_project_manager() -> ProjectManager:
    """Get project manager instance."""
    return ProjectManager(get_db().db_path)


def get_subtask_manager() -> SubtaskManager:
    """Get subtask manager instance."""
    return SubtaskManager(get_db().db_path)


def get_kanban_manager() -> KanbanManager:
    """Get KANBAN manager instance."""
    return KanbanManager(get_db().db_path)


def get_cycle_manager() -> CycleManager:
    """Get cycle manager instance."""
    return CycleManager(get_db().db_path)


def parse_priority(priority: str) -> Priority:
    """Parse priority string to Priority enum."""
    priority_map = {
        "p0": Priority.P0,
        "p1": Priority.P1,
        "p2": Priority.P2,
        "p3": Priority.P3,
        "0": Priority.P0,
        "1": Priority.P1,
        "2": Priority.P2,
        "3": Priority.P3,
    }
    # Use config default if no match
    config = get_config()
    default = priority_map.get(config.default_priority.lower(), Priority.P2)
    return priority_map.get(priority.lower(), default)


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime."""
    if not date_str:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y",
        "%m/%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Handle year-less formats
            if dt.year == 1900:
                dt = dt.replace(year=datetime.now().year)
            return dt
        except ValueError:
            continue

    return None


@app.command()
def add(
    task: str = typer.Argument(..., help="The task description"),
    priority: Optional[str] = typer.Option(None, "-p", "--priority", help="Priority (p0-p3, default from config)"),
    project: Optional[str] = typer.Option(None, "-P", "--project", help="Project name"),
    tags: Optional[str] = typer.Option(None, "-t", "--tags", help="Comma-separated tags"),
    due: Optional[str] = typer.Option(None, "-d", "--due", help="Due date (YYYY-MM-DD)"),
    recur: Optional[str] = typer.Option(None, "-r", "--recur", help="Recurrence pattern (daily, weekly, monthly, yearly, 'every N days', 'every mon,wed,fri')"),
    until: Optional[str] = typer.Option(None, "--until", help="End date for recurrence (YYYY-MM-DD)"),
):
    """Add a new todo.

    Examples:
        todo add "Daily standup" --recur daily
        todo add "Weekly review" --recur weekly --until 2025-12-31
        todo add "Workout" --recur "every mon,wed,fri"
        todo add "Rent payment" --recur "monthly on 1"
    """
    db = get_db()

    # Use config default if no priority specified
    if priority is None:
        priority = get_config().default_priority
    parsed_priority = parse_priority(priority)
    parsed_due = parse_date(due) if due else None
    parsed_tags = [t.strip() for t in tags.split(",")] if tags else []
    parsed_until = parse_date(until) if until else None

    # Validate recurrence pattern before creating task
    rm = RecurrenceManager()
    parsed_pattern = None
    if recur:
        try:
            parsed_pattern = rm.parse_pattern(recur)
        except ValueError as e:
            error(f"Invalid recurrence pattern: {e}")
            raise typer.Exit(1)

    # Resolve project name to project_id if provided
    project_id = None
    if project:
        pm = get_project_manager()
        project_obj = pm.get_project_by_name(project)
        if not project_obj:
            error(f"Project '{project}' not found")
            raise typer.Exit(1)
        project_id = project_obj.id

    todo = db.add(
        task=task,
        priority=parsed_priority,
        project_id=project_id,
        tags=parsed_tags,
        due_date=parsed_due,
    )

    # Create recurrence rule if pattern specified
    if parsed_pattern:
        db.add_recurrence_rule(
            task_id=todo.id,
            pattern=parsed_pattern.pattern,
            interval=parsed_pattern.interval,
            days_of_week=parsed_pattern.days_of_week,
            day_of_month=parsed_pattern.day_of_month,
            end_date=parsed_until,
        )
        recur_desc = rm.format_pattern(db.get_recurrence_rule_by_task(todo.id))
        success(f"Added recurring todo #{todo.id}: {task} ({recur_desc})")
    else:
        success(f"Added todo #{todo.id}: {task}")

    # Auto-start timer if configured
    config = get_config()
    if config.auto_start_on_add:
        # Stop any existing timer first
        active = db.get_active_timer()
        if active and active.id != todo.id:
            db.stop_timer(active.id)
            warning(f"Stopped timer on todo #{active.id}")
        db.start_timer(todo.id)
        info(f"Timer started automatically")


@app.command("list")
def list_todos(
    all_: Optional[bool] = typer.Option(None, "-a", "--all", help="Include completed todos (default from config)"),
    project: Optional[str] = typer.Option(None, "-P", "--project", help="Filter by project name"),
    status: Optional[str] = typer.Option(None, "-s", "--status", help="Filter by status"),
    parent: Optional[int] = typer.Option(None, "--parent", help="Show only subtasks of this parent ID"),
    has_children: Optional[bool] = typer.Option(None, "--has-children", help="Show only tasks with subtasks"),
    is_subtask: Optional[bool] = typer.Option(None, "--is-subtask", help="Show only subtasks (tasks with parents)"),
    tree: bool = typer.Option(False, "--tree", "-T", help="Display in hierarchical tree view"),
    due: Optional[str] = typer.Option(None, "--due", "-d", help="Filter by due date: today, tomorrow, week, or YYYY-MM-DD"),
    overdue: bool = typer.Option(False, "--overdue", help="Show only overdue tasks"),
    due_before: Optional[str] = typer.Option(None, "--due-before", help="Show tasks due before date (YYYY-MM-DD)"),
    due_after: Optional[str] = typer.Option(None, "--due-after", help="Show tasks due after date (YYYY-MM-DD)"),
):
    """List todos.

    Examples:
        todo list --due today        # Tasks due today
        todo list --due tomorrow     # Tasks due tomorrow
        todo list --due week         # Tasks due this week
        todo list --overdue          # All overdue tasks
        todo list --due 2025-01-15   # Tasks due on specific date
        todo list --due-before 2025-01-15  # Tasks due before date
        todo list --due-after 2025-01-15   # Tasks due after date
    """
    db = get_db()
    sm = get_subtask_manager()

    # Use config default if --all not specified
    config = get_config()
    include_done = all_ if all_ is not None else config.show_completed_in_list

    status_filter = None
    if status:
        status_map = {"todo": Status.TODO, "doing": Status.DOING, "done": Status.DONE}
        status_filter = status_map.get(status.lower())

    # Resolve project name to project_id if provided
    # If project exists in projects table, use project_id filter
    # Otherwise check if there are legacy tasks with that project string (backwards compatibility)
    project_id = None
    legacy_project = None
    if project:
        pm = get_project_manager()
        project_obj = pm.get_project_by_name(project)
        if project_obj:
            project_id = project_obj.id
        else:
            # Check if there are any legacy tasks with this project string
            legacy_tasks = db.list_all(project=project, include_done=True)
            if legacy_tasks:
                # Backwards compatibility: use legacy project string filter
                legacy_project = project
            else:
                error(f"Project '{project}' not found")
                raise typer.Exit(1)

    todos = db.list_all(status=status_filter, project_id=project_id, project=legacy_project, include_done=include_done)

    # Apply subtask filters
    if parent is not None:
        # Show only subtasks of specified parent
        children = sm.get_children(parent)
        child_ids = {c['id'] for c in children}
        todos = [t for t in todos if t.id in child_ids]

    if has_children:
        # Show only tasks that have subtasks
        todos = [t for t in todos if sm.has_children(t.id)]

    if is_subtask:
        # Show only tasks that are subtasks
        todos = [t for t in todos if sm.is_subtask(t.id)]

    # Apply due date filters
    from datetime import date, datetime, timedelta

    today = date.today()

    if due:
        due_lower = due.lower()
        if due_lower == "today":
            # Tasks due today
            todos = [t for t in todos if t.due_date and t.due_date.date() == today]
        elif due_lower == "tomorrow":
            # Tasks due tomorrow
            tomorrow = today + timedelta(days=1)
            todos = [t for t in todos if t.due_date and t.due_date.date() == tomorrow]
        elif due_lower == "week":
            # Tasks due this week (next 7 days including today)
            week_end = today + timedelta(days=7)
            todos = [t for t in todos if t.due_date and today <= t.due_date.date() <= week_end]
        else:
            # Try to parse as specific date (YYYY-MM-DD)
            try:
                target_date = datetime.strptime(due, "%Y-%m-%d").date()
                todos = [t for t in todos if t.due_date and t.due_date.date() == target_date]
            except ValueError:
                error(f"Invalid due date format: {due}. Use: today, tomorrow, week, or YYYY-MM-DD")
                raise typer.Exit(1)

    if overdue:
        # Show only overdue tasks (due date < today and not done)
        todos = [t for t in todos if t.due_date and t.due_date.date() < today and t.status != Status.DONE]

    if due_before:
        try:
            before_date = datetime.strptime(due_before, "%Y-%m-%d").date()
            todos = [t for t in todos if t.due_date and t.due_date.date() < before_date]
        except ValueError:
            error(f"Invalid date format for --due-before: {due_before}. Use: YYYY-MM-DD")
            raise typer.Exit(1)

    if due_after:
        try:
            after_date = datetime.strptime(due_after, "%Y-%m-%d").date()
            todos = [t for t in todos if t.due_date and t.due_date.date() > after_date]
        except ValueError:
            error(f"Invalid date format for --due-after: {due_after}. Use: YYYY-MM-DD")
            raise typer.Exit(1)

    if tree:
        display_todos_tree(todos, sm)
    else:
        display_todos(todos, subtask_manager=sm)


@app.command()
def show(
    todo_id: int = typer.Argument(..., help="Todo ID"),
):
    """Show detailed view of a todo."""
    db = get_db()
    todo = db.get(todo_id)

    if not todo:
        error(f"Todo #{todo_id} not found")
        raise typer.Exit(1)

    display_todo_detail(todo)


@app.command()
def done(
    todo_id: int = typer.Argument(..., help="Todo ID to mark as done"),
    force: bool = typer.Option(False, "-f", "--force", help="Force complete even with incomplete subtasks"),
):
    """Mark a todo as done.

    If the task has incomplete subtasks, completion will be blocked unless --force is used.
    If completing the last incomplete child, the parent will be auto-completed.
    """
    db = get_db()
    config = get_config()
    sm = SubtaskManager(config.get_db_path())

    # Check if todo exists
    todo = db.get(todo_id)
    if not todo:
        error(f"Todo #{todo_id} not found")
        raise typer.Exit(1)

    # Check if task has incomplete children
    can_complete, message = sm.can_complete_parent(todo_id)
    if not can_complete and not force:
        # Get the list of incomplete child IDs for the error message
        status = sm.get_children_completion_status(todo_id)
        incomplete_ids = ", ".join(f"#{id}" for id in status['incomplete_ids'])
        error(f"Cannot complete #{todo_id}. Incomplete sub-tasks: {incomplete_ids}")
        raise typer.Exit(1)

    if not can_complete and force:
        warning(f"Force completing #{todo_id} with incomplete subtasks")

    # Complete the task
    todo = db.mark_done(todo_id)

    time_str = todo.format_time()
    success(f"Completed todo #{todo_id}: {todo.task}")
    if todo.time_spent.total_seconds() > 0:
        info(f"Total time spent: {time_str}")

    # Check if this is a recurring task and create next occurrence
    rm = RecurrenceManager()
    rule = db.get_recurrence_rule_by_task(todo_id)
    if rule:
        next_task = rm.create_occurrence(db, todo_id)
        if next_task:
            due_str = next_task.due_date.strftime('%Y-%m-%d') if next_task.due_date else "no due date"
            info(f"↻ Created next occurrence: #{next_task.id} (due: {due_str})")
        elif rule.has_reached_limit:
            info(f"↻ Recurrence limit reached ({rule.max_occurrences} occurrences)")
        elif rule.has_expired:
            info(f"↻ Recurrence ended (end date: {rule.end_date.strftime('%Y-%m-%d')})")

    # Check if this was the last incomplete child of a parent
    parent_info = sm.get_parent(todo_id)
    if parent_info:
        parent_id = parent_info['id']
        parent_can_complete, _ = sm.can_complete_parent(parent_id)
        if parent_can_complete:
            # Auto-complete the parent
            parent_todo = db.get(parent_id)
            if parent_todo and parent_todo.status != Status.DONE:
                db.mark_done(parent_id)
                success(f"Parent #{parent_id} also completed.")


@app.command()
def uncomplete(
    todo_id: int = typer.Argument(..., help="Todo ID to uncomplete"),
):
    """Mark a completed todo as not done.

    If the task is a child and the parent was complete, the parent will be
    auto-uncompleted as well.
    """
    db = get_db()
    config = get_config()
    sm = SubtaskManager(config.get_db_path())

    # Check if todo exists
    todo = db.get(todo_id)
    if not todo:
        error(f"Todo #{todo_id} not found")
        raise typer.Exit(1)

    if todo.status != Status.DONE:
        warning(f"Todo #{todo_id} is not completed")
        raise typer.Exit(1)

    # Uncomplete the task
    todo = db.mark_undone(todo_id)
    success(f"Uncompleted todo #{todo_id}: {todo.task}")

    # Check if parent needs to be uncompleted
    parent_info = sm.get_parent(todo_id)
    if parent_info:
        parent_id = parent_info['id']
        parent_todo = db.get(parent_id)
        if parent_todo and parent_todo.status == Status.DONE:
            db.mark_undone(parent_id)
            success(f"Parent #{parent_id} also uncompleted.")


@app.command()
def delete(
    todo_id: int = typer.Argument(..., help="Todo ID to delete"),
    force: bool = typer.Option(False, "-f", "--force", help="Skip confirmation"),
):
    """Delete a todo."""
    db = get_db()
    todo = db.get(todo_id)

    if not todo:
        error(f"Todo #{todo_id} not found")
        raise typer.Exit(1)

    # Check config for confirm_delete setting
    config = get_config()
    should_confirm = config.confirm_delete and not force

    if should_confirm:
        confirm = typer.confirm(f"Delete todo #{todo_id}: '{todo.task}'?")
        if not confirm:
            info("Cancelled")
            return

    db.delete(todo_id)
    success(f"Deleted todo #{todo_id}")


@app.command()
def start(
    todo_id: int = typer.Argument(..., help="Todo ID to start tracking"),
):
    """Start time tracking on a todo."""
    db = get_db()

    # Check for existing active timer
    active = db.get_active_timer()
    if active and active.id != todo_id:
        warning(f"Stopping timer on todo #{active.id}: {active.task}")
        db.stop_timer(active.id)

    todo = db.start_timer(todo_id)

    if not todo:
        error(f"Todo #{todo_id} not found")
        raise typer.Exit(1)

    success(f"Started tracking todo #{todo_id}: {todo.task}")


@app.command()
def stop(
    todo_id: Optional[int] = typer.Argument(None, help="Todo ID (optional, stops any active)"),
):
    """Stop time tracking."""
    db = get_db()

    todo = db.stop_timer(todo_id)

    if not todo:
        if todo_id:
            error(f"No active timer on todo #{todo_id}")
        else:
            info("No active timer")
        return

    time_str = todo.format_time()
    success(f"Stopped tracking todo #{todo.id}: {todo.task}")
    info(f"Time spent: {time_str}")


@app.command()
def status(
    todo_id: int = typer.Argument(..., help="Todo ID"),
    new_status: str = typer.Argument(..., help="New status (todo, doing, done)"),
):
    """Change todo status."""
    db = get_db()
    todo = db.get(todo_id)

    if not todo:
        error(f"Todo #{todo_id} not found")
        raise typer.Exit(1)

    status_map = {"todo": Status.TODO, "doing": Status.DOING, "done": Status.DONE}
    parsed_status = status_map.get(new_status.lower())

    if not parsed_status:
        error(f"Invalid status: {new_status}. Use: todo, doing, done")
        raise typer.Exit(1)

    todo.status = parsed_status
    if parsed_status == Status.DONE:
        todo.completed_at = datetime.now()

    db.update(todo)
    success(f"Updated todo #{todo_id} status to {parsed_status.value}")


@app.command()
def edit(
    todo_id: int = typer.Argument(..., help="Todo ID"),
    task: Optional[str] = typer.Option(None, "-t", "--task", help="New task description"),
    priority: Optional[str] = typer.Option(None, "-p", "--priority", help="New priority"),
    project: Optional[str] = typer.Option(None, "-P", "--project", help="New project"),
    tags: Optional[str] = typer.Option(None, "--tags", help="New tags (comma-separated)"),
    due: Optional[str] = typer.Option(None, "-d", "--due", help="New due date"),
):
    """Edit a todo."""
    db = get_db()
    todo = db.get(todo_id)

    if not todo:
        error(f"Todo #{todo_id} not found")
        raise typer.Exit(1)

    if task:
        todo.task = task
    if priority:
        todo.priority = parse_priority(priority)
    if project is not None:
        todo.project = project if project else None
    if tags is not None:
        todo.tags = [t.strip() for t in tags.split(",")] if tags else []
    if due is not None:
        todo.due_date = parse_date(due)

    db.update(todo)
    success(f"Updated todo #{todo_id}")


# Project commands moved to project_app sub-application (see below)


@app.command()
def stats():
    """Show todo statistics."""
    db = get_db()
    stats_data = db.get_stats()
    display_stats(stats_data)


@app.command()
def active():
    """Show currently tracking todo."""
    db = get_db()
    todo = db.get_active_timer()

    if not todo:
        info("No active timer")
        return

    display_todo_detail(todo)


@app.command()
def version():
    """Show version."""
    console.print(f"Todo CLI v{__version__}")


@app.command()
def report(
    report_type: str = typer.Argument("daily", help="Report type: daily, weekly, project"),
    project: Optional[str] = typer.Option(None, "-P", "--project", help="Project for project report"),
):
    """Generate time tracking reports."""
    db = get_db()

    if report_type == "daily":
        daily_report(db)
    elif report_type == "weekly":
        weekly_report(db)
    elif report_type == "project":
        project_report(db, project)
    else:
        error(f"Unknown report type: {report_type}. Use: daily, weekly, project")
        raise typer.Exit(1)


@app.command()
def export(
    format: str = typer.Argument("json", help="Export format: json, csv, md"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output file path"),
    all_: bool = typer.Option(True, "-a", "--all", help="Include completed todos"),
    project: Optional[str] = typer.Option(None, "-P", "--project", help="Filter by project"),
):
    """Export todos to file."""
    from pathlib import Path

    db = get_db()
    output_path = Path(output) if output else None

    try:
        result_path = export_todos(db, format, output_path, include_done=all_, project=project)
        success(f"Exported to: {result_path}")
    except ValueError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command()
def interactive():
    """Launch interactive menu mode."""
    from .interactive import run_interactive
    run_interactive()


@app.command("config")
def config_cmd(
    show: bool = typer.Option(False, "--show", "-s", help="Show current config"),
    init: bool = typer.Option(False, "--init", help="Create default config file"),
    set_option: Optional[str] = typer.Option(None, "--set", help="Set option (key=value)"),
    path: bool = typer.Option(False, "--path", help="Show config file path"),
    validate: bool = typer.Option(False, "--validate", "-v", help="Validate current config"),
):
    """View or modify configuration."""
    config = get_config()

    if path:
        console.print(f"Config file: {DEFAULT_CONFIG_PATH}")
        console.print(f"Exists: {DEFAULT_CONFIG_PATH.exists()}")
        return

    if validate:
        warnings = config.validate()
        if warnings:
            for warn in warnings:
                warning(warn)
        else:
            success("Config is valid")
        return

    if init:
        if DEFAULT_CONFIG_PATH.exists():
            if not typer.confirm("Config file exists. Overwrite?"):
                info("Cancelled")
                return
        config = Config()  # Reset to defaults
        save_config(config)
        success(f"Created config at: {DEFAULT_CONFIG_PATH}")
        return

    if set_option:
        try:
            key, value = set_option.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Type conversion for known boolean fields
            if key in ("confirm_delete", "auto_start_on_add", "show_completed_in_list"):
                value = value.lower() in ("true", "1", "yes", "on")

            if not hasattr(config, key):
                error(f"Unknown config option: {key}")
                raise typer.Exit(1)

            # Validate specific fields before setting
            if key == "default_priority" and value.lower() not in VALID_PRIORITIES:
                error(f"Invalid priority. Valid: {', '.join(sorted(VALID_PRIORITIES))}")
                raise typer.Exit(1)

            if key == "date_format" and value not in VALID_DATE_FORMATS:
                error(f"Invalid date format. Valid: {', '.join(sorted(VALID_DATE_FORMATS))}")
                raise typer.Exit(1)

            if key == "time_format" and value not in VALID_TIME_FORMATS:
                error(f"Invalid time format. Valid: {', '.join(sorted(VALID_TIME_FORMATS))}")
                raise typer.Exit(1)

            if key == "color_scheme" and value.lower() not in VALID_COLOR_SCHEMES:
                error(f"Invalid color scheme. Valid: {', '.join(sorted(VALID_COLOR_SCHEMES))}")
                raise typer.Exit(1)

            setattr(config, key, value)
            save_config(config)
            success(f"Set {key} = {value}")
        except ValueError:
            error("Invalid format. Use: --set key=value")
            raise typer.Exit(1)
        return

    # Default: show config
    from rich.table import Table

    table = Table(title="Configuration", show_header=True)
    table.add_column("Option", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Description", style="dim")

    descriptions = {
        "default_priority": "Default priority for new todos",
        "date_format": "Date display format",
        "time_format": "Time display format (12h/24h)",
        "color_scheme": "Color scheme (auto/dark/light/none)",
        "confirm_delete": "Confirm before deleting",
        "auto_start_on_add": "Auto-start timer on add",
        "show_completed_in_list": "Show completed in list by default",
        "db_path": "Custom database path",
    }

    for key, desc in descriptions.items():
        value = getattr(config, key, None)
        value_str = str(value) if value is not None else "(default)"
        table.add_row(key, value_str, desc)

    console.print(table)
    console.print(f"\n[dim]Config file: {DEFAULT_CONFIG_PATH}[/dim]")


# ============================================================================
# PROJECT SUBCOMMANDS
# ============================================================================

@project_app.command("create")
def project_create(
    name: str = typer.Argument(..., help="Project name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Project description"),
    color: Optional[str] = typer.Option(None, "--color", "-c", help="Project color"),
):
    """Create a new project."""
    pm = get_project_manager()

    try:
        project = pm.create_project(name, description, color)
        success(f"Created project: {project.name}")
    except ValueError as e:
        error(str(e))
        raise typer.Exit(1)


@project_app.command("list")
def project_list(
    archived: bool = typer.Option(False, "--archived", "-a", help="Show archived projects"),
):
    """List all projects."""
    pm = get_project_manager()
    projects = pm.list_projects(archived=archived)

    if not projects:
        info("No projects found")
        return

    display_projects(projects)


@project_app.command("show")
def project_show(
    name: str = typer.Argument(..., help="Project name"),
):
    """Show project details."""
    pm = get_project_manager()
    project = pm.get_project_by_name(name)

    if not project:
        error(f"Project '{name}' not found")
        raise typer.Exit(1)

    # Get project stats and tasks
    stats = pm.get_project_stats(project.id)
    display_project_detail(stats)


@project_app.command("delete")
def project_delete(
    name: str = typer.Argument(..., help="Project name"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a project. Tasks in the project will persist."""
    pm = get_project_manager()
    project = pm.get_project_by_name(name)

    if not project:
        error(f"Project '{name}' not found")
        raise typer.Exit(1)

    # Confirm deletion
    if not force:
        confirm = typer.confirm(
            f"Delete project '{project.name}'? (Tasks will remain with no project)"
        )
        if not confirm:
            info("Cancelled")
            return

    if pm.delete_project(project.id):
        success(f"Deleted project: {project.name}")
    else:
        error("Failed to delete project")
        raise typer.Exit(1)


@project_app.command("update")
def project_update(
    name: str = typer.Argument(..., help="Current project name"),
    new_name: Optional[str] = typer.Option(None, "--name", "-n", help="New project name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New description"),
    color: Optional[str] = typer.Option(None, "--color", "-c", help="New color"),
):
    """Update project details."""
    pm = get_project_manager()
    project = pm.get_project_by_name(name)

    if not project:
        error(f"Project '{name}' not found")
        raise typer.Exit(1)

    try:
        updated = pm.update_project(project.id, new_name, description, color)
        if updated:
            success(f"Updated project: {updated.name}")
        else:
            error("Failed to update project")
            raise typer.Exit(1)
    except ValueError as e:
        error(str(e))
        raise typer.Exit(1)


@project_app.command("archive")
def project_archive(
    name: str = typer.Argument(..., help="Project name"),
):
    """Archive a project."""
    pm = get_project_manager()
    project = pm.get_project_by_name(name)

    if not project:
        error(f"Project '{name}' not found")
        raise typer.Exit(1)

    archived = pm.archive_project(project.id)
    if archived:
        success(f"Archived project: {archived.name}")
    else:
        error("Failed to archive project")
        raise typer.Exit(1)


@project_app.command("unarchive")
def project_unarchive(
    name: str = typer.Argument(..., help="Project name"),
):
    """Unarchive a project."""
    pm = get_project_manager()
    project = pm.get_project_by_name(name)

    if not project:
        error(f"Project '{name}' not found")
        raise typer.Exit(1)

    unarchived = pm.unarchive_project(project.id)
    if unarchived:
        success(f"Unarchived project: {unarchived.name}")
    else:
        error("Failed to unarchive project")
        raise typer.Exit(1)


# ============================================================================
# KANBAN COMMANDS
# ============================================================================

@app.command()
def kanban(
    project: Optional[str] = typer.Option(None, "-P", "--project", help="Filter by project name"),
    priority: Optional[str] = typer.Option(None, "-p", "--priority", help="Filter by priority (p0-p3)"),
    tags: Optional[str] = typer.Option(None, "-t", "--tags", help="Filter by tags (comma-separated)"),
    compact: bool = typer.Option(False, "--compact", "-c", help="Use compact table view"),
    include_done: bool = typer.Option(False, "--done", "-d", help="Include done column"),
    show_empty: bool = typer.Option(False, "--show-empty", "-e", help="Show empty columns"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Launch interactive TUI mode"),
):
    """Display KANBAN board view.

    Shows tasks organized in columns: Backlog, Todo, In Progress, Review, Done.
    By default, the Done column and empty columns are hidden for more space.

    Use --interactive/-i to launch the interactive TUI mode with keyboard navigation:
    - h/l or Left/Right: Navigate between columns
    - j/k or Up/Down: Navigate between tasks
    - Enter: Move task to next column
    - m: Move task to specific column
    - d: Toggle done column visibility
    - r: Refresh board
    - ?: Show help
    - q/Escape: Quit
    """
    # Resolve project name to project_id
    project_id = None
    if project:
        pm = get_project_manager()
        project_obj = pm.get_project_by_name(project)
        if not project_obj:
            error(f"Project '{project}' not found")
            raise typer.Exit(1)
        project_id = project_obj.id

    # Parse priority filter
    priority_val = None
    if priority:
        parsed = parse_priority(priority)
        priority_val = parsed.value

    # Parse tags filter
    tags_list = None
    if tags:
        tags_list = [t.strip() for t in tags.split(",")]

    # Launch interactive TUI mode if requested
    if interactive:
        run_kanban_interactive(
            db_path=get_config().get_db_path(),
            project_id=project_id,
            priority=priority_val,
            tags=tags_list,
        )
        return

    # Get and display board (static view)
    km = get_kanban_manager()
    board = km.get_board(
        project_id=project_id,
        priority=priority_val,
        tags=tags_list,
        include_done=include_done,
    )

    if compact:
        display_kanban_compact(board, hide_empty=not show_empty)
    else:
        display_kanban_board(board, hide_empty=not show_empty)


@app.command()
def move(
    task_id: int = typer.Argument(..., help="Task ID to move"),
    column: str = typer.Argument(..., help="Target column (backlog, todo, in-progress, review, done)"),
):
    """Move a task to a different KANBAN column.

    Valid columns: backlog, todo, in-progress (or doing), review, done.
    Moving to 'done' automatically marks the task as complete.
    """
    km = get_kanban_manager()

    ok, message = km.move_task(task_id, column)

    if ok:
        success(message)
    else:
        error(message)
        raise typer.Exit(1)


# ============================================================================
# SUBTASK COMMANDS
# ============================================================================

@app.command("add-subtask")
def add_subtask(
    parent_id: int = typer.Argument(..., help="ID of the parent task"),
    task: str = typer.Argument(..., help="The subtask description"),
    priority: Optional[str] = typer.Option(None, "-p", "--priority", help="Priority (p0-p3, inherits from parent if not set)"),
    tags: Optional[str] = typer.Option(None, "-t", "--tags", help="Comma-separated tags (adds to parent's tags)"),
    due: Optional[str] = typer.Option(None, "-d", "--due", help="Due date (YYYY-MM-DD)"),
):
    """Add a subtask to an existing task.

    Creates a new task as a child of the specified parent task.
    The subtask inherits the parent's project and tags (additional tags can be specified).
    """
    db = get_db()
    sm = get_subtask_manager()

    # Get parent task
    parent = db.get(parent_id)
    if not parent:
        error(f"Parent task #{parent_id} not found")
        raise typer.Exit(1)

    # Create the subtask - inherit parent's properties
    if priority is None:
        parsed_priority = parent.priority
    else:
        parsed_priority = parse_priority(priority)

    parsed_due = parse_date(due) if due else None

    # Combine parent's tags with any additional specified tags
    parent_tags = parent.tags or []
    additional_tags = [t.strip() for t in tags.split(",")] if tags else []
    combined_tags = list(set(parent_tags + additional_tags))

    # Create the task first
    child = db.add(
        task=task,
        priority=parsed_priority,
        project_id=parent.project_id,
        tags=combined_tags,
        due_date=parsed_due,
    )

    # Add the subtask relationship
    can_add, validation_error = sm.can_add_subtask(parent_id, child.id)
    if not can_add:
        # Rollback: delete the created task
        db.delete(child.id)
        error(validation_error)
        raise typer.Exit(1)

    ok, message = sm.add_subtask(parent_id, child.id)
    if not ok:
        # Rollback: delete the created task
        db.delete(child.id)
        error(message)
        raise typer.Exit(1)

    success(f"Added subtask #{child.id}: {task} (parent: #{parent_id})")


@app.command("unlink")
def unlink_subtask(
    child_id: int = typer.Argument(..., help="ID of the subtask to unlink"),
):
    """Unlink a subtask from its parent (make it a top-level task).

    This removes the parent-child relationship but does not delete the task.
    The task will become a standalone top-level task.
    """
    db = get_db()
    sm = get_subtask_manager()

    # Check if task exists
    child = db.get(child_id)
    if not child:
        error(f"Task #{child_id} not found")
        raise typer.Exit(1)

    # Check if it's actually a subtask
    parent = sm.get_parent(child_id)
    if not parent:
        error(f"Task #{child_id} is not a subtask (no parent)")
        raise typer.Exit(1)

    parent_id = parent['id']

    # Remove the relationship
    ok, message = sm.remove_subtask(parent_id, child_id)
    if not ok:
        error(message)
        raise typer.Exit(1)

    success(f"Unlinked task #{child_id} from parent #{parent_id}")


# ============================================================================
# CALENDAR COMMANDS
# ============================================================================

@app.command("calendar")
def calendar_cmd(
    month: Optional[str] = typer.Option(None, "--month", "-m", help="Month to display (YYYY-MM format)"),
    week: bool = typer.Option(False, "--week", "-w", help="Show week view instead of month"),
    prev: bool = typer.Option(False, "--prev", "-p", help="Show previous month/week"),
    next_: bool = typer.Option(False, "--next", "-n", help="Show next month/week"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Launch interactive calendar TUI"),
):
    """Show calendar view with task counts.

    By default shows the current month. Use --week for a week view.
    Navigate with --prev or --next to see other months/weeks.
    Use --interactive (-i) to launch the interactive TUI.

    Examples:
        todo calendar              # Current month
        todo calendar --week       # Current week
        todo calendar -m 2025-02   # February 2025
        todo calendar --prev       # Previous month
        todo calendar -w --next    # Next week
        todo calendar -i           # Interactive mode
    """
    from datetime import date, timedelta

    db = get_db()

    if interactive:
        from .calendar_interactive import run_interactive_calendar
        run_interactive_calendar(db)
        return

    cv = CalendarView(db)
    today = date.today()

    if week:
        # Week view
        # Get Monday of current week
        week_start = today - timedelta(days=today.weekday())

        if prev:
            week_start = week_start - timedelta(weeks=1)
        elif next_:
            week_start = week_start + timedelta(weeks=1)

        calendar_data = cv.build_week_calendar(week_start)
        display_week_calendar(calendar_data)
    else:
        # Month view
        year = today.year
        month_num = today.month

        if month:
            # Parse YYYY-MM format
            try:
                parts = month.split("-")
                year = int(parts[0])
                month_num = int(parts[1])
                if month_num < 1 or month_num > 12:
                    raise ValueError("Month must be 1-12")
            except (ValueError, IndexError):
                error(f"Invalid month format: {month}. Use YYYY-MM (e.g., 2025-02)")
                raise typer.Exit(1)

        if prev:
            month_num -= 1
            if month_num < 1:
                month_num = 12
                year -= 1
        elif next_:
            month_num += 1
            if month_num > 12:
                month_num = 1
                year += 1

        calendar_data = cv.build_month_calendar(year, month_num)
        display_month_calendar(calendar_data, year, month_num)


# ============================================================================
# CYCLE COMMANDS
# ============================================================================

@cycle_app.command("create")
def cycle_create(
    name: str = typer.Argument(..., help="Cycle name"),
    duration: int = typer.Option(2, "--duration", "-d", help="Duration in weeks (1, 2, or 4)"),
):
    """Create a new cycle.

    Only one cycle can be active at a time. Valid durations: 1, 2, or 4 weeks.
    """
    cm = get_cycle_manager()

    ok, result = cm.create_cycle(name, duration)

    if ok:
        success(f"Created cycle: {result.name}")
        info(f"  Duration: {duration} weeks")
        info(f"  Start: {result.start_date.strftime('%Y-%m-%d')}")
        info(f"  End: {result.end_date.strftime('%Y-%m-%d')}")
    else:
        error(result)
        raise typer.Exit(1)


@cycle_app.command("list")
def cycle_list(
    all_: bool = typer.Option(False, "--all", "-a", help="Include closed cycles"),
):
    """List cycles."""
    from rich.table import Table

    cm = get_cycle_manager()
    cycles = cm.list_cycles(include_closed=all_)

    if not cycles:
        info("No cycles found")
        return

    table = Table(title="Cycles", show_header=True)
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Duration", style="dim")
    table.add_column("Start", style="dim")
    table.add_column("End", style="dim")
    table.add_column("Days Left", style="yellow")

    for cycle in cycles:
        status_style = "green" if cycle.status == CycleStatus.ACTIVE else "dim"
        days_left = str(cycle.days_remaining) if cycle.is_active and cycle.days_remaining >= 0 else "-"

        table.add_row(
            str(cycle.id),
            cycle.name,
            f"[{status_style}]{cycle.status.value}[/{status_style}]",
            f"{cycle.duration_weeks}w",
            cycle.start_date.strftime("%Y-%m-%d"),
            cycle.end_date.strftime("%Y-%m-%d"),
            days_left,
        )

    console.print(table)


@cycle_app.command("current")
def cycle_current():
    """Show current active cycle with progress."""
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TextColumn

    cm = get_cycle_manager()
    cycle = cm.get_active_cycle()

    if not cycle:
        info("No active cycle")
        return

    # Get progress stats
    progress_data = cm.get_cycle_progress(cycle.id)

    # Build progress display
    lines = []
    lines.append(f"[bold cyan]{cycle.name}[/bold cyan]")
    lines.append(f"[dim]Duration: {cycle.duration_weeks} weeks ({cycle.start_date.strftime('%Y-%m-%d')} to {cycle.end_date.strftime('%Y-%m-%d')})[/dim]")
    lines.append("")

    # Progress bar
    pct = progress_data['completion_percentage']
    completed = progress_data['completed_tasks']
    total = progress_data['total_tasks']

    # Create simple progress bar
    bar_width = 30
    filled = int(bar_width * pct / 100)
    bar = "█" * filled + "░" * (bar_width - filled)
    lines.append(f"[green]{bar}[/green] {pct:.0f}% ({completed}/{total} tasks)")
    lines.append("")

    # Stats
    lines.append(f"Days remaining: [yellow]{cycle.days_remaining}[/yellow]")
    lines.append(f"Velocity: [cyan]{progress_data['velocity']:.1f}[/cyan] tasks/day")
    lines.append(f"Projected: [dim]{progress_data['projected_completion']:.0f} tasks by end[/dim]")

    panel = Panel(
        "\n".join(lines),
        title="Active Cycle",
        border_style="green",
    )
    console.print(panel)


@cycle_app.command("assign")
def cycle_assign(
    task_id: int = typer.Argument(..., help="Task ID to assign"),
    cycle_name: Optional[str] = typer.Option(None, "--cycle", "-c", help="Cycle name (default: active cycle)"),
):
    """Assign a task to a cycle.

    If no cycle is specified, assigns to the current active cycle.
    """
    cm = get_cycle_manager()
    db = get_db()

    # Verify task exists
    task = db.get(task_id)
    if not task:
        error(f"Task #{task_id} not found")
        raise typer.Exit(1)

    # Get cycle
    if cycle_name:
        cycle = cm.get_cycle_by_name(cycle_name)
        if not cycle:
            error(f"Cycle '{cycle_name}' not found")
            raise typer.Exit(1)
    else:
        cycle = cm.get_active_cycle()
        if not cycle:
            error("No active cycle. Create one with 'cycle create' or specify --cycle")
            raise typer.Exit(1)

    ok, message = cm.assign_task(cycle.id, task_id)

    if ok:
        success(f"Assigned task #{task_id} to cycle '{cycle.name}'")
    else:
        error(message)
        raise typer.Exit(1)


@cycle_app.command("unassign")
def cycle_unassign(
    task_id: int = typer.Argument(..., help="Task ID to unassign"),
):
    """Unassign a task from its cycle."""
    cm = get_cycle_manager()
    db = get_db()

    # Verify task exists
    task = db.get(task_id)
    if not task:
        error(f"Task #{task_id} not found")
        raise typer.Exit(1)

    ok, message = cm.unassign_task(task_id)

    if ok:
        success(f"Unassigned task #{task_id} from cycle")
    else:
        error(message)
        raise typer.Exit(1)


@cycle_app.command("tasks")
def cycle_tasks(
    cycle_name: Optional[str] = typer.Option(None, "--cycle", "-c", help="Cycle name (default: active cycle)"),
):
    """Show tasks in a cycle."""
    from rich.table import Table

    cm = get_cycle_manager()

    # Get cycle
    if cycle_name:
        cycle = cm.get_cycle_by_name(cycle_name)
        if not cycle:
            error(f"Cycle '{cycle_name}' not found")
            raise typer.Exit(1)
    else:
        cycle = cm.get_active_cycle()
        if not cycle:
            error("No active cycle. Specify --cycle or create one")
            raise typer.Exit(1)

    tasks = cm.get_cycle_tasks(cycle.id)

    if not tasks:
        info(f"No tasks in cycle '{cycle.name}'")
        return

    table = Table(title=f"Tasks in '{cycle.name}'", show_header=True)
    table.add_column("ID", style="dim")
    table.add_column("Task", style="cyan")
    table.add_column("Priority")
    table.add_column("Status")
    table.add_column("Added", style="dim")

    priority_icons = {0: "🔴", 1: "🟡", 2: "🔵", 3: "⚪"}
    status_styles = {"todo": "dim", "doing": "yellow", "done": "green"}

    for task in tasks:
        p_icon = priority_icons.get(task.priority, "⚪")
        s_style = status_styles.get(task.status, "dim")
        added = task.added_at.strftime("%Y-%m-%d") if task.added_at else "-"

        table.add_row(
            str(task.task_id),
            task.task_name[:40] + ("..." if len(task.task_name) > 40 else ""),
            p_icon,
            f"[{s_style}]{task.status}[/{s_style}]",
            added,
        )

    console.print(table)


@cycle_app.command("report")
def cycle_report(
    cycle_name: Optional[str] = typer.Option(None, "--cycle", "-c", help="Cycle name (default: active cycle)"),
    format_: str = typer.Option("md", "--format", "-f", help="Output format: md, json"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output file path"),
):
    """Generate cycle report.

    Output formats: md (Markdown), json.
    """
    from pathlib import Path

    cm = get_cycle_manager()

    # Get cycle
    if cycle_name:
        cycle = cm.get_cycle_by_name(cycle_name)
        if not cycle:
            error(f"Cycle '{cycle_name}' not found")
            raise typer.Exit(1)
    else:
        cycle = cm.get_active_cycle()
        if not cycle:
            error("No active cycle. Specify --cycle or create one")
            raise typer.Exit(1)

    # Generate report
    if format_.lower() == "md":
        content = cm.generate_report_markdown(cycle.id)
        default_ext = ".md"
    elif format_.lower() == "json":
        content = cm.export_json(cycle.id)
        default_ext = ".json"
    else:
        error(f"Unknown format: {format_}. Use: md, json")
        raise typer.Exit(1)

    # Output
    if output:
        output_path = Path(output)
        output_path.write_text(content)
        success(f"Report saved to: {output_path}")
    else:
        console.print(content)


@cycle_app.command("close")
def cycle_close(
    cycle_name: Optional[str] = typer.Option(None, "--cycle", "-c", help="Cycle name (default: active cycle)"),
    rollover: bool = typer.Option(False, "--rollover", "-r", help="Roll over incomplete tasks to new cycle"),
    new_name: Optional[str] = typer.Option(None, "--new-name", help="Name for new cycle (with --rollover)"),
    duration: int = typer.Option(2, "--duration", "-d", help="Duration for new cycle (with --rollover)"),
):
    """Close a cycle.

    With --rollover, incomplete tasks are moved to a new cycle.
    """
    cm = get_cycle_manager()

    # Get cycle
    if cycle_name:
        cycle = cm.get_cycle_by_name(cycle_name)
        if not cycle:
            error(f"Cycle '{cycle_name}' not found")
            raise typer.Exit(1)
    else:
        cycle = cm.get_active_cycle()
        if not cycle:
            error("No active cycle to close")
            raise typer.Exit(1)

    # Close the cycle
    ok, result = cm.close_cycle(
        cycle.id,
        rollover=rollover,
        new_cycle_name=new_name,
        new_cycle_duration=duration,
    )

    if ok:
        success(f"Closed cycle: {cycle.name}")
        if rollover and isinstance(result, dict) and result.get("new_cycle"):
            new_cycle = result["new_cycle"]
            rolled = result.get("rolled_tasks", 0)
            info(f"Created new cycle: {new_cycle.name}")
            info(f"Rolled over {rolled} incomplete tasks")
    else:
        error(result)
        raise typer.Exit(1)


# ============================================================================
# RECURRENCE COMMANDS
# ============================================================================

@recur_app.command("list")
def recur_list():
    """List all recurring tasks.

    Shows all tasks with active recurrence rules, their patterns,
    and next scheduled occurrence dates.
    """
    from rich.table import Table

    db = get_db()
    rm = RecurrenceManager()

    recurring_tasks = db.list_recurring_tasks()

    if not recurring_tasks:
        info("No recurring tasks found")
        return

    table = Table(title="Recurring Tasks", show_header=True)
    table.add_column("ID", style="dim", width=4)
    table.add_column("Task", no_wrap=False)
    table.add_column("Pattern", style="cyan")
    table.add_column("Next Due", style="yellow")
    table.add_column("Created", style="dim", justify="right")

    for todo, rule in recurring_tasks:
        pattern_str = rm.format_pattern(rule)

        # Calculate next occurrence
        from datetime import date
        base_date = todo.due_date.date() if todo.due_date else date.today()
        next_date = rm.get_next_occurrence(rule, base_date)
        next_str = next_date.strftime('%Y-%m-%d') if next_date else "ended"

        created_str = f"{rule.occurrences_created}"
        if rule.max_occurrences:
            created_str += f"/{rule.max_occurrences}"

        table.add_row(
            str(todo.id),
            todo.task[:40] + ("..." if len(todo.task) > 40 else ""),
            pattern_str,
            next_str,
            created_str,
        )

    console.print(table)


@recur_app.command("show")
def recur_show(
    task_id: int = typer.Argument(..., help="ID of the recurring task"),
):
    """Show detailed recurrence information for a task."""
    from rich.panel import Panel
    from datetime import date

    db = get_db()
    rm = RecurrenceManager()

    todo = db.get(task_id)
    if not todo:
        error(f"Task #{task_id} not found")
        raise typer.Exit(1)

    rule = db.get_recurrence_rule_by_task(task_id)
    if not rule:
        error(f"Task #{task_id} has no recurrence rule")
        raise typer.Exit(1)

    # Build detail display
    lines = []
    lines.append(f"[bold]Task #{task_id}:[/bold] {todo.task}")
    lines.append("")
    lines.append(f"[bold]Pattern:[/bold] {rm.format_pattern(rule)}")
    lines.append(f"[bold]Interval:[/bold] {rule.interval}")

    if rule.days_of_week:
        lines.append(f"[bold]Days:[/bold] {', '.join(rule.days_of_week)}")

    if rule.day_of_month:
        lines.append(f"[bold]Day of Month:[/bold] {rule.day_of_month}")

    lines.append(f"[bold]Occurrences Created:[/bold] {rule.occurrences_created}")

    if rule.max_occurrences:
        lines.append(f"[bold]Max Occurrences:[/bold] {rule.max_occurrences}")

    if rule.end_date:
        lines.append(f"[bold]End Date:[/bold] {rule.end_date.strftime('%Y-%m-%d')}")

    # Calculate next occurrence
    base_date = todo.due_date.date() if todo.due_date else date.today()
    next_date = rm.get_next_occurrence(rule, base_date)
    if next_date:
        lines.append(f"[bold]Next Due:[/bold] [yellow]{next_date.strftime('%Y-%m-%d')}[/yellow]")
    else:
        lines.append(f"[bold]Status:[/bold] [dim]Recurrence ended[/dim]")

    panel = Panel(
        "\n".join(lines),
        title="Recurrence Details",
        border_style="cyan",
    )
    console.print(panel)


@recur_app.command("generate")
def recur_generate(
    task_id: Optional[int] = typer.Argument(None, help="ID of the recurring task (optional, generates for all if omitted)"),
):
    """Manually generate the next occurrence of a recurring task.

    If no task ID is provided, generates next occurrences for all
    recurring tasks that are ready for a new occurrence.

    Examples:
        todo recur generate 5     # Generate next for task #5
        todo recur generate       # Generate for all eligible tasks
    """
    db = get_db()
    rm = RecurrenceManager()

    if task_id:
        # Generate for specific task
        todo = db.get(task_id)
        if not todo:
            error(f"Task #{task_id} not found")
            raise typer.Exit(1)

        rule = db.get_recurrence_rule_by_task(task_id)
        if not rule:
            error(f"Task #{task_id} has no recurrence rule")
            raise typer.Exit(1)

        next_task = rm.create_occurrence(db, task_id)
        if next_task:
            due_str = next_task.due_date.strftime('%Y-%m-%d') if next_task.due_date else "no due date"
            success(f"Created occurrence #{next_task.id} (due: {due_str})")
        elif rule.has_reached_limit:
            warning(f"Recurrence limit reached ({rule.max_occurrences} occurrences)")
        elif rule.has_expired:
            warning(f"Recurrence ended (end date: {rule.end_date.strftime('%Y-%m-%d')})")
        else:
            warning("Could not create occurrence")
    else:
        # Generate for all eligible recurring tasks
        recurring_tasks = db.list_recurring_tasks()
        if not recurring_tasks:
            info("No recurring tasks found")
            return

        created_count = 0
        for todo, rule in recurring_tasks:
            if rm.should_create_occurrence(rule):
                next_task = rm.create_occurrence(db, todo.id)
                if next_task:
                    due_str = next_task.due_date.strftime('%Y-%m-%d') if next_task.due_date else "no due date"
                    success(f"#{todo.id} → #{next_task.id} (due: {due_str})")
                    created_count += 1

        if created_count == 0:
            info("No occurrences generated (all limits reached or no eligible tasks)")
        else:
            success(f"Generated {created_count} occurrence(s)")


@recur_app.command("stop")
def recur_stop(
    task_id: int = typer.Argument(..., help="ID of the recurring task to stop"),
):
    """Stop future occurrences for a recurring task.

    This deactivates the recurrence rule but keeps the task and
    any previously created occurrences.
    """
    db = get_db()

    todo = db.get(task_id)
    if not todo:
        error(f"Task #{task_id} not found")
        raise typer.Exit(1)

    rule = db.get_recurrence_rule_by_task(task_id)
    if not rule:
        error(f"Task #{task_id} has no recurrence rule")
        raise typer.Exit(1)

    # Delete the recurrence rule
    if db.delete_recurrence_rule(rule.id):
        success(f"Stopped recurrence for task #{task_id}")
        info("Existing occurrences are preserved")
    else:
        error("Failed to stop recurrence")
        raise typer.Exit(1)


@recur_app.command("edit")
def recur_edit(
    task_id: int = typer.Argument(..., help="ID of the recurring task to edit"),
    pattern: Optional[str] = typer.Option(None, "--pattern", "-p", help="New pattern (daily, weekly, monthly, yearly, or custom)"),
    interval: Optional[int] = typer.Option(None, "--interval", "-i", help="New interval (e.g., every N days)"),
    days: Optional[str] = typer.Option(None, "--days", "-d", help="Days of week for custom pattern (e.g., 'mon,wed,fri')"),
    until: Optional[str] = typer.Option(None, "--until", help="End date in YYYY-MM-DD format"),
    max_occurrences: Optional[int] = typer.Option(None, "--max", help="Maximum number of occurrences"),
    clear_end: bool = typer.Option(False, "--clear-end", help="Remove the end date limit"),
    clear_max: bool = typer.Option(False, "--clear-max", help="Remove the max occurrences limit"),
):
    """Edit a recurrence pattern for a task.

    Examples:
        todo recur edit 5 --interval 2       # Change to every 2 units
        todo recur edit 5 --pattern weekly   # Change to weekly
        todo recur edit 5 --days mon,fri     # Change specific days
        todo recur edit 5 --until 2025-06-01 # Set end date
        todo recur edit 5 --clear-end        # Remove end date
    """
    from .recurrence import RecurrenceManager, DAY_NAMES, SHORT_DAY_NAMES
    from .models import RecurrencePattern

    db = get_db()
    rm = RecurrenceManager()

    todo = db.get(task_id)
    if not todo:
        error(f"Task #{task_id} not found")
        raise typer.Exit(1)

    rule = db.get_recurrence_rule_by_task(task_id)
    if not rule:
        error(f"Task #{task_id} has no recurrence rule")
        raise typer.Exit(1)

    # Track if any changes were made
    changes = []

    # Update pattern if specified
    if pattern:
        pattern_lower = pattern.lower()
        pattern_map = {
            "daily": RecurrencePattern.DAILY,
            "weekly": RecurrencePattern.WEEKLY,
            "monthly": RecurrencePattern.MONTHLY,
            "yearly": RecurrencePattern.YEARLY,
            "custom": RecurrencePattern.CUSTOM,
        }
        if pattern_lower not in pattern_map:
            error(f"Invalid pattern: {pattern}. Use: daily, weekly, monthly, yearly, custom")
            raise typer.Exit(1)
        rule.pattern = pattern_map[pattern_lower]
        changes.append(f"pattern={pattern_lower}")

    # Update interval if specified
    if interval is not None:
        if interval < 1:
            error("Interval must be at least 1")
            raise typer.Exit(1)
        rule.interval = interval
        changes.append(f"interval={interval}")

    # Update days_of_week if specified
    if days:
        day_list = [d.strip().lower() for d in days.split(",")]
        parsed_days = []
        for day in day_list:
            if day not in DAY_NAMES:
                error(f"Invalid day: {day}. Use: mon, tue, wed, thu, fri, sat, sun")
                raise typer.Exit(1)
            parsed_days.append(SHORT_DAY_NAMES[DAY_NAMES[day]])
        rule.days_of_week = sorted(set(parsed_days), key=lambda d: DAY_NAMES[d])
        rule.pattern = RecurrencePattern.CUSTOM  # Auto-set to custom
        changes.append(f"days={','.join(rule.days_of_week)}")

    # Update end_date if specified
    if until:
        try:
            end_date = parse_date(until)
            rule.end_date = end_date
            changes.append(f"until={end_date.strftime('%Y-%m-%d')}")
        except ValueError:
            error(f"Invalid date format: {until}. Use YYYY-MM-DD")
            raise typer.Exit(1)

    # Clear end date if requested
    if clear_end:
        rule.end_date = None
        changes.append("end_date=none")

    # Update max_occurrences if specified
    if max_occurrences is not None:
        if max_occurrences < 1:
            error("Max occurrences must be at least 1")
            raise typer.Exit(1)
        rule.max_occurrences = max_occurrences
        changes.append(f"max={max_occurrences}")

    # Clear max occurrences if requested
    if clear_max:
        rule.max_occurrences = None
        changes.append("max_occurrences=none")

    if not changes:
        info("No changes specified")
        return

    # Save the updated rule
    db.update_recurrence_rule(rule)

    success(f"Updated recurrence for task #{task_id}")
    info(f"Changes: {', '.join(changes)}")
    info(f"New pattern: {rm.format_pattern(rule)}")


@recur_app.command("delete")
def recur_delete(
    task_id: int = typer.Argument(..., help="ID of the recurring task"),
):
    """Delete a recurrence rule (alias for 'stop').

    The task and any previously created occurrences are preserved.
    Only the recurrence rule is removed.
    """
    db = get_db()

    todo = db.get(task_id)
    if not todo:
        error(f"Task #{task_id} not found")
        raise typer.Exit(1)

    rule = db.get_recurrence_rule_by_task(task_id)
    if not rule:
        error(f"Task #{task_id} has no recurrence rule")
        raise typer.Exit(1)

    if db.delete_recurrence_rule(rule.id):
        success(f"Deleted recurrence rule for task #{task_id}")
        info("Task and existing occurrences are preserved")
    else:
        error("Failed to delete recurrence rule")
        raise typer.Exit(1)


# ============================================================================
# MAIN CALLBACK
# ============================================================================

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Todo CLI - A command-line todo manager with time tracking."""
    # Load config and display any warnings
    get_config()
    for warn in get_config_warnings():
        warning(warn)


if __name__ == "__main__":
    app()
