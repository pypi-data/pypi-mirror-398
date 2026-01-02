"""Interactive calendar TUI for Todo CLI.

Uses Textual framework to provide an interactive calendar experience.
"""

from datetime import date, datetime, timedelta
from typing import Optional

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Input, Label, Static
from textual.screen import ModalScreen

from .database import Database
from .calendar_view import CalendarView, get_tasks_for_date
from .models import Todo, Priority


class DayCell(Static):
    """A single day cell in the calendar grid."""

    DEFAULT_CSS = """
    DayCell {
        width: 1fr;
        height: 3;
        text-align: center;
        border: solid $surface-lighten-2;
        padding: 0 1;
    }

    DayCell:hover {
        background: $surface-lighten-2;
    }

    DayCell.selected {
        border: solid $accent;
        background: $accent 20%;
    }

    DayCell.today {
        color: $accent;
    }

    DayCell.overdue {
        color: $error;
    }

    DayCell.other-month {
        color: $text-muted;
    }

    DayCell.has-tasks {
        border: solid $primary;
    }
    """

    def __init__(
        self,
        day_date: date,
        task_count: int = 0,
        is_today: bool = False,
        is_overdue: bool = False,
        is_current_month: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.day_date = day_date
        self.task_count = task_count
        self.is_today = is_today
        self.is_overdue = is_overdue
        self.is_current_month = is_current_month

    def compose(self) -> ComposeResult:
        text = Text()
        text.append(f"{self.day_date.day:2d}\n")
        if self.task_count > 0:
            text.append(f"({self.task_count})", style="dim")
        yield Label(text)

    def on_mount(self) -> None:
        if self.is_today:
            self.add_class("today")
        if self.is_overdue:
            self.add_class("overdue")
        if not self.is_current_month:
            self.add_class("other-month")
        if self.task_count > 0:
            self.add_class("has-tasks")


class CalendarGrid(Container):
    """Grid container for calendar days."""

    DEFAULT_CSS = """
    CalendarGrid {
        layout: grid;
        grid-size: 7;
        grid-gutter: 0;
        padding: 1;
    }
    """


class WeekdayHeader(Static):
    """Header showing weekday names."""

    DEFAULT_CSS = """
    WeekdayHeader {
        width: 1fr;
        height: 1;
        text-align: center;
        color: $text;
        text-style: bold;
    }
    """


class TaskListModal(ModalScreen):
    """Modal showing tasks for a specific date."""

    DEFAULT_CSS = """
    TaskListModal {
        align: center middle;
    }

    TaskListModal > Container {
        width: 60;
        height: auto;
        max-height: 80%;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    TaskListModal .task-item {
        padding: 0 1;
    }

    TaskListModal .task-item.done {
        text-style: strike;
        color: $text-muted;
    }

    TaskListModal Button {
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("q", "dismiss", "Close"),
    ]

    def __init__(self, target_date: date, tasks: list[Todo], **kwargs):
        super().__init__(**kwargs)
        self.target_date = target_date
        self.tasks = tasks

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(f"Tasks for {self.target_date.strftime('%B %d, %Y')}", id="modal-title")
            yield Static("---")

            if self.tasks:
                for task in self.tasks:
                    priority_icons = {0: "P0", 1: "P1", 2: "P2", 3: "P3"}
                    priority = priority_icons.get(task.priority.value, "P?")
                    status = "x" if task.status.value == "done" else " "
                    text = f"[{status}] #{task.id} [{priority}] {task.task}"
                    widget = Static(text, classes="task-item")
                    if task.status.value == "done":
                        widget.add_class("done")
                    yield widget
            else:
                yield Static("No tasks for this date.", classes="empty")

            yield Button("Close [Esc]", id="close-btn", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-btn":
            self.dismiss()


class AddTaskModal(ModalScreen[Optional[str]]):
    """Modal for adding a new task with the selected date."""

    DEFAULT_CSS = """
    AddTaskModal {
        align: center middle;
    }

    AddTaskModal > Container {
        width: 60;
        height: auto;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }

    AddTaskModal Input {
        margin: 1 0;
    }

    AddTaskModal #button-row {
        layout: horizontal;
        height: 3;
        margin-top: 1;
    }

    AddTaskModal #button-row Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, target_date: date, **kwargs):
        super().__init__(**kwargs)
        self.target_date = target_date

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(f"Add Task for {self.target_date.strftime('%B %d, %Y')}", id="modal-title")
            yield Static("---")
            yield Label("Task description:")
            yield Input(placeholder="Enter task description...", id="task-input")
            with Horizontal(id="button-row"):
                yield Button("Add [Enter]", id="add-btn", variant="primary")
                yield Button("Cancel [Esc]", id="cancel-btn", variant="default")

    def on_mount(self) -> None:
        self.query_one("#task-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-btn":
            self._submit_task()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit_task()

    def _submit_task(self) -> None:
        task_input = self.query_one("#task-input", Input)
        task_text = task_input.value.strip()
        if task_text:
            self.dismiss(task_text)
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class InteractiveCalendar(App):
    """Interactive calendar application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #calendar-container {
        height: auto;
        padding: 1;
    }

    #month-header {
        text-align: center;
        text-style: bold;
        padding: 1;
        color: $accent;
    }

    #weekday-row {
        layout: horizontal;
        height: 1;
        padding: 0 1;
    }

    #nav-row {
        layout: horizontal;
        align: center middle;
        height: 3;
        padding: 1;
    }

    #nav-row Button {
        margin: 0 1;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        padding: 0 1;
        background: $surface-lighten-1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
        Binding("left", "move_left", "Previous day"),
        Binding("right", "move_right", "Next day"),
        Binding("up", "move_up", "Previous week"),
        Binding("down", "move_down", "Next week"),
        Binding("enter", "show_tasks", "View tasks"),
        Binding("a", "add_task", "Add task"),
        Binding("n", "next_month", "Next month"),
        Binding("p", "prev_month", "Previous month"),
        Binding("t", "goto_today", "Go to today"),
    ]

    WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, db: Database, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.calendar_view = CalendarView(db)
        self.current_year = date.today().year
        self.current_month = date.today().month
        self.selected_date = date.today()
        self.day_cells: dict[date, DayCell] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Vertical(id="calendar-container"):
            yield Label(self._get_month_title(), id="month-header")

            with Horizontal(id="nav-row"):
                yield Button("< Prev [p]", id="prev-btn", variant="default")
                yield Button("Today [t]", id="today-btn", variant="primary")
                yield Button("Next > [n]", id="next-btn", variant="default")

            with Horizontal(id="weekday-row"):
                for name in self.WEEKDAY_NAMES:
                    yield WeekdayHeader(name)

            yield CalendarGrid(id="calendar-grid")

        yield Static("Arrow keys: Navigate | Enter: View | a: Add task | n/p: Month | t: Today | q: Quit", id="status-bar")
        yield Footer()

    def _get_month_title(self) -> str:
        months = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return f"{months[self.current_month]} {self.current_year}"

    def on_mount(self) -> None:
        self._rebuild_calendar()

    def _rebuild_calendar(self) -> None:
        """Rebuild the calendar grid for the current month."""
        grid = self.query_one("#calendar-grid", CalendarGrid)
        grid.remove_children()
        self.day_cells.clear()

        # Build calendar data
        weeks = self.calendar_view.build_month_calendar(
            self.current_year, self.current_month
        )

        # Create day cells
        for week in weeks:
            for day_data in week:
                cell = DayCell(
                    day_date=day_data.date,
                    task_count=day_data.task_count,
                    is_today=day_data.is_today,
                    is_overdue=day_data.is_overdue,
                    is_current_month=day_data.is_current_month,
                    id=f"day-{day_data.date.isoformat()}",
                )
                self.day_cells[day_data.date] = cell
                grid.mount(cell)

        # Update selection
        self._update_selection()

        # Update month header
        header = self.query_one("#month-header", Label)
        header.update(self._get_month_title())

    def _update_selection(self) -> None:
        """Update the visual selection indicator."""
        for cell in self.day_cells.values():
            cell.remove_class("selected")

        if self.selected_date in self.day_cells:
            self.day_cells[self.selected_date].add_class("selected")

    def action_quit(self) -> None:
        self.exit()

    def action_move_left(self) -> None:
        self.selected_date -= timedelta(days=1)
        self._handle_date_change()

    def action_move_right(self) -> None:
        self.selected_date += timedelta(days=1)
        self._handle_date_change()

    def action_move_up(self) -> None:
        self.selected_date -= timedelta(weeks=1)
        self._handle_date_change()

    def action_move_down(self) -> None:
        self.selected_date += timedelta(weeks=1)
        self._handle_date_change()

    def _handle_date_change(self) -> None:
        """Handle when selected date changes."""
        # Check if we need to switch months
        if (self.selected_date.year != self.current_year or
            self.selected_date.month != self.current_month):
            self.current_year = self.selected_date.year
            self.current_month = self.selected_date.month
            self._rebuild_calendar()
        else:
            self._update_selection()

    def action_next_month(self) -> None:
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        # Move selected date to same day in new month (or last day)
        try:
            self.selected_date = self.selected_date.replace(
                year=self.current_year, month=self.current_month
            )
        except ValueError:
            # Day doesn't exist in new month, go to last day
            if self.current_month == 12:
                next_month = date(self.current_year + 1, 1, 1)
            else:
                next_month = date(self.current_year, self.current_month + 1, 1)
            self.selected_date = next_month - timedelta(days=1)
        self._rebuild_calendar()

    def action_prev_month(self) -> None:
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        # Move selected date to same day in new month (or last day)
        try:
            self.selected_date = self.selected_date.replace(
                year=self.current_year, month=self.current_month
            )
        except ValueError:
            # Day doesn't exist in new month, go to last day
            if self.current_month == 12:
                next_month = date(self.current_year + 1, 1, 1)
            else:
                next_month = date(self.current_year, self.current_month + 1, 1)
            self.selected_date = next_month - timedelta(days=1)
        self._rebuild_calendar()

    def action_goto_today(self) -> None:
        self.selected_date = date.today()
        self.current_year = self.selected_date.year
        self.current_month = self.selected_date.month
        self._rebuild_calendar()

    def action_show_tasks(self) -> None:
        """Show tasks for the selected date."""
        tasks = get_tasks_for_date(self.db, self.selected_date, include_done=True)
        self.push_screen(TaskListModal(self.selected_date, tasks))

    def action_add_task(self) -> None:
        """Add a task with the selected date as due date."""
        def handle_task_result(task_text: Optional[str]) -> None:
            if task_text:
                # Convert selected date to datetime for due_date
                due_datetime = datetime.combine(self.selected_date, datetime.min.time())
                self.db.add(
                    task=task_text,
                    priority=Priority.P2,  # Default priority
                    due_date=due_datetime,
                )
                # Rebuild calendar to show updated task counts
                self._rebuild_calendar()
                self.notify(f"Task added for {self.selected_date.strftime('%b %d')}")

        self.push_screen(AddTaskModal(self.selected_date), handle_task_result)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "prev-btn":
            self.action_prev_month()
        elif event.button.id == "next-btn":
            self.action_next_month()
        elif event.button.id == "today-btn":
            self.action_goto_today()


def run_interactive_calendar(db: Database) -> None:
    """Launch the interactive calendar TUI.

    Args:
        db: Database instance
    """
    app = InteractiveCalendar(db)
    app.run()
