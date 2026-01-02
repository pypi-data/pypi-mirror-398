"""SQLite database operations for Todo CLI."""

import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import Todo, Priority, Status, RecurrenceRule, RecurrencePattern
from .config import get_config
from .migrations import MigrationManager


class Database:
    """SQLite database manager for todos."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = get_config().get_db_path()

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_conn(self):
        """Get database connection as context manager that auto-closes."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema and run migrations."""
        with self._get_conn() as conn:
            # Create base todos table (v0 schema)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    priority INTEGER DEFAULT 2,
                    status TEXT DEFAULT 'todo',
                    project TEXT,
                    tags TEXT DEFAULT '[]',
                    due_date TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    time_spent_seconds INTEGER DEFAULT 0,
                    timer_started TEXT
                )
            """)
            conn.commit()

            # Run migrations to bring database up to current version
            migrator = MigrationManager(self.db_path)
            if migrator.needs_migration(conn):
                print(f"Migrating database from v{migrator.get_current_version(conn)} to v{migrator.CURRENT_VERSION}...")
                success = migrator.migrate(conn)
                if success:
                    print(f"Migration complete! Database is now at v{migrator.CURRENT_VERSION}")
                else:
                    print("Migration failed. Database remains at previous version.")
                    print("Your data is safe. Check error messages above.")

    def _row_to_todo(self, row: sqlite3.Row) -> Todo:
        """Convert database row to Todo object."""
        return Todo(
            id=row["id"],
            task=row["task"],
            priority=Priority(row["priority"]),
            status=Status(row["status"]),
            project=row["project"],
            project_id=row["project_id"] if "project_id" in row.keys() else None,
            tags=json.loads(row["tags"]) if row["tags"] else [],
            due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            time_spent=timedelta(seconds=row["time_spent_seconds"]),
            timer_started=datetime.fromisoformat(row["timer_started"]) if row["timer_started"] else None,
        )

    def add(self, task: str, priority: Priority = Priority.P2,
            project: Optional[str] = None, project_id: Optional[int] = None,
            tags: list[str] = None, due_date: Optional[datetime] = None) -> Todo:
        """Add a new todo.

        Args:
            task: Task description
            priority: Task priority (P0-P3)
            project: Legacy project string (for backwards compatibility)
            project_id: Project ID (preferred method)
            tags: List of tags
            due_date: Due date

        Returns:
            Created Todo object
        """
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO todos (task, priority, project, project_id, tags, due_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task,
                    priority.value,
                    project,
                    project_id,
                    json.dumps(tags or []),
                    due_date.isoformat() if due_date else None,
                    datetime.now().isoformat(),
                )
            )
            conn.commit()
            return self.get(cursor.lastrowid)

    def get(self, todo_id: int) -> Optional[Todo]:
        """Get a todo by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM todos WHERE id = ?", (todo_id,)
            ).fetchone()
            return self._row_to_todo(row) if row else None

    def list_all(self, status: Optional[Status] = None,
                 project: Optional[str] = None,
                 project_id: Optional[int] = None,
                 include_done: bool = False) -> list[Todo]:
        """List todos with optional filters.

        Args:
            status: Filter by status (todo, doing, done)
            project: Legacy project string filter (for backwards compatibility)
            project_id: Filter by project ID (preferred method)
            include_done: Include completed todos

        Returns:
            List of Todo objects matching filters
        """
        query = "SELECT * FROM todos WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status.value)
        elif not include_done:
            query += " AND status != 'done'"

        # Prefer project_id over legacy project string
        if project_id is not None:
            query += " AND project_id = ?"
            params.append(project_id)
        elif project:
            # Backwards compatibility: support legacy project string
            query += " AND project = ?"
            params.append(project)

        query += " ORDER BY priority ASC, due_date ASC NULLS LAST, created_at DESC"

        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_todo(row) for row in rows]

    def update(self, todo: Todo):
        """Update a todo."""
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE todos SET
                    task = ?, priority = ?, status = ?, project = ?,
                    tags = ?, due_date = ?, completed_at = ?,
                    time_spent_seconds = ?, timer_started = ?
                WHERE id = ?
                """,
                (
                    todo.task,
                    todo.priority.value,
                    todo.status.value,
                    todo.project,
                    json.dumps(todo.tags),
                    todo.due_date.isoformat() if todo.due_date else None,
                    todo.completed_at.isoformat() if todo.completed_at else None,
                    int(todo.time_spent.total_seconds()),
                    todo.timer_started.isoformat() if todo.timer_started else None,
                    todo.id,
                )
            )
            conn.commit()

    def delete(self, todo_id: int) -> bool:
        """Delete a todo."""
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
            conn.commit()
            return cursor.rowcount > 0

    def start_timer(self, todo_id: int) -> Optional[Todo]:
        """Start time tracking for a todo."""
        todo = self.get(todo_id)
        if not todo:
            return None

        if todo.timer_started:
            return todo  # Already tracking

        todo.timer_started = datetime.now()
        todo.status = Status.DOING
        self.update(todo)
        return todo

    def stop_timer(self, todo_id: Optional[int] = None) -> Optional[Todo]:
        """Stop time tracking. If no ID, stops any active timer."""
        if todo_id:
            todo = self.get(todo_id)
            if todo and todo.timer_started:
                elapsed = datetime.now() - todo.timer_started
                todo.time_spent += elapsed
                todo.timer_started = None
                self.update(todo)
                return todo
        else:
            # Find and stop any active timer
            with self._get_conn() as conn:
                row = conn.execute(
                    "SELECT * FROM todos WHERE timer_started IS NOT NULL"
                ).fetchone()
                if row:
                    return self.stop_timer(row["id"])
        return None

    def mark_done(self, todo_id: int) -> Optional[Todo]:
        """Mark a todo as done."""
        todo = self.get(todo_id)
        if not todo:
            return None

        # Stop timer if running
        if todo.timer_started:
            elapsed = datetime.now() - todo.timer_started
            todo.time_spent += elapsed
            todo.timer_started = None

        todo.status = Status.DONE
        todo.completed_at = datetime.now()
        self.update(todo)
        return todo

    def mark_undone(self, todo_id: int) -> Optional[Todo]:
        """Mark a completed todo as not done (uncomplete it)."""
        todo = self.get(todo_id)
        if not todo:
            return None

        todo.status = Status.TODO
        todo.completed_at = None
        self.update(todo)
        return todo

    def get_active_timer(self) -> Optional[Todo]:
        """Get the currently tracking todo."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM todos WHERE timer_started IS NOT NULL"
            ).fetchone()
            return self._row_to_todo(row) if row else None

    def get_projects(self) -> list[str]:
        """Get list of all projects."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT project FROM todos WHERE project IS NOT NULL ORDER BY project"
            ).fetchall()
            return [row["project"] for row in rows]

    def get_stats(self) -> dict:
        """Get todo statistics."""
        with self._get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
            done = conn.execute("SELECT COUNT(*) FROM todos WHERE status = 'done'").fetchone()[0]
            doing = conn.execute("SELECT COUNT(*) FROM todos WHERE status = 'doing'").fetchone()[0]
            todo = conn.execute("SELECT COUNT(*) FROM todos WHERE status = 'todo'").fetchone()[0]
            total_time = conn.execute("SELECT SUM(time_spent_seconds) FROM todos").fetchone()[0] or 0

            # Count overdue tasks (due before today and not done)
            today_str = datetime.now().date().isoformat()
            overdue = conn.execute(
                """SELECT COUNT(*) FROM todos
                   WHERE due_date IS NOT NULL
                   AND date(due_date) < date(?)
                   AND status != 'done'""",
                (today_str,)
            ).fetchone()[0]

            return {
                "total": total,
                "done": done,
                "doing": doing,
                "todo": todo,
                "overdue": overdue,
                "total_time_seconds": total_time,
            }

    # Recurrence Rule Methods

    def _row_to_recurrence_rule(self, row: sqlite3.Row) -> RecurrenceRule:
        """Convert database row to RecurrenceRule object."""
        return RecurrenceRule(
            id=row["id"],
            task_id=row["task_id"],
            pattern=RecurrencePattern(row["pattern"]),
            interval=row["interval"],
            days_of_week=json.loads(row["days_of_week"]) if row["days_of_week"] else None,
            day_of_month=row["day_of_month"],
            end_date=datetime.fromisoformat(row["end_date"]) if row["end_date"] else None,
            max_occurrences=row["max_occurrences"],
            occurrences_created=row["occurrences_created"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(),
        )

    def add_recurrence_rule(
        self,
        task_id: int,
        pattern: RecurrencePattern,
        interval: int = 1,
        days_of_week: Optional[list[str]] = None,
        day_of_month: Optional[int] = None,
        end_date: Optional[datetime] = None,
        max_occurrences: Optional[int] = None,
    ) -> RecurrenceRule:
        """Add a recurrence rule for a task.

        Args:
            task_id: ID of the task this rule applies to
            pattern: Recurrence pattern (daily, weekly, monthly, yearly, custom)
            interval: Every N days/weeks/months/years
            days_of_week: For custom pattern: list of day names
            day_of_month: For monthly: specific day of month
            end_date: Optional end date for recurrence
            max_occurrences: Optional maximum number of occurrences

        Returns:
            Created RecurrenceRule object
        """
        now = datetime.now().isoformat()
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT INTO recurrence_rules
                (task_id, pattern, interval, days_of_week, day_of_month,
                 end_date, max_occurrences, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    pattern.value,
                    interval,
                    json.dumps(days_of_week) if days_of_week else None,
                    day_of_month,
                    end_date.isoformat() if end_date else None,
                    max_occurrences,
                    now,
                    now,
                )
            )
            conn.commit()
            return self.get_recurrence_rule(cursor.lastrowid)

    def get_recurrence_rule(self, rule_id: int) -> Optional[RecurrenceRule]:
        """Get a recurrence rule by ID."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM recurrence_rules WHERE id = ?", (rule_id,)
            ).fetchone()
            return self._row_to_recurrence_rule(row) if row else None

    def get_recurrence_rule_by_task(self, task_id: int) -> Optional[RecurrenceRule]:
        """Get the recurrence rule for a task."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM recurrence_rules WHERE task_id = ?", (task_id,)
            ).fetchone()
            return self._row_to_recurrence_rule(row) if row else None

    def update_recurrence_rule(self, rule: RecurrenceRule) -> None:
        """Update a recurrence rule."""
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE recurrence_rules SET
                    pattern = ?, interval = ?, days_of_week = ?,
                    day_of_month = ?, end_date = ?, max_occurrences = ?,
                    occurrences_created = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    rule.pattern.value,
                    rule.interval,
                    json.dumps(rule.days_of_week) if rule.days_of_week else None,
                    rule.day_of_month,
                    rule.end_date.isoformat() if rule.end_date else None,
                    rule.max_occurrences,
                    rule.occurrences_created,
                    datetime.now().isoformat(),
                    rule.id,
                )
            )
            conn.commit()

    def delete_recurrence_rule(self, rule_id: int) -> bool:
        """Delete a recurrence rule."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM recurrence_rules WHERE id = ?", (rule_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_recurring_tasks(self) -> list[tuple[Todo, RecurrenceRule]]:
        """List all tasks with recurrence rules.

        Returns:
            List of (Todo, RecurrenceRule) tuples
        """
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT t.*, r.id as rule_id, r.task_id as r_task_id,
                       r.pattern, r.interval, r.days_of_week, r.day_of_month,
                       r.end_date as r_end_date, r.max_occurrences,
                       r.occurrences_created, r.created_at as r_created_at,
                       r.updated_at as r_updated_at
                FROM todos t
                JOIN recurrence_rules r ON t.id = r.task_id
                ORDER BY t.priority ASC, t.created_at DESC
                """
            ).fetchall()

            result = []
            for row in rows:
                todo = self._row_to_todo(row)
                rule = RecurrenceRule(
                    id=row["rule_id"],
                    task_id=row["r_task_id"],
                    pattern=RecurrencePattern(row["pattern"]),
                    interval=row["interval"],
                    days_of_week=json.loads(row["days_of_week"]) if row["days_of_week"] else None,
                    day_of_month=row["day_of_month"],
                    end_date=datetime.fromisoformat(row["r_end_date"]) if row["r_end_date"] else None,
                    max_occurrences=row["max_occurrences"],
                    occurrences_created=row["occurrences_created"],
                    created_at=datetime.fromisoformat(row["r_created_at"]) if row["r_created_at"] else datetime.now(),
                    updated_at=datetime.fromisoformat(row["r_updated_at"]) if row["r_updated_at"] else datetime.now(),
                )
                result.append((todo, rule))
            return result
