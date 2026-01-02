# 🎉 Todo CLI v1.1.0a1 - Epic 1: Foundation (Alpha Release) Now Available!

Hi everyone! 👋

I'm excited to announce the first alpha release of **Todo CLI v1.1.0a1**, completing **Epic 1: Foundation**!

This release introduces **project management**, **database schema v1**, and **comprehensive performance optimizations** to the Todo CLI.

---

## 🚀 What's New

### Project Management System

You can now organize your tasks with proper project management:

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

---

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

---

## 📊 Testing & Quality

This release comes with comprehensive testing:

- **313 tests** with **87% code coverage**
- Performance regression tests prevent slowdowns
- Multi-version Python support (3.10, 3.11, 3.12, 3.13)
- CI/CD with GitHub Actions

---

## 🔄 Migration Notes

**For existing users:**

Migration is:
- ✅ Fully automatic
- ✅ Backward compatible
- ✅ Safe (creates backups)
- ✅ Fast (<5 seconds)
- ✅ Idempotent (safe to re-run)

Your existing tasks, tags, dates, and time tracking are fully preserved.

---

## 📚 Documentation

- **[MIGRATION_GUIDE.md](https://github.com/AgileInnov8tor/todo-cli/blob/main/MIGRATION_GUIDE.md)** - Complete migration documentation
- **[CHANGELOG.md](https://github.com/AgileInnov8tor/todo-cli/blob/main/CHANGELOG.md)** - Detailed release notes
- **[README.md](https://github.com/AgileInnov8tor/todo-cli/blob/main/README.md)** - Updated with Epic 1 features
- **[Release Notes](https://github.com/AgileInnov8tor/todo-cli/releases/tag/v1.1.0a1)** - Full release information

---

## 🐛 Known Issues

None at this time. Please report any issues at: https://github.com/AgileInnov8tor/todo-cli/issues

---

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

---

## 💬 Feedback

**This is an alpha release!** I'd love to hear your feedback:

- **Report bugs:** https://github.com/AgileInnov8tor/todo-cli/issues/new?labels=bug,epic-1
- **Request features:** https://github.com/AgileInnov8tor/todo-cli/issues/new?labels=enhancement
- **Ask questions:** https://github.com/AgileInnov8tor/todo-cli/discussions/new?category=q-a
- **Share your experience:** https://github.com/AgileInnov8tor/todo-cli/discussions/new?category=show-and-tell

Your feedback helps shape the future of Todo CLI!

---

## ⚠️ Alpha Release Note

This is an **alpha release** intended for early testing and feedback. Features are stable but may evolve based on user feedback. Please test thoroughly before using in production workflows.

---

## 🙏 Thank You

Thank you to everyone who has contributed feedback, bug reports, and feature requests. Your input has been invaluable in shaping Epic 1!

If you find this tool useful, please:
- ⭐ Star the repository on GitHub
- 📢 Share with others who might benefit
- 💬 Join the discussions and share your workflows

---

## 📋 Quick Reference

**Installation:**
```bash
pip install agile-todo-cli==1.1.0a1
```

**Verify installation:**
```bash
todo version  # Should show: Todo CLI v1.1.0a1
```

**Get started:**
```bash
todo project create "My First Project"
todo add "First task" -P "My First Project"
todo list --project "My First Project"
```

---

**Questions?** Ask in the [Q&A Discussions](https://github.com/AgileInnov8tor/todo-cli/discussions/new?category=q-a)

**Found a bug?** [Report it here](https://github.com/AgileInnov8tor/todo-cli/issues/new?labels=bug,epic-1)

**Happy task management!** 🚀
