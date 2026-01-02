"""Rich display utilities for Todo CLI."""

from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.theme import Theme
from rich.tree import Tree

from .models import Todo, Priority, Status
from .config import get_config


def get_console() -> Console:
    """Get console configured based on color_scheme setting.

    When not running in an interactive terminal (e.g., in tests or CI),
    uses a fixed width to ensure consistent table rendering.
    """
    import sys
    config = get_config()
    scheme = config.color_scheme.lower()

    # Use fixed width when not in interactive terminal (tests, CI, pipes)
    # This ensures tables render properly with all columns visible
    width = None if sys.stdout.isatty() else 120

    if scheme == "none":
        return Console(no_color=True, width=width)
    elif scheme == "light":
        # Light theme with adjusted colors for light backgrounds
        light_theme = Theme({
            "info": "blue",
            "warning": "yellow",
            "error": "red",
            "success": "green",
            "dim": "bright_black",
        })
        return Console(theme=light_theme, width=width)
    elif scheme == "dark":
        # Dark theme (default Rich colors work well on dark backgrounds)
        return Console(width=width)
    else:  # auto
        return Console(width=width)




PRIORITY_COLORS = {
    Priority.P0: "bold red",
    Priority.P1: "yellow",
    Priority.P2: "blue",
    Priority.P3: "dim",
}

PRIORITY_ICONS = {
    Priority.P0: "🔴",
    Priority.P1: "🟡",
    Priority.P2: "🔵",
    Priority.P3: "⚪",
}

STATUS_ICONS = {
    Status.TODO: "○",
    Status.DOING: "◐",
    Status.DONE: "●",
}

# Tree view status icons (more visual for hierarchical display)
TREE_STATUS_ICONS = {
    Status.TODO: "⬜",
    Status.DOING: "🟡",
    Status.DONE: "✅",
}


def format_due_date(todo: Todo, show_relative: bool = True) -> Text:
    """Format due date with overdue highlighting.

    Args:
        todo: Todo object with due_date
        show_relative: If True, show relative dates (e.g., "2d overdue", "today", "tomorrow")
    """
    if not todo.due_date:
        return Text("-", style="dim")

    config = get_config()
    today = datetime.now().date()
    due_date = todo.due_date.date()

    if todo.is_overdue:
        # Show days overdue
        days_overdue = (today - due_date).days
        if show_relative:
            overdue_str = f"{days_overdue}d overdue"
            return Text(f"⚠️ {overdue_str}", style="bold red")
        else:
            date_str = todo.due_date.strftime(config.get_date_format_str())
            return Text(f"⚠️ {date_str}", style="bold red")

    # Check if due today
    if due_date == today:
        return Text("📅 today", style="yellow")

    # Check if due tomorrow
    tomorrow = today + timedelta(days=1)
    if due_date == tomorrow:
        return Text("tomorrow", style="cyan")

    # Otherwise show the date
    date_str = todo.due_date.strftime(config.get_date_format_str())
    return Text(date_str)


def display_todos(todos: list[Todo], title: str = "Todos", subtask_manager=None, show_overdue_warning: bool = True):
    """Display todos in a rich table.

    Args:
        todos: List of Todo objects to display
        title: Table title
        subtask_manager: Optional SubtaskManager for showing sub-task counts
        show_overdue_warning: Whether to show overdue task warning header
    """
    console = get_console()

    if not todos:
        console.print("[dim]No todos found.[/dim]")
        return

    # Count and display overdue tasks warning
    if show_overdue_warning:
        overdue_count = sum(1 for t in todos if t.is_overdue and t.status != Status.DONE)
        if overdue_count > 0:
            task_word = "task" if overdue_count == 1 else "tasks"
            console.print(f"[bold red]⚠️  {overdue_count} {task_word} overdue[/bold red]\n")

    # Get ProjectManager to resolve project_ids to names
    from .projects import ProjectManager
    from .database import Database
    pm = ProjectManager(get_config().get_db_path())
    db = Database(get_config().get_db_path())

    # Build set of recurring task IDs for efficient lookup
    recurring_task_ids = {todo.id for todo, rule in db.list_recurring_tasks()}

    table = Table(title=title, show_header=True, header_style="bold cyan")

    table.add_column("ID", style="dim", width=4)
    table.add_column("P", width=3)
    table.add_column("Status", width=6)
    table.add_column("Task", no_wrap=False, overflow="fold", min_width=20)
    table.add_column("Project", width=12)
    table.add_column("Tags", width=15)
    table.add_column("Time", width=10)
    table.add_column("Due", width=12)

    for todo in todos:
        priority_icon = PRIORITY_ICONS[todo.priority]
        status_icon = STATUS_ICONS[todo.status]

        # Style task based on status
        task_style = ""
        if todo.status == Status.DONE:
            task_style = "dim strike"
        elif todo.is_tracking:
            task_style = "bold green"

        # Format time with tracking indicator
        time_str = todo.format_time()
        if todo.is_tracking:
            time_str = f"⏱️ {time_str}"

        # Format tags
        tags_str = ", ".join(todo.tags) if todo.tags else "-"

        # Resolve project_id to project name (prefer project_id over legacy project string)
        project_name = "-"
        if todo.project_id:
            project_obj = pm.get_project(todo.project_id)
            if project_obj:
                project_name = project_obj.name
        elif todo.project:
            # Fallback to legacy project string for backwards compatibility
            project_name = todo.project

        # Build task text with optional indicators
        task_text = todo.task

        # Add recurrence indicator for recurring tasks
        if todo.id in recurring_task_ids:
            task_text = f"🔄 {task_text}"

        # Add sub-task count indicator
        if subtask_manager:
            child_count = subtask_manager.get_child_count(todo.id)
            if child_count > 0:
                suffix = "sub-task" if child_count == 1 else "sub-tasks"
                task_text = f"{task_text} ({child_count} {suffix})"

        table.add_row(
            str(todo.id),
            priority_icon,
            status_icon,
            Text(task_text, style=task_style) if task_style else Text(task_text),
            project_name,
            tags_str,
            time_str,
            format_due_date(todo),
        )

    console.print(table)


def display_todos_tree(todos: list[Todo], subtask_manager, title: str = "Todos"):
    """Display todos in a hierarchical tree view.

    Args:
        todos: List of Todo objects to display
        subtask_manager: SubtaskManager instance for hierarchy queries
        title: Tree title
    """
    if not todos:
        get_console().print("[dim]No todos found.[/dim]")
        return

    # Get ProjectManager to resolve project_ids to names
    from .projects import ProjectManager
    pm = ProjectManager(get_config().get_db_path())

    # Build lookup for quick access
    todo_by_id = {todo.id: todo for todo in todos}

    # Separate parents (top-level) and children
    parent_todos = []
    child_ids = set()
    orphaned_subtasks = []

    for todo in todos:
        if subtask_manager.is_subtask(todo.id):
            child_ids.add(todo.id)
            # Check if parent is in the filtered list
            parent_info = subtask_manager.get_parent(todo.id)
            if parent_info and parent_info['id'] not in todo_by_id:
                # Parent not in filtered list, show as orphan at root level
                orphaned_subtasks.append(todo)
        else:
            parent_todos.append(todo)

    tree = Tree(f"[bold cyan]{title}[/bold cyan]")

    def format_todo_line(todo: Todo, show_completion: bool = False) -> str:
        """Format a single todo for tree display."""
        status_icon = TREE_STATUS_ICONS[todo.status]
        priority_icon = PRIORITY_ICONS[todo.priority]

        # Style task based on status
        task_text = todo.task
        if todo.status == Status.DONE:
            task_text = f"[dim strike]{task_text}[/dim strike]"
        elif todo.is_tracking:
            task_text = f"[bold green]{task_text}[/bold green]"

        # Build the line
        line = f"{status_icon} {priority_icon} [dim]#{todo.id}[/dim] {task_text}"

        # Add completion status for parents with children
        if show_completion:
            completion = subtask_manager.get_children_completion_status(todo.id)
            if completion['total'] > 0:
                line += f" [dim]({completion['completed']}/{completion['total']})[/dim]"

        # Add project if set
        project_name = None
        if todo.project_id:
            project_obj = pm.get_project(todo.project_id)
            if project_obj:
                project_name = project_obj.name
        elif todo.project:
            project_name = todo.project

        if project_name:
            line += f" [dim]@{project_name}[/dim]"

        return line

    # Add parent todos to tree
    for parent in parent_todos:
        has_children = subtask_manager.has_children(parent.id)
        parent_line = format_todo_line(parent, show_completion=has_children)

        if has_children:
            # Create branch for parent with children
            branch = tree.add(parent_line)

            # Get and add children
            children = subtask_manager.get_children(parent.id)
            for child_info in children:
                child_id = child_info['id']
                if child_id in todo_by_id:
                    child_todo = todo_by_id[child_id]
                    child_line = format_todo_line(child_todo, show_completion=False)
                    branch.add(child_line)
        else:
            # Add leaf node (no children)
            tree.add(parent_line)

    # Add orphaned subtasks (children whose parents aren't in filtered list)
    for orphan in orphaned_subtasks:
        orphan_line = format_todo_line(orphan, show_completion=False)
        tree.add(orphan_line)

    get_console().print(tree)


def display_todo_detail(todo: Todo):
    """Display detailed view of a single todo."""
    config = get_config()
    date_fmt = config.get_date_format_str()
    time_fmt = config.get_time_format_str()
    datetime_fmt = f"{date_fmt} {time_fmt}"

    priority_color = PRIORITY_COLORS[todo.priority]
    priority_icon = PRIORITY_ICONS[todo.priority]

    # Resolve project_id to project name
    from .projects import ProjectManager
    from .database import Database
    from .recurrence import RecurrenceManager
    pm = ProjectManager(config.get_db_path())
    db = Database(config.get_db_path())
    project_name = 'None'
    if todo.project_id:
        project_obj = pm.get_project(todo.project_id)
        if project_obj:
            project_name = project_obj.name
    elif todo.project:
        project_name = todo.project

    # Get recurrence info if any
    recurrence_info = 'None'
    recurrence_rule = db.get_recurrence_rule_by_task(todo.id)
    if recurrence_rule:
        recurrence_mgr = RecurrenceManager()
        recurrence_info = f"🔄 {recurrence_mgr.format_pattern(recurrence_rule)}"
        if recurrence_rule.end_date:
            recurrence_info += f" (until {recurrence_rule.end_date.strftime(date_fmt)})"
        if recurrence_rule.max_occurrences:
            recurrence_info += f" ({recurrence_rule.occurrences_created}/{recurrence_rule.max_occurrences} created)"

    content = f"""
[bold]Task:[/bold] {todo.task}
[bold]Priority:[/bold] [{priority_color}]{priority_icon} {todo.priority}[/{priority_color}]
[bold]Status:[/bold] {STATUS_ICONS[todo.status]} {todo.status.value}
[bold]Project:[/bold] {project_name}
[bold]Tags:[/bold] {', '.join(todo.tags) if todo.tags else 'None'}
[bold]Due Date:[/bold] {todo.due_date.strftime(datetime_fmt) if todo.due_date else 'None'}
[bold]Recurrence:[/bold] {recurrence_info}
[bold]Created:[/bold] {todo.created_at.strftime(datetime_fmt)}
[bold]Completed:[/bold] {todo.completed_at.strftime(datetime_fmt) if todo.completed_at else 'Not completed'}
[bold]Time Spent:[/bold] {todo.format_time()}{'  ⏱️ Currently tracking' if todo.is_tracking else ''}
"""

    title = f"Todo #{todo.id}"
    if todo.is_overdue:
        title += " [bold red]OVERDUE[/bold red]"

    get_console().print(Panel(content.strip(), title=title, border_style="cyan"))


def display_stats(stats: dict):
    """Display todo statistics."""
    console = get_console()
    total_seconds = stats["total_time_seconds"]
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

    # Show overdue warning if any
    overdue = stats.get("overdue", 0)
    if overdue > 0:
        task_word = "task" if overdue == 1 else "tasks"
        console.print(f"[bold red]⚠️  {overdue} {task_word} overdue[/bold red]\n")

    table = Table(title="Statistics", show_header=False, box=None)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold")

    table.add_row("Total Todos", str(stats["total"]))
    table.add_row("  Todo", str(stats["todo"]))
    table.add_row("  In Progress", str(stats["doing"]))
    table.add_row("  Completed", str(stats["done"]))
    if overdue > 0:
        table.add_row("  Overdue", f"[bold red]{overdue}[/bold red]")
    table.add_row("Total Time Tracked", time_str)

    console.print(table)


def success(message: str):
    """Display success message."""
    get_console().print(f"[green]✓[/green] {message}")


def error(message: str):
    """Display error message."""
    get_console().print(f"[red]✗[/red] {message}")


def warning(message: str):
    """Display warning message."""
    get_console().print(f"[yellow]⚠[/yellow] {message}")


def info(message: str):
    """Display info message."""
    get_console().print(f"[blue]ℹ[/blue] {message}")


def display_projects(projects: list):
    """Display list of projects in a table.

    Args:
        projects: List of Project objects
    """
    console = get_console()

    table = Table(title="Projects", show_header=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="dim")
    table.add_column("Tasks", justify="right")
    table.add_column("Completed", justify="right")
    table.add_column("Progress", justify="right")

    for project in projects:
        # Calculate progress bar
        if project.total_tasks > 0:
            progress = project.completed_tasks / project.total_tasks
            bar_length = 10
            filled = int(progress * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            progress_text = f"{bar} {progress*100:.0f}%"
        else:
            progress_text = "No tasks"

        # Apply color if set
        name_text = f"[{project.color}]{project.name}[/{project.color}]" if project.color else project.name

        table.add_row(
            name_text,
            project.description or "",
            str(project.total_tasks),
            str(project.completed_tasks),
            progress_text
        )

    console.print(table)


def display_project_detail(stats: dict):
    """Display detailed project information.

    Args:
        stats: Dictionary with project statistics from ProjectManager.get_project_stats()
    """
    console = get_console()
    project = stats['project']

    # Create project header
    title = f"📁 {project.name}"
    if project.color:
        title = f"[{project.color}]{title}[/{project.color}]"

    # Build detail text
    details = []

    if project.description:
        details.append(f"[dim]{project.description}[/dim]\n")

    details.append(f"[bold]Statistics:[/bold]")
    details.append(f"  Total Tasks: {stats['total_tasks']}")
    details.append(f"  Completed: {stats['completed_tasks']}")
    details.append(f"  Active: {stats['active_tasks']}")

    if stats['total_tasks'] > 0:
        details.append(f"  Completion Rate: {stats['completion_rate']:.1f}%")

    if stats['total_time_seconds'] > 0:
        hours = stats['total_time_seconds'] / 3600
        details.append(f"  Time Spent: {hours:.1f}h")

    if stats['earliest_due_date']:
        due_date = stats['earliest_due_date']
        config = get_config()
        date_str = due_date.strftime(config.get_date_format())
        details.append(f"  Next Due Date: {date_str}")

    if stats['priority_breakdown']:
        details.append(f"\n[bold]Priority Breakdown:[/bold]")
        priority_names = {0: "P0 (Urgent)", 1: "P1 (High)", 2: "P2 (Normal)", 3: "P3 (Low)"}
        for priority, count in sorted(stats['priority_breakdown'].items()):
            priority_name = priority_names.get(priority, f"P{priority}")
            details.append(f"  {priority_name}: {count}")

    panel = Panel(
        "\n".join(details),
        title=title,
        border_style="cyan"
    )

    console.print(panel)
