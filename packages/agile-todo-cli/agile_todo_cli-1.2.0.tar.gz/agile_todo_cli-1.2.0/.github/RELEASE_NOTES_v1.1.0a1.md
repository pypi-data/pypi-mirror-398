# Todo CLI v1.1.0a1 - Epic 1: Foundation (Alpha Release)

> **⚠️ Alpha Release:** This is an early testing release. Features are stable but may evolve based on user feedback.

This is the first alpha release of Epic 1, introducing **project management**, **database schema v1**, and **comprehensive performance optimizations**.

## 🎉 What's New

### Project Management System

Organize your tasks with proper project management:

```bash
# Create a project
todo project create "My App" --description "Mobile app development" --color cyan

# List all projects with statistics
todo project list

# Add tasks to a project
todo add "Design login screen" -P "My App"

# Filter tasks by project
todo list --project "My App"

# View project details
todo project show "My App"

# Archive completed projects
todo project archive "My App"
```

### Automatic Database Migrations

- **Seamless upgrade** - First run automatically migrates your database
- **Automatic backups** - Created before migration for safety
- **Data preservation** - All your tasks, tags, dates, time tracking fully preserved
- **Backward compatible** - All existing commands continue to work
- **Migration time** - Typically <5 seconds

### Performance Optimizations

All common queries are now blazingly fast:

- ✅ **List 1000 tasks:** ~10ms (target: <100ms)
- ✅ **Filter by project:** ~0.23ms (target: <100ms)
- ✅ **Project statistics:** ~0.43ms (target: <200ms)

Strategic database indexing ensures optimal performance even with thousands of tasks.

### Enhanced Filtering

Combine multiple filters for precise task lists:

```bash
# Filter by project
todo list --project "Backend"

# Combine project + status
todo list --project "Backend" --status doing

# Case-insensitive matching
todo list --project "backend"  # Also works!
```

### Comprehensive Testing

- **313 tests** with **87% code coverage**
- Performance regression tests prevent slowdowns
- Multi-version Python support (3.10, 3.11, 3.12, 3.13)
- CI/CD with GitHub Actions

## 📦 Installation

### New Users

```bash
pip install agile-todo-cli==1.1.0a1
```

### Existing Users (Upgrading from v1.0.0)

```bash
# Upgrade
pip install --upgrade agile-todo-cli==1.1.0a1

# First run triggers automatic migration
todo list

# You'll see:
# Migrating database from version 0 to version 1...
# Creating backup: todos.db.backup_20251226_143022
# Migration complete! Database is now at v1
```

**⚠️ Important:** See [MIGRATION_GUIDE.md](https://github.com/AgileInnov8tor/todo-cli/blob/main/MIGRATION_GUIDE.md) for complete migration documentation.

## 🔄 Migration Guide

**For existing users:**

1. **Backup recommended** (automatic backups are created, but manual backup is good practice)
   ```bash
   cp ~/.local/share/todo-cli/todos.db ~/.local/share/todo-cli/todos.db.manual-backup
   ```

2. **Upgrade**
   ```bash
   pip install --upgrade agile-todo-cli==1.1.0a1
   ```

3. **Run any command** (migration is automatic)
   ```bash
   todo list
   ```

4. **Verify data**
   ```bash
   todo list --all        # All tasks preserved
   todo project list      # Projects created from legacy strings
   todo stats            # Statistics still accurate
   ```

**Migration is:**
- ✅ Fully automatic
- ✅ Backward compatible
- ✅ Safe (creates backups)
- ✅ Fast (<5 seconds)
- ✅ Idempotent (safe to re-run)

## 📚 Documentation

- **[MIGRATION_GUIDE.md](https://github.com/AgileInnov8tor/todo-cli/blob/main/MIGRATION_GUIDE.md)** - Complete migration documentation
- **[CONTRIBUTING.md](https://github.com/AgileInnov8tor/todo-cli/blob/main/CONTRIBUTING.md)** - Development guide
- **[CHANGELOG.md](https://github.com/AgileInnov8tor/todo-cli/blob/main/CHANGELOG.md)** - Detailed release notes
- **[docs/performance.md](https://github.com/AgileInnov8tor/todo-cli/blob/main/docs/performance.md)** - Performance benchmarks
- **[docs/architecture.md](https://github.com/AgileInnov8tor/todo-cli/blob/main/docs/architecture.md)** - System architecture

## 🚀 What's Coming Next

### Epic 2: Sub-tasks (Planned)
- Hierarchical task relationships
- Tree view for task lists
- Parent-child task dependencies
- Nested time tracking

### Epic 3: KANBAN Board (Planned)
- Visual board view (Todo/Doing/Done columns)
- Drag-and-drop task movement
- Column customization
- Workflow automation

### Epic 4: Cycles & Sprints (Planned)
- Sprint/iteration management
- Cycle-based task organization
- Sprint planning and retrospectives
- Burndown charts

## 🔧 Technical Details

### Database Schema

**New Tables:**
- `projects` - Store project information with status tracking
- `subtasks` - Parent-child task relationships (Epic 2 foundation)
- `cycles` - Sprint/iteration management (Epic 4 foundation)
- `cycle_tasks` - Task-to-cycle associations (Epic 4 foundation)

**Enhanced Tables:**
- `todos` - Added `project_id` foreign key and `kanban_column` field

**New Indexes:**
- `idx_todos_status_priority` - Fast status filtering with priority ordering
- `idx_todos_project_id` - Fast project-based queries
- `idx_todos_priority` - Fast priority + due date ordering

### Testing & Quality

- **Total tests:** 313
- **Coverage:** 87% (exceeds 80% target)
- **Test execution:** <30 seconds (excluding performance benchmarks)
- **CI/CD:** GitHub Actions with multi-version Python testing
- **Performance tests:** Regression tests ensure queries stay fast

### Python Version Support

- **Minimum:** Python 3.10
- **Tested:** Python 3.10, 3.11, 3.12, 3.13
- **Recommended:** Python 3.13

## ⚠️ Breaking Changes

**None!** This release is fully backward compatible with v1.0.0.

### Deprecations

The following internal patterns are deprecated but still functional (will be removed in v2.0.0):

- Legacy `todos.project` string field (now use `todos.project_id` foreign key)
- CLI commands automatically handle this - no user action required

## 🐛 Known Issues

None at this time. Please report any issues at: https://github.com/AgileInnov8tor/todo-cli/issues

## 📝 Full Changelog

See [CHANGELOG.md](https://github.com/AgileInnov8tor/todo-cli/blob/main/CHANGELOG.md) for complete release notes.

## 💬 Feedback

We'd love to hear your feedback on Epic 1!

- **Report bugs:** https://github.com/AgileInnov8tor/todo-cli/issues/new?labels=bug,epic-1
- **Request features:** https://github.com/AgileInnov8tor/todo-cli/issues/new?labels=enhancement
- **Ask questions:** https://github.com/AgileInnov8tor/todo-cli/discussions/new?category=q-a
- **Share your experience:** https://github.com/AgileInnov8tor/todo-cli/discussions/new?category=show-and-tell

Your feedback helps shape the future of Todo CLI!

## 🙏 Contributors

- Core development and Epic 1 implementation
- Testing framework and CI/CD setup
- Documentation and migration guide

## 📄 License

See [LICENSE](https://github.com/AgileInnov8tor/todo-cli/blob/main/LICENSE) file for details.

---

**Release Checklist for Maintainers:**

- [x] Version updated to 1.1.0a1
- [x] CHANGELOG.md updated
- [x] README.md updated
- [x] MIGRATION_GUIDE.md created
- [x] All tests passing (313 tests, 87% coverage)
- [x] Git tag created (v1.1.0a1)
- [ ] PyPI release (see PYPI_RELEASE.md)
- [ ] GitHub release published
- [ ] Announcement posted to Discussions
- [ ] Users notified of alpha release

**Installation Verification:**

```bash
# Install from PyPI
pip install agile-todo-cli==1.1.0a1

# Verify version
todo version  # Should show: Todo CLI v1.1.0a1

# Test basic functionality
todo add "Test task"
todo list
todo project create "Test Project"
todo project list
```

---

Built with ❤️ using Python, Typer, and Rich.
