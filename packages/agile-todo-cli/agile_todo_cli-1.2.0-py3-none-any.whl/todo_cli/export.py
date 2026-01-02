"""Export functionality for Todo CLI."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console

from .database import Database
from .models import Todo, Status


console = Console()


def todo_to_dict(todo: Todo) -> dict:
    """Convert Todo to dictionary for export."""
    return {
        "id": todo.id,
        "task": todo.task,
        "priority": str(todo.priority),
        "status": todo.status.value,
        "project": todo.project,
        "tags": todo.tags,
        "due_date": todo.due_date.isoformat() if todo.due_date else None,
        "created_at": todo.created_at.isoformat(),
        "completed_at": todo.completed_at.isoformat() if todo.completed_at else None,
        "time_spent_seconds": int(todo.time_spent.total_seconds()),
        "time_spent_formatted": todo.format_time(),
        "is_tracking": todo.is_tracking,
        "is_overdue": todo.is_overdue,
    }


def export_json(
    db: Database,
    output_path: Optional[Path] = None,
    include_done: bool = True,
    project: Optional[str] = None,
) -> Path:
    """Export todos to JSON file."""
    todos = db.list_all(include_done=include_done, project=project)

    data = {
        "exported_at": datetime.now().isoformat(),
        "total_count": len(todos),
        "todos": [todo_to_dict(t) for t in todos],
    }

    if output_path is None:
        output_path = Path.cwd() / f"todos-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    return output_path


def export_csv(
    db: Database,
    output_path: Optional[Path] = None,
    include_done: bool = True,
    project: Optional[str] = None,
) -> Path:
    """Export todos to CSV file."""
    todos = db.list_all(include_done=include_done, project=project)

    if output_path is None:
        output_path = Path.cwd() / f"todos-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"

    headers = [
        "ID",
        "Task",
        "Priority",
        "Status",
        "Project",
        "Tags",
        "Due Date",
        "Created At",
        "Completed At",
        "Time Spent",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for todo in todos:
            writer.writerow([
                todo.id,
                todo.task,
                str(todo.priority),
                todo.status.value,
                todo.project or "",
                ", ".join(todo.tags),
                todo.due_date.strftime("%Y-%m-%d") if todo.due_date else "",
                todo.created_at.strftime("%Y-%m-%d %H:%M"),
                todo.completed_at.strftime("%Y-%m-%d %H:%M") if todo.completed_at else "",
                todo.format_time(),
            ])

    return output_path


def export_markdown(
    db: Database,
    output_path: Optional[Path] = None,
    include_done: bool = True,
    project: Optional[str] = None,
) -> Path:
    """Export todos to Markdown file."""
    todos = db.list_all(include_done=include_done, project=project)
    stats = db.get_stats()

    if output_path is None:
        output_path = Path.cwd() / f"todos-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"

    lines = [
        "# Todo Export",
        "",
        f"*Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "## Summary",
        "",
        f"- **Total:** {stats['total']}",
        f"- **Todo:** {stats['todo']}",
        f"- **In Progress:** {stats['doing']}",
        f"- **Done:** {stats['done']}",
        "",
        "## Tasks",
        "",
    ]

    # Group by project
    projects: dict[str, list[Todo]] = {}
    for todo in todos:
        proj = todo.project or "(No Project)"
        if proj not in projects:
            projects[proj] = []
        projects[proj].append(todo)

    for proj_name in sorted(projects.keys()):
        proj_todos = projects[proj_name]
        lines.append(f"### {proj_name}")
        lines.append("")

        for todo in proj_todos:
            checkbox = "x" if todo.status == Status.DONE else " "
            priority = str(todo.priority)
            time = todo.format_time()

            line = f"- [{checkbox}] **{priority}** {todo.task}"

            if todo.tags:
                line += f" `{', '.join(todo.tags)}`"

            if todo.due_date:
                due_str = todo.due_date.strftime("%Y-%m-%d")
                if todo.is_overdue:
                    line += f" ⚠️ **DUE: {due_str}**"
                else:
                    line += f" (due: {due_str})"

            if todo.time_spent.total_seconds() > 0:
                line += f" [{time}]"

            lines.append(line)

        lines.append("")

    # Time tracking summary
    if stats["total_time_seconds"] > 0:
        hours, remainder = divmod(stats["total_time_seconds"], 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

        lines.extend([
            "## Time Tracking",
            "",
            f"**Total time tracked:** {time_str}",
            "",
        ])

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return output_path


def export_todos(
    db: Database,
    format: str,
    output_path: Optional[Path] = None,
    include_done: bool = True,
    project: Optional[str] = None,
) -> Path:
    """Export todos to specified format."""
    format = format.lower()

    if format == "json":
        return export_json(db, output_path, include_done, project)
    elif format == "csv":
        return export_csv(db, output_path, include_done, project)
    elif format in ("md", "markdown"):
        return export_markdown(db, output_path, include_done, project)
    else:
        raise ValueError(f"Unsupported format: {format}. Use: json, csv, md")
