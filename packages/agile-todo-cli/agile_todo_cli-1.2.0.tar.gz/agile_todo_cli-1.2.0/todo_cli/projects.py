"""Project management operations for Todo CLI."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .config import get_config


@dataclass
class Project:
    """Project data model."""
    id: int
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    archived: bool = False
    created_at: datetime = None
    updated_at: datetime = None

    # Statistics (populated from queries)
    total_tasks: int = 0
    completed_tasks: int = 0
    active_tasks: int = 0


class ProjectManager:
    """Manages project CRUD operations."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize project manager.

        Args:
            db_path: Path to database file. Uses config default if None.
        """
        if db_path is None:
            db_path = get_config().get_db_path()
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_project(self, name: str, description: Optional[str] = None,
                      color: Optional[str] = None) -> Project:
        """Create a new project.

        Args:
            name: Project name (must be unique, case-insensitive)
            description: Optional project description
            color: Optional color for display (e.g., 'blue', '#FF0000')

        Returns:
            Created Project object

        Raises:
            ValueError: If project name already exists (case-insensitive)
        """
        # Validate name is not empty
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")

        name = name.strip()

        # Check for duplicate name (case-insensitive)
        existing = self.get_project_by_name(name)
        if existing:
            raise ValueError(f"Project '{name}' already exists")

        conn = self._get_conn()
        try:
            now = datetime.now().isoformat()
            cursor = conn.execute(
                """
                INSERT INTO projects (name, description, color, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, description, color, now, now)
            )
            conn.commit()
            project_id = cursor.lastrowid

            return self.get_project(project_id)
        finally:
            conn.close()

    def get_project(self, project_id: int) -> Optional[Project]:
        """Get project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project object or None if not found
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                """
                SELECT
                    p.*,
                    COUNT(DISTINCT t.id) as total_tasks,
                    COUNT(DISTINCT CASE WHEN t.status = 'done' THEN t.id END) as completed_tasks,
                    COUNT(DISTINCT CASE WHEN t.status != 'done' THEN t.id END) as active_tasks
                FROM projects p
                LEFT JOIN todos t ON p.id = t.project_id
                WHERE p.id = ?
                GROUP BY p.id
                """,
                (project_id,)
            ).fetchone()

            if row:
                return self._row_to_project(row)
            return None
        finally:
            conn.close()

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """Get project by name (case-insensitive).

        Args:
            name: Project name (case-insensitive match)

        Returns:
            Project object or None if not found
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                """
                SELECT
                    p.*,
                    COUNT(DISTINCT t.id) as total_tasks,
                    COUNT(DISTINCT CASE WHEN t.status = 'done' THEN t.id END) as completed_tasks,
                    COUNT(DISTINCT CASE WHEN t.status != 'done' THEN t.id END) as active_tasks
                FROM projects p
                LEFT JOIN todos t ON p.id = t.project_id
                WHERE LOWER(p.name) = LOWER(?)
                GROUP BY p.id
                """,
                (name,)
            ).fetchone()

            if row:
                return self._row_to_project(row)
            return None
        finally:
            conn.close()

    def list_projects(self, archived: bool = False,
                     include_stats: bool = True) -> list[Project]:
        """List all projects.

        Args:
            archived: If True, show archived projects. If False, show active only.
            include_stats: If True, calculate task statistics for each project.

        Returns:
            List of Project objects
        """
        conn = self._get_conn()
        try:
            if include_stats:
                rows = conn.execute(
                    """
                    SELECT
                        p.*,
                        COUNT(DISTINCT t.id) as total_tasks,
                        COUNT(DISTINCT CASE WHEN t.status = 'done' THEN t.id END) as completed_tasks,
                        COUNT(DISTINCT CASE WHEN t.status != 'done' THEN t.id END) as active_tasks
                    FROM projects p
                    LEFT JOIN todos t ON p.id = t.project_id
                    WHERE p.archived = ?
                    GROUP BY p.id
                    ORDER BY p.name COLLATE NOCASE
                    """,
                    (1 if archived else 0,)
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT * FROM projects
                    WHERE archived = ?
                    ORDER BY name COLLATE NOCASE
                    """,
                    (1 if archived else 0,)
                ).fetchall()

            return [self._row_to_project(row) for row in rows]
        finally:
            conn.close()

    def update_project(self, project_id: int, name: Optional[str] = None,
                      description: Optional[str] = None,
                      color: Optional[str] = None) -> Optional[Project]:
        """Update project details.

        Args:
            project_id: Project ID
            name: New name (must be unique if provided)
            description: New description
            color: New color

        Returns:
            Updated Project object or None if not found

        Raises:
            ValueError: If new name already exists
        """
        project = self.get_project(project_id)
        if not project:
            return None

        # Check for name uniqueness if changing name
        if name and name.strip() and name.strip().lower() != project.name.lower():
            existing = self.get_project_by_name(name)
            if existing:
                raise ValueError(f"Project '{name}' already exists")

        conn = self._get_conn()
        try:
            # Build update query dynamically
            updates = []
            params = []

            if name is not None and name.strip():
                updates.append("name = ?")
                params.append(name.strip())

            if description is not None:
                updates.append("description = ?")
                params.append(description)

            if color is not None:
                updates.append("color = ?")
                params.append(color)

            if updates:
                updates.append("updated_at = ?")
                params.append(datetime.now().isoformat())
                params.append(project_id)

                conn.execute(
                    f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
                    params
                )
                conn.commit()

            return self.get_project(project_id)
        finally:
            conn.close()

    def delete_project(self, project_id: int) -> bool:
        """Delete a project. Tasks associated with the project will persist
        with their project_id set to NULL.

        Args:
            project_id: Project ID to delete

        Returns:
            True if deleted, False if not found
        """
        conn = self._get_conn()
        try:
            # Set project_id to NULL for all tasks in this project
            conn.execute(
                "UPDATE todos SET project_id = NULL WHERE project_id = ?",
                (project_id,)
            )

            # Delete the project
            cursor = conn.execute(
                "DELETE FROM projects WHERE id = ?",
                (project_id,)
            )
            conn.commit()

            return cursor.rowcount > 0
        finally:
            conn.close()

    def archive_project(self, project_id: int) -> Optional[Project]:
        """Archive a project (soft delete).

        Args:
            project_id: Project ID to archive

        Returns:
            Archived Project object or None if not found
        """
        conn = self._get_conn()
        try:
            conn.execute(
                """
                UPDATE projects
                SET archived = 1, updated_at = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), project_id)
            )
            conn.commit()

            return self.get_project(project_id)
        finally:
            conn.close()

    def unarchive_project(self, project_id: int) -> Optional[Project]:
        """Unarchive a project.

        Args:
            project_id: Project ID to unarchive

        Returns:
            Unarchived Project object or None if not found
        """
        conn = self._get_conn()
        try:
            conn.execute(
                """
                UPDATE projects
                SET archived = 0, updated_at = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), project_id)
            )
            conn.commit()

            return self.get_project(project_id)
        finally:
            conn.close()

    def get_project_stats(self, project_id: int) -> Optional[dict]:
        """Get detailed statistics for a project.

        Args:
            project_id: Project ID

        Returns:
            Dictionary with project statistics or None if not found
        """
        project = self.get_project(project_id)
        if not project:
            return None

        conn = self._get_conn()
        try:
            # Get earliest due date
            earliest_due = conn.execute(
                """
                SELECT MIN(due_date)
                FROM todos
                WHERE project_id = ? AND status != 'done' AND due_date IS NOT NULL
                """,
                (project_id,)
            ).fetchone()[0]

            # Get total time spent
            total_time = conn.execute(
                """
                SELECT SUM(time_spent_seconds)
                FROM todos
                WHERE project_id = ?
                """,
                (project_id,)
            ).fetchone()[0] or 0

            # Get priority breakdown
            priority_counts = {}
            for row in conn.execute(
                """
                SELECT priority, COUNT(*) as count
                FROM todos
                WHERE project_id = ? AND status != 'done'
                GROUP BY priority
                """,
                (project_id,)
            ).fetchall():
                priority_counts[row['priority']] = row['count']

            return {
                'project': project,
                'total_tasks': project.total_tasks,
                'completed_tasks': project.completed_tasks,
                'active_tasks': project.active_tasks,
                'completion_rate': project.completed_tasks / project.total_tasks * 100 if project.total_tasks > 0 else 0,
                'earliest_due_date': datetime.fromisoformat(earliest_due) if earliest_due else None,
                'total_time_seconds': total_time,
                'priority_breakdown': priority_counts
            }
        finally:
            conn.close()

    def _row_to_project(self, row: sqlite3.Row) -> Project:
        """Convert database row to Project object."""
        # Try to get stats columns if they exist
        try:
            total_tasks = row['total_tasks']
            completed_tasks = row['completed_tasks']
            active_tasks = row['active_tasks']
        except (KeyError, IndexError):
            # Stats not included in query
            total_tasks = 0
            completed_tasks = 0
            active_tasks = 0

        return Project(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            color=row['color'],
            archived=bool(row['archived']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            active_tasks=active_tasks
        )
