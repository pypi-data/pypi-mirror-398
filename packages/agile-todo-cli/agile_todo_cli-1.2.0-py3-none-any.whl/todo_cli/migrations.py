"""Database migration framework for todo-cli.

Handles versioned database schema migrations with automatic backup and rollback.
Uses SQLite PRAGMA user_version for version tracking.
"""

import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class MigrationManager:
    """Manages database schema migrations with version tracking and rollback support.

    Migration versions:
    - v0: Initial schema (todos table only)
    - v1: Adds projects, subtasks, cycles, cycle_tasks tables + indexes
    - v2: Adds views for KANBAN and project hierarchies
    - v3: Adds recurrence_rules table for recurring tasks
    """

    CURRENT_VERSION = 3

    def __init__(self, db_path: Path):
        """Initialize migration manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.backup_dir = self.db_path.parent / '.migrations_backup'
        self.backup_dir.mkdir(exist_ok=True)

    def get_current_version(self, conn: sqlite3.Connection) -> int:
        """Get current database schema version.

        Args:
            conn: Database connection

        Returns:
            Current version number (0 if not set)
        """
        cursor = conn.execute("PRAGMA user_version")
        version = cursor.fetchone()[0]
        return version

    def set_version(self, conn: sqlite3.Connection, version: int) -> None:
        """Set database schema version.

        Args:
            conn: Database connection
            version: Version number to set
        """
        conn.execute(f"PRAGMA user_version = {version}")
        conn.commit()

    def needs_migration(self, conn: sqlite3.Connection) -> bool:
        """Check if database needs migration.

        Args:
            conn: Database connection

        Returns:
            True if migration needed, False otherwise
        """
        current = self.get_current_version(conn)
        return current < self.CURRENT_VERSION

    def migrate(self, conn: sqlite3.Connection) -> bool:
        """Run all pending migrations.

        Migrations are idempotent and can be safely re-run.
        Automatically creates backup before migration.
        Rolls back on failure.

        Args:
            conn: Database connection

        Returns:
            True if migration successful, False otherwise
        """
        current_version = self.get_current_version(conn)

        if current_version >= self.CURRENT_VERSION:
            return True

        # Create backup before migration
        backup_path = self._create_backup(conn, current_version)

        try:
            # Run migrations sequentially
            if current_version < 1:
                self._migrate_v0_to_v1(conn)
                self.set_version(conn, 1)
                current_version = 1

            if current_version < 2:
                self._migrate_v1_to_v2(conn)
                self.set_version(conn, 2)
                current_version = 2

            if current_version < 3:
                self._migrate_v2_to_v3(conn)
                self.set_version(conn, 3)
                current_version = 3

            return True

        except Exception as e:
            # Rollback on failure
            print(f"Migration failed: {e}")
            print(f"Rolling back to version {current_version}...")
            self.rollback(conn, current_version, backup_path)
            return False

    def _create_backup(self, conn: sqlite3.Connection, version: int) -> Path:
        """Create database backup before migration.

        Args:
            conn: Database connection
            version: Current version being backed up

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"todo_v{version}_{timestamp}.db"
        backup_path = self.backup_dir / backup_name

        # Close connection temporarily for file copy
        conn.commit()
        shutil.copy2(self.db_path, backup_path)

        return backup_path

    def rollback(self, conn: sqlite3.Connection, target_version: int,
                 backup_path: Optional[Path] = None) -> bool:
        """Rollback to previous version using backup.

        Args:
            conn: Database connection
            target_version: Version to roll back to
            backup_path: Optional specific backup to restore

        Returns:
            True if rollback successful, False otherwise
        """
        try:
            if backup_path is None:
                # Find most recent backup for target version
                backups = sorted(self.backup_dir.glob(f"todo_v{target_version}_*.db"))
                if not backups:
                    print(f"No backup found for version {target_version}")
                    return False
                backup_path = backups[-1]

            # Close connection and restore backup
            conn.close()
            shutil.copy2(backup_path, self.db_path)
            print(f"Rolled back to version {target_version} using {backup_path.name}")
            return True

        except Exception as e:
            print(f"Rollback failed: {e}")
            return False

    def _migrate_v0_to_v1(self, conn: sqlite3.Connection) -> None:
        """Migrate from v0 to v1.

        Changes:
        - Create projects table
        - Create subtasks table
        - Create cycles table
        - Create cycle_tasks table
        - Add project_id column to todos
        - Add kanban_column column to todos
        - Create performance indexes

        Args:
            conn: Database connection
        """
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        # Create projects table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                color TEXT,
                archived INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Create subtasks table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subtasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_task_id INTEGER NOT NULL,
                child_task_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (parent_task_id) REFERENCES todos(id) ON DELETE CASCADE,
                FOREIGN KEY (child_task_id) REFERENCES todos(id) ON DELETE CASCADE,
                UNIQUE (parent_task_id, child_task_id)
            )
        """)

        # Create cycles table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)

        # Create cycle_tasks table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cycle_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                added_at TEXT NOT NULL,
                FOREIGN KEY (cycle_id) REFERENCES cycles(id) ON DELETE CASCADE,
                FOREIGN KEY (task_id) REFERENCES todos(id) ON DELETE CASCADE,
                UNIQUE (cycle_id, task_id)
            )
        """)

        # Add new columns to todos table if they don't exist
        # Check if columns exist first
        cursor = conn.execute("PRAGMA table_info(todos)")
        columns = {row[1] for row in cursor.fetchall()}

        if 'project_id' not in columns:
            conn.execute("""
                ALTER TABLE todos
                ADD COLUMN project_id INTEGER
                REFERENCES projects(id) ON DELETE SET NULL
            """)

        if 'kanban_column' not in columns:
            conn.execute("""
                ALTER TABLE todos
                ADD COLUMN kanban_column TEXT DEFAULT 'backlog'
            """)

        # Create indexes for performance
        self._create_indexes_v1(conn)

        conn.commit()

    def _create_indexes_v1(self, conn: sqlite3.Connection) -> None:
        """Create performance indexes for v1 schema.

        Args:
            conn: Database connection
        """
        indexes = [
            # Todos table indexes
            ("idx_todos_status", "todos", "status"),
            ("idx_todos_priority", "todos", "priority"),
            ("idx_todos_project_id", "todos", "project_id"),
            ("idx_todos_kanban_column", "todos", "kanban_column"),
            ("idx_todos_due_date", "todos", "due_date"),
            ("idx_todos_created_at", "todos", "created_at"),

            # Composite indexes for common queries
            ("idx_todos_status_priority", "todos", "status, priority DESC"),
            ("idx_todos_project_status", "todos", "project_id, status"),
            ("idx_todos_kanban_priority", "todos", "kanban_column, priority DESC"),

            # Projects table indexes
            ("idx_projects_archived", "projects", "archived"),
            ("idx_projects_name", "projects", "name"),

            # Subtasks table indexes
            ("idx_subtasks_parent", "subtasks", "parent_task_id"),
            ("idx_subtasks_child", "subtasks", "child_task_id"),

            # Cycles table indexes
            ("idx_cycles_status", "cycles", "status"),
            ("idx_cycles_dates", "cycles", "start_date, end_date"),

            # Cycle_tasks table indexes
            ("idx_cycle_tasks_cycle", "cycle_tasks", "cycle_id"),
            ("idx_cycle_tasks_task", "cycle_tasks", "task_id"),
        ]

        for idx_name, table, columns in indexes:
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {idx_name}
                ON {table} ({columns})
            """)

    def _migrate_v1_to_v2(self, conn: sqlite3.Connection) -> None:
        """Migrate from v1 to v2.

        Changes:
        - Create KANBAN board view
        - Create project hierarchy view
        - Create active cycle view

        Args:
            conn: Database connection
        """
        # Create KANBAN board view
        conn.execute("""
            CREATE VIEW IF NOT EXISTS kanban_board AS
            SELECT
                t.id,
                t.task,
                t.priority,
                t.status,
                t.kanban_column,
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
            WHERE t.status != 'done'
            ORDER BY
                CASE t.kanban_column
                    WHEN 'backlog' THEN 1
                    WHEN 'todo' THEN 2
                    WHEN 'in-progress' THEN 3
                    WHEN 'review' THEN 4
                    ELSE 5
                END,
                t.priority DESC,
                t.created_at ASC
        """)

        # Create project hierarchy view
        conn.execute("""
            CREATE VIEW IF NOT EXISTS project_hierarchy AS
            SELECT
                p.id as project_id,
                p.name as project_name,
                p.color,
                COUNT(DISTINCT t.id) as total_tasks,
                COUNT(DISTINCT CASE WHEN t.status = 'done' THEN t.id END) as completed_tasks,
                COUNT(DISTINCT CASE WHEN t.status != 'done' THEN t.id END) as active_tasks,
                MIN(t.due_date) as earliest_due_date,
                MAX(COALESCE(t.completed_at, t.created_at)) as last_activity
            FROM projects p
            LEFT JOIN todos t ON p.id = t.project_id
            WHERE p.archived = 0
            GROUP BY p.id, p.name, p.color
        """)

        # Create active cycle view
        conn.execute("""
            CREATE VIEW IF NOT EXISTS active_cycle_tasks AS
            SELECT
                c.id as cycle_id,
                c.name as cycle_name,
                c.start_date,
                c.end_date,
                t.id as task_id,
                t.task,
                t.status,
                t.priority,
                t.project_id,
                p.name as project_name,
                ct.added_at
            FROM cycles c
            JOIN cycle_tasks ct ON c.id = ct.cycle_id
            JOIN todos t ON ct.task_id = t.id
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE c.status = 'active'
            ORDER BY t.priority DESC, ct.added_at ASC
        """)

        conn.commit()

    def _migrate_v2_to_v3(self, conn: sqlite3.Connection) -> None:
        """Migrate from v2 to v3.

        Changes:
        - Create recurrence_rules table for recurring tasks

        Args:
            conn: Database connection
        """
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        # Create recurrence_rules table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recurrence_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                pattern TEXT NOT NULL CHECK(pattern IN ('daily', 'weekly', 'monthly', 'yearly', 'custom')),
                interval INTEGER DEFAULT 1,
                days_of_week TEXT,
                day_of_month INTEGER,
                end_date TEXT,
                max_occurrences INTEGER,
                occurrences_created INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES todos(id) ON DELETE CASCADE
            )
        """)

        # Create indexes for recurrence_rules
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_recurrence_rules_task_id
            ON recurrence_rules (task_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_recurrence_rules_pattern
            ON recurrence_rules (pattern)
        """)

        conn.commit()

    def get_migration_history(self) -> list[dict]:
        """Get history of all database backups.

        Returns:
            List of backup info dicts with version, timestamp, and path
        """
        backups = []
        for backup_file in sorted(self.backup_dir.glob("todo_v*.db")):
            # Parse filename: todo_v{version}_{timestamp}.db
            parts = backup_file.stem.split('_')
            if len(parts) >= 3:
                version = parts[1].replace('v', '')
                timestamp = '_'.join(parts[2:])
                backups.append({
                    'version': int(version),
                    'timestamp': timestamp,
                    'path': str(backup_file),
                    'size': backup_file.stat().st_size
                })
        return backups
