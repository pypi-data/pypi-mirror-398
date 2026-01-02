# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0a1] - 2025-12-26

### Epic 1: Foundation Release (Alpha)

This is the first alpha release of Epic 1, introducing project management, database schema v1, and comprehensive performance optimizations.

### Added

#### Project Management System
- **Project CRUD operations** - Create, read, update, delete, archive/unarchive projects
  - `todo project create <name>` - Create new projects with optional description and color
  - `todo project list` - List all active projects with task counts and statistics
  - `todo project show <name>` - Show detailed project information and task breakdown
  - `todo project edit <name>` - Edit project name, description, or color
  - `todo project archive <name>` - Archive projects to hide from active list
  - `todo project unarchive <name>` - Restore archived projects
  - `todo project delete <name>` - Delete projects (tasks remain unassigned)

#### Enhanced Filtering
- **Project-based filtering** - Filter tasks by project with `--project` flag
  - `todo list --project "My App"` - Show tasks for specific project
  - `todo list --project "My App" --status doing` - Combine project and status filters
  - Case-insensitive project name matching
  - Backward compatibility with legacy project strings

#### Database Schema v1
- **New tables** for future Epic features:
  - `projects` - Store project information with status tracking
  - `subtasks` - Parent-child task relationships (Epic 2 foundation)
  - `cycles` - Sprint/iteration management (Epic 4 foundation)
  - `cycle_tasks` - Task-to-cycle associations (Epic 4 foundation)
- **Enhanced todos table**:
  - Added `project_id` foreign key to `projects` table
  - Added `kanban_column` field for KANBAN board (Epic 3 foundation)
  - Preserved all existing fields and data

#### Performance Optimizations
- **Comprehensive database indexing**:
  - `idx_todos_status_priority` - Fast status filtering with priority ordering
  - `idx_todos_project_id` - Fast project-based queries
  - `idx_todos_priority` - Fast priority + due date ordering
- **Query optimization**:
  - List all tasks: ~10ms (target: <100ms) ✅
  - List by project: ~0.23ms (target: <100ms) ✅
  - Project statistics: ~0.43ms (target: <200ms) ✅
  - All queries use appropriate indexes (verified via EXPLAIN QUERY PLAN)

#### Migration Framework
- **Automatic schema migrations** on first run after upgrade
- **Backup creation** before each migration (timestamped)
- **Idempotent migrations** - Safe to run multiple times
- **Migration history tracking** via `PRAGMA user_version`
- **Data preservation** - All existing task data fully preserved
- **Legacy project migration** - Converts old project strings to project references

#### Testing & Quality
- **313+ comprehensive tests** covering all features
- **87% test coverage** (exceeds 80% target)
- **Performance regression tests** to prevent performance degradation
- **Migration tests** for all migration paths (v0→v1, idempotency, rollback)
- **CI/CD integration** with GitHub Actions
  - Multi-version testing (Python 3.10, 3.11, 3.12, 3.13)
  - Coverage reporting to Codecov
  - Performance benchmark validation
  - Code quality checks (ruff, mypy)

#### Documentation
- **MIGRATION_GUIDE.md** - Comprehensive migration documentation
  - Step-by-step migration process
  - Data preservation guarantees
  - Rollback instructions
  - Troubleshooting guide
  - FAQ section
- **Enhanced README.md** - Updated with Epic 1 features
  - Project management examples
  - Performance metrics
  - Roadmap with Epic 1 marked complete
  - Installation and quick start guide
- **CONTRIBUTING.md** - Development and testing guidelines
- **docs/performance.md** - Detailed performance benchmarks and optimization decisions
- **docs/architecture.md** - Complete system architecture and Epic roadmap

### Changed

- **Project handling** - Legacy project strings now create/reference proper project records
- **Database location** - Defaults to `~/.local/share/todo-cli/todos.db` (XDG Base Directory compliant)
- **Performance** - All common queries optimized with database indexing

### Fixed

- **Project filtering** - Now uses proper foreign key relationships instead of string matching
- **Query performance** - Eliminated full table scans with strategic indexing
- **Case sensitivity** - Project name matching is now case-insensitive

### Migration Notes

**⚠️ Important for existing users:**

- **Automatic migration** on first run (creates backup automatically)
- **Backward compatible** - All existing commands continue to work
- **Data preservation** - All task data, tags, dates, time tracking fully preserved
- **Legacy support** - Old project strings still work (creates projects as needed)
- See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for complete migration documentation

**Migration time:**
- Small databases (<100 tasks): <1 second
- Medium databases (100-1000 tasks): 1-2 seconds
- Large databases (1000+ tasks): 2-5 seconds

### Technical Details

**Database Schema Version:** v1 (from v0)

**New Dependencies:** None (all existing dependencies maintained)

**Python Version Support:**
- Minimum: Python 3.10
- Tested: Python 3.10, 3.11, 3.12, 3.13
- Recommended: Python 3.13

**Performance Targets (All Met):**
- ✅ List all tasks: <100ms (actual: ~10ms)
- ✅ Filter by project: <100ms (actual: ~0.23ms)
- ✅ Project statistics: <200ms (actual: ~0.43ms)

**Test Coverage:**
- Lines: 87% (target: 80%)
- Branches: 85%
- Total tests: 313
- Test execution time: <30 seconds (excluding performance benchmarks)

### Known Issues

None at this time. Please report any issues at: https://github.com/AgileInnov8tor/todo-cli/issues

### Deprecations

The following patterns are deprecated but still functional (will be removed in v2.0.0):

- **Legacy project strings** in `todos.project` field (use `todos.project_id` instead)
  - CLI automatically handles this - no user action required
  - Internal APIs should use ProjectManager and foreign keys

### Security

No security issues identified or fixed in this release.

### Contributors

- Core development and Epic 1 implementation
- Testing framework and CI/CD setup
- Documentation and migration guide

---

## [1.0.0] - 2025-12-01

### Initial Release

- Basic task management (add, list, show, done, delete)
- Time tracking (start, stop, active)
- Priority levels (p0-p3)
- Tags support
- Due dates
- Status management (todo/doing/done)
- Interactive mode (TUI)
- Reports (daily, weekly, project)
- Export (JSON, CSV, Markdown)
- Configuration system
- SQLite database storage

---

## Release Naming Convention

- **Major.Minor.Patch** - Stable releases (e.g., 1.1.0)
- **Major.Minor.PatchaN** - Alpha releases (e.g., 1.1.0a1)
- **Major.Minor.PatchbN** - Beta releases (e.g., 1.1.0b1)
- **Major.Minor.PatchrcN** - Release candidates (e.g., 1.1.0rc1)

## Versioning Strategy

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backward compatible manner
- **PATCH** version for backward compatible bug fixes

Pre-release versions:
- **Alpha (aN)** - Early testing, features may be incomplete
- **Beta (bN)** - Feature complete, testing for stability
- **Release Candidate (rcN)** - Final testing before stable release

## Links

- [Repository](https://github.com/AgileInnov8tor/todo-cli)
- [Issues](https://github.com/AgileInnov8tor/todo-cli/issues)
- [Discussions](https://github.com/AgileInnov8tor/todo-cli/discussions)
- [Documentation](https://github.com/AgileInnov8tor/todo-cli/tree/main/docs)

---

[1.1.0a1]: https://github.com/AgileInnov8tor/todo-cli/releases/tag/v1.1.0a1
[1.0.0]: https://github.com/AgileInnov8tor/todo-cli/releases/tag/v1.0.0
