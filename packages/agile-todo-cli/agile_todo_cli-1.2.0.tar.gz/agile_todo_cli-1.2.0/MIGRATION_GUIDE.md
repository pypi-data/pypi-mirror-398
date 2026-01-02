# Migration Guide: Upgrading to v1.1.0-alpha (Epic 1)

This guide covers migrating from earlier versions of Todo CLI to v1.1.0-alpha, which includes the Epic 1 foundation features.

## Quick Summary

**Good News:** Migration is **fully automatic** and **backward compatible**. Your existing data will be preserved and enhanced with new features.

**What You Need to Do:**
1. Upgrade to v1.1.0-alpha
2. Run any todo command (e.g., `todo list`)
3. Migration happens automatically on first run
4. Verify your data with `todo list` and `todo project list`

**Time Required:** ~1 second (automatic migration)

---

## Table of Contents

- [What's New in Epic 1](#whats-new-in-epic-1)
- [Before You Migrate](#before-you-migrate)
- [Migration Process](#migration-process)
- [What Happens to Your Data](#what-happens-to-your-data)
- [After Migration](#after-migration)
- [Breaking Changes](#breaking-changes)
- [Rollback Instructions](#rollback-instructions)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## What's New in Epic 1

### New Features

1. **Project Management System**
   - Create, list, edit, archive, and delete projects
   - Project-based task organization
   - Project statistics and reporting
   - Color-coded project visualization

2. **Database Schema v1**
   - New `projects` table for proper project management
   - New `subtasks` table (foundation for Epic 2)
   - New `cycles` and `cycle_tasks` tables (foundation for Epic 4)
   - Enhanced `todos` table with `project_id` foreign key
   - `kanban_column` field (foundation for Epic 3)

3. **Performance Optimizations**
   - Comprehensive database indexing
   - Query optimization (all queries <200ms)
   - Verified index usage via EXPLAIN QUERY PLAN

4. **Enhanced Filtering**
   - Filter by project: `todo list --project "My App"`
   - Combine filters: `todo list --project "My App" --status doing`
   - Case-insensitive project name matching

5. **Improved Testing**
   - 313+ tests with 87% coverage
   - Performance regression tests
   - Comprehensive test fixtures

### Schema Changes

**New Tables:**
```sql
-- Projects table
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    color TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL
);

-- Subtasks table (Epic 2 foundation)
CREATE TABLE subtasks (
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    position INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    PRIMARY KEY (parent_id, child_id),
    FOREIGN KEY (parent_id) REFERENCES todos(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES todos(id) ON DELETE CASCADE
);

-- Cycles table (Epic 4 foundation)
CREATE TABLE cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL
);

-- Cycle tasks junction table (Epic 4 foundation)
CREATE TABLE cycle_tasks (
    cycle_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    added_at TEXT NOT NULL,
    PRIMARY KEY (cycle_id, task_id),
    FOREIGN KEY (cycle_id) REFERENCES cycles(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES todos(id) ON DELETE CASCADE
);
```

**Modified Tables:**
```sql
-- todos table: added columns
ALTER TABLE todos ADD COLUMN project_id INTEGER REFERENCES projects(id);
ALTER TABLE todos ADD COLUMN kanban_column TEXT DEFAULT 'todo';
```

**New Indexes:**
```sql
CREATE INDEX idx_todos_status_priority ON todos(status, priority);
CREATE INDEX idx_todos_project_id ON todos(project_id);
CREATE INDEX idx_todos_priority ON todos(priority, due_date);
```

---

## Before You Migrate

### 1. Backup Your Database (Recommended)

While automatic backups are created during migration, we recommend creating your own backup:

```bash
# Find your database location
todo config path

# The database is typically at:
# ~/.local/share/todo-cli/todos.db

# Create a manual backup
cp ~/.local/share/todo-cli/todos.db ~/.local/share/todo-cli/todos.db.pre-epic1.backup
```

### 2. Note Your Current Setup

Document any important information:
- Number of tasks: `todo list --all | wc -l`
- Projects you're using (if using legacy project strings)
- Any custom configurations: `todo config show`

### 3. Update Todo CLI

```bash
# If installed in development mode
cd /path/to/todo-cli
git pull origin main
pip install -e .

# If installed via pip
pip install --upgrade todo-cli
```

---

## Migration Process

### Automatic Migration

Migration happens automatically the first time you run any todo command after upgrading:

```bash
# Run any command to trigger migration
todo list

# You'll see output like:
# Migrating database from version 0 to version 1...
# Creating backup: todos.db.backup_20251226_143022
# Migration v0→v1 completed successfully
# Database migrated to version 1
```

### What Happens During Migration

The migration system performs these steps:

1. **Version Check**
   - Reads current schema version (stored in `PRAGMA user_version`)
   - Determines if migration is needed

2. **Backup Creation**
   - Creates timestamped backup: `todos.db.backup_YYYYMMDD_HHMMSS`
   - Stored in same directory as original database

3. **Schema Migration (v0 → v1)**
   - Creates new tables: `projects`, `subtasks`, `cycles`, `cycle_tasks`
   - Adds new columns to `todos`: `project_id`, `kanban_column`
   - Creates performance indexes
   - **Migrates legacy project strings to projects table**

4. **Data Migration**
   - Extracts unique project names from `todos.project` (old string field)
   - Creates project records in `projects` table
   - Updates `todos.project_id` to reference new project records
   - Preserves all task data, tags, due dates, time tracking

5. **Validation**
   - Verifies foreign key constraints
   - Confirms index creation
   - Sets schema version to 1

6. **Completion**
   - Migration marked complete
   - Database ready to use

### Migration Performance

- **Small databases (<100 tasks):** <1 second
- **Medium databases (100-1000 tasks):** 1-2 seconds
- **Large databases (1000+ tasks):** 2-5 seconds

---

## What Happens to Your Data

### Tasks (Todos)

**✅ Fully Preserved:**
- All task descriptions
- All priorities
- All statuses (todo/doing/done)
- All tags
- All due dates
- All creation timestamps
- All completion timestamps
- All time tracking data (`time_spent`, `started_at`)

**🔄 Enhanced:**
- Legacy project strings → Proper project references
- New `kanban_column` field (defaults to 'todo')

### Projects

**Before Migration:**
```
Task 1: "Build login page" project="myapp"
Task 2: "Fix bug #123" project="myapp"
Task 3: "Write tests" project="backend"
```

**After Migration:**
```
Projects table:
  - id=1, name="myapp", status="active"
  - id=2, name="backend", status="active"

Tasks:
  - Task 1: project_id=1 (references "myapp")
  - Task 2: project_id=1 (references "myapp")
  - Task 3: project_id=2 (references "backend")
```

### Configuration

**✅ Fully Preserved:**
- All config settings unchanged
- Config file location unchanged
- Custom database path honored

---

## After Migration

### 1. Verify Your Data

```bash
# List all tasks (should show same tasks as before)
todo list --all

# List all projects (converted from legacy strings)
todo project list

# Check specific project
todo project show "myapp"

# Verify stats
todo stats
```

### 2. Try New Features

```bash
# Create a new project
todo project create "New Project" --description "My new project" --color cyan

# Add task to project
todo add "New task" -P "New Project"

# Filter by project
todo list --project "New Project"

# View project stats
todo project show "New Project"
```

### 3. Performance Verification

The migration includes performance optimizations. Verify they're working:

```bash
# These should all be fast (<200ms)
todo list
todo list --project "myapp"
todo project list
```

### 4. Check Backup

Migration creates an automatic backup. Verify it exists:

```bash
ls -lh ~/.local/share/todo-cli/todos.db.backup_*
```

---

## Breaking Changes

### None! (v1.1.0-alpha is fully backward compatible)

There are **no breaking changes** in this release:

- ✅ All existing commands work exactly as before
- ✅ Legacy project strings in `todo add -P "project"` still work
- ✅ Configuration files unchanged
- ✅ Export formats unchanged
- ✅ Interactive mode unchanged

### Deprecation Notices

While fully compatible, some patterns are now deprecated:

1. **Legacy project strings (deprecated, will work until v2.0)**
   ```bash
   # Old way (still works, but creates project if not exists)
   todo add "Task" -P "myapp"

   # New way (recommended)
   todo project create "myapp"
   todo add "Task" -P "myapp"
   ```

2. **Direct project string access (internal)**
   - The `todos.project` field is deprecated
   - Use `todos.project_id` and join with `projects` table
   - CLI commands handle this automatically

---

## Rollback Instructions

If you encounter issues and need to rollback:

### Option 1: Use Automatic Backup

```bash
# Stop any running todo commands
# Find your backup
ls ~/.local/share/todo-cli/todos.db.backup_*

# Restore from backup
cp ~/.local/share/todo-cli/todos.db.backup_20251226_143022 \
   ~/.local/share/todo-cli/todos.db

# Downgrade to previous version
pip install agile-todo-cli==1.0.0  # or your previous version
```

### Option 2: Use Manual Backup

```bash
# Restore your manual backup
cp ~/.local/share/todo-cli/todos.db.pre-epic1.backup \
   ~/.local/share/todo-cli/todos.db

# Downgrade to previous version
pip install agile-todo-cli==1.0.0
```

### Verification After Rollback

```bash
# Verify tasks are present
todo list --all

# Check version
todo version
```

---

## Troubleshooting

### Migration Fails with "Database is locked"

**Cause:** Another process is using the database.

**Solution:**
```bash
# Find processes using the database
lsof ~/.local/share/todo-cli/todos.db

# Close other todo CLI instances
# Or reboot if necessary

# Retry
todo list
```

### Migration Fails with "Foreign key constraint failed"

**Cause:** Corrupted data in database.

**Solution:**
```bash
# This is very rare. Restore from backup:
cp ~/.local/share/todo-cli/todos.db.backup_* \
   ~/.local/share/todo-cli/todos.db

# Report issue: https://github.com/AgileInnov8tor/todo-cli/issues
```

### Some Projects Missing After Migration

**Cause:** Tasks with empty or NULL project strings aren't migrated.

**Solution:**
```bash
# Check tasks without projects
todo list | grep "No project"

# Manually assign to project
todo edit <id> --project "My Project"
```

### Performance Slower Than Expected

**Cause:** Indexes might not have been created.

**Solution:**
```bash
# Verify indexes exist
sqlite3 ~/.local/share/todo-cli/todos.db "PRAGMA index_list('todos');"

# Should show: idx_todos_status_priority, idx_todos_project_id, idx_todos_priority

# If missing, re-run migration (idempotent)
todo list
```

### Config File Issues

**Cause:** Rare config file corruption.

**Solution:**
```bash
# Reset config to defaults
todo config set default_priority p2
todo config set date_format YYYY-MM-DD

# Or delete config file (will regenerate)
rm ~/.config/todo-cli/config.yaml
todo config show
```

---

## FAQ

### Q: Will my existing tasks be affected?

**A:** No, all task data is fully preserved. The migration only adds new capabilities without modifying existing data.

### Q: How long does migration take?

**A:** Typically <1 second for most databases. Large databases (1000+ tasks) may take 2-5 seconds.

### Q: Can I skip the migration?

**A:** No, migration is automatic and required. However, it's safe, backward compatible, and creates backups.

### Q: What if I don't have any projects?

**A:** Migration still runs successfully. The `projects` table will be empty, and you can start creating projects with `todo project create`.

### Q: Do I need to update my scripts/automation?

**A:** No, all existing commands work exactly as before. New features are additive.

### Q: Can I run migration multiple times?

**A:** Yes! Migration is **idempotent**. Running it multiple times is safe and won't duplicate data.

### Q: Where are backups stored?

**A:** Same directory as your database:
```
~/.local/share/todo-cli/
├── todos.db                        # Current database
├── todos.db.backup_20251226_143022 # Automatic backup
└── todos.db.pre-epic1.backup       # Your manual backup (if created)
```

### Q: How do I verify migration succeeded?

**A:** Run these commands:
```bash
# Should show version 1
sqlite3 ~/.local/share/todo-cli/todos.db "PRAGMA user_version;"

# Should list tables including 'projects'
sqlite3 ~/.local/share/todo-cli/todos.db ".tables"

# Should show your projects
todo project list
```

### Q: Can I migrate back to v0 schema?

**A:** Yes, restore from backup and downgrade Todo CLI version. See [Rollback Instructions](#rollback-instructions).

### Q: Will future migrations be this smooth?

**A:** Yes! We're committed to maintaining backward compatibility and automatic migrations for all future releases.

---

## Support

If you encounter issues not covered in this guide:

- **GitHub Issues:** Report bugs at https://github.com/AgileInnov8tor/todo-cli/issues
- **Discussions:** Ask questions at https://github.com/AgileInnov8tor/todo-cli/discussions
- **Documentation:** See full docs at [docs/](docs/)

---

## Version History

| Version | Schema | Release Date | Migration From | Notes |
|---------|--------|--------------|----------------|-------|
| v1.1.0-alpha | v1 | 2025-12-26 | v0 | Epic 1: Foundation, Projects, Performance |
| v1.0.0 | v0 | 2025-12-01 | - | Initial release |

---

**Migration Summary:**
- ✅ Automatic and seamless
- ✅ Backward compatible
- ✅ No breaking changes
- ✅ Automatic backups
- ✅ Idempotent (safe to re-run)
- ✅ Performance optimized
- ✅ Full data preservation

**Estimated Migration Time:** <5 seconds for most users

Welcome to Epic 1! 🚀
