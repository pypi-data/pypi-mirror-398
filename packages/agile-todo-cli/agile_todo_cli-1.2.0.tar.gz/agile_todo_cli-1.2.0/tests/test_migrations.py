"""Tests for database migration framework."""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime

from todo_cli.migrations import MigrationManager


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()

    # Cleanup backup directory
    backup_dir = db_path.parent / '.migrations_backup'
    if backup_dir.exists():
        for backup_file in backup_dir.glob('*.db'):
            backup_file.unlink()
        backup_dir.rmdir()


@pytest.fixture
def v0_db(temp_db):
    """Create a v0 database with todos table only."""
    conn = sqlite3.connect(temp_db)
    conn.execute("""
        CREATE TABLE todos (
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

    # Insert some test data
    conn.execute("""
        INSERT INTO todos (task, priority, status, created_at)
        VALUES ('Test task 1', 1, 'todo', ?)
    """, (datetime.now().isoformat(),))

    conn.execute("""
        INSERT INTO todos (task, priority, status, project, created_at)
        VALUES ('Test task 2', 2, 'doing', 'test-project', ?)
    """, (datetime.now().isoformat(),))

    # Set version to 0
    conn.execute("PRAGMA user_version = 0")
    conn.commit()
    conn.close()

    return temp_db


class TestMigrationManager:
    """Test MigrationManager functionality."""

    def test_get_current_version_new_db(self, temp_db):
        """Test getting version from a new database."""
        migrator = MigrationManager(temp_db)
        conn = sqlite3.connect(temp_db)

        version = migrator.get_current_version(conn)
        assert version == 0

        conn.close()

    def test_set_version(self, temp_db):
        """Test setting database version."""
        migrator = MigrationManager(temp_db)
        conn = sqlite3.connect(temp_db)

        migrator.set_version(conn, 1)
        assert migrator.get_current_version(conn) == 1

        migrator.set_version(conn, 2)
        assert migrator.get_current_version(conn) == 2

        conn.close()

    def test_needs_migration_new_db(self, temp_db):
        """Test migration check on new database."""
        migrator = MigrationManager(temp_db)
        conn = sqlite3.connect(temp_db)

        assert migrator.needs_migration(conn) is True

        conn.close()

    def test_needs_migration_current_version(self, temp_db):
        """Test migration check on current version database."""
        migrator = MigrationManager(temp_db)
        conn = sqlite3.connect(temp_db)

        migrator.set_version(conn, MigrationManager.CURRENT_VERSION)
        assert migrator.needs_migration(conn) is False

        conn.close()

    def test_create_backup(self, v0_db):
        """Test backup creation before migration."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        backup_path = migrator._create_backup(conn, 0)

        assert backup_path.exists()
        assert backup_path.parent == migrator.backup_dir
        assert 'todo_v0_' in backup_path.name

        # Verify backup contains data
        backup_conn = sqlite3.connect(backup_path)
        count = backup_conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
        assert count == 2
        backup_conn.close()

        conn.close()

    def test_migrate_v0_to_v1(self, v0_db):
        """Test migration from v0 to v1."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Verify initial state
        assert migrator.get_current_version(conn) == 0

        # Run migration
        success = migrator.migrate(conn)
        assert success is True

        # Verify version updated
        assert migrator.get_current_version(conn) >= 1

        # Verify new tables created
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('projects', 'subtasks', 'cycles', 'cycle_tasks')
        """)
        tables = {row[0] for row in cursor.fetchall()}
        assert tables == {'projects', 'subtasks', 'cycles', 'cycle_tasks'}

        # Verify new columns added to todos
        cursor = conn.execute("PRAGMA table_info(todos)")
        columns = {row[1] for row in cursor.fetchall()}
        assert 'project_id' in columns
        assert 'kanban_column' in columns

        # Verify indexes created
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        indexes = {row[0] for row in cursor.fetchall()}

        # Check for key indexes
        assert 'idx_todos_status' in indexes
        assert 'idx_todos_priority' in indexes
        assert 'idx_todos_project_id' in indexes
        assert 'idx_todos_kanban_column' in indexes

        # Verify existing data preserved
        count = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
        assert count == 2

        conn.close()

    def test_migrate_v1_to_v2(self, v0_db):
        """Test migration from v1 to v2 (views)."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Run full migration
        success = migrator.migrate(conn)
        assert success is True
        assert migrator.get_current_version(conn) >= 2

        # Verify views created
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='view'
        """)
        views = {row[0] for row in cursor.fetchall()}
        assert 'kanban_board' in views
        assert 'project_hierarchy' in views
        assert 'active_cycle_tasks' in views

        conn.close()

    def test_migrate_v2_to_v3(self, v0_db):
        """Test migration from v2 to v3 (recurrence_rules table)."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Run full migration to v3
        success = migrator.migrate(conn)
        assert success is True
        assert migrator.get_current_version(conn) == 3

        # Verify recurrence_rules table created
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='recurrence_rules'
        """)
        tables = cursor.fetchall()
        assert len(tables) == 1

        # Verify recurrence_rules table columns
        cursor = conn.execute("PRAGMA table_info(recurrence_rules)")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {
            'id', 'task_id', 'pattern', 'interval', 'days_of_week',
            'day_of_month', 'end_date', 'max_occurrences', 'occurrences_created',
            'created_at', 'updated_at'
        }
        assert expected_columns.issubset(columns)

        # Verify indexes created
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_recurrence%'
        """)
        indexes = {row[0] for row in cursor.fetchall()}
        assert 'idx_recurrence_rules_task_id' in indexes
        assert 'idx_recurrence_rules_pattern' in indexes

        conn.close()

    def test_recurrence_rules_foreign_key(self, v0_db):
        """Test recurrence_rules foreign key to todos."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Run migration
        migrator.migrate(conn)

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        # Create a recurrence rule for task 1
        conn.execute("""
            INSERT INTO recurrence_rules (task_id, pattern, interval)
            VALUES (1, 'daily', 1)
        """)
        conn.commit()

        # Verify rule created
        cursor = conn.execute("SELECT * FROM recurrence_rules WHERE task_id = 1")
        rule = cursor.fetchone()
        assert rule is not None

        # Delete task 1 - should cascade delete the rule
        conn.execute("DELETE FROM todos WHERE id = 1")
        conn.commit()

        # Verify rule was deleted
        cursor = conn.execute("SELECT * FROM recurrence_rules WHERE task_id = 1")
        rule = cursor.fetchone()
        assert rule is None

        conn.close()

    def test_recurrence_rules_pattern_constraint(self, v0_db):
        """Test recurrence_rules pattern CHECK constraint."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Run migration
        migrator.migrate(conn)

        # Valid patterns should work
        valid_patterns = ['daily', 'weekly', 'monthly', 'yearly', 'custom']
        for i, pattern in enumerate(valid_patterns):
            conn.execute("""
                INSERT INTO recurrence_rules (task_id, pattern, interval)
                VALUES (?, ?, 1)
            """, (1, pattern))

        # Invalid pattern should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO recurrence_rules (task_id, pattern, interval)
                VALUES (1, 'invalid_pattern', 1)
            """)

        conn.close()

    def test_recurrence_rules_defaults(self, v0_db):
        """Test recurrence_rules default values."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Run migration
        migrator.migrate(conn)

        # Insert minimal rule
        conn.execute("""
            INSERT INTO recurrence_rules (task_id, pattern)
            VALUES (1, 'daily')
        """)
        conn.commit()

        # Verify defaults
        cursor = conn.execute("""
            SELECT interval, occurrences_created, created_at, updated_at
            FROM recurrence_rules WHERE task_id = 1
        """)
        row = cursor.fetchone()
        interval, occurrences, created_at, updated_at = row

        assert interval == 1  # Default interval
        assert occurrences == 0  # Default occurrences_created
        assert created_at is not None  # Should have timestamp
        assert updated_at is not None  # Should have timestamp

        conn.close()

    def test_migration_idempotent(self, v0_db):
        """Test that migrations are idempotent."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Run migration twice
        success1 = migrator.migrate(conn)
        assert success1 is True

        # Get row count
        count1 = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]

        # Try to migrate again
        success2 = migrator.migrate(conn)
        assert success2 is True

        # Verify no duplicate data
        count2 = conn.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
        assert count1 == count2

        conn.close()

    def test_migration_preserves_data(self, v0_db):
        """Test that migration preserves existing todo data."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Get original data
        cursor = conn.execute("SELECT id, task, priority, status FROM todos ORDER BY id")
        original_data = cursor.fetchall()

        # Run migration
        migrator.migrate(conn)

        # Verify data preserved
        cursor = conn.execute("SELECT id, task, priority, status FROM todos ORDER BY id")
        migrated_data = cursor.fetchall()

        assert original_data == migrated_data

        conn.close()

    def test_foreign_key_constraints(self, v0_db):
        """Test that foreign key constraints work correctly."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Run migration
        migrator.migrate(conn)

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        # Create a project
        cursor = conn.execute("""
            INSERT INTO projects (name, created_at, updated_at)
            VALUES ('Test Project', ?, ?)
        """, (datetime.now().isoformat(), datetime.now().isoformat()))
        project_id = cursor.lastrowid

        # Update a todo with the project
        conn.execute("""
            UPDATE todos SET project_id = ? WHERE id = 1
        """, (project_id,))

        # Verify relationship
        cursor = conn.execute("""
            SELECT t.id, t.task, p.name
            FROM todos t
            JOIN projects p ON t.project_id = p.id
            WHERE t.id = 1
        """)
        result = cursor.fetchone()
        assert result is not None
        assert result[2] == 'Test Project'

        # Test CASCADE delete
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))

        # Verify todo's project_id is SET NULL
        cursor = conn.execute("SELECT project_id FROM todos WHERE id = 1")
        project_id_after = cursor.fetchone()[0]
        assert project_id_after is None

        conn.close()

    def test_kanban_column_default(self, v0_db):
        """Test that kanban_column defaults to 'backlog'."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Run migration
        migrator.migrate(conn)

        # Check existing todos have default kanban_column
        cursor = conn.execute("SELECT kanban_column FROM todos")
        columns = cursor.fetchall()

        for col in columns:
            assert col[0] == 'backlog'

        conn.close()

    def test_get_migration_history(self, v0_db):
        """Test getting migration history."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Run migration (creates backup)
        migrator.migrate(conn)

        # Get history
        history = migrator.get_migration_history()

        assert len(history) > 0
        assert history[0]['version'] == 0
        assert 'timestamp' in history[0]
        assert 'path' in history[0]
        assert 'size' in history[0]

        conn.close()

    def test_indexes_improve_performance(self, v0_db):
        """Test that indexes are created for performance."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Run migration
        migrator.migrate(conn)

        # Get all indexes on todos table
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='todos'
        """)
        indexes = {row[0] for row in cursor.fetchall()}

        # Verify key performance indexes exist
        required_indexes = {
            'idx_todos_status',
            'idx_todos_priority',
            'idx_todos_project_id',
            'idx_todos_kanban_column',
            'idx_todos_status_priority',
            'idx_todos_project_status',
            'idx_todos_kanban_priority'
        }

        assert required_indexes.issubset(indexes)

        conn.close()

    def test_views_work_correctly(self, v0_db):
        """Test that views return correct data."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Run migration
        migrator.migrate(conn)

        # Test kanban_board view
        cursor = conn.execute("SELECT * FROM kanban_board")
        kanban_tasks = cursor.fetchall()
        assert len(kanban_tasks) > 0

        # Test project_hierarchy view (should be empty since no projects)
        cursor = conn.execute("SELECT * FROM project_hierarchy")
        projects = cursor.fetchall()
        assert len(projects) == 0

        # Test active_cycle_tasks view (should be empty since no cycles)
        cursor = conn.execute("SELECT * FROM active_cycle_tasks")
        cycle_tasks = cursor.fetchall()
        assert len(cycle_tasks) == 0

        conn.close()

    def test_subtask_relationships(self, v0_db):
        """Test parent-child task relationships."""
        migrator = MigrationManager(v0_db)
        conn = sqlite3.connect(v0_db)

        # Run migration
        migrator.migrate(conn)

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        # Create subtask relationship
        conn.execute("""
            INSERT INTO subtasks (parent_task_id, child_task_id, created_at)
            VALUES (1, 2, ?)
        """, (datetime.now().isoformat(),))

        # Verify relationship created
        cursor = conn.execute("""
            SELECT parent_task_id, child_task_id FROM subtasks
        """)
        result = cursor.fetchone()
        assert result == (1, 2)

        # Test CASCADE delete on parent
        conn.execute("DELETE FROM todos WHERE id = 1")

        # Verify subtask relationship removed
        count = conn.execute("SELECT COUNT(*) FROM subtasks").fetchone()[0]
        assert count == 0

        conn.close()


class TestMigrationIntegration:
    """Test migration integration with Database class."""

    def test_database_auto_migrates(self, temp_db):
        """Test that Database class automatically migrates on init."""
        from todo_cli.database import Database

        # Create v0 database manually
        conn = sqlite3.connect(temp_db)
        conn.execute("""
            CREATE TABLE todos (
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
        conn.execute("PRAGMA user_version = 0")
        conn.commit()
        conn.close()

        # Initialize Database (should trigger migration)
        db = Database(temp_db)

        # Verify migration completed
        with db._get_conn() as conn:
            migrator = MigrationManager(temp_db)
            version = migrator.get_current_version(conn)
            assert version == MigrationManager.CURRENT_VERSION

            # Verify new tables exist
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('projects', 'subtasks', 'cycles', 'cycle_tasks')
            """)
            tables = {row[0] for row in cursor.fetchall()}
            assert len(tables) == 4
