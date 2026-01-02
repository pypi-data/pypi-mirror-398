"""Interactive menu interface for Todo CLI."""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt

from .database import Database
from .display import display_todos, display_todo_detail, display_stats, success, error, info
from .models import Priority, Status
from .reports import daily_report, weekly_report, project_report
from .export import export_todos


console = Console()


MENU_OPTIONS = """
[bold cyan]Commands:[/bold cyan]
  [green]a[/green]dd      Add new todo
  [green]l[/green]ist     List todos
  [green]s[/green]how     Show todo details
  [green]d[/green]one     Mark todo done
  [green]del[/green]ete   Delete todo
  [green]st[/green]art    Start time tracking
  [green]sto[/green]p     Stop time tracking
  [green]e[/green]dit     Edit todo
  [green]r[/green]eport   Time reports
  [green]ex[/green]port   Export todos
  [green]stat[/green]s    Show statistics
  [green]p[/green]rojects List projects
  [green]q[/green]uit     Exit
"""


def parse_priority(priority: str) -> Priority:
    """Parse priority string to Priority enum."""
    priority_map = {
        "p0": Priority.P0, "0": Priority.P0,
        "p1": Priority.P1, "1": Priority.P1,
        "p2": Priority.P2, "2": Priority.P2,
        "p3": Priority.P3, "3": Priority.P3,
    }
    return priority_map.get(priority.lower(), Priority.P2)


def interactive_add(db: Database):
    """Interactive add todo."""
    console.print("\n[bold]Add New Todo[/bold]\n")

    task = Prompt.ask("Task description")
    if not task.strip():
        error("Task cannot be empty")
        return

    priority_str = Prompt.ask("Priority", default="p2", choices=["p0", "p1", "p2", "p3"])
    priority = parse_priority(priority_str)

    project = Prompt.ask("Project (optional)", default="")
    project = project.strip() if project.strip() else None

    tags_str = Prompt.ask("Tags (comma-separated, optional)", default="")
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]

    due_str = Prompt.ask("Due date YYYY-MM-DD (optional)", default="")
    due_date = None
    if due_str:
        from datetime import datetime
        try:
            due_date = datetime.strptime(due_str, "%Y-%m-%d")
        except ValueError:
            error("Invalid date format, skipping due date")

    todo = db.add(task=task, priority=priority, project=project, tags=tags, due_date=due_date)
    success(f"Added todo #{todo.id}: {task}")


def interactive_list(db: Database):
    """Interactive list todos."""
    console.print("\n[bold]List Todos[/bold]\n")

    include_done = Confirm.ask("Include completed?", default=False)
    project = Prompt.ask("Filter by project (optional)", default="")
    project = project.strip() if project.strip() else None

    todos = db.list_all(include_done=include_done, project=project)
    display_todos(todos)


def interactive_show(db: Database):
    """Interactive show todo details."""
    todo_id = IntPrompt.ask("Todo ID")
    todo = db.get(todo_id)

    if not todo:
        error(f"Todo #{todo_id} not found")
        return

    display_todo_detail(todo)


def interactive_done(db: Database):
    """Interactive mark todo done."""
    todo_id = IntPrompt.ask("Todo ID to mark done")
    todo = db.mark_done(todo_id)

    if not todo:
        error(f"Todo #{todo_id} not found")
        return

    success(f"Completed todo #{todo_id}: {todo.task}")
    if todo.time_spent.total_seconds() > 0:
        info(f"Total time spent: {todo.format_time()}")


def interactive_delete(db: Database):
    """Interactive delete todo."""
    todo_id = IntPrompt.ask("Todo ID to delete")
    todo = db.get(todo_id)

    if not todo:
        error(f"Todo #{todo_id} not found")
        return

    if Confirm.ask(f"Delete todo #{todo_id}: '{todo.task}'?"):
        db.delete(todo_id)
        success(f"Deleted todo #{todo_id}")
    else:
        info("Cancelled")


def interactive_start(db: Database):
    """Interactive start time tracking."""
    # Check for active timer
    active = db.get_active_timer()
    if active:
        console.print(f"[yellow]Currently tracking: #{active.id} {active.task}[/yellow]")
        if not Confirm.ask("Stop current timer and start new one?"):
            return
        db.stop_timer(active.id)

    todo_id = IntPrompt.ask("Todo ID to start tracking")
    todo = db.start_timer(todo_id)

    if not todo:
        error(f"Todo #{todo_id} not found")
        return

    success(f"Started tracking todo #{todo_id}: {todo.task}")


def interactive_stop(db: Database):
    """Interactive stop time tracking."""
    active = db.get_active_timer()

    if not active:
        info("No active timer")
        return

    console.print(f"[cyan]Active timer: #{active.id} {active.task}[/cyan]")

    if Confirm.ask("Stop this timer?", default=True):
        todo = db.stop_timer(active.id)
        success(f"Stopped tracking todo #{todo.id}")
        info(f"Time spent: {todo.format_time()}")


def interactive_edit(db: Database):
    """Interactive edit todo."""
    todo_id = IntPrompt.ask("Todo ID to edit")
    todo = db.get(todo_id)

    if not todo:
        error(f"Todo #{todo_id} not found")
        return

    display_todo_detail(todo)
    console.print("\n[dim]Press Enter to keep current value[/dim]\n")

    new_task = Prompt.ask("Task", default=todo.task)
    new_priority = Prompt.ask("Priority", default=str(todo.priority).lower(), choices=["p0", "p1", "p2", "p3"])
    new_project = Prompt.ask("Project", default=todo.project or "")
    new_tags = Prompt.ask("Tags", default=", ".join(todo.tags))
    new_status = Prompt.ask("Status", default=todo.status.value, choices=["todo", "doing", "done"])

    todo.task = new_task
    todo.priority = parse_priority(new_priority)
    todo.project = new_project.strip() if new_project.strip() else None
    todo.tags = [t.strip() for t in new_tags.split(",") if t.strip()]

    status_map = {"todo": Status.TODO, "doing": Status.DOING, "done": Status.DONE}
    todo.status = status_map[new_status]

    db.update(todo)
    success(f"Updated todo #{todo_id}")


def interactive_report(db: Database):
    """Interactive time reports."""
    console.print("\n[bold]Time Reports[/bold]\n")

    report_type = Prompt.ask("Report type", choices=["daily", "weekly", "project"])

    if report_type == "daily":
        daily_report(db)
    elif report_type == "weekly":
        weekly_report(db)
    elif report_type == "project":
        project = Prompt.ask("Project name (blank for all)", default="")
        project_report(db, project.strip() if project.strip() else None)


def interactive_export(db: Database):
    """Interactive export todos."""
    console.print("\n[bold]Export Todos[/bold]\n")

    format = Prompt.ask("Format", choices=["json", "csv", "md"])
    include_done = Confirm.ask("Include completed?", default=True)

    from pathlib import Path
    output_path = export_todos(db, format, include_done=include_done)
    success(f"Exported to: {output_path}")


def interactive_projects(db: Database):
    """Interactive list projects."""
    projects = db.get_projects()

    if not projects:
        info("No projects found")
        return

    console.print("\n[bold]Projects:[/bold]")
    for p in projects:
        console.print(f"  • {p}")


def run_interactive():
    """Run interactive menu loop."""
    db = Database()

    console.print(Panel("[bold]Todo CLI[/bold]\nTime tracking todo manager", border_style="cyan"))

    # Show current todos on start
    todos = db.list_all()
    if todos:
        display_todos(todos, title="Current Todos")
    else:
        info("No todos yet. Add one with 'a' or 'add'")

    console.print(MENU_OPTIONS)

    while True:
        try:
            console.print()
            cmd = Prompt.ask("[bold cyan]>[/bold cyan]").strip().lower()

            if not cmd:
                continue

            if cmd in ("q", "quit", "exit"):
                # Stop any active timer before exiting
                active = db.get_active_timer()
                if active:
                    console.print(f"[yellow]Active timer on: #{active.id} {active.task}[/yellow]")
                    if Confirm.ask("Stop timer before exiting?", default=True):
                        db.stop_timer(active.id)
                        info(f"Timer stopped. Time: {active.format_time()}")
                console.print("[dim]Goodbye![/dim]")
                break

            elif cmd in ("a", "add"):
                interactive_add(db)

            elif cmd in ("l", "list", "ls"):
                interactive_list(db)

            elif cmd in ("s", "show", "view"):
                interactive_show(db)

            elif cmd in ("d", "done", "complete"):
                interactive_done(db)

            elif cmd in ("del", "delete", "rm"):
                interactive_delete(db)

            elif cmd in ("st", "start"):
                interactive_start(db)

            elif cmd in ("sto", "stop"):
                interactive_stop(db)

            elif cmd in ("e", "edit"):
                interactive_edit(db)

            elif cmd in ("r", "report", "reports"):
                interactive_report(db)

            elif cmd in ("ex", "export"):
                interactive_export(db)

            elif cmd in ("stat", "stats", "statistics"):
                display_stats(db.get_stats())

            elif cmd in ("p", "projects", "proj"):
                interactive_projects(db)

            elif cmd in ("?", "h", "help"):
                console.print(MENU_OPTIONS)

            elif cmd == "active":
                active = db.get_active_timer()
                if active:
                    display_todo_detail(active)
                else:
                    info("No active timer")

            else:
                error(f"Unknown command: {cmd}")
                console.print("[dim]Type '?' for help[/dim]")

        except KeyboardInterrupt:
            console.print("\n[dim]Use 'q' to quit[/dim]")
        except Exception as e:
            error(f"Error: {e}")


if __name__ == "__main__":
    run_interactive()
