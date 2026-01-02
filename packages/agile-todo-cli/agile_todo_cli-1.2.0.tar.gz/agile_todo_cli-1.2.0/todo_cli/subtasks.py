"""Hierarchical task relationship management for Todo CLI.

This module manages parent-child relationships between tasks, enabling
users to break down large features into sub-tasks with a maximum nesting
depth of 1 level (parent -> children only, no grandchildren).
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .config import get_config


@dataclass
class SubtaskRelation:
    """Represents a parent-child relationship."""
    id: int
    parent_task_id: int
    child_task_id: int
    created_at: datetime


class SubtaskManager:
    """Manages parent-child task relationships.

    Enforces:
    - Maximum 1-level nesting (no grandchildren)
    - No circular references
    - No self-references
    - Proper cascade behavior on delete
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize subtask manager.

        Args:
            db_path: Path to database file. Uses config default if None.
        """
        if db_path is None:
            db_path = get_config().get_db_path()
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _task_exists(self, conn: sqlite3.Connection, task_id: int) -> bool:
        """Check if a task exists."""
        result = conn.execute(
            "SELECT 1 FROM todos WHERE id = ?",
            (task_id,)
        ).fetchone()
        return result is not None

    def can_add_subtask(self, parent_id: int, child_id: int) -> tuple[bool, str]:
        """Validate if a subtask relationship can be created.

        Checks:
        1. Both tasks exist
        2. No self-reference (parent_id != child_id)
        3. Child is not already a subtask (depth constraint)
        4. Parent is not already a subtask (depth constraint)
        5. Child doesn't have children (would create depth > 1)

        Args:
            parent_id: ID of the parent task
            child_id: ID of the child task

        Returns:
            Tuple of (can_add: bool, error_message: str)
            If can_add is True, error_message is empty.
        """
        # Check self-reference
        if parent_id == child_id:
            return False, "A task cannot be its own subtask"

        conn = self._get_conn()
        try:
            # Check both tasks exist
            if not self._task_exists(conn, parent_id):
                return False, f"Parent task #{parent_id} not found"
            if not self._task_exists(conn, child_id):
                return False, f"Child task #{child_id} not found"

            # Check if relationship already exists
            existing = conn.execute(
                "SELECT 1 FROM subtasks WHERE parent_task_id = ? AND child_task_id = ?",
                (parent_id, child_id)
            ).fetchone()
            if existing:
                return False, f"Task #{child_id} is already a subtask of #{parent_id}"

            # Check if child is already a subtask of another task (depth constraint)
            child_parent = conn.execute(
                "SELECT parent_task_id FROM subtasks WHERE child_task_id = ?",
                (child_id,)
            ).fetchone()
            if child_parent:
                return False, (
                    f"Task #{child_id} is already a subtask of #{child_parent['parent_task_id']}. "
                    "A task can only have one parent."
                )

            # Check if parent is already a subtask (depth constraint - no grandchildren)
            parent_is_child = conn.execute(
                "SELECT parent_task_id FROM subtasks WHERE child_task_id = ?",
                (parent_id,)
            ).fetchone()
            if parent_is_child:
                return False, (
                    f"Task #{parent_id} is already a subtask of #{parent_is_child['parent_task_id']}. "
                    "Cannot add subtasks to a task that is already a subtask (max depth: 1)."
                )

            # Check if child has children (would create depth > 1)
            child_has_children = conn.execute(
                "SELECT COUNT(*) as count FROM subtasks WHERE parent_task_id = ?",
                (child_id,)
            ).fetchone()
            if child_has_children['count'] > 0:
                return False, (
                    f"Task #{child_id} has {child_has_children['count']} subtask(s). "
                    "Cannot make a parent task into a subtask."
                )

            return True, ""
        finally:
            conn.close()

    def add_subtask(self, parent_id: int, child_id: int,
                    position: Optional[int] = None) -> tuple[bool, str]:
        """Create a parent-child relationship between tasks.

        Args:
            parent_id: ID of the parent task
            child_id: ID of the child task
            position: Ignored (kept for API compatibility, ordering by created_at)

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Validate first
        can_add, error = self.can_add_subtask(parent_id, child_id)
        if not can_add:
            return False, error

        conn = self._get_conn()
        try:
            # Insert relationship (no position column in current schema)
            conn.execute(
                """
                INSERT INTO subtasks (parent_task_id, child_task_id, created_at)
                VALUES (?, ?, ?)
                """,
                (parent_id, child_id, datetime.now().isoformat())
            )
            conn.commit()

            return True, f"Task #{child_id} added as subtask of #{parent_id}"
        except sqlite3.IntegrityError as e:
            return False, f"Database error: {e}"
        finally:
            conn.close()

    def remove_subtask(self, parent_id: int, child_id: int) -> tuple[bool, str]:
        """Remove a parent-child relationship (child becomes top-level).

        This only removes the relationship; the child task is not deleted.

        Args:
            parent_id: ID of the parent task
            child_id: ID of the child task

        Returns:
            Tuple of (success: bool, message: str)
        """
        conn = self._get_conn()
        try:
            # Check if relationship exists
            existing = conn.execute(
                "SELECT 1 FROM subtasks WHERE parent_task_id = ? AND child_task_id = ?",
                (parent_id, child_id)
            ).fetchone()

            if not existing:
                return False, f"Task #{child_id} is not a subtask of #{parent_id}"

            # Remove relationship
            conn.execute(
                "DELETE FROM subtasks WHERE parent_task_id = ? AND child_task_id = ?",
                (parent_id, child_id)
            )
            conn.commit()

            return True, f"Task #{child_id} unlinked from parent #{parent_id}"
        finally:
            conn.close()

    def get_children(self, parent_id: int) -> list[dict]:
        """Get all children of a parent task.

        Args:
            parent_id: ID of the parent task

        Returns:
            List of child task dictionaries, ordered by created_at
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT t.*
                FROM todos t
                JOIN subtasks s ON t.id = s.child_task_id
                WHERE s.parent_task_id = ?
                ORDER BY s.created_at, t.created_at
                """,
                (parent_id,)
            ).fetchall()

            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_parent(self, child_id: int) -> Optional[dict]:
        """Get the parent of a child task.

        Args:
            child_id: ID of the child task

        Returns:
            Parent task dictionary, or None if task is top-level
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                """
                SELECT t.*
                FROM todos t
                JOIN subtasks s ON t.id = s.parent_task_id
                WHERE s.child_task_id = ?
                """,
                (child_id,)
            ).fetchone()

            return dict(row) if row else None
        finally:
            conn.close()

    def is_subtask(self, task_id: int) -> bool:
        """Check if a task is a subtask (has a parent).

        Args:
            task_id: ID of the task to check

        Returns:
            True if the task is a subtask, False otherwise
        """
        conn = self._get_conn()
        try:
            result = conn.execute(
                "SELECT 1 FROM subtasks WHERE child_task_id = ? LIMIT 1",
                (task_id,)
            ).fetchone()
            return result is not None
        finally:
            conn.close()

    def has_children(self, task_id: int) -> bool:
        """Check if a task has children (is a parent).

        Args:
            task_id: ID of the task to check

        Returns:
            True if the task has children, False otherwise
        """
        conn = self._get_conn()
        try:
            result = conn.execute(
                "SELECT 1 FROM subtasks WHERE parent_task_id = ? LIMIT 1",
                (task_id,)
            ).fetchone()
            return result is not None
        finally:
            conn.close()

    def get_child_count(self, task_id: int) -> int:
        """Get the number of children for a task.

        Args:
            task_id: ID of the task

        Returns:
            Number of children
        """
        conn = self._get_conn()
        try:
            result = conn.execute(
                "SELECT COUNT(*) as count FROM subtasks WHERE parent_task_id = ?",
                (task_id,)
            ).fetchone()
            return result['count']
        finally:
            conn.close()

    def get_children_completion_status(self, parent_id: int) -> dict:
        """Get completion status of all children for a parent task.

        Args:
            parent_id: ID of the parent task

        Returns:
            Dictionary with:
            - total: Total number of children
            - completed: Number of completed children
            - incomplete_ids: List of IDs of incomplete children
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                """
                SELECT t.id, t.status
                FROM todos t
                JOIN subtasks s ON t.id = s.child_task_id
                WHERE s.parent_task_id = ?
                """,
                (parent_id,)
            ).fetchall()

            total = len(rows)
            completed = sum(1 for row in rows if row['status'] == 'done')
            incomplete_ids = [row['id'] for row in rows if row['status'] != 'done']

            return {
                'total': total,
                'completed': completed,
                'incomplete_ids': incomplete_ids
            }
        finally:
            conn.close()

    def can_complete_parent(self, parent_id: int) -> tuple[bool, str]:
        """Check if a parent task can be completed.

        A parent can only be completed if all its children are complete.

        Args:
            parent_id: ID of the parent task

        Returns:
            Tuple of (can_complete: bool, message: str)
        """
        status = self.get_children_completion_status(parent_id)

        if status['total'] == 0:
            return True, "Task has no subtasks"

        if status['incomplete_ids']:
            return False, (
                f"Cannot complete: {len(status['incomplete_ids'])} subtask(s) "
                f"still incomplete (IDs: {status['incomplete_ids']})"
            )

        return True, "All subtasks complete"

    def reorder_children(self, parent_id: int, child_ids: list[int]) -> tuple[bool, str]:
        """Reorder children (placeholder - current schema has no position column).

        Note: The current database schema does not have a position column.
        This method validates the child IDs but ordering is by created_at.

        Args:
            parent_id: ID of the parent task
            child_ids: List of child IDs in desired order

        Returns:
            Tuple of (success: bool, message: str)
        """
        conn = self._get_conn()
        try:
            # Verify all provided IDs are actually children of this parent
            existing_children = conn.execute(
                "SELECT child_task_id FROM subtasks WHERE parent_task_id = ?",
                (parent_id,)
            ).fetchall()
            existing_ids = {row['child_task_id'] for row in existing_children}

            provided_ids = set(child_ids)
            if provided_ids != existing_ids:
                missing = existing_ids - provided_ids
                extra = provided_ids - existing_ids
                errors = []
                if missing:
                    errors.append(f"Missing children: {missing}")
                if extra:
                    errors.append(f"Invalid children: {extra}")
                return False, "; ".join(errors)

            # Current schema has no position column - ordering is by created_at
            # Return success since IDs are valid (no actual reordering happens)
            return True, f"Validated {len(child_ids)} children (ordering by created_at)"
        finally:
            conn.close()

    def get_task_hierarchy_info(self, task_id: int) -> dict:
        """Get complete hierarchy information for a task.

        Args:
            task_id: ID of the task

        Returns:
            Dictionary with:
            - is_subtask: Whether this task is a child
            - parent_id: Parent task ID (if subtask)
            - has_children: Whether this task has children
            - child_count: Number of children
            - can_have_children: Whether children can be added
            - can_become_subtask: Whether this task can become a subtask
        """
        conn = self._get_conn()
        try:
            # Check if task exists
            if not self._task_exists(conn, task_id):
                return {'error': f'Task #{task_id} not found'}

            # Check if subtask
            parent_row = conn.execute(
                "SELECT parent_task_id FROM subtasks WHERE child_task_id = ?",
                (task_id,)
            ).fetchone()
            is_subtask = parent_row is not None
            parent_id = parent_row['parent_task_id'] if parent_row else None

            # Check for children
            child_count_row = conn.execute(
                "SELECT COUNT(*) as count FROM subtasks WHERE parent_task_id = ?",
                (task_id,)
            ).fetchone()
            child_count = child_count_row['count']
            has_children = child_count > 0

            return {
                'is_subtask': is_subtask,
                'parent_id': parent_id,
                'has_children': has_children,
                'child_count': child_count,
                'can_have_children': not is_subtask,  # Subtasks can't have children
                'can_become_subtask': not has_children and not is_subtask  # Parents can't become subtasks
            }
        finally:
            conn.close()
