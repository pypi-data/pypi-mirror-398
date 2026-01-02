"""Interactive KANBAN board TUI using Textual framework."""

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView, Static

from .config import get_config
from .kanban import KanbanColumn, KanbanManager, KanbanTask


class TaskItem(ListItem):
    """A task displayed in a KANBAN column."""

    def __init__(self, kanban_task: KanbanTask, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kanban_task = kanban_task

    def compose(self) -> ComposeResult:
        """Compose the task item."""
        priority_colors = {0: "red", 1: "yellow", 2: "blue", 3: "white"}
        color = priority_colors.get(self.kanban_task.priority, "white")

        # Build task display
        task_text = self.kanban_task.task
        if len(task_text) > 22:
            task_text = task_text[:21] + "..."

        # Status indicator
        status_indicator = ""
        if self.kanban_task.is_overdue:
            status_indicator = " [bold red]![/bold red]"
        elif self.kanban_task.status == "doing":
            status_indicator = " [yellow]*[/yellow]"

        # Subtask indicator
        subtask_indicator = ""
        if self.kanban_task.subtask_count > 0:
            subtask_indicator = f" [{self.kanban_task.completed_subtasks}/{self.kanban_task.subtask_count}]"

        yield Label(
            f"[{color}]{self.kanban_task.priority_icon}[/{color}] [dim]#{self.kanban_task.id}[/dim] {task_text}{status_indicator}{subtask_indicator}"
        )


class KanbanColumnWidget(Vertical):
    """A single KANBAN column widget."""

    DEFAULT_CSS = """
    KanbanColumnWidget {
        width: 1fr;
        border: solid $primary;
        padding: 0 1;
        margin: 0 1;
    }

    KanbanColumnWidget .column-header {
        text-align: center;
        text-style: bold;
        padding: 1 0;
        background: $surface;
    }

    KanbanColumnWidget ListView {
        height: 1fr;
        background: $surface-darken-1;
    }

    KanbanColumnWidget.focused {
        border: double $accent;
    }
    """

    def __init__(
        self,
        column: KanbanColumn,
        tasks: list[KanbanTask],
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.column = column
        self.tasks = tasks
        self.border_title = f"{column.display_name} ({len(tasks)})"

    def compose(self) -> ComposeResult:
        """Compose the column widget."""
        yield Label(
            f"[bold]{self.column.display_name}[/bold] ({len(self.tasks)})",
            classes="column-header",
        )

        list_view = ListView(*[TaskItem(task) for task in self.tasks], id=f"list-{self.column.value}")
        yield list_view

    def refresh_tasks(self, tasks: list[KanbanTask]):
        """Refresh the tasks in this column."""
        self.tasks = tasks
        self.border_title = f"{self.column.display_name} ({len(tasks)})"

        # Update header
        header = self.query_one(".column-header", Label)
        header.update(f"[bold]{self.column.display_name}[/bold] ({len(tasks)})")

        # Clear and repopulate list
        list_view = self.query_one(ListView)
        list_view.clear()
        for task in tasks:
            list_view.append(TaskItem(task))


class MoveTaskScreen(ModalScreen[Optional[str]]):
    """Modal screen for moving a task."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    MoveTaskScreen {
        align: center middle;
    }

    MoveTaskScreen > Vertical {
        width: 50;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    MoveTaskScreen Button {
        width: 100%;
        margin: 1 0;
    }
    """

    def __init__(self, task: KanbanTask):
        super().__init__()
        self.move_task = task

    @property
    def task(self) -> KanbanTask:
        """Alias for backward compatibility with tests."""
        return self.move_task

    def compose(self) -> ComposeResult:
        """Compose the modal."""
        with Vertical():
            yield Label(f"[bold]Move Task #{self.move_task.id}[/bold]")
            yield Label(f"{self.move_task.task[:40]}...", classes="dim")
            yield Label("")
            yield Label("Select target column:")
            yield Label("")
            for col in KanbanColumn:
                if col.value != self.move_task.kanban_column:
                    yield Button(col.display_name, id=f"move-{col.value}", variant="primary")
            yield Label("")
            yield Button("Cancel", id="cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id.startswith("move-"):
            column = event.button.id.replace("move-", "")
            self.dismiss(column)

    def action_cancel(self) -> None:
        """Cancel and close."""
        self.dismiss(None)


class HelpScreen(ModalScreen):
    """Help screen showing keyboard shortcuts."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("q", "close", "Close"),
    ]

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }

    HelpScreen > Vertical {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }

    HelpScreen .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    HelpScreen .shortcut {
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with Vertical():
            yield Label("[bold cyan]KANBAN Interactive Mode[/bold cyan]", classes="title")
            yield Label("")
            yield Label("[bold]Navigation:[/bold]")
            yield Label("  [green]h / Left[/green]   Move to previous column", classes="shortcut")
            yield Label("  [green]l / Right[/green]  Move to next column", classes="shortcut")
            yield Label("  [green]j / Down[/green]   Select next task", classes="shortcut")
            yield Label("  [green]k / Up[/green]     Select previous task", classes="shortcut")
            yield Label("")
            yield Label("[bold]Actions:[/bold]")
            yield Label("  [green]Enter[/green]      Move task to next column", classes="shortcut")
            yield Label("  [green]m[/green]          Move task to specific column", classes="shortcut")
            yield Label("  [green]r[/green]          Refresh board", classes="shortcut")
            yield Label("  [green]d[/green]          Toggle done column visibility", classes="shortcut")
            yield Label("")
            yield Label("[bold]Other:[/bold]")
            yield Label("  [green]?[/green]          Show this help", classes="shortcut")
            yield Label("  [green]q / Escape[/green] Quit", classes="shortcut")
            yield Label("")
            yield Button("Close", id="close", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        self.dismiss()

    def action_close(self) -> None:
        """Close the help screen."""
        self.dismiss()


class KanbanApp(App):
    """Interactive KANBAN board TUI application."""

    TITLE = "KANBAN Board"
    CSS = """
    Screen {
        layout: horizontal;
    }

    #board-container {
        width: 100%;
        height: 1fr;
    }

    .status-bar {
        dock: bottom;
        height: 1;
        background: $primary;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("escape", "quit", "Quit"),
        Binding("?", "show_help", "Help", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("d", "toggle_done", "Toggle Done", show=True),
        Binding("h", "prev_column", "Prev Column"),
        Binding("l", "next_column", "Next Column"),
        Binding("left", "prev_column", "Prev Column"),
        Binding("right", "next_column", "Next Column"),
        Binding("j", "next_task", "Next Task"),
        Binding("k", "prev_task", "Prev Task"),
        Binding("down", "next_task", "Next Task"),
        Binding("up", "prev_task", "Prev Task"),
        Binding("enter", "move_next", "Move to Next Column", show=True),
        Binding("m", "move_to", "Move To...", show=True),
    ]

    # Reactive state
    current_column_idx = reactive(0)
    show_done = reactive(False)

    def __init__(
        self,
        db_path: Optional[Path] = None,
        project_id: Optional[int] = None,
        priority: Optional[int] = None,
        tags: Optional[list[str]] = None,
    ):
        super().__init__()
        if db_path is None:
            db_path = get_config().get_db_path()
        self.km = KanbanManager(db_path)
        self.project_id = project_id
        self.priority = priority
        self.tags = tags
        self.board: dict[str, list[KanbanTask]] = {}
        self.columns: list[KanbanColumn] = []

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header()

        with Horizontal(id="board-container"):
            # Columns will be added dynamically
            pass

        yield Footer()

    def on_mount(self) -> None:
        """Load the board on mount."""
        self.refresh_board()

    def refresh_board(self) -> None:
        """Refresh the KANBAN board data and display."""
        self.board = self.km.get_board(
            project_id=self.project_id,
            priority=self.priority,
            tags=self.tags,
            include_done=self.show_done,
        )

        # Determine visible columns
        self.columns = [col for col in KanbanColumn if col.value in self.board]

        # Clear and rebuild the board container
        container = self.query_one("#board-container")
        container.remove_children()

        for i, col in enumerate(self.columns):
            tasks = self.board.get(col.value, [])
            widget = KanbanColumnWidget(col, tasks, id=f"col-{col.value}")
            if i == self.current_column_idx:
                widget.add_class("focused")
            container.mount(widget)

        # Focus first column's list if available
        if self.columns:
            self._focus_current_column()

    def _get_current_column_widget(self) -> Optional[KanbanColumnWidget]:
        """Get the currently focused column widget."""
        if not self.columns:
            return None
        try:
            col = self.columns[self.current_column_idx]
            return self.query_one(f"#col-{col.value}", KanbanColumnWidget)
        except Exception:
            return None

    def _get_current_list_view(self) -> Optional[ListView]:
        """Get the ListView in the current column."""
        widget = self._get_current_column_widget()
        if widget:
            try:
                return widget.query_one(ListView)
            except Exception:
                return None
        return None

    def _get_selected_task(self) -> Optional[KanbanTask]:
        """Get the currently selected task."""
        list_view = self._get_current_list_view()
        if list_view and list_view.highlighted_child:
            task_item = list_view.highlighted_child
            if isinstance(task_item, TaskItem):
                return task_item.kanban_task
        return None

    def _focus_current_column(self) -> None:
        """Focus the current column's list view."""
        # Remove focus styling from all columns
        for col in self.columns:
            try:
                widget = self.query_one(f"#col-{col.value}", KanbanColumnWidget)
                widget.remove_class("focused")
            except Exception:
                pass

        # Add focus styling to current column
        current_widget = self._get_current_column_widget()
        if current_widget:
            current_widget.add_class("focused")

        # Focus the list view
        list_view = self._get_current_list_view()
        if list_view:
            list_view.focus()

    def action_show_help(self) -> None:
        """Show the help screen."""
        self.push_screen(HelpScreen())

    def action_refresh(self) -> None:
        """Refresh the board."""
        self.refresh_board()
        self.notify("Board refreshed", timeout=1)

    def action_toggle_done(self) -> None:
        """Toggle visibility of done column."""
        self.show_done = not self.show_done
        # Clamp column index if needed
        if self.current_column_idx >= len(self.columns):
            self.current_column_idx = max(0, len(self.columns) - 1)
        self.refresh_board()
        status = "shown" if self.show_done else "hidden"
        self.notify(f"Done column {status}", timeout=1)

    def action_prev_column(self) -> None:
        """Move focus to previous column."""
        if self.columns and self.current_column_idx > 0:
            self.current_column_idx -= 1
            self._focus_current_column()

    def action_next_column(self) -> None:
        """Move focus to next column."""
        if self.columns and self.current_column_idx < len(self.columns) - 1:
            self.current_column_idx += 1
            self._focus_current_column()

    def action_prev_task(self) -> None:
        """Select previous task in current column."""
        list_view = self._get_current_list_view()
        if list_view:
            list_view.action_cursor_up()

    def action_next_task(self) -> None:
        """Select next task in current column."""
        list_view = self._get_current_list_view()
        if list_view:
            list_view.action_cursor_down()

    def action_move_next(self) -> None:
        """Move selected task to the next column."""
        task = self._get_selected_task()
        if not task:
            self.notify("No task selected", severity="warning", timeout=2)
            return

        # Find current column index and move to next
        try:
            current_col = KanbanColumn(task.kanban_column)
            current_idx = list(KanbanColumn).index(current_col)
            if current_idx < len(KanbanColumn) - 1:
                next_col = list(KanbanColumn)[current_idx + 1]
                self._move_task(task, next_col.value)
            else:
                self.notify("Task is already in the last column", timeout=2)
        except ValueError:
            self.notify("Cannot determine current column", severity="error", timeout=2)

    def action_move_to(self) -> None:
        """Open dialog to move task to specific column."""
        task = self._get_selected_task()
        if not task:
            self.notify("No task selected", severity="warning", timeout=2)
            return

        def handle_result(target_column: Optional[str]) -> None:
            if target_column:
                self._move_task(task, target_column)

        self.push_screen(MoveTaskScreen(task), handle_result)

    def _move_task(self, task: KanbanTask, target_column: str) -> None:
        """Move a task to a target column."""
        ok, message = self.km.move_task(task.id, target_column)
        if ok:
            self.notify(message, timeout=2)
            self.refresh_board()
        else:
            self.notify(message, severity="error", timeout=3)


def run_kanban_interactive(
    db_path: Optional[Path] = None,
    project_id: Optional[int] = None,
    priority: Optional[int] = None,
    tags: Optional[list[str]] = None,
) -> None:
    """Run the interactive KANBAN board.

    Args:
        db_path: Path to database file
        project_id: Filter by project ID
        priority: Filter by priority (0-3)
        tags: Filter by tags
    """
    app = KanbanApp(
        db_path=db_path,
        project_id=project_id,
        priority=priority,
        tags=tags,
    )
    app.run()
