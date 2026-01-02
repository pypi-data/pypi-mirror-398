"""KANBAN board visualization and column management for Todo CLI."""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.text import Text

from .config import get_config


class KanbanColumn(Enum):
    """Valid KANBAN columns."""
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in-progress"
    REVIEW = "review"
    DONE = "done"

    @classmethod
    def from_string(cls, value: str) -> Optional["KanbanColumn"]:
        """Convert string to KanbanColumn, handling aliases."""
        aliases = {
            "backlog": cls.BACKLOG,
            "todo": cls.TODO,
            "in-progress": cls.IN_PROGRESS,
            "inprogress": cls.IN_PROGRESS,
            "in_progress": cls.IN_PROGRESS,
            "progress": cls.IN_PROGRESS,
            "doing": cls.IN_PROGRESS,
            "review": cls.REVIEW,
            "done": cls.DONE,
            "complete": cls.DONE,
            "completed": cls.DONE,
        }
        return aliases.get(value.lower().strip())

    @property
    def display_name(self) -> str:
        """Get human-readable display name."""
        names = {
            KanbanColumn.BACKLOG: "Backlog",
            KanbanColumn.TODO: "Todo",
            KanbanColumn.IN_PROGRESS: "In Progress",
            KanbanColumn.REVIEW: "Review",
            KanbanColumn.DONE: "Done",
        }
        return names[self]

    @property
    def color(self) -> str:
        """Get column color for Rich styling."""
        colors = {
            KanbanColumn.BACKLOG: "dim",
            KanbanColumn.TODO: "blue",
            KanbanColumn.IN_PROGRESS: "yellow",
            KanbanColumn.REVIEW: "magenta",
            KanbanColumn.DONE: "green",
        }
        return colors[self]


@dataclass
class KanbanTask:
    """A task as displayed on the KANBAN board."""
    id: int
    task: str
    priority: int
    status: str
    kanban_column: str
    project_id: Optional[int]
    project_name: Optional[str]
    project_color: Optional[str]
    due_date: Optional[str]
    tags: str
    subtask_count: int
    completed_subtasks: int

    @property
    def priority_icon(self) -> str:
        """Get priority icon."""
        icons = {0: "🔴", 1: "🟡", 2: "🔵", 3: "⚪"}
        return icons.get(self.priority, "⚪")

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.due_date:
            try:
                due = datetime.fromisoformat(self.due_date)
                return datetime.now() > due
            except ValueError:
                return False
        return False


class KanbanManager:
    """Manages KANBAN board operations."""

    VALID_COLUMNS = [col.value for col in KanbanColumn]

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize KANBAN manager.

        Args:
            db_path: Path to database file
        """
        if db_path is None:
            db_path = get_config().get_db_path()
        self.db_path = db_path

    @contextmanager
    def _get_conn(self):
        """Get database connection as context manager."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get_board(self, project_id: Optional[int] = None,
                  priority: Optional[int] = None,
                  tags: Optional[list[str]] = None,
                  include_done: bool = False) -> dict[str, list[KanbanTask]]:
        """Get KANBAN board grouped by columns.

        Args:
            project_id: Filter by project ID
            priority: Filter by priority (0-3)
            tags: Filter by tags (any match)
            include_done: Include done column

        Returns:
            Dict mapping column names to lists of KanbanTask
        """
        query = """
            SELECT
                t.id,
                t.task,
                t.priority,
                t.status,
                COALESCE(t.kanban_column, 'backlog') as kanban_column,
                t.project_id,
                p.name as project_name,
                p.color as project_color,
                t.due_date,
                t.tags,
                (SELECT COUNT(*) FROM subtasks WHERE parent_task_id = t.id) as subtask_count,
                (SELECT COUNT(*) FROM subtasks s
                 JOIN todos st ON s.child_task_id = st.id
                 WHERE s.parent_task_id = t.id AND st.status = 'done') as completed_subtasks
            FROM todos t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE 1=1
        """
        params = []

        if not include_done:
            query += " AND t.status != 'done'"

        if project_id is not None:
            query += " AND t.project_id = ?"
            params.append(project_id)

        if priority is not None:
            query += " AND t.priority = ?"
            params.append(priority)

        if tags:
            # Filter by any matching tag
            tag_conditions = []
            for tag in tags:
                tag_conditions.append("t.tags LIKE ?")
                params.append(f"%{tag}%")
            query += f" AND ({' OR '.join(tag_conditions)})"

        query += """
            ORDER BY
                CASE t.kanban_column
                    WHEN 'backlog' THEN 1
                    WHEN 'todo' THEN 2
                    WHEN 'in-progress' THEN 3
                    WHEN 'review' THEN 4
                    WHEN 'done' THEN 5
                    ELSE 6
                END,
                t.priority ASC,
                t.created_at ASC
        """

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()

        # Group by column
        board = {col.value: [] for col in KanbanColumn}
        if not include_done:
            del board[KanbanColumn.DONE.value]

        for row in rows:
            task = KanbanTask(
                id=row["id"],
                task=row["task"],
                priority=row["priority"],
                status=row["status"],
                kanban_column=row["kanban_column"] or "backlog",
                project_id=row["project_id"],
                project_name=row["project_name"],
                project_color=row["project_color"],
                due_date=row["due_date"],
                tags=row["tags"],
                subtask_count=row["subtask_count"],
                completed_subtasks=row["completed_subtasks"],
            )
            column = task.kanban_column
            if column in board:
                board[column].append(task)

        return board

    def move_task(self, task_id: int, target_column: str) -> tuple[bool, str]:
        """Move a task to a different KANBAN column.

        Args:
            task_id: ID of task to move
            target_column: Target column name or alias

        Returns:
            Tuple of (success, message)
        """
        # Parse column
        column = KanbanColumn.from_string(target_column)
        if column is None:
            valid = ", ".join(self.VALID_COLUMNS)
            return False, f"Invalid column '{target_column}'. Valid columns: {valid}"

        with self._get_conn() as conn:
            # Check task exists
            row = conn.execute(
                "SELECT id, task, kanban_column, status FROM todos WHERE id = ?",
                (task_id,)
            ).fetchone()

            if not row:
                return False, f"Task #{task_id} not found"

            old_column = row["kanban_column"] or "backlog"
            task_name = row["task"]

            # Update column
            conn.execute(
                "UPDATE todos SET kanban_column = ? WHERE id = ?",
                (column.value, task_id)
            )

            # Auto-complete if moved to done
            if column == KanbanColumn.DONE and row["status"] != "done":
                conn.execute(
                    "UPDATE todos SET status = 'done', completed_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), task_id)
                )
                conn.commit()
                return True, f"Moved #{task_id} '{task_name}' from {old_column} to {column.value} (auto-completed)"

            # Set status to 'doing' if moved to in-progress
            if column == KanbanColumn.IN_PROGRESS and row["status"] == "todo":
                conn.execute(
                    "UPDATE todos SET status = 'doing' WHERE id = ?",
                    (task_id,)
                )

            conn.commit()
            return True, f"Moved #{task_id} '{task_name}' from {old_column} to {column.value}"

    def get_task_column(self, task_id: int) -> Optional[str]:
        """Get the current column for a task.

        Args:
            task_id: Task ID

        Returns:
            Column name or None if not found
        """
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT kanban_column FROM todos WHERE id = ?",
                (task_id,)
            ).fetchone()
            return row["kanban_column"] if row else None

    def get_column_counts(self) -> dict[str, int]:
        """Get task count per column.

        Returns:
            Dict mapping column names to counts
        """
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT COALESCE(kanban_column, 'backlog') as col, COUNT(*) as cnt
                FROM todos
                WHERE status != 'done'
                GROUP BY kanban_column
            """).fetchall()

        counts = {col.value: 0 for col in KanbanColumn if col != KanbanColumn.DONE}
        for row in rows:
            col = row["col"] or "backlog"
            if col in counts:
                counts[col] = row["cnt"]

        return counts


def display_kanban_board(
    board: dict[str, list[KanbanTask]],
    console: Optional[Console] = None,
    hide_empty: bool = True,
):
    """Display KANBAN board using Rich panels.

    Args:
        board: Dict mapping column names to lists of KanbanTask
        console: Optional Rich console
        hide_empty: Hide columns with no tasks (default True for more space)
    """
    if console is None:
        from .display import get_console
        console = get_console()

    # Calculate dynamic widths based on terminal size
    terminal_width = console.size.width

    # Filter columns: optionally hide empty ones to maximize space
    visible_columns = [
        c.value for c in KanbanColumn
        if c.value in board and (not hide_empty or board.get(c.value))
    ]
    num_columns = len(visible_columns)

    if num_columns == 0:
        console.print("[dim]No tasks to display.[/dim]")
        return

    # Calculate panel width: distribute terminal width across columns
    # Account for gaps between panels (2 chars each) and margins
    available_width = terminal_width - (num_columns - 1) * 2 - 2
    panel_width = max(28, available_width // num_columns)

    # Task text length: panel width minus icons, ID, padding, borders
    # Format: "🔴 #123 Task text (2/5)" = ~12 chars overhead
    max_task_len = max(15, panel_width - 12)

    panels = []

    for col_value in visible_columns:
        column = KanbanColumn(col_value)
        tasks = board.get(col_value, [])

        # Build task list content
        if tasks:
            lines = []
            for task in tasks:
                line = _format_task_line(task, max_task_len=max_task_len)
                lines.append(line)
            content = "\n".join(lines)
        else:
            content = "[dim]No tasks[/dim]"

        # Create panel for column
        panel = Panel(
            content,
            title=f"{column.display_name} ({len(tasks)})",
            border_style=column.color,
            width=panel_width,
            padding=(0, 1),
        )
        panels.append(panel)

    # Display as columns
    console.print(Columns(panels, equal=True, expand=True))


def _format_task_line(task: KanbanTask, max_task_len: int = 18) -> str:
    """Format a single task for KANBAN display.

    Args:
        task: KanbanTask to format
        max_task_len: Maximum length for task text before truncation

    Returns:
        Formatted string for Rich
    """
    parts = []

    # Overdue indicator (red !)
    if task.is_overdue:
        parts.append("[bold red]![/bold red]")

    # Priority icon
    parts.append(task.priority_icon)

    # Task ID
    parts.append(f"[dim]#{task.id}[/dim]")

    # Task name (truncated if needed)
    task_text = task.task
    if len(task_text) > max_task_len:
        task_text = task_text[:max_task_len-1] + "…"

    # Style based on status
    if task.is_overdue:
        task_text = f"[bold red]{task_text}[/bold red]"
    elif task.status == "doing":
        task_text = f"[bold yellow]{task_text}[/bold yellow]"

    parts.append(task_text)

    # Subtask indicator
    if task.subtask_count > 0:
        parts.append(f"[dim]({task.completed_subtasks}/{task.subtask_count})[/dim]")

    return " ".join(parts)


def display_kanban_compact(
    board: dict[str, list[KanbanTask]],
    console: Optional[Console] = None,
    hide_empty: bool = True,
):
    """Display KANBAN board in compact table format.

    Args:
        board: Dict mapping column names to lists of KanbanTask
        console: Optional Rich console
        hide_empty: Hide columns with no tasks (default True for more space)
    """
    if console is None:
        from .display import get_console
        console = get_console()

    # Calculate dynamic widths based on terminal size
    terminal_width = console.size.width

    # Filter columns: optionally hide empty ones to maximize space
    visible_columns = [
        c.value for c in KanbanColumn
        if c.value in board and (not hide_empty or board.get(c.value))
    ]
    num_columns = len(visible_columns)

    if num_columns == 0:
        console.print("[dim]No tasks to display.[/dim]")
        return

    # Calculate column width: distribute terminal width across columns
    # Account for table borders and padding (~3 chars per column)
    available_width = terminal_width - (num_columns * 3) - 4
    col_width = max(20, available_width // num_columns)

    # Task text length: column width minus icons and ID (~8 chars overhead)
    max_task_len = max(12, col_width - 8)

    table = Table(title="KANBAN Board", show_header=True, header_style="bold cyan")

    # Add columns with calculated width
    for col_value in visible_columns:
        column = KanbanColumn(col_value)
        tasks = board.get(col_value, [])
        table.add_column(
            f"{column.display_name} ({len(tasks)})",
            style=column.color,
            width=col_width,
            no_wrap=True,
        )

    # Find max rows needed
    max_rows = max(len(tasks) for tasks in board.values()) if board.values() else 0

    # Add rows
    for i in range(max_rows):
        row = []
        for col_value in visible_columns:
            tasks = board.get(col_value, [])
            if i < len(tasks):
                task = tasks[i]
                task_text = task.task
                if len(task_text) > max_task_len:
                    task_text = task_text[:max_task_len-1] + "…"
                cell = f"{task.priority_icon} #{task.id} {task_text}"
                row.append(cell)
            else:
                row.append("")
        table.add_row(*row)

    console.print(table)
