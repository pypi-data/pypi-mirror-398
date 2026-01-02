"""Data models for Todo CLI."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class Priority(Enum):
    """Task priority levels."""
    P0 = 0  # Critical/Urgent
    P1 = 1  # High priority
    P2 = 2  # Medium priority
    P3 = 3  # Low priority

    def __str__(self) -> str:
        return self.name


class Status(Enum):
    """Task status."""
    TODO = "todo"
    DOING = "doing"
    DONE = "done"

    def __str__(self) -> str:
        return self.value


class RecurrencePattern(Enum):
    """Recurrence pattern types."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"

    def __str__(self) -> str:
        return self.value


@dataclass
class Todo:
    """A todo item with time tracking."""
    id: int
    task: str
    priority: Priority = Priority.P2
    status: Status = Status.TODO
    project: Optional[str] = None
    project_id: Optional[int] = None
    tags: list[str] = field(default_factory=list)
    due_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    time_spent: timedelta = field(default_factory=lambda: timedelta())
    timer_started: Optional[datetime] = None

    @property
    def is_tracking(self) -> bool:
        """Check if timer is currently running."""
        return self.timer_started is not None

    @property
    def total_time(self) -> timedelta:
        """Get total time including current tracking session."""
        if self.timer_started:
            return self.time_spent + (datetime.now() - self.timer_started)
        return self.time_spent

    def format_time(self) -> str:
        """Format total time as HH:MM:SS."""
        total = self.total_time
        hours, remainder = divmod(int(total.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.due_date and self.status != Status.DONE:
            return datetime.now() > self.due_date
        return False


@dataclass
class RecurrenceRule:
    """A recurrence rule for recurring tasks.

    Attributes:
        id: Unique identifier for the rule
        task_id: ID of the task this rule applies to
        pattern: Recurrence pattern (daily, weekly, monthly, yearly, custom)
        interval: Every N days/weeks/months/years (default 1)
        days_of_week: For weekly: list of day names (mon, tue, wed, thu, fri, sat, sun)
        day_of_month: For monthly: day of month (1-31)
        end_date: Optional end date for recurrence
        max_occurrences: Optional maximum number of occurrences
        occurrences_created: Number of occurrences already created
        created_at: When the rule was created
        updated_at: When the rule was last updated
    """
    id: int
    task_id: int
    pattern: RecurrencePattern
    interval: int = 1
    days_of_week: Optional[list[str]] = None
    day_of_month: Optional[int] = None
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None
    occurrences_created: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def has_reached_limit(self) -> bool:
        """Check if max occurrences limit has been reached."""
        if self.max_occurrences is None:
            return False
        return self.occurrences_created >= self.max_occurrences

    @property
    def has_expired(self) -> bool:
        """Check if recurrence has passed end date."""
        if self.end_date is None:
            return False
        return datetime.now() > self.end_date

    @property
    def is_active(self) -> bool:
        """Check if recurrence rule is still active."""
        return not self.has_reached_limit and not self.has_expired
