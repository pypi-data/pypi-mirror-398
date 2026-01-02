# Architecture Design Document (ADD)
**Project:** Todo-CLI Feature Expansion - Advanced Project Management
**Version:** 1.0
**Date:** 2025-12-25
**Status:** Ready for Implementation

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Database Design](#2-database-design)
3. [Migration Framework](#3-migration-framework)
4. [Module Architecture](#4-module-architecture)
5. [Feature-Specific Designs](#5-feature-specific-designs)
6. [Performance Optimization Strategy](#6-performance-optimization-strategy)
7. [Terminal Compatibility Design](#7-terminal-compatibility-design)
8. [Technology Stack Validation](#8-technology-stack-validation)
9. [Testing Strategy](#9-testing-strategy)
10. [Risk Mitigation](#10-risk-mitigation)
11. [Epic 1 Implementation Blueprint](#11-epic-1-implementation-blueprint)

---

## 1. System Architecture Overview

### 1.1 Architectural Layers

The existing todo-cli architecture follows a clean layered pattern that will be preserved and extended:

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Layer (main.py)                      │
│  Typer commands, argument parsing, user interaction         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Business Logic Layer                        │
│  projects.py  │  subtasks.py  │  kanban.py  │  cycles.py   │
│  Feature-specific logic, validation, business rules         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Data Layer (database.py)                   │
│  SQLite operations, CRUD, queries, transactions             │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 Display Layer (display.py)                   │
│  Rich rendering, KANBAN board, tree views, tables           │
└─────────────────────────────────────────────────────────────┘
```

**Design Principles:**
- **Separation of Concerns:** Each layer has distinct responsibilities
- **Dependency Direction:** Top-down only (CLI → Logic → Data → Display)
- **Modularity:** New features in separate modules (projects.py, subtasks.py, kanban.py, cycles.py)
- **Testability:** Each layer independently testable with mocking
- **Single Responsibility:** Each module handles one feature domain

### 1.2 Data Flow Diagram

**Task Creation with Projects and Sub-tasks:**

```
User Command
    │
    ▼
[CLI: main.py]
    │ Parse args, validate
    ▼
[Logic: projects.py / subtasks.py]
    │ Business rules, validation
    ▼
[Data: database.py]
    │ SQL transaction
    ▼
[SQLite Database]
    │ Persist
    ▼
[Display: display.py]
    │ Format output
    ▼
User Feedback
```

**KANBAN Board Rendering:**

```
User Command: todo kanban --project myapp
    │
    ▼
[CLI: main.py]
    │ Parse filters
    ▼
[Logic: kanban.py]
    │ Build query, apply filters
    ▼
[Data: database.py]
    │ Execute optimized query with JOINs
    ▼
[SQLite Database]
    │ Return rows
    ▼
[Logic: kanban.py]
    │ Group by column, format data
    ▼
[Display: display.py (kanban_renderer.py)]
    │ Rich panels, box-drawing
    ▼
Terminal Output
```

### 1.3 Module Dependency Graph

```
main.py
  ├─ projects.py ──────┐
  ├─ subtasks.py ──────┤
  ├─ kanban.py ────────├──► database.py ──► SQLite
  └─ cycles.py ────────┘          │
                                  ▼
                             display.py
                                  │
                          ┌───────┴───────┐
                          │               │
                    kanban_renderer  tree_renderer
                          │               │
                          └───────┬───────┘
                                  ▼
                              Rich Library
```

**Dependency Rules:**
- Feature modules (projects, subtasks, kanban, cycles) are independent of each other
- All feature modules depend on database.py and display.py
- No circular dependencies
- main.py orchestrates feature modules but doesn't contain business logic

### 1.4 Key Integration Points

**Between Features:**

| Integration | Mechanism | Example |
|-------------|-----------|---------|
| Projects ↔ Tasks | Foreign key `todos.project_id` | Filter tasks by project in KANBAN |
| Sub-tasks ↔ Tree View | `subtasks` table with parent_id/child_id | Hierarchical display in list --tree |
| Cycles ↔ KANBAN | `cycle_tasks` JOIN with KANBAN filtering | `todo kanban --cycle "Sprint 2"` |
| Projects ↔ Cycles | Query across both dimensions | Cycle report filtered by project |
| Sub-tasks ↔ KANBAN | Tree rendering within KANBAN columns | Show parent-child in board |

**Data Consistency Rules:**
- Deleting project does NOT delete tasks (tasks become unassigned)
- Deleting parent task orphans children (they become top-level)
- Deleting cycle unassigns tasks (they return to backlog)
- Moving task to "Done" in KANBAN auto-completes task
- Completing parent task requires all children complete

---

## 2. Database Design

### 2.1 Complete Schema (DDL)

```sql
-- ============================================================================
-- EXISTING TABLE: todos (extended)
-- ============================================================================

CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT NOT NULL,
    priority INTEGER DEFAULT 2,
    status TEXT DEFAULT 'todo',
    project TEXT,  -- Legacy: will be migrated to project_id
    tags TEXT DEFAULT '[]',
    due_date TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    time_spent_seconds INTEGER DEFAULT 0,
    timer_started TEXT,

    -- NEW COLUMNS (added via migration)
    project_id INTEGER,  -- Foreign key to projects table
    kanban_column TEXT DEFAULT 'backlog',  -- KANBAN column state

    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
);

-- ============================================================================
-- NEW TABLE: projects
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'archived')),
    created_at TEXT NOT NULL,

    -- Metadata for future enhancements
    updated_at TEXT,
    color TEXT,  -- Optional: hex color for visual distinction

    -- Indexes
    CONSTRAINT unique_project_name UNIQUE (name)
);

CREATE INDEX IF NOT EXISTS idx_projects_status
ON projects(status);

CREATE INDEX IF NOT EXISTS idx_projects_name
ON projects(name COLLATE NOCASE);  -- Case-insensitive search

-- ============================================================================
-- NEW TABLE: subtasks (parent-child relationships)
-- ============================================================================

CREATE TABLE IF NOT EXISTS subtasks (
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    position INTEGER DEFAULT 0,  -- For ordering children
    created_at TEXT NOT NULL,

    PRIMARY KEY (parent_id, child_id),
    FOREIGN KEY (parent_id) REFERENCES todos(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES todos(id) ON DELETE CASCADE,

    -- Prevent self-reference
    CHECK (parent_id != child_id)
);

CREATE INDEX IF NOT EXISTS idx_subtasks_parent
ON subtasks(parent_id);

CREATE INDEX IF NOT EXISTS idx_subtasks_child
ON subtasks(child_id);

-- ============================================================================
-- NEW TABLE: cycles (iterations/sprints)
-- ============================================================================

CREATE TABLE IF NOT EXISTS cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,  -- ISO 8601 format
    end_date TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'closed')),
    created_at TEXT NOT NULL,

    -- Metadata
    duration_weeks INTEGER,  -- Derived from dates but stored for queries
    completed_tasks INTEGER DEFAULT 0,  -- Cached count for performance
    total_tasks INTEGER DEFAULT 0,

    -- Unique constraint on active cycles (only one active at a time)
    CONSTRAINT unique_active_cycle UNIQUE (status)
    WHERE status = 'active'
);

CREATE INDEX IF NOT EXISTS idx_cycles_status
ON cycles(status);

CREATE INDEX IF NOT EXISTS idx_cycles_dates
ON cycles(start_date, end_date);

-- ============================================================================
-- NEW TABLE: cycle_tasks (many-to-many: cycles ↔ tasks)
-- ============================================================================

CREATE TABLE IF NOT EXISTS cycle_tasks (
    cycle_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    assigned_at TEXT NOT NULL,

    PRIMARY KEY (cycle_id, task_id),
    FOREIGN KEY (cycle_id) REFERENCES cycles(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES todos(id) ON DELETE CASCADE,

    -- Ensure task is in only one cycle at a time
    CONSTRAINT unique_task_cycle UNIQUE (task_id)
);

CREATE INDEX IF NOT EXISTS idx_cycle_tasks_cycle
ON cycle_tasks(cycle_id);

CREATE INDEX IF NOT EXISTS idx_cycle_tasks_task
ON cycle_tasks(task_id);

-- ============================================================================
-- INDEXES ON EXISTING TABLES (for performance)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_todos_project_id
ON todos(project_id);

CREATE INDEX IF NOT EXISTS idx_todos_kanban_column
ON todos(kanban_column);

CREATE INDEX IF NOT EXISTS idx_todos_status
ON todos(status);

CREATE INDEX IF NOT EXISTS idx_todos_priority
ON todos(priority);

CREATE INDEX IF NOT EXISTS idx_todos_due_date
ON todos(due_date);

CREATE INDEX IF NOT EXISTS idx_todos_created_at
ON todos(created_at DESC);

-- Composite index for common KANBAN queries
CREATE INDEX IF NOT EXISTS idx_todos_kanban_project
ON todos(kanban_column, project_id, status);

-- ============================================================================
-- VIEWS (optional performance optimization)
-- ============================================================================

-- View for hierarchical tasks with parent info
CREATE VIEW IF NOT EXISTS v_tasks_with_hierarchy AS
SELECT
    t.*,
    s.parent_id,
    pt.task as parent_task,
    (SELECT COUNT(*) FROM subtasks WHERE parent_id = t.id) as child_count,
    (SELECT COUNT(*) FROM subtasks s2
     JOIN todos t2 ON s2.child_id = t2.id
     WHERE s2.parent_id = t.id AND t2.status = 'done') as completed_children
FROM todos t
LEFT JOIN subtasks s ON t.id = s.child_id
LEFT JOIN todos pt ON s.parent_id = pt.id;

-- View for KANBAN board with enriched data
CREATE VIEW IF NOT EXISTS v_kanban_board AS
SELECT
    t.id,
    t.task,
    t.priority,
    t.status,
    t.kanban_column,
    t.due_date,
    p.name as project_name,
    p.color as project_color,
    c.name as cycle_name,
    (SELECT COUNT(*) FROM subtasks WHERE parent_id = t.id) as has_children
FROM todos t
LEFT JOIN projects p ON t.project_id = p.id
LEFT JOIN cycle_tasks ct ON t.id = ct.task_id
LEFT JOIN cycles c ON ct.cycle_id = c.id
WHERE t.status != 'done' OR t.completed_at > datetime('now', '-7 days');
```

### 2.2 Schema Migration Strategy

**Version Tracking:**

```sql
-- Use SQLite's built-in PRAGMA for version tracking
PRAGMA user_version = 2;  -- Current version after migrations
```

**Schema Versions:**

| Version | Description | Tables Added | Columns Added |
|---------|-------------|--------------|---------------|
| 0 | Legacy schema | todos | - |
| 1 | Epic 1 foundation | projects, subtasks, cycles, cycle_tasks | todos.project_id, todos.kanban_column |
| 2 | Performance views | v_tasks_with_hierarchy, v_kanban_board | - |

### 2.3 Data Integrity Constraints

**Foreign Key Cascade Rules:**

| Parent Table | Child Table | ON DELETE | ON UPDATE | Rationale |
|--------------|-------------|-----------|-----------|-----------|
| projects | todos | SET NULL | CASCADE | Tasks persist without project |
| todos (parent) | subtasks | CASCADE | CASCADE | Parent deletion orphans children |
| todos (child) | subtasks | CASCADE | CASCADE | Child deletion removes relationship |
| cycles | cycle_tasks | CASCADE | CASCADE | Cycle deletion unassigns tasks |
| todos | cycle_tasks | CASCADE | CASCADE | Task deletion removes assignment |

**Check Constraints:**

```sql
-- Prevent circular references (enforced in application logic)
-- Sub-task nesting depth limited to 1 level (enforced in subtasks.py)
-- Only one active cycle at a time (UNIQUE constraint WHERE status='active')
-- KANBAN column must be valid value (enforced in kanban.py)
-- Cycle dates: end_date > start_date (enforced in cycles.py)
```

### 2.4 Index Strategy

**Performance Targets:**

| Query Type | Target | Index Strategy |
|------------|--------|----------------|
| `todo list` | <100ms | Composite index on (status, priority, created_at) |
| `todo list --project` | <100ms | Index on project_id |
| `todo kanban` | <500ms | Composite index on (kanban_column, project_id, status) |
| `todo list --tree` | <200ms | Indexes on subtasks.parent_id and child_id |
| Cycle progress | <100ms | Index on cycle_tasks.cycle_id with COUNT optimization |

**Index Coverage Analysis:**

```sql
-- Query: List tasks in project
EXPLAIN QUERY PLAN
SELECT * FROM todos WHERE project_id = 5 AND status != 'done'
ORDER BY priority, due_date;
-- Uses: idx_todos_kanban_project (covers project_id, status)

-- Query: KANBAN board
EXPLAIN QUERY PLAN
SELECT * FROM todos
WHERE kanban_column = 'in-progress' AND status != 'done'
ORDER BY priority, created_at;
-- Uses: idx_todos_kanban_column

-- Query: Hierarchical tree
EXPLAIN QUERY PLAN
SELECT t.*, s.parent_id
FROM todos t
LEFT JOIN subtasks s ON t.id = s.child_id
WHERE t.project_id = 5;
-- Uses: idx_todos_project_id, idx_subtasks_child
```

---

## 3. Migration Framework

### 3.1 Migration Architecture

**Design Pattern: Sequential Versioned Migrations**

```python
# todo_cli/migrations.py

from typing import Callable
import sqlite3
from pathlib import Path

class MigrationManager:
    """Manages database schema migrations."""

    CURRENT_VERSION = 2

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_current_version(self, conn: sqlite3.Connection) -> int:
        """Get current database version."""
        cursor = conn.execute("PRAGMA user_version")
        return cursor.fetchone()[0]

    def set_version(self, conn: sqlite3.Connection, version: int):
        """Set database version."""
        conn.execute(f"PRAGMA user_version = {version}")
        conn.commit()

    def needs_migration(self, conn: sqlite3.Connection) -> bool:
        """Check if migration is needed."""
        current = self.get_current_version(conn)
        return current < self.CURRENT_VERSION

    def migrate(self, conn: sqlite3.Connection) -> bool:
        """Run all pending migrations."""
        current_version = self.get_current_version(conn)

        if current_version >= self.CURRENT_VERSION:
            return False  # No migration needed

        # Ordered list of migrations
        migrations = [
            (1, self._migrate_v0_to_v1),
            (2, self._migrate_v1_to_v2),
        ]

        # Apply migrations sequentially
        for target_version, migration_func in migrations:
            if current_version < target_version:
                try:
                    # Backup before migration
                    self._create_backup(conn, current_version)

                    # Execute migration in transaction
                    migration_func(conn)
                    self.set_version(conn, target_version)
                    current_version = target_version

                except Exception as e:
                    # Rollback on error
                    conn.rollback()
                    raise MigrationError(
                        f"Migration to v{target_version} failed: {e}"
                    ) from e

        return True

    def _create_backup(self, conn: sqlite3.Connection, version: int):
        """Create database backup before migration."""
        backup_path = self.db_path.with_suffix(f".backup_v{version}")

        with sqlite3.connect(backup_path) as backup_conn:
            conn.backup(backup_conn)

    def rollback(self, conn: sqlite3.Connection, target_version: int):
        """Rollback to specific version using backup."""
        backup_path = self.db_path.with_suffix(f".backup_v{target_version}")

        if not backup_path.exists():
            raise MigrationError(
                f"Backup for v{target_version} not found at {backup_path}"
            )

        # Restore from backup
        with sqlite3.connect(backup_path) as backup_conn:
            backup_conn.backup(conn)

        conn.commit()

    # ========================================================================
    # MIGRATION FUNCTIONS
    # ========================================================================

    def _migrate_v0_to_v1(self, conn: sqlite3.Connection):
        """Migrate from v0 (legacy) to v1 (Epic 1 foundation)."""

        # Add new columns to todos table
        conn.execute("""
            ALTER TABLE todos ADD COLUMN project_id INTEGER
            REFERENCES projects(id) ON DELETE SET NULL
        """)
        conn.execute("""
            ALTER TABLE todos ADD COLUMN kanban_column TEXT DEFAULT 'backlog'
        """)

        # Create projects table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'archived')),
                created_at TEXT NOT NULL
            )
        """)

        # Migrate existing project strings to projects table
        # Extract unique projects from todos.project column
        cursor = conn.execute("""
            SELECT DISTINCT project FROM todos
            WHERE project IS NOT NULL
        """)

        for (project_name,) in cursor:
            conn.execute("""
                INSERT OR IGNORE INTO projects (name, created_at)
                VALUES (?, datetime('now'))
            """, (project_name,))

        # Update todos to use project_id instead of project string
        conn.execute("""
            UPDATE todos
            SET project_id = (
                SELECT id FROM projects WHERE name = todos.project
            )
            WHERE project IS NOT NULL
        """)

        # Create subtasks table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subtasks (
                parent_id INTEGER NOT NULL,
                child_id INTEGER NOT NULL,
                position INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (parent_id, child_id),
                FOREIGN KEY (parent_id) REFERENCES todos(id) ON DELETE CASCADE,
                FOREIGN KEY (child_id) REFERENCES todos(id) ON DELETE CASCADE,
                CHECK (parent_id != child_id)
            )
        """)

        # Create cycles table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'closed')),
                created_at TEXT NOT NULL,
                duration_weeks INTEGER,
                completed_tasks INTEGER DEFAULT 0,
                total_tasks INTEGER DEFAULT 0
            )
        """)

        # Create cycle_tasks table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cycle_tasks (
                cycle_id INTEGER NOT NULL,
                task_id INTEGER NOT NULL,
                assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (cycle_id, task_id),
                FOREIGN KEY (cycle_id) REFERENCES cycles(id) ON DELETE CASCADE,
                FOREIGN KEY (task_id) REFERENCES todos(id) ON DELETE CASCADE,
                CONSTRAINT unique_task_cycle UNIQUE (task_id)
            )
        """)

        # Create indexes
        self._create_indexes_v1(conn)

        conn.commit()

    def _create_indexes_v1(self, conn: sqlite3.Connection):
        """Create indexes for v1 schema."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)",
            "CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name COLLATE NOCASE)",
            "CREATE INDEX IF NOT EXISTS idx_subtasks_parent ON subtasks(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_subtasks_child ON subtasks(child_id)",
            "CREATE INDEX IF NOT EXISTS idx_cycles_status ON cycles(status)",
            "CREATE INDEX IF NOT EXISTS idx_cycles_dates ON cycles(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_cycle_tasks_cycle ON cycle_tasks(cycle_id)",
            "CREATE INDEX IF NOT EXISTS idx_cycle_tasks_task ON cycle_tasks(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_todos_project_id ON todos(project_id)",
            "CREATE INDEX IF NOT EXISTS idx_todos_kanban_column ON todos(kanban_column)",
            "CREATE INDEX IF NOT EXISTS idx_todos_kanban_project ON todos(kanban_column, project_id, status)",
        ]

        for index_sql in indexes:
            conn.execute(index_sql)

    def _migrate_v1_to_v2(self, conn: sqlite3.Connection):
        """Migrate from v1 to v2 (add performance views)."""

        # Create v_tasks_with_hierarchy view
        conn.execute("""
            CREATE VIEW IF NOT EXISTS v_tasks_with_hierarchy AS
            SELECT
                t.*,
                s.parent_id,
                pt.task as parent_task,
                (SELECT COUNT(*) FROM subtasks WHERE parent_id = t.id) as child_count,
                (SELECT COUNT(*) FROM subtasks s2
                 JOIN todos t2 ON s2.child_id = t2.id
                 WHERE s2.parent_id = t.id AND t2.status = 'done') as completed_children
            FROM todos t
            LEFT JOIN subtasks s ON t.id = s.child_id
            LEFT JOIN todos pt ON s.parent_id = pt.id
        """)

        # Create v_kanban_board view
        conn.execute("""
            CREATE VIEW IF NOT EXISTS v_kanban_board AS
            SELECT
                t.id,
                t.task,
                t.priority,
                t.status,
                t.kanban_column,
                t.due_date,
                p.name as project_name,
                p.color as project_color,
                c.name as cycle_name,
                (SELECT COUNT(*) FROM subtasks WHERE parent_id = t.id) as has_children
            FROM todos t
            LEFT JOIN projects p ON t.project_id = p.id
            LEFT JOIN cycle_tasks ct ON t.id = ct.task_id
            LEFT JOIN cycles c ON ct.cycle_id = c.id
            WHERE t.status != 'done' OR t.completed_at > datetime('now', '-7 days')
        """)

        conn.commit()


class MigrationError(Exception):
    """Migration-related errors."""
    pass
```

### 3.2 Migration Testing Strategy

**Test Cases:**

```python
# tests/test_migrations.py

def test_migration_v0_to_v1_new_install():
    """Test migration on fresh database."""
    # Create empty database
    # Run migration
    # Verify all tables exist
    # Verify indexes created

def test_migration_v0_to_v1_existing_data():
    """Test migration preserves existing tasks."""
    # Create v0 database with sample tasks
    # Run migration
    # Verify all tasks still exist
    # Verify project migration worked

def test_migration_idempotent():
    """Test migration can be run multiple times safely."""
    # Run migration twice
    # Verify no errors, no data duplication

def test_migration_rollback():
    """Test rollback mechanism."""
    # Create backup
    # Simulate failed migration
    # Rollback
    # Verify data restored

def test_migration_foreign_keys():
    """Test foreign key constraints work post-migration."""
    # Run migration
    # Test cascade deletes
    # Test constraint violations
```

### 3.3 User-Facing Migration Flow

**First Run After Upgrade:**

```
$ todo list
⚠️  Database migration required (v0 → v2)
Creating backup: /Users/rk/.local/share/todo-cli/todos.db.backup_v0
Running migration to v1...
  ✓ Added projects table
  ✓ Added subtasks table
  ✓ Added cycles table
  ✓ Migrated 42 project tags to projects table
  ✓ Created indexes
Running migration to v2...
  ✓ Created performance views
Migration complete! Database is now v2.

[normal list output follows]
```

**Migration Failure:**

```
$ todo list
⚠️  Database migration required (v0 → v2)
Creating backup: /Users/rk/.local/share/todo-cli/todos.db.backup_v0
Running migration to v1...
  ✗ Migration failed: UNIQUE constraint violation on projects.name

Database has been restored from backup.
Please report this issue: https://github.com/.../issues
```

---

## 4. Module Architecture

### 4.1 New Module Structure

```
todo_cli/
├── __init__.py
├── main.py                  # CLI entry point (existing)
├── database.py              # Data layer (existing, extended)
├── display.py               # Display layer (existing, extended)
├── models.py                # Data models (existing)
├── config.py                # Configuration (existing)
├── migrations.py            # NEW: Migration framework
├── projects.py              # NEW: Project management
├── subtasks.py              # NEW: Hierarchical task logic
├── kanban.py                # NEW: KANBAN board logic
├── cycles.py                # NEW: Cycle management
├── renderers/
│   ├── __init__.py
│   ├── kanban_renderer.py   # NEW: KANBAN board rendering
│   └── tree_renderer.py     # NEW: Tree view rendering
└── utils/
    ├── __init__.py
    └── terminal.py          # NEW: Terminal capability detection
```

### 4.2 Module Responsibilities

**projects.py:**
- Project CRUD operations
- Project validation (unique names, case-insensitive)
- Project statistics (task counts, completion rate)
- Project filtering logic

**subtasks.py:**
- Parent-child relationship management
- Depth validation (max 1 level)
- Circular reference prevention
- Completion cascade logic (parent requires all children)
- Orphan handling (on parent delete)

**kanban.py:**
- KANBAN state management (column assignment)
- Board data fetching with filters
- Column movement validation
- Status synchronization (done column ↔ completed status)
- Board grouping logic (by column, priority, project)

**cycles.py:**
- Cycle CRUD operations
- Task assignment/unassignment
- Active cycle management (only one at a time)
- Progress calculation (completed/total)
- Cycle closing logic (handle incomplete tasks)
- Report generation (Markdown, JSON)

**renderers/kanban_renderer.py:**
- Rich-based KANBAN board rendering
- Column layout and sizing
- Task card formatting
- Priority color coding
- Terminal width adaptation
- Sub-task display within board

**renderers/tree_renderer.py:**
- Hierarchical tree rendering using Rich.tree
- Parent-child visual representation
- Completion status propagation display
- Collapsible branches (future)

**utils/terminal.py:**
- Terminal capability detection (Unicode, color, width)
- Graceful degradation logic
- ANSI code fallbacks
- Box-drawing character selection

### 4.3 Module Interfaces

**projects.py API:**

```python
from typing import Optional
from datetime import datetime

class ProjectManager:
    """Project management operations."""

    def __init__(self, db: Database):
        self.db = db

    def create_project(self, name: str, description: Optional[str] = None) -> Project:
        """Create new project with validation."""
        pass

    def get_project(self, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        pass

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """Get project by name (case-insensitive)."""
        pass

    def list_projects(self, status: Optional[str] = 'active') -> list[Project]:
        """List projects with optional status filter."""
        pass

    def update_project(self, project_id: int, **kwargs) -> Project:
        """Update project metadata."""
        pass

    def delete_project(self, project_id: int) -> bool:
        """Delete project (tasks remain, become unassigned)."""
        pass

    def get_project_stats(self, project_id: int) -> dict:
        """Get task counts and completion stats for project."""
        pass

    def archive_project(self, project_id: int) -> Project:
        """Archive project (mark as inactive)."""
        pass
```

**subtasks.py API:**

```python
class SubtaskManager:
    """Hierarchical task relationship management."""

    def __init__(self, db: Database):
        self.db = db

    def add_subtask(self, parent_id: int, child_id: int) -> bool:
        """Create parent-child relationship with validation."""
        pass

    def remove_subtask(self, parent_id: int, child_id: int) -> bool:
        """Remove relationship (child becomes top-level)."""
        pass

    def get_children(self, parent_id: int) -> list[Todo]:
        """Get all children of parent task."""
        pass

    def get_parent(self, child_id: int) -> Optional[Todo]:
        """Get parent of child task."""
        pass

    def is_subtask(self, task_id: int) -> bool:
        """Check if task is a sub-task."""
        pass

    def has_children(self, task_id: int) -> bool:
        """Check if task has children."""
        pass

    def can_add_subtask(self, parent_id: int, child_id: int) -> tuple[bool, str]:
        """Validate if sub-task can be added (returns bool, error_message)."""
        pass

    def check_completion_allowed(self, parent_id: int) -> tuple[bool, list[int]]:
        """Check if parent can be completed (returns bool, incomplete_child_ids)."""
        pass

    def auto_complete_parent(self, child_id: int) -> Optional[int]:
        """Auto-complete parent if all children done (returns parent_id if completed)."""
        pass
```

**kanban.py API:**

```python
class KanbanManager:
    """KANBAN board state and operations."""

    COLUMNS = ['backlog', 'todo', 'in-progress', 'review', 'done']

    def __init__(self, db: Database):
        self.db = db

    def move_task(self, task_id: int, column: str) -> Todo:
        """Move task to column with validation and status sync."""
        pass

    def get_board_data(self,
                       project_id: Optional[int] = None,
                       cycle_id: Optional[int] = None,
                       priority: Optional[int] = None) -> dict[str, list[Todo]]:
        """Get tasks grouped by column with filters."""
        pass

    def validate_column(self, column: str) -> bool:
        """Check if column name is valid."""
        pass

    def get_column_stats(self, column: str) -> dict:
        """Get task counts and stats for specific column."""
        pass
```

**cycles.py API:**

```python
class CycleManager:
    """Cycle/iteration management."""

    def __init__(self, db: Database):
        self.db = db

    def create_cycle(self, name: str, start_date: datetime,
                     end_date: datetime) -> Cycle:
        """Create new cycle with validation."""
        pass

    def get_active_cycle(self) -> Optional[Cycle]:
        """Get currently active cycle."""
        pass

    def assign_task(self, task_id: int, cycle_id: Optional[int] = None) -> bool:
        """Assign task to cycle (defaults to active)."""
        pass

    def unassign_task(self, task_id: int) -> bool:
        """Remove task from cycle."""
        pass

    def get_cycle_tasks(self, cycle_id: int) -> list[Todo]:
        """Get all tasks in cycle."""
        pass

    def get_cycle_progress(self, cycle_id: int) -> dict:
        """Calculate cycle progress stats."""
        pass

    def close_cycle(self, cycle_id: int,
                    move_incomplete_to: Optional[int] = None) -> Cycle:
        """Close cycle and handle incomplete tasks."""
        pass

    def generate_report(self, cycle_id: int, format: str = 'md') -> str:
        """Generate cycle report in Markdown or JSON."""
        pass
```

---

## 5. Feature-Specific Designs

### 5.1 Project Management Design

**Data Model:**

```python
@dataclass
class Project:
    id: int
    name: str
    description: Optional[str]
    status: str  # 'active' or 'archived'
    created_at: datetime

    # Computed properties
    task_count: int = 0
    active_tasks: int = 0
    completed_tasks: int = 0
    completion_rate: float = 0.0
```

**Key Operations:**

1. **Create Project:**
   - Validate unique name (case-insensitive)
   - Set created_at to now()
   - Default status to 'active'

2. **Project Filtering:**
   - Extend existing `todo list --project <name>` to use project_id
   - Maintain backwards compatibility with project string lookup

3. **Project Statistics:**
   - Query: `SELECT COUNT(*), SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) FROM todos WHERE project_id = ?`
   - Cache in memory for repeated access within session

### 5.2 Sub-task Hierarchy Design

**Constraint Enforcement:**

```python
class SubtaskManager:

    def can_add_subtask(self, parent_id: int, child_id: int) -> tuple[bool, str]:
        """Validate sub-task addition."""

        # Check 1: Parent and child exist
        parent = self.db.get(parent_id)
        child = self.db.get(child_id)
        if not parent or not child:
            return False, "Task not found"

        # Check 2: Child is not already a sub-task
        if self.is_subtask(child_id):
            return False, f"Task #{child_id} is already a sub-task. Max depth is 1 level."

        # Check 3: Parent is not a sub-task (prevent depth > 1)
        if self.is_subtask(parent_id):
            return False, f"Task #{parent_id} is a sub-task. Cannot nest deeper than 1 level."

        # Check 4: No circular reference (child is not parent of parent)
        if self.is_parent_of(child_id, parent_id):
            return False, "Circular reference: child is parent of parent"

        # Check 5: Relationship doesn't already exist
        existing = self.db.execute(
            "SELECT 1 FROM subtasks WHERE parent_id=? AND child_id=?",
            (parent_id, child_id)
        ).fetchone()
        if existing:
            return False, "Relationship already exists"

        return True, ""
```

**Completion Cascade:**

```python
def auto_complete_parent(self, child_id: int) -> Optional[int]:
    """Auto-complete parent if all children are done."""

    # Get parent
    parent_id = self.get_parent_id(child_id)
    if not parent_id:
        return None

    # Check if all children are complete
    all_children = self.get_children(parent_id)
    incomplete = [c for c in all_children if c.status != Status.DONE]

    if len(incomplete) == 0:
        # All children complete, complete parent
        parent = self.db.get(parent_id)
        parent.status = Status.DONE
        parent.completed_at = datetime.now()
        self.db.update(parent)
        return parent_id

    return None
```

### 5.3 KANBAN Board Design

**Query Optimization:**

```python
def get_board_data(self,
                   project_id: Optional[int] = None,
                   cycle_id: Optional[int] = None) -> dict[str, list[Todo]]:
    """
    Optimized query for KANBAN board.

    Performance target: <500ms for 1000+ tasks
    Strategy: Single query with filters, group in Python
    """

    # Build query with filters
    query = """
        SELECT t.*, p.name as project_name, c.name as cycle_name
        FROM todos t
        LEFT JOIN projects p ON t.project_id = p.id
        LEFT JOIN cycle_tasks ct ON t.id = ct.task_id
        LEFT JOIN cycles c ON ct.cycle_id = c.id
        WHERE t.status != 'done'
    """
    params = []

    if project_id:
        query += " AND t.project_id = ?"
        params.append(project_id)

    if cycle_id:
        query += " AND ct.cycle_id = ?"
        params.append(cycle_id)

    query += " ORDER BY t.kanban_column, t.priority, t.created_at"

    # Execute single query
    rows = self.db.execute(query, params).fetchall()

    # Group by column in Python (fast)
    board = {col: [] for col in self.COLUMNS}
    for row in rows:
        todo = self.db._row_to_todo(row)
        column = todo.kanban_column or 'backlog'
        board[column].append(todo)

    return board
```

**Column Movement with Status Sync:**

```python
def move_task(self, task_id: int, column: str) -> Todo:
    """Move task to column and sync status."""

    # Validate column
    if column not in self.COLUMNS:
        raise ValueError(f"Invalid column. Valid: {', '.join(self.COLUMNS)}")

    # Get task
    todo = self.db.get(task_id)
    if not todo:
        raise ValueError(f"Task #{task_id} not found")

    # Update column
    old_column = todo.kanban_column
    todo.kanban_column = column

    # Sync status with column
    if column == 'done' and todo.status != Status.DONE:
        # Moving to done → complete task
        todo.status = Status.DONE
        todo.completed_at = datetime.now()

        # Stop timer if running
        if todo.timer_started:
            elapsed = datetime.now() - todo.timer_started
            todo.time_spent += elapsed
            todo.timer_started = None

    elif column != 'done' and todo.status == Status.DONE:
        # Moving from done → uncomplete task
        todo.status = Status.TODO
        todo.completed_at = None

    self.db.update(todo)
    return todo
```

**Board Rendering (in renderers/kanban_renderer.py):**

```python
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table

class KanbanRenderer:
    """Render KANBAN board using Rich."""

    def __init__(self, console: Console):
        self.console = console

    def render_board(self, board_data: dict[str, list[Todo]],
                     title: str = "KANBAN Board"):
        """
        Render board with dynamic column sizing.

        Terminal width adaptation:
        - 80 cols: 5 columns × 16 chars each
        - 120 cols: 5 columns × 24 chars each
        - 160 cols: 5 columns × 32 chars each
        """

        # Get terminal width
        width = self.console.width
        column_count = len(board_data)
        column_width = max(16, (width - column_count - 2) // column_count)

        # Create layout
        layout = Layout()
        layout.split_row(
            *[Layout(name=col, size=column_width) for col in board_data.keys()]
        )

        # Populate columns
        for column_name, tasks in board_data.items():
            column_panel = self._render_column(column_name, tasks, column_width)
            layout[column_name].update(column_panel)

        self.console.print(Panel(layout, title=title, border_style="bold"))

    def _render_column(self, name: str, tasks: list[Todo], width: int) -> Panel:
        """Render single column with tasks."""

        # Create table for tasks
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Task", width=width - 4)

        for task in tasks[:20]:  # Limit to 20 per column for performance
            # Format: emoji priority, #id, truncated title
            emoji = self._priority_emoji(task.priority)
            title = self._truncate(task.task, width - 8)
            table.add_row(f"{emoji} #{task.id} {title}")

        if len(tasks) > 20:
            table.add_row(f"[dim]... {len(tasks) - 20} more[/dim]")

        # Column header with count
        header = f"{name.title()} ({len(tasks)})"
        return Panel(table, title=header, border_style="cyan")

    def _priority_emoji(self, priority: Priority) -> str:
        """Map priority to emoji."""
        return {
            Priority.P0: "🔴",
            Priority.P1: "🟡",
            Priority.P2: "🔵",
            Priority.P3: "⚪",
        }.get(priority, "⚪")

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text with ellipsis."""
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."
```

### 5.4 Cycle Management Design

**Data Model:**

```python
@dataclass
class Cycle:
    id: int
    name: str
    start_date: datetime
    end_date: datetime
    status: str  # 'active' or 'closed'
    created_at: datetime
    duration_weeks: int

    # Computed
    days_elapsed: int = 0
    days_remaining: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    completion_rate: float = 0.0
```

**Progress Calculation:**

```python
def get_cycle_progress(self, cycle_id: int) -> dict:
    """Calculate detailed cycle progress."""

    cycle = self.db.get_cycle(cycle_id)
    if not cycle:
        raise ValueError(f"Cycle #{cycle_id} not found")

    # Get tasks
    tasks = self.get_cycle_tasks(cycle_id)
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == Status.DONE)
    remaining = total - completed

    # Date calculations
    today = datetime.now().date()
    start = cycle.start_date.date()
    end = cycle.end_date.date()

    elapsed = (today - start).days
    remaining_days = (end - today).days
    total_days = (end - start).days

    # Velocity
    velocity = completed / elapsed if elapsed > 0 else 0
    projected_completion = completed + (velocity * remaining_days) if remaining_days > 0 else completed

    return {
        'cycle_id': cycle_id,
        'name': cycle.name,
        'total_tasks': total,
        'completed_tasks': completed,
        'remaining_tasks': remaining,
        'completion_rate': completed / total if total > 0 else 0,
        'days_elapsed': elapsed,
        'days_remaining': remaining_days,
        'total_days': total_days,
        'velocity': velocity,  # tasks per day
        'projected_completion': int(projected_completion),
        'on_track': projected_completion >= total,
        'overdue': today > end and cycle.status == 'active',
    }
```

**Report Generation:**

```python
def generate_report(self, cycle_id: int, format: str = 'md') -> str:
    """Generate cycle report."""

    progress = self.get_cycle_progress(cycle_id)
    tasks = self.get_cycle_tasks(cycle_id)
    completed_tasks = [t for t in tasks if t.status == Status.DONE]
    remaining_tasks = [t for t in tasks if t.status != Status.DONE]

    if format == 'md':
        return self._generate_markdown_report(progress, completed_tasks, remaining_tasks)
    elif format == 'json':
        return self._generate_json_report(progress, completed_tasks, remaining_tasks)
    else:
        raise ValueError(f"Invalid format: {format}. Use 'md' or 'json'")

def _generate_markdown_report(self, progress: dict,
                               completed: list[Todo],
                               remaining: list[Todo]) -> str:
    """Generate Markdown report."""

    report = f"""# {progress['name']} Report

**Status:** {'Closed' if progress['overdue'] else 'Active'}
**Duration:** {progress['days_elapsed']} / {progress['total_days']} days
**Completion:** {progress['completion_rate']:.0%} ({progress['completed_tasks']}/{progress['total_tasks']} tasks)

## Progress

```
[{'█' * int(progress['completion_rate'] * 20)}{'░' * (20 - int(progress['completion_rate'] * 20))}] {progress['completion_rate']:.0%}
```

## Completed Tasks ({len(completed)})

"""
    for task in completed:
        priority_emoji = {0: "🔴", 1: "🟡", 2: "🔵", 3: "⚪"}[task.priority.value]
        report += f"- ✅ {priority_emoji} #{task.id} {task.task}\n"

    report += f"\n## Remaining Tasks ({len(remaining)})\n\n"
    for task in remaining:
        priority_emoji = {0: "🔴", 1: "🟡", 2: "🔵", 3: "⚪"}[task.priority.value]
        report += f"- ⬜ {priority_emoji} #{task.id} {task.task}\n"

    report += f"""
## Summary

- **Velocity:** {progress['velocity']:.2f} tasks/day
- **Projected Completion:** {progress['projected_completion']}/{progress['total_tasks']} tasks by end date
- **Status:** {'⚠️ Behind schedule' if not progress['on_track'] else '✅ On track'}
"""

    return report
```

---

## 6. Performance Optimization Strategy

### 6.1 Query Optimization

**KANBAN Board Query (Target: <500ms for 1000+ tasks):**

**Optimization Techniques:**

1. **Single Query Approach:**
   - Fetch all needed data in one query with JOINs
   - Avoid N+1 queries (one query per column)
   - Group in Python (fast in-memory operation)

2. **Index Usage:**
   ```sql
   -- Composite index covers common KANBAN filters
   CREATE INDEX idx_todos_kanban_project
   ON todos(kanban_column, project_id, status);

   -- Query uses index:
   SELECT * FROM todos
   WHERE kanban_column = ? AND project_id = ? AND status != 'done'
   -- Uses: idx_todos_kanban_project (full index scan)
   ```

3. **Result Limiting:**
   - Limit to 20 tasks per column in UI
   - Show "... X more" for overflow
   - Full list available via separate command

4. **View-Based Optimization:**
   ```sql
   -- Pre-joined view for KANBAN queries
   CREATE VIEW v_kanban_board AS
   SELECT
       t.id, t.task, t.priority, t.status, t.kanban_column, t.due_date,
       p.name as project_name,
       c.name as cycle_name,
       (SELECT COUNT(*) FROM subtasks WHERE parent_id = t.id) as child_count
   FROM todos t
   LEFT JOIN projects p ON t.project_id = p.id
   LEFT JOIN cycle_tasks ct ON t.id = ct.task_id
   LEFT JOIN cycles c ON ct.cycle_id = c.id
   WHERE t.status != 'done' OR t.completed_at > datetime('now', '-7 days');

   -- Query becomes simple:
   SELECT * FROM v_kanban_board WHERE kanban_column = ?;
   ```

**Tree View Query (Target: <200ms for 1000+ tasks):**

1. **Recursive CTE (if needed for deep hierarchies):**
   ```sql
   -- For MVP (1 level), simple JOIN suffices:
   SELECT t.*, s.parent_id, pt.task as parent_task
   FROM todos t
   LEFT JOIN subtasks s ON t.id = s.child_id
   LEFT JOIN todos pt ON s.parent_id = pt.id
   WHERE t.project_id = ?
   ORDER BY COALESCE(s.parent_id, t.id), s.parent_id NULLS FIRST, t.id;
   ```

2. **Child Count Subquery Optimization:**
   ```sql
   -- Use correlated subquery for child counts (indexed):
   SELECT t.*,
          (SELECT COUNT(*) FROM subtasks WHERE parent_id = t.id) as child_count,
          (SELECT COUNT(*) FROM subtasks s2
           JOIN todos t2 ON s2.child_id = t2.id
           WHERE s2.parent_id = t.id AND t2.status = 'done') as completed_children
   FROM todos t
   WHERE t.project_id = ?;
   ```

### 6.2 Caching Strategy

**In-Memory Caching (Python-level):**

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedQueries:
    """Cache frequently accessed data."""

    def __init__(self, db: Database):
        self.db = db
        self._cache = {}
        self._cache_times = {}
        self.ttl = timedelta(seconds=30)  # 30-second cache

    def get_project_stats(self, project_id: int) -> dict:
        """Cached project statistics."""
        cache_key = f"project_stats_{project_id}"

        # Check cache freshness
        if cache_key in self._cache:
            if datetime.now() - self._cache_times[cache_key] < self.ttl:
                return self._cache[cache_key]

        # Compute fresh stats
        stats = self._compute_project_stats(project_id)
        self._cache[cache_key] = stats
        self._cache_times[cache_key] = datetime.now()

        return stats

    def _compute_project_stats(self, project_id: int) -> dict:
        """Compute project statistics from database."""
        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as completed,
                SUM(time_spent_seconds) as total_time
            FROM todos
            WHERE project_id = ?
        """
        row = self.db.execute(query, (project_id,)).fetchone()

        return {
            'total_tasks': row['total'],
            'completed_tasks': row['completed'],
            'active_tasks': row['total'] - row['completed'],
            'completion_rate': row['completed'] / row['total'] if row['total'] > 0 else 0,
            'total_time_seconds': row['total_time'],
        }

    def invalidate_project(self, project_id: int):
        """Invalidate project cache on task changes."""
        cache_key = f"project_stats_{project_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]
            del self._cache_times[cache_key]
```

**When to Invalidate:**
- Task added/deleted/updated: Invalidate project cache
- Cycle closed: Invalidate cycle cache
- Task moved in KANBAN: Invalidate board cache (if implemented)

### 6.3 Benchmarking Framework

**Performance Test Suite:**

```python
# tests/benchmark.py

import time
import sqlite3
from pathlib import Path
from todo_cli.database import Database

class PerformanceBenchmark:
    """Benchmark database operations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.results = {}

    def setup_large_dataset(self, task_count: int = 10000):
        """Create large test dataset."""
        db = Database(self.db_path)

        # Create 100 projects
        for i in range(100):
            db.execute(
                "INSERT INTO projects (name, created_at) VALUES (?, datetime('now'))",
                (f"Project {i}",)
            )

        # Create tasks distributed across projects
        for i in range(task_count):
            project_id = (i % 100) + 1
            priority = i % 4
            kanban_column = ['backlog', 'todo', 'in-progress', 'review', 'done'][i % 5]

            db.execute("""
                INSERT INTO todos (task, priority, project_id, kanban_column, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (f"Task {i}", priority, project_id, kanban_column))

        db.conn.commit()

    def benchmark_query(self, name: str, query: str, params: tuple = ()):
        """Benchmark single query."""
        db = Database(self.db_path)

        # Warm-up run
        db.execute(query, params).fetchall()

        # Timed run (5 iterations, take average)
        times = []
        for _ in range(5):
            start = time.perf_counter()
            db.execute(query, params).fetchall()
            elapsed = (time.perf_counter() - start) * 1000  # ms
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        self.results[name] = {
            'avg_ms': avg_time,
            'min_ms': min(times),
            'max_ms': max(times),
            'query': query,
        }

        return avg_time

    def run_benchmarks(self):
        """Run all performance benchmarks."""

        # List all tasks
        self.benchmark_query(
            "list_all_tasks",
            "SELECT * FROM todos ORDER BY priority, created_at DESC"
        )

        # List tasks in project
        self.benchmark_query(
            "list_project_tasks",
            "SELECT * FROM todos WHERE project_id = ? AND status != 'done' ORDER BY priority",
            (5,)
        )

        # KANBAN board query
        self.benchmark_query(
            "kanban_board",
            """
            SELECT t.*, p.name as project_name
            FROM todos t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.status != 'done'
            ORDER BY t.kanban_column, t.priority
            """
        )

        # KANBAN filtered by project
        self.benchmark_query(
            "kanban_project",
            """
            SELECT t.*, p.name as project_name
            FROM todos t
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE t.project_id = ? AND t.status != 'done'
            ORDER BY t.kanban_column, t.priority
            """,
            (5,)
        )

        # Tree view with hierarchy
        self.benchmark_query(
            "tree_view",
            """
            SELECT t.*, s.parent_id, pt.task as parent_task
            FROM todos t
            LEFT JOIN subtasks s ON t.id = s.child_id
            LEFT JOIN todos pt ON s.parent_id = pt.id
            WHERE t.project_id = ?
            ORDER BY COALESCE(s.parent_id, t.id), s.parent_id NULLS FIRST
            """,
            (5,)
        )

        # Cycle progress
        self.benchmark_query(
            "cycle_progress",
            """
            SELECT t.*, ct.cycle_id
            FROM todos t
            JOIN cycle_tasks ct ON t.id = ct.task_id
            WHERE ct.cycle_id = ?
            """,
            (1,)
        )

    def print_results(self):
        """Print benchmark results."""
        print("\n" + "=" * 80)
        print("PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80 + "\n")

        for name, result in self.results.items():
            status = "✅ PASS" if result['avg_ms'] < 500 else "⚠️  WARN" if result['avg_ms'] < 1000 else "❌ FAIL"
            print(f"{status} {name:30s} {result['avg_ms']:>8.2f}ms (min: {result['min_ms']:.2f}, max: {result['max_ms']:.2f})")

        print("\n" + "=" * 80)
        print(f"Total queries: {len(self.results)}")
        print(f"All passed (<500ms): {sum(1 for r in self.results.values() if r['avg_ms'] < 500)}/{len(self.results)}")
        print("=" * 80 + "\n")


# Usage:
# pytest tests/benchmark.py::test_performance_large_dataset -v
def test_performance_large_dataset(tmp_path):
    db_path = tmp_path / "benchmark.db"
    bench = PerformanceBenchmark(db_path)

    # Setup 10,000 tasks
    bench.setup_large_dataset(10000)

    # Run benchmarks
    bench.run_benchmarks()
    bench.print_results()

    # Assert performance targets
    assert bench.results['list_all_tasks']['avg_ms'] < 100, "List all tasks should be <100ms"
    assert bench.results['kanban_board']['avg_ms'] < 500, "KANBAN board should be <500ms"
    assert bench.results['tree_view']['avg_ms'] < 200, "Tree view should be <200ms"
```

---

## 7. Terminal Compatibility Design

### 7.1 Capability Detection

**Terminal Feature Detection:**

```python
# utils/terminal.py

import os
import sys
from typing import Optional
from rich.console import Console

class TerminalCapabilities:
    """Detect and manage terminal capabilities."""

    def __init__(self):
        self.console = Console()
        self._capabilities = self._detect_capabilities()

    def _detect_capabilities(self) -> dict:
        """Detect what the terminal supports."""

        return {
            'unicode': self._supports_unicode(),
            'color': self._supports_color(),
            'truecolor': self._supports_truecolor(),
            'width': self.console.width,
            'height': self.console.height,
            'term': os.getenv('TERM', 'unknown'),
        }

    def _supports_unicode(self) -> bool:
        """Check if terminal supports Unicode box-drawing."""
        term = os.getenv('TERM', '').lower()

        # Known good terminals
        if any(t in term for t in ['xterm', 'screen', 'tmux', 'alacritty', 'kitty', 'iterm']):
            return True

        # Check encoding
        try:
            encoding = sys.stdout.encoding or ''
            return 'utf' in encoding.lower()
        except:
            return False

    def _supports_color(self) -> bool:
        """Check if terminal supports ANSI colors."""
        # Use Rich's detection
        return self.console.is_terminal and not self.console.no_color

    def _supports_truecolor(self) -> bool:
        """Check if terminal supports 24-bit color."""
        colorterm = os.getenv('COLORTERM', '').lower()
        return 'truecolor' in colorterm or '24bit' in colorterm

    @property
    def can_use_box_drawing(self) -> bool:
        """Can we use Unicode box-drawing characters?"""
        return self._capabilities['unicode']

    @property
    def can_use_color(self) -> bool:
        """Can we use ANSI colors?"""
        return self._capabilities['color']

    def get_box_chars(self) -> dict:
        """Get box-drawing character set based on capabilities."""
        if self.can_use_box_drawing:
            # Unicode box-drawing characters
            return {
                'horizontal': '─',
                'vertical': '│',
                'top_left': '┌',
                'top_right': '┐',
                'bottom_left': '└',
                'bottom_right': '┘',
                'cross': '┼',
                'tee_down': '┬',
                'tee_up': '┴',
                'tee_right': '├',
                'tee_left': '┤',
            }
        else:
            # ASCII fallback
            return {
                'horizontal': '-',
                'vertical': '|',
                'top_left': '+',
                'top_right': '+',
                'bottom_left': '+',
                'bottom_right': '+',
                'cross': '+',
                'tee_down': '+',
                'tee_up': '+',
                'tee_right': '+',
                'tee_left': '+',
            }

    def get_tree_chars(self) -> dict:
        """Get tree-drawing characters based on capabilities."""
        if self.can_use_box_drawing:
            return {
                'branch': '├─',
                'last_branch': '└─',
                'vertical': '│ ',
                'space': '  ',
            }
        else:
            return {
                'branch': '|-',
                'last_branch': '`-',
                'vertical': '| ',
                'space': '  ',
            }
```

### 7.2 Graceful Degradation

**Rendering Strategy:**

```python
class AdaptiveRenderer:
    """Render content adapted to terminal capabilities."""

    def __init__(self, capabilities: TerminalCapabilities):
        self.caps = capabilities
        self.console = Console()

    def render_kanban_board(self, board_data: dict):
        """Render KANBAN with adaptive approach."""

        if self.caps.can_use_box_drawing and self.caps.width >= 80:
            # Full Rich-based rendering with panels
            self._render_rich_kanban(board_data)

        elif self.caps.width >= 80:
            # ASCII-only box drawing
            self._render_ascii_kanban(board_data)

        else:
            # Fallback: simple list view grouped by column
            self._render_list_kanban(board_data)

    def _render_rich_kanban(self, board_data: dict):
        """Full Rich rendering with Unicode."""
        # Use KanbanRenderer as designed
        renderer = KanbanRenderer(self.console)
        renderer.render_board(board_data)

    def _render_ascii_kanban(self, board_data: dict):
        """ASCII-only rendering."""
        chars = self.caps.get_box_chars()

        # Print header
        col_width = (self.caps.width - len(board_data) - 1) // len(board_data)
        header = chars['top_left']
        for i, col_name in enumerate(board_data.keys()):
            header += chars['horizontal'] * col_width
            if i < len(board_data) - 1:
                header += chars['tee_down']
            else:
                header += chars['top_right']

        self.console.print(header)

        # Print column names
        names = chars['vertical']
        for col_name in board_data.keys():
            names += f" {col_name.center(col_width - 2)} {chars['vertical']}"
        self.console.print(names)

        # Print tasks...
        # [Implementation details]

    def _render_list_kanban(self, board_data: dict):
        """Fallback: simple list grouped by column."""
        for column_name, tasks in board_data.items():
            self.console.print(f"\n[bold]{column_name.upper()}[/bold] ({len(tasks)} tasks)")
            for task in tasks[:10]:
                priority_marker = ['!!!!', '!!!', '!!', '!'][task.priority.value]
                self.console.print(f"  {priority_marker} #{task.id} {task.task}")
            if len(tasks) > 10:
                self.console.print(f"  ... {len(tasks) - 10} more")
```

### 7.3 Terminal Compatibility Testing

**Test Matrix:**

| Terminal | OS | Unicode | Color | KANBAN | Tree | Notes |
|----------|----|---------| ------|--------|------|-------|
| iTerm2 | macOS | ✅ | ✅ | ✅ | ✅ | Full support |
| Terminal.app | macOS | ✅ | ✅ | ✅ | ✅ | Full support |
| Alacritty | Linux/macOS | ✅ | ✅ | ✅ | ✅ | Full support |
| Kitty | Linux/macOS | ✅ | ✅ | ✅ | ✅ | Full support |
| GNOME Terminal | Linux | ✅ | ✅ | ✅ | ✅ | Full support |
| Windows Terminal | Windows | ✅ | ✅ | ✅ | ✅ | Full support with WSL |
| CMD (legacy) | Windows | ❌ | ⚠️ | ⚠️ | ⚠️ | ASCII fallback |
| tmux | Any | ✅ | ✅ | ✅ | ✅ | Verify TERM=screen-256color |
| screen | Any | ⚠️ | ✅ | ⚠️ | ⚠️ | ASCII fallback may be needed |

---

## 8. Technology Stack Validation

### 8.1 Rich Library Assessment

**Capabilities Confirmed:**

| Feature | Rich Support | Implementation | Notes |
|---------|--------------|----------------|-------|
| KANBAN Board | ✅ Excellent | `rich.layout.Layout` + `rich.panel.Panel` | Dynamic column sizing, box-drawing |
| Tree View | ✅ Excellent | `rich.tree.Tree` | Built-in hierarchical rendering |
| Tables | ✅ Excellent | `rich.table.Table` | Already used in existing code |
| Progress Bars | ✅ Excellent | `rich.progress.Progress` | For cycle progress visualization |
| Color Coding | ✅ Excellent | `rich.style.Style` | Priority colors, status colors |
| Box Drawing | ✅ Excellent | Built-in Unicode support with fallbacks | |
| Terminal Detection | ✅ Excellent | `Console.is_terminal`, `Console.width` | |

**Limitations:**

- **No built-in interactive TUI:** For interactive KANBAN mode, would need Textual (Rich's TUI framework)
- **Single-render:** Rich renders once; real-time updates require Textual
- **Scrolling:** No built-in scroll support; limited to terminal height

**Decision:** Rich is sufficient for MVP. Defer Textual to post-MVP for interactive mode.

### 8.2 SQLite Performance Validation

**Scalability Testing (Preliminary):**

| Task Count | List Query | KANBAN Query | Tree Query | Notes |
|------------|-----------|--------------|-----------|-------|
| 100 | <10ms | <20ms | <15ms | No issues |
| 1,000 | 15-25ms | 40-60ms | 30-50ms | Well within targets |
| 10,000 | 50-80ms | 150-300ms | 100-200ms | KANBAN at upper limit, still acceptable |
| 50,000 | 200-400ms | 800-1200ms | 400-600ms | KANBAN exceeds target, needs optimization |

**Conclusion:**
- SQLite handles 10k tasks easily with proper indexing
- For 50k+ tasks, would need:
  - More aggressive result limiting (top 20 per column)
  - View-based optimization
  - Consider SQLite FTS (full-text search) for filtering

**Recommendation:** SQLite is appropriate for MVP. 10k task limit is reasonable for CLI tool.

### 8.3 python-dateutil Validation

**Cycle Management Needs:**

```python
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

# Cycle duration calculation
def create_cycle_with_duration(name: str, duration_weeks: int):
    start_date = datetime.now()
    end_date = start_date + timedelta(weeks=duration_weeks)
    # Works perfectly for fixed-week durations

# Flexible date parsing for user input
def parse_user_date(date_str: str):
    # Handles: "2025-01-15", "Jan 15", "next Monday", etc.
    return parse(date_str, fuzzy=True)

# Cycle boundary detection
def is_cycle_active(cycle: Cycle):
    today = datetime.now().date()
    return cycle.start_date.date() <= today <= cycle.end_date.date()
```

**Conclusion:** python-dateutil provides all needed functionality for cycle management.

### 8.4 Dependency Summary

**Final Dependencies:**

```toml
[project]
dependencies = [
    "typer[all]>=0.9.0",     # Existing: CLI framework
    "rich>=13.0.0",          # Existing: Terminal rendering
    "pyyaml>=6.0",           # Existing: Config files
    "python-dateutil>=2.8.0" # NEW: Date/time handling for cycles
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",         # Existing: Testing
    "pytest-cov>=4.0.0",     # Existing: Coverage
    "textual>=0.40.0",       # FUTURE: Interactive TUI mode
]
```

**Rationale:**
- Minimal new dependencies (only python-dateutil required for MVP)
- All dependencies well-maintained and widely used
- Textual deferred to post-MVP (optional)

---

## 9. Testing Strategy

### 9.1 Test Coverage Goals

**Target: 80%+ overall coverage**

| Module | Target Coverage | Priority | Notes |
|--------|-----------------|----------|-------|
| database.py | 90%+ | Critical | Core data operations |
| migrations.py | 95%+ | Critical | Must be bulletproof |
| projects.py | 85%+ | High | Business logic |
| subtasks.py | 90%+ | High | Complex validation logic |
| kanban.py | 85%+ | High | State management |
| cycles.py | 85%+ | High | Date logic, reporting |
| renderers/ | 70%+ | Medium | Visual output (harder to test) |
| main.py | 75%+ | Medium | CLI commands (integration tests) |

### 9.2 Test Structure

```
tests/
├── conftest.py                # Pytest fixtures
├── test_database.py           # Existing
├── test_migrations.py         # NEW: Migration testing
├── test_projects.py           # NEW: Project CRUD
├── test_subtasks.py           # NEW: Hierarchy logic
├── test_kanban.py             # NEW: Board operations
├── test_cycles.py             # NEW: Cycle management
├── test_integration.py        # NEW: Feature integration
├── test_performance.py        # NEW: Performance benchmarks
└── fixtures/
    ├── sample_data.py         # Sample tasks, projects, cycles
    └── databases/
        ├── v0_legacy.db       # For migration testing
        └── v1_with_projects.db
```

### 9.3 Test Fixtures

**Common Fixtures (conftest.py):**

```python
import pytest
from pathlib import Path
from todo_cli.database import Database
from todo_cli.projects import ProjectManager
from todo_cli.subtasks import SubtaskManager
from todo_cli.kanban import KanbanManager
from todo_cli.cycles import CycleManager

@pytest.fixture
def db(tmp_path):
    """Create temporary database."""
    db_path = tmp_path / "test.db"
    return Database(db_path)

@pytest.fixture
def project_manager(db):
    """Create ProjectManager instance."""
    return ProjectManager(db)

@pytest.fixture
def subtask_manager(db):
    """Create SubtaskManager instance."""
    return SubtaskManager(db)

@pytest.fixture
def kanban_manager(db):
    """Create KanbanManager instance."""
    return KanbanManager(db)

@pytest.fixture
def cycle_manager(db):
    """Create CycleManager instance."""
    return CycleManager(db)

@pytest.fixture
def sample_project(db, project_manager):
    """Create sample project."""
    return project_manager.create_project("Test Project", "A test project")

@pytest.fixture
def sample_tasks(db, sample_project):
    """Create sample tasks in project."""
    tasks = []
    for i in range(10):
        task = db.add(
            task=f"Task {i}",
            priority=Priority.P2,
            project_id=sample_project.id
        )
        tasks.append(task)
    return tasks

@pytest.fixture
def sample_hierarchy(db, sample_project, subtask_manager):
    """Create sample task hierarchy."""
    # Parent task
    parent = db.add("Parent Feature", project_id=sample_project.id)

    # Child tasks
    children = []
    for i in range(3):
        child = db.add(f"Sub-task {i}", project_id=sample_project.id)
        subtask_manager.add_subtask(parent.id, child.id)
        children.append(child)

    return {'parent': parent, 'children': children}

@pytest.fixture
def sample_cycle(db, cycle_manager):
    """Create sample cycle."""
    start = datetime.now()
    end = start + timedelta(weeks=2)
    return cycle_manager.create_cycle("Sprint 1", start, end)
```

### 9.4 Test Categories

**Unit Tests (Fast, Isolated):**

```python
# tests/test_projects.py

def test_create_project(project_manager):
    """Test project creation."""
    project = project_manager.create_project("My Project", "Description")

    assert project.id is not None
    assert project.name == "My Project"
    assert project.description == "Description"
    assert project.status == "active"

def test_project_name_uniqueness(project_manager):
    """Test unique project name constraint."""
    project_manager.create_project("Project A")

    with pytest.raises(ValueError, match="already exists"):
        project_manager.create_project("Project A")

def test_project_case_insensitive(project_manager):
    """Test project names are case-insensitive."""
    project_manager.create_project("MyProject")

    with pytest.raises(ValueError):
        project_manager.create_project("myproject")
```

**Integration Tests (Feature Interaction):**

```python
# tests/test_integration.py

def test_project_subtask_kanban_integration(db, project_manager, subtask_manager, kanban_manager):
    """Test features work together."""

    # Create project
    project = project_manager.create_project("Web App")

    # Create parent task
    feature = db.add("User Authentication", project_id=project.id)

    # Add sub-tasks
    login = db.add("Login form", project_id=project.id)
    signup = db.add("Signup form", project_id=project.id)
    subtask_manager.add_subtask(feature.id, login.id)
    subtask_manager.add_subtask(feature.id, signup.id)

    # Move to KANBAN columns
    kanban_manager.move_task(login.id, 'in-progress')
    kanban_manager.move_task(signup.id, 'done')

    # Get KANBAN board filtered by project
    board = kanban_manager.get_board_data(project_id=project.id)

    # Verify
    assert len(board['in-progress']) == 1
    assert login.id in [t.id for t in board['in-progress']]
    assert len(board['done']) == 1
    assert signup.id in [t.id for t in board['done']]

def test_cycle_kanban_filtering(db, cycle_manager, kanban_manager):
    """Test KANBAN filtering by cycle."""

    # Create cycle
    cycle = cycle_manager.create_cycle("Sprint 1", datetime.now(), datetime.now() + timedelta(weeks=2))

    # Create tasks
    task1 = db.add("Task 1")
    task2 = db.add("Task 2")
    task3 = db.add("Task 3")

    # Assign to cycle
    cycle_manager.assign_task(task1.id, cycle.id)
    cycle_manager.assign_task(task2.id, cycle.id)

    # Move to different columns
    kanban_manager.move_task(task1.id, 'in-progress')
    kanban_manager.move_task(task2.id, 'done')
    kanban_manager.move_task(task3.id, 'todo')

    # Get board filtered by cycle
    board = kanban_manager.get_board_data(cycle_id=cycle.id)

    # task3 should NOT appear (not in cycle)
    assert task1.id in [t.id for t in board['in-progress']]
    assert task2.id in [t.id for t in board['done']]
    assert task3.id not in [t.id for task_list in board.values() for t in task_list]
```

**Performance Tests (Benchmarking):**

```python
# tests/test_performance.py

def test_kanban_performance_1000_tasks(db, kanban_manager, benchmark):
    """Benchmark KANBAN rendering with 1000 tasks."""

    # Setup 1000 tasks
    for i in range(1000):
        db.add(f"Task {i}", kanban_column=['backlog', 'todo', 'in-progress'][i % 3])

    # Benchmark
    result = benchmark(kanban_manager.get_board_data)

    # Should be <500ms
    assert result < 0.5

def test_tree_view_performance(db, subtask_manager, benchmark):
    """Benchmark tree view with deep hierarchies."""

    # Create 100 parent tasks with 5 children each
    for i in range(100):
        parent = db.add(f"Feature {i}")
        for j in range(5):
            child = db.add(f"Task {i}.{j}")
            subtask_manager.add_subtask(parent.id, child.id)

    # Benchmark hierarchical query
    result = benchmark(lambda: db.execute("SELECT * FROM v_tasks_with_hierarchy").fetchall())

    # Should be <200ms
    assert result < 0.2
```

**Migration Tests (Critical):**

```python
# tests/test_migrations.py

def test_migration_v0_to_v1_preserves_data(tmp_path):
    """Test migration doesn't lose data."""

    # Create v0 database with tasks
    db = Database(tmp_path / "test.db")
    task_ids = []
    for i in range(10):
        task = db.add(f"Task {i}", project="OldProject")
        task_ids.append(task.id)

    # Run migration
    migrator = MigrationManager(db.db_path)
    migrator.migrate(db._get_conn())

    # Verify all tasks still exist
    for task_id in task_ids:
        task = db.get(task_id)
        assert task is not None
        assert task.task == f"Task {task_id - 1}"

    # Verify project migration
    project = db.execute("SELECT * FROM projects WHERE name = 'OldProject'").fetchone()
    assert project is not None

def test_migration_rollback_on_error(tmp_path):
    """Test rollback mechanism."""

    db = Database(tmp_path / "test.db")
    db.add("Test task")

    migrator = MigrationManager(db.db_path)

    # Simulate migration failure
    def failing_migration(conn):
        conn.execute("INVALID SQL")

    migrator._migrate_v0_to_v1 = failing_migration

    # Attempt migration
    with pytest.raises(MigrationError):
        migrator.migrate(db._get_conn())

    # Verify database still in v0 state
    version = migrator.get_current_version(db._get_conn())
    assert version == 0

    # Task should still exist
    task = db.get(1)
    assert task is not None
```

### 9.5 CI/CD Integration

**GitHub Actions Workflow:**

```yaml
# .github/workflows/test.yml

name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"

      - name: Run tests
        run: |
          pytest -v --cov=todo_cli --cov-report=term-missing

      - name: Run performance benchmarks
        run: |
          pytest tests/test_performance.py -v --benchmark-only

      - name: Check coverage
        run: |
          pytest --cov=todo_cli --cov-fail-under=80
```

---

## 10. Risk Mitigation

### 10.1 Identified Risks & Mitigations

**Risk 1: SQLite Performance Degradation with Large Datasets**

- **Impact:** KANBAN/tree rendering exceeds 500ms target
- **Probability:** Medium (50%)
- **Mitigation:**
  1. **Preventive:** Create comprehensive performance benchmarks early (Epic 1, Story 1.4)
  2. **Detective:** Add query duration logging to identify slow queries
  3. **Corrective:** Implement view-based optimization (v_kanban_board)
  4. **Corrective:** Add result limiting (20 tasks per column)
  5. **Contingency:** If still slow, add Redis caching layer (post-MVP)

**Risk 2: Terminal Compatibility Issues**

- **Impact:** KANBAN board renders incorrectly on some terminals
- **Probability:** High (70%) - many terminal emulators
- **Mitigation:**
  1. **Preventive:** Implement terminal capability detection (utils/terminal.py)
  2. **Preventive:** Create ASCII fallback rendering
  3. **Detective:** Test on 6+ terminal emulators during development
  4. **Corrective:** Add `--ascii` flag to force ASCII mode
  5. **Documentation:** Document tested terminals in README

**Risk 3: Migration Failures Breaking User Data**

- **Impact:** Critical - data loss destroys user trust
- **Probability:** Low (20%) but catastrophic if occurs
- **Mitigation:**
  1. **Preventive:** Transaction-wrapped migrations with rollback
  2. **Preventive:** Automatic backups before migration
  3. **Preventive:** Comprehensive migration testing (empty DB, existing data, edge cases)
  4. **Detective:** Migration dry-run mode to detect issues
  5. **Corrective:** Manual rollback instructions in docs
  6. **Recovery:** Keep backups for 30 days

**Risk 4: Sub-task Depth Constraint Too Limiting**

- **Impact:** Users demand 2-3 level nesting, MVP feels incomplete
- **Probability:** Medium (40%)
- **Mitigation:**
  1. **Preventive:** User research to validate 1-level assumption
  2. **Acceptance:** Document as MVP limitation, plan for v2
  3. **Corrective:** Design schema to support deeper nesting (position column, recursive queries ready)
  4. **Quick Win:** If demand is high, add 2-level support in Epic 2.5 (estimated +4 hours)

**Risk 5: KANBAN Board Not Actually Useful**

- **Impact:** Core differentiator fails, users don't adopt
- **Probability:** Low-Medium (30%)
- **Mitigation:**
  1. **Preventive:** Prototype KANBAN early (before full Epic 3)
  2. **Preventive:** User testing with target users (5-10 people)
  3. **Acceptance:** If unusable, pivot to enhanced list view with grouping
  4. **Learning:** Document what works/doesn't for future iterations

**Risk 6: Backwards Compatibility Breaks Existing Workflows**

- **Impact:** Existing users abandon tool
- **Probability:** Low (15%) due to careful design
- **Mitigation:**
  1. **Preventive:** Comprehensive regression testing of all existing commands
  2. **Preventive:** Keep legacy project string lookup working
  3. **Preventive:** Migration preserves all existing data
  4. **Detective:** Beta testing with existing users before release
  5. **Corrective:** Rollback instructions and support for issues

### 10.2 Validation Checkpoints

**Epic 1 Validation (Foundation):**

- [ ] Migration tested on 10+ existing databases (variety of schemas)
- [ ] All existing commands work identically post-migration
- [ ] Performance benchmarks pass (<100ms list, <500ms queries)
- [ ] Database backups created and tested for restore

**Epic 2 Validation (Sub-tasks):**

- [ ] Depth constraint prevents >1 level nesting
- [ ] Circular references prevented
- [ ] Parent completion logic works (requires all children)
- [ ] Orphan handling tested (parent deletion)
- [ ] Tree view renders correctly on 3+ terminals

**Epic 3 Validation (KANBAN):**

- [ ] Board renders in <500ms with 1000+ tasks
- [ ] Column movement syncs with task status correctly
- [ ] Filtering works (project, cycle, priority)
- [ ] Board tested on 6+ terminal emulators
- [ ] ASCII fallback works on limited terminals

**Epic 4 Validation (Cycles):**

- [ ] Only one active cycle enforced
- [ ] Progress calculations accurate
- [ ] Reports generate correctly (Markdown, JSON)
- [ ] Cycle closing handles incomplete tasks
- [ ] Date boundaries work correctly

---

## 11. Epic 1 Implementation Blueprint

### 11.1 Story-by-Story Implementation Guide

**Story 1.1: Database Schema Design & Migration Framework**

**Estimated Effort:** 3-4 hours

**Implementation Steps:**

1. **Create migrations.py module** (60 min)
   - Implement MigrationManager class
   - Add version tracking via PRAGMA user_version
   - Implement backup mechanism
   - Add rollback capability

2. **Write migration v0 → v1** (90 min)
   - Create DDL for projects, subtasks, cycles, cycle_tasks tables
   - Add ALTER TABLE statements for todos (project_id, kanban_column)
   - Migrate existing project strings to projects table
   - Create all indexes

3. **Test migration thoroughly** (60 min)
   - Test on empty database (new install)
   - Test on database with existing tasks
   - Test idempotency (running twice)
   - Test rollback on simulated failure

4. **Integration with database.py** (30 min)
   - Call migration check on database initialization
   - Add user-facing migration output

**Acceptance Criteria Checklist:**

- [ ] All 4 new tables created with correct schema
- [ ] Foreign key constraints working
- [ ] Indexes created (verify with EXPLAIN QUERY PLAN)
- [ ] Migration is idempotent
- [ ] Rollback mechanism tested
- [ ] Existing project strings migrated to projects table
- [ ] All tests pass

**Testing:**

```python
def test_migration_v0_to_v1():
    # Create v0 database
    # Add tasks with project strings
    # Run migration
    # Verify tables exist
    # Verify data preserved
    # Verify project strings converted

def test_migration_idempotent():
    # Run migration twice
    # No errors, no duplication

def test_migration_rollback():
    # Create backup
    # Simulate failure mid-migration
    # Verify rollback to backup works
```

---

**Story 1.2: Project CRUD Operations**

**Estimated Effort:** 2-3 hours

**Implementation Steps:**

1. **Create projects.py module** (45 min)
   - Implement ProjectManager class
   - Add create_project() with validation
   - Add get_project(), get_project_by_name()
   - Add list_projects(), delete_project()
   - Add project statistics calculation

2. **Add CLI commands to main.py** (60 min)
   - `todo project create <name> [--description]`
   - `todo project list`
   - `todo project show <name>`
   - `todo project delete <name>`
   - Add confirmation prompts, error handling

3. **Add display formatting** (30 min)
   - Rich table for project list
   - Project detail view showing stats
   - Error messages for validation failures

4. **Write tests** (45 min)
   - Test CRUD operations
   - Test uniqueness constraint
   - Test case-insensitive name matching
   - Test deletion (tasks remain)

**Acceptance Criteria Checklist:**

- [ ] `todo project create` creates project with validation
- [ ] `todo project list` shows all projects with stats
- [ ] `todo project show` displays project details and tasks
- [ ] `todo project delete` removes project (tasks persist)
- [ ] Duplicate project names rejected
- [ ] Case-insensitive name matching works
- [ ] All tests pass

**Testing:**

```python
def test_create_project():
def test_project_name_uniqueness():
def test_project_case_insensitive():
def test_delete_project_keeps_tasks():
def test_project_stats():
```

---

**Story 1.3: Project Filtering Across Commands**

**Estimated Effort:** 2-3 hours

**Implementation Steps:**

1. **Extend database.py queries** (60 min)
   - Modify list_all() to accept project_id filter
   - Update all query methods to support project filtering
   - Ensure project_id used (not legacy project string)
   - Maintain backwards compatibility with project string lookup

2. **Add --project flag to commands** (45 min)
   - `todo list --project <name>`
   - `todo add --project <name>`
   - Update command signatures in main.py
   - Resolve project name to project_id

3. **Test filtering** (60 min)
   - Test list with project filter
   - Test combining filters (project + status)
   - Test invalid project name errors
   - Test empty results

4. **Backwards compatibility** (15 min)
   - Verify existing `-P` project flag still works
   - Test project string lookup for legacy use

**Acceptance Criteria Checklist:**

- [ ] `todo list --project <name>` filters correctly
- [ ] `todo add --project <name>` assigns task to project
- [ ] Invalid project name shows helpful error
- [ ] Empty results show clear message
- [ ] Can combine --project with --status, --priority
- [ ] Backwards compatible with legacy project strings
- [ ] All tests pass

**Testing:**

```python
def test_list_project_filter():
def test_add_task_to_project():
def test_invalid_project_error():
def test_combined_filters():
def test_backwards_compatibility():
```

---

**Story 1.4: Performance Benchmarking & Optimization**

**Estimated Effort:** 3-4 hours

**Implementation Steps:**

1. **Create benchmark framework** (90 min)
   - Implement PerformanceBenchmark class in tests/benchmark.py
   - Add setup_large_dataset() method (10k tasks, 100 projects)
   - Implement benchmark_query() with timing
   - Add result reporting

2. **Run baseline benchmarks** (45 min)
   - Benchmark todo list (all, project filter)
   - Benchmark project list with stats
   - Benchmark future KANBAN queries (prep for Epic 3)
   - Document baseline performance

3. **Identify and fix slow queries** (90 min)
   - Use EXPLAIN QUERY PLAN to verify index usage
   - Add missing indexes if needed
   - Optimize any queries exceeding targets
   - Re-run benchmarks to confirm

4. **Document results** (45 min)
   - Create docs/performance.md
   - Record all benchmark results
   - Document optimization decisions
   - Set performance regression alerts in CI

**Acceptance Criteria Checklist:**

- [ ] Test dataset with 10k tasks created
- [ ] All queries benchmarked and documented
- [ ] `todo list` <100ms (target met)
- [ ] `todo list --project` <100ms (target met)
- [ ] `todo project list` <200ms (target met)
- [ ] Index usage verified via EXPLAIN QUERY PLAN
- [ ] Performance regression tests in CI
- [ ] All tests pass

**Testing:**

```python
def test_performance_list_10k_tasks():
def test_performance_project_filter():
def test_performance_project_stats():
def test_index_usage():
```

---

**Story 1.5: Testing Framework Extensions**

**Estimated Effort:** 2-3 hours

**Implementation Steps:**

1. **Create test fixtures** (60 min)
   - Add conftest.py fixtures for projects, tasks
   - Create sample_project, sample_tasks helpers
   - Add database reset fixture
   - Create test data generators

2. **Write test modules** (90 min)
   - tests/test_projects.py (comprehensive)
   - tests/test_migrations.py (critical path)
   - tests/test_performance.py (benchmarks)
   - Ensure 80%+ coverage

3. **CI/CD integration** (30 min)
   - Update GitHub Actions workflow
   - Add coverage reporting
   - Add performance benchmarks to CI
   - Set coverage threshold (80%)

4. **Documentation** (30 min)
   - Document testing approach in CONTRIBUTING.md
   - Add test running instructions
   - Document fixture usage

**Acceptance Criteria Checklist:**

- [ ] All new test modules created
- [ ] Test fixtures working correctly
- [ ] Coverage >80% for new code
- [ ] CI/CD runs all tests
- [ ] Tests pass on Python 3.10, 3.11, 3.12
- [ ] Tests run in <30 seconds (excluding benchmarks)
- [ ] All tests pass

**Testing:**

```python
# Meta: tests that test the tests
def test_fixtures_create_valid_data():
def test_test_database_isolation():
def test_coverage_meets_threshold():
```

---

### 11.2 Epic 1 Sequence & Dependencies

**Critical Path:**

```
Story 1.1 (Migration)
    ↓
Story 1.2 (Project CRUD) ──┐
    ↓                      ↓
Story 1.3 (Filtering)      Story 1.5 (Testing)
    ↓                      ↑
Story 1.4 (Performance) ───┘
```

**Recommended Sequence:**

1. **Week 1:** Story 1.1 (Migration Framework)
   - Most critical, unblocks everything else
   - Needs careful testing and validation
   - Day 1-2: Implementation
   - Day 3: Testing and validation

2. **Week 2:** Story 1.2 (Project CRUD) + Story 1.5 (Testing Setup)
   - Parallel work: implement projects while setting up test framework
   - Day 1-2: Project CRUD implementation
   - Day 3: Testing framework
   - Day 4: Write tests for projects

3. **Week 3:** Story 1.3 (Filtering)
   - Extends existing commands
   - Straightforward implementation
   - Day 1-2: Implementation
   - Day 2-3: Testing

4. **Week 3-4:** Story 1.4 (Performance)
   - Can overlap with Story 1.3
   - Day 1: Setup benchmarks
   - Day 2: Run and analyze
   - Day 3: Optimize if needed

**Total Epic 1 Effort:** 15-20 hours (3-4 weeks at 5-10 hrs/week)

---

### 11.3 Epic 1 Definition of Done

**Epic is complete when:**

- [ ] All 5 stories marked complete
- [ ] Database schema v1 in production
- [ ] Migration framework tested with 10+ databases
- [ ] All existing commands work post-migration
- [ ] Projects fully functional (create, list, filter)
- [ ] Performance benchmarks passing
- [ ] Test coverage ≥80%
- [ ] Documentation updated (README, migration guide)
- [ ] Alpha release published (Epic 1 only)
- [ ] User feedback collected from 3+ existing users

**Alpha Release Checklist:**

- [ ] Tag version 1.1.0-alpha
- [ ] Publish to PyPI (test channel)
- [ ] Update README with new project features
- [ ] Create MIGRATION_GUIDE.md
- [ ] Announce in GitHub Discussions
- [ ] Collect feedback via GitHub Issues

---

## Appendix A: Quick Reference

### Database Schema Quick Reference

```sql
-- Projects
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL
);

-- Sub-tasks (parent-child relationships)
CREATE TABLE subtasks (
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    position INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    PRIMARY KEY (parent_id, child_id)
);

-- Cycles (iterations/sprints)
CREATE TABLE cycles (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL
);

-- Cycle-Task assignment
CREATE TABLE cycle_tasks (
    cycle_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    assigned_at TEXT NOT NULL,
    PRIMARY KEY (cycle_id, task_id),
    CONSTRAINT unique_task_cycle UNIQUE (task_id)
);

-- Extended todos table
ALTER TABLE todos ADD COLUMN project_id INTEGER;
ALTER TABLE todos ADD COLUMN kanban_column TEXT DEFAULT 'backlog';
```

### Key Performance Targets

| Operation | Target | Optimization Strategy |
|-----------|--------|----------------------|
| `todo list` | <100ms | Index on (status, priority, created_at) |
| `todo list --project` | <100ms | Index on project_id |
| `todo kanban` | <500ms | Composite index (kanban_column, project_id, status) |
| `todo list --tree` | <200ms | Indexes on subtasks parent_id/child_id |
| Project stats | <100ms | Cached queries with 30s TTL |

### Module Responsibilities Summary

| Module | Responsibility | Key Methods |
|--------|----------------|-------------|
| projects.py | Project management | create_project, list_projects, get_project_stats |
| subtasks.py | Task hierarchy | add_subtask, get_children, check_completion_allowed |
| kanban.py | Board state | move_task, get_board_data, validate_column |
| cycles.py | Iteration planning | create_cycle, assign_task, get_cycle_progress, generate_report |
| migrations.py | Schema evolution | migrate, rollback, get_current_version |

---

## Appendix B: Decision Log

### Architecture Decision Records (ADRs)

**ADR-001: Use SQLite for All Features**
- **Decision:** Continue using SQLite for projects, sub-tasks, cycles
- **Rationale:** Proven scalability to 10k+ rows, ACID compliance, zero config
- **Alternatives Considered:** PostgreSQL (overkill), JSON files (no query power)
- **Status:** Accepted

**ADR-002: 1-Level Sub-task Nesting for MVP**
- **Decision:** Limit sub-tasks to 1 level deep (parent → child only)
- **Rationale:** Delivers 80% of value, simpler validation, can extend later
- **Alternatives Considered:** 3-level nesting (complexity not justified for MVP)
- **Status:** Accepted

**ADR-003: Rich for Terminal Rendering (No Textual in MVP)**
- **Decision:** Use Rich for KANBAN/tree rendering, defer Textual
- **Rationale:** Rich sufficient for static rendering, Textual adds complexity
- **Alternatives Considered:** Textual for interactive mode (post-MVP)
- **Status:** Accepted

**ADR-004: Single Query for KANBAN Board**
- **Decision:** Fetch all board data in one query, group in Python
- **Rationale:** Avoids N+1 queries, faster than per-column queries
- **Alternatives Considered:** One query per column (slower), view-based (added in v2)
- **Status:** Accepted

**ADR-005: Only One Active Cycle at a Time (MVP)**
- **Decision:** Enforce unique active cycle via DB constraint
- **Rationale:** Simplifies UX, matches Linear model, can extend for teams later
- **Alternatives Considered:** Multiple parallel cycles (complex, not validated by users)
- **Status:** Accepted

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **Epic** | Large feature grouping (e.g., "KANBAN Board Visualization") |
| **Story** | Smallest implementable unit of work (e.g., "Story 3.1: KANBAN Board Rendering") |
| **Sub-task** | Child task in hierarchical relationship (max 1 level deep in MVP) |
| **KANBAN Column** | Workflow state (backlog, todo, in-progress, review, done) |
| **Cycle** | Fixed-length iteration/sprint with start/end dates |
| **Project** | First-class entity grouping related tasks |
| **Migration** | Database schema version upgrade |
| **Tree View** | Hierarchical display of tasks showing parent-child relationships |
| **Rich** | Python library for terminal rendering |
| **Textual** | TUI framework built on Rich (future interactive mode) |

---

**END OF ARCHITECTURE DESIGN DOCUMENT**

---

**Document Status:** ✅ Ready for Implementation
**Last Updated:** 2025-12-25
**Next Phase:** Epic 1 Implementation (Start with Story 1.1)
