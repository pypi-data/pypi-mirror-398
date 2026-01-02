"""Cycle management for Todo CLI - Linear-style sprint/cycle workflows."""

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

from .config import get_config


class CycleStatus(Enum):
    """Cycle status values."""
    ACTIVE = "active"
    CLOSED = "closed"

    def __str__(self) -> str:
        return self.value


@dataclass
class Cycle:
    """A development cycle (sprint)."""
    id: int
    name: str
    start_date: datetime
    end_date: datetime
    status: CycleStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

    @property
    def duration_weeks(self) -> int:
        """Get cycle duration in weeks."""
        delta = self.end_date - self.start_date
        return max(1, delta.days // 7)

    @property
    def days_remaining(self) -> int:
        """Get days remaining in cycle."""
        if self.status == CycleStatus.CLOSED:
            return 0
        delta = self.end_date - datetime.now()
        return max(0, delta.days)

    @property
    def is_active(self) -> bool:
        """Check if cycle is active."""
        return self.status == CycleStatus.ACTIVE

    @property
    def progress_percentage(self) -> float:
        """Get time-based progress percentage."""
        if self.status == CycleStatus.CLOSED:
            return 100.0
        total = (self.end_date - self.start_date).total_seconds()
        elapsed = (datetime.now() - self.start_date).total_seconds()
        return min(100.0, max(0.0, (elapsed / total) * 100))


@dataclass
class CycleTask:
    """A task assigned to a cycle."""
    task_id: int
    task_name: str
    status: str
    priority: int
    project_id: Optional[int]
    project_name: Optional[str]
    added_at: datetime
    completed_at: Optional[datetime] = None
    time_spent_seconds: int = 0


class CycleManager:
    """Manages cycle operations."""

    VALID_DURATIONS = [1, 2, 4]  # Valid cycle durations in weeks

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize cycle manager.

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
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def _row_to_cycle(self, row: sqlite3.Row) -> Cycle:
        """Convert database row to Cycle object."""
        return Cycle(
            id=row["id"],
            name=row["name"],
            start_date=datetime.fromisoformat(row["start_date"]),
            end_date=datetime.fromisoformat(row["end_date"]),
            status=CycleStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
        )

    def create_cycle(self, name: str, duration_weeks: int = 2,
                     start_date: Optional[datetime] = None) -> tuple[bool, "Cycle | str"]:
        """Create a new cycle.

        Args:
            name: Cycle name
            duration_weeks: Duration in weeks (1, 2, or 4)
            start_date: Optional start date (defaults to now)

        Returns:
            Tuple of (success, cycle_or_error_message)
        """
        # Validate duration
        if duration_weeks not in self.VALID_DURATIONS:
            return False, f"Invalid duration. Must be one of: {self.VALID_DURATIONS} weeks"

        # Check for existing active cycle (MVP constraint: only one active cycle)
        active = self.get_active_cycle()
        if active:
            return False, f"Active cycle '{active.name}' already exists. Close it first."

        # Set dates
        if start_date is None:
            start_date = datetime.now()
        end_date = start_date + timedelta(weeks=duration_weeks)

        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO cycles (name, start_date, end_date, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    name,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    CycleStatus.ACTIVE.value,
                    datetime.now().isoformat(),
                )
            )
            conn.commit()
            cycle_id = cursor.lastrowid

        cycle = self.get_cycle(cycle_id)
        return True, cycle

    def get_cycle(self, cycle_id: int) -> Optional[Cycle]:
        """Get a cycle by ID.

        Args:
            cycle_id: Cycle ID

        Returns:
            Cycle object or None
        """
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM cycles WHERE id = ?",
                (cycle_id,)
            ).fetchone()
            return self._row_to_cycle(row) if row else None

    def get_active_cycle(self) -> Optional[Cycle]:
        """Get the current active cycle.

        Returns:
            Active cycle or None
        """
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM cycles WHERE status = ?",
                (CycleStatus.ACTIVE.value,)
            ).fetchone()
            return self._row_to_cycle(row) if row else None

    def get_cycle_by_name(self, name: str) -> Optional[Cycle]:
        """Get a cycle by name.

        Args:
            name: Cycle name

        Returns:
            Cycle object or None
        """
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM cycles WHERE name = ?",
                (name,)
            ).fetchone()
            return self._row_to_cycle(row) if row else None

    def list_cycles(self, include_closed: bool = False) -> list[Cycle]:
        """List all cycles.

        Args:
            include_closed: Include closed cycles

        Returns:
            List of Cycle objects
        """
        query = "SELECT * FROM cycles"
        params = []

        if not include_closed:
            query += " WHERE status = ?"
            params.append(CycleStatus.ACTIVE.value)

        query += " ORDER BY created_at DESC"

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_cycle(row) for row in rows]

    def assign_task(self, cycle_id: int, task_id: int) -> tuple[bool, str]:
        """Assign a task to a cycle.

        Args:
            cycle_id: Cycle ID to assign to
            task_id: Task ID to assign

        Returns:
            Tuple of (success, message)
        """
        # Get target cycle
        cycle = self.get_cycle(cycle_id)
        if not cycle:
            return False, f"Cycle #{cycle_id} not found"

        with self._get_conn() as conn:
            # Check task exists
            task_row = conn.execute(
                "SELECT id, task, status FROM todos WHERE id = ?",
                (task_id,)
            ).fetchone()

            if not task_row:
                return False, f"Task #{task_id} not found"

            # Check not already assigned
            existing = conn.execute(
                "SELECT id FROM cycle_tasks WHERE cycle_id = ? AND task_id = ?",
                (cycle_id, task_id)
            ).fetchone()

            if existing:
                return False, f"Task #{task_id} already assigned to cycle '{cycle.name}'"

            # Assign task
            conn.execute(
                """
                INSERT INTO cycle_tasks (cycle_id, task_id, added_at)
                VALUES (?, ?, ?)
                """,
                (cycle_id, task_id, datetime.now().isoformat())
            )
            conn.commit()

        return True, f"Assigned task #{task_id} '{task_row['task']}' to cycle '{cycle.name}'"

    def unassign_task(self, task_id: int, cycle_id: Optional[int] = None) -> tuple[bool, str]:
        """Remove a task from a cycle.

        Args:
            task_id: Task ID to unassign
            cycle_id: Optional cycle ID (defaults to active cycle)

        Returns:
            Tuple of (success, message)
        """
        # Get target cycle
        if cycle_id is None:
            cycle = self.get_active_cycle()
            if not cycle:
                return False, "No active cycle"
            cycle_id = cycle.id
        else:
            cycle = self.get_cycle(cycle_id)
            if not cycle:
                return False, f"Cycle #{cycle_id} not found"

        with self._get_conn() as conn:
            # Check assignment exists
            existing = conn.execute(
                "SELECT id FROM cycle_tasks WHERE cycle_id = ? AND task_id = ?",
                (cycle_id, task_id)
            ).fetchone()

            if not existing:
                return False, f"Task #{task_id} not assigned to cycle '{cycle.name}'"

            # Remove assignment
            conn.execute(
                "DELETE FROM cycle_tasks WHERE cycle_id = ? AND task_id = ?",
                (cycle_id, task_id)
            )
            conn.commit()

        return True, f"Removed task #{task_id} from cycle '{cycle.name}'"

    def get_cycle_tasks(self, cycle_id: Optional[int] = None) -> list[CycleTask]:
        """Get all tasks in a cycle.

        Args:
            cycle_id: Optional cycle ID (defaults to active cycle)

        Returns:
            List of CycleTask objects
        """
        if cycle_id is None:
            cycle = self.get_active_cycle()
            if not cycle:
                return []
            cycle_id = cycle.id

        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT
                    t.id,
                    t.task,
                    t.status,
                    t.priority,
                    t.project_id,
                    p.name as project_name,
                    ct.added_at,
                    t.completed_at,
                    t.time_spent_seconds
                FROM cycle_tasks ct
                JOIN todos t ON ct.task_id = t.id
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE ct.cycle_id = ?
                ORDER BY t.priority ASC, ct.added_at ASC
                """,
                (cycle_id,)
            ).fetchall()

        tasks = []
        for row in rows:
            tasks.append(CycleTask(
                task_id=row["id"],
                task_name=row["task"],
                status=row["status"],
                priority=row["priority"],
                project_id=row["project_id"],
                project_name=row["project_name"],
                added_at=datetime.fromisoformat(row["added_at"]),
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                time_spent_seconds=row["time_spent_seconds"] or 0,
            ))
        return tasks

    def get_cycle_progress(self, cycle_id: Optional[int] = None) -> dict:
        """Get progress statistics for a cycle.

        Args:
            cycle_id: Optional cycle ID (defaults to active cycle)

        Returns:
            Dict with progress statistics
        """
        if cycle_id is None:
            cycle = self.get_active_cycle()
            if not cycle:
                return {
                    "cycle": None,
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "in_progress_tasks": 0,
                    "todo_tasks": 0,
                    "completion_percentage": 0.0,
                    "total_time_seconds": 0,
                    "days_remaining": 0,
                    "time_progress": 0.0,
                    "velocity": 0.0,
                    "projected_completion": 0.0,
                }
            cycle_id = cycle.id
        else:
            cycle = self.get_cycle(cycle_id)

        tasks = self.get_cycle_tasks(cycle_id)

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == "done")
        in_progress = sum(1 for t in tasks if t.status == "doing")
        todo = sum(1 for t in tasks if t.status == "todo")
        total_time = sum(t.time_spent_seconds for t in tasks)

        completion_percentage = (completed / total * 100) if total > 0 else 0.0

        # Calculate velocity (tasks completed per day)
        if cycle and completed > 0:
            elapsed_days = (datetime.now() - cycle.start_date).days or 1
            velocity = completed / elapsed_days
        else:
            velocity = 0.0

        # Calculate projected completion (tasks expected by cycle end)
        days_remaining = cycle.days_remaining if cycle else 0
        projected_completion = completed + (velocity * days_remaining)

        return {
            "cycle": cycle,
            "total_tasks": total,
            "completed_tasks": completed,
            "in_progress_tasks": in_progress,
            "todo_tasks": todo,
            "completion_percentage": completion_percentage,
            "total_time_seconds": total_time,
            "days_remaining": days_remaining,
            "time_progress": cycle.progress_percentage if cycle else 0.0,
            "velocity": velocity,
            "projected_completion": projected_completion,
        }

    def close_cycle(self, cycle_id: int,
                    rollover: bool = False,
                    new_cycle_name: Optional[str] = None,
                    new_cycle_duration: int = 2) -> tuple[bool, "str | dict"]:
        """Close a cycle.

        Args:
            cycle_id: Cycle ID to close
            rollover: If True, create new cycle and roll over incomplete tasks
            new_cycle_name: Name for new cycle (with rollover)
            new_cycle_duration: Duration for new cycle in weeks (with rollover)

        Returns:
            Tuple of (success, message_or_result)
            On success with rollover: result is dict with new_cycle and rolled_tasks
            On success without rollover: result is success message
            On failure: result is error message
        """
        cycle = self.get_cycle(cycle_id)
        if not cycle:
            return False, f"Cycle #{cycle_id} not found"

        if cycle.status == CycleStatus.CLOSED:
            return False, f"Cycle '{cycle.name}' is already closed"

        # Get incomplete tasks
        tasks = self.get_cycle_tasks(cycle_id)
        incomplete_ids = [t.task_id for t in tasks if t.status != "done"]

        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE cycles
                SET status = ?, completed_at = ?
                WHERE id = ?
                """,
                (CycleStatus.CLOSED.value, datetime.now().isoformat(), cycle_id)
            )
            conn.commit()

        completed_count = len(tasks) - len(incomplete_ids)

        # Handle rollover
        if rollover and incomplete_ids:
            # Create new cycle
            if not new_cycle_name:
                new_cycle_name = f"{cycle.name} (continued)"

            ok, new_cycle_result = self.create_cycle(new_cycle_name, new_cycle_duration)
            if not ok:
                return True, f"Closed cycle '{cycle.name}' but failed to create new cycle: {new_cycle_result}"

            new_cycle = new_cycle_result

            # Assign incomplete tasks to new cycle
            rolled = 0
            for task_id in incomplete_ids:
                self.assign_task(new_cycle.id, task_id)
                rolled += 1

            return True, {
                "new_cycle": new_cycle,
                "rolled_tasks": rolled,
                "completed_count": completed_count,
                "total_tasks": len(tasks),
            }

        message = f"Closed cycle '{cycle.name}' ({completed_count}/{len(tasks)} tasks completed)"
        if incomplete_ids:
            message += f" - {len(incomplete_ids)} incomplete tasks"

        return True, message

    def generate_report_markdown(self, cycle_id: Optional[int] = None) -> str:
        """Generate a Markdown report for a cycle.

        Args:
            cycle_id: Optional cycle ID (defaults to active cycle)

        Returns:
            Markdown formatted report string
        """
        progress = self.get_cycle_progress(cycle_id)
        cycle = progress["cycle"]

        if not cycle:
            return "# No Cycle Data\n\nNo active cycle found."

        tasks = self.get_cycle_tasks(cycle.id)

        # Build report
        lines = []
        lines.append(f"# Cycle Report: {cycle.name}")
        lines.append("")
        lines.append("## Overview")
        lines.append("")
        lines.append(f"- **Status:** {cycle.status.value.title()}")
        lines.append(f"- **Duration:** {cycle.duration_weeks} week(s)")
        lines.append(f"- **Start Date:** {cycle.start_date.strftime('%Y-%m-%d')}")
        lines.append(f"- **End Date:** {cycle.end_date.strftime('%Y-%m-%d')}")

        if cycle.is_active:
            lines.append(f"- **Days Remaining:** {cycle.days_remaining}")
            lines.append(f"- **Time Progress:** {progress['time_progress']:.1f}%")

        lines.append("")
        lines.append("## Progress")
        lines.append("")
        lines.append(f"- **Total Tasks:** {progress['total_tasks']}")
        lines.append(f"- **Completed:** {progress['completed_tasks']}")
        lines.append(f"- **In Progress:** {progress['in_progress_tasks']}")
        lines.append(f"- **Todo:** {progress['todo_tasks']}")
        lines.append(f"- **Completion Rate:** {progress['completion_percentage']:.1f}%")

        if progress['velocity'] > 0:
            lines.append(f"- **Velocity:** {progress['velocity']:.2f} tasks/day")

        # Format time spent
        total_hours = progress['total_time_seconds'] / 3600
        lines.append(f"- **Total Time Tracked:** {total_hours:.1f} hours")

        lines.append("")
        lines.append("## Tasks")
        lines.append("")

        # Group tasks by status
        completed = [t for t in tasks if t.status == "done"]
        in_progress = [t for t in tasks if t.status == "doing"]
        todo = [t for t in tasks if t.status == "todo"]

        if completed:
            lines.append("### Completed")
            lines.append("")
            for task in completed:
                project = f" @{task.project_name}" if task.project_name else ""
                lines.append(f"- [x] #{task.task_id} {task.task_name}{project}")
            lines.append("")

        if in_progress:
            lines.append("### In Progress")
            lines.append("")
            for task in in_progress:
                project = f" @{task.project_name}" if task.project_name else ""
                lines.append(f"- [ ] #{task.task_id} {task.task_name}{project}")
            lines.append("")

        if todo:
            lines.append("### Todo")
            lines.append("")
            for task in todo:
                project = f" @{task.project_name}" if task.project_name else ""
                lines.append(f"- [ ] #{task.task_id} {task.task_name}{project}")
            lines.append("")

        lines.append("---")
        lines.append(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)

    def export_json(self, cycle_id: Optional[int] = None) -> str:
        """Export cycle data as JSON string.

        Args:
            cycle_id: Optional cycle ID (defaults to active cycle)

        Returns:
            JSON formatted string with cycle data
        """
        progress = self.get_cycle_progress(cycle_id)
        cycle = progress["cycle"]

        if not cycle:
            return json.dumps({"error": "No cycle found"}, indent=2)

        tasks = self.get_cycle_tasks(cycle.id)

        data = {
            "cycle": {
                "id": cycle.id,
                "name": cycle.name,
                "status": cycle.status.value,
                "start_date": cycle.start_date.isoformat(),
                "end_date": cycle.end_date.isoformat(),
                "duration_weeks": cycle.duration_weeks,
                "days_remaining": cycle.days_remaining,
                "created_at": cycle.created_at.isoformat(),
                "completed_at": cycle.completed_at.isoformat() if cycle.completed_at else None,
            },
            "progress": {
                "total_tasks": progress["total_tasks"],
                "completed_tasks": progress["completed_tasks"],
                "in_progress_tasks": progress["in_progress_tasks"],
                "todo_tasks": progress["todo_tasks"],
                "completion_percentage": round(progress["completion_percentage"], 2),
                "time_progress": round(progress["time_progress"], 2),
                "velocity": round(progress["velocity"], 2),
                "projected_completion": progress["projected_completion"],
                "total_time_hours": round(progress["total_time_seconds"] / 3600, 2),
            },
            "tasks": [
                {
                    "id": t.task_id,
                    "task": t.task_name,
                    "status": t.status,
                    "priority": t.priority,
                    "project_id": t.project_id,
                    "project_name": t.project_name,
                    "added_at": t.added_at.isoformat(),
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    "time_spent_hours": round(t.time_spent_seconds / 3600, 2),
                }
                for t in tasks
            ],
            "generated_at": datetime.now().isoformat(),
        }
        return json.dumps(data, indent=2)
