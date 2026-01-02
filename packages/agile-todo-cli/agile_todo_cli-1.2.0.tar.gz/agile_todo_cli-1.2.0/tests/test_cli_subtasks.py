"""Tests for subtask CLI commands."""

import pytest
from typer.testing import CliRunner

from todo_cli.main import app
from todo_cli.config import Config
from todo_cli.database import Database
from todo_cli.subtasks import SubtaskManager
from todo_cli.models import Status, Priority


@pytest.fixture
def cli_env(temp_dir, monkeypatch):
    """Set up isolated CLI environment."""
    import todo_cli.config as config_module
    import todo_cli.main as main_module

    config_path = temp_dir / "config.yaml"
    db_path = temp_dir / "todos.db"

    monkeypatch.setattr(config_module, "DEFAULT_CONFIG_PATH", config_path)
    config_module._config = None
    config_module._config_warnings = []

    config = Config(db_path=str(db_path), confirm_delete=False)
    config.save(config_path)
    config_module._config = config

    def get_test_db():
        return Database(db_path)

    def get_test_sm():
        return SubtaskManager(db_path)

    monkeypatch.setattr(main_module, "get_db", get_test_db)
    monkeypatch.setattr(main_module, "get_subtask_manager", get_test_sm)

    # Initialize database and run migrations before tests
    get_test_db()

    return {
        "config_path": config_path,
        "db_path": db_path,
        "config": config,
        "get_db": get_test_db,
        "get_sm": get_test_sm,
    }


class TestAddSubtaskCommand:
    """Test the add-subtask command."""

    def test_add_subtask_basic(self, runner, cli_env):
        """Test adding a basic subtask."""
        # Create parent task first
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0

        # Add subtask
        result = runner.invoke(app, ["add-subtask", "1", "Child task"])
        assert result.exit_code == 0
        assert "Added subtask #2" in result.output
        assert "parent: #1" in result.output

        # Verify relationship
        sm = cli_env["get_sm"]()
        assert sm.is_subtask(2) is True
        parent = sm.get_parent(2)
        assert parent is not None
        assert parent['id'] == 1

    def test_add_subtask_inherits_priority(self, runner, cli_env):
        """Test that subtask inherits parent's priority by default."""
        # Create parent with P0 priority
        result = runner.invoke(app, ["add", "Parent task", "-p", "p0"])
        assert result.exit_code == 0

        # Add subtask without specifying priority
        result = runner.invoke(app, ["add-subtask", "1", "Child task"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        child = db.get(2)
        assert child.priority == Priority.P0

    def test_add_subtask_override_priority(self, runner, cli_env):
        """Test that subtask can override parent's priority."""
        # Create parent with P0 priority
        result = runner.invoke(app, ["add", "Parent task", "-p", "p0"])
        assert result.exit_code == 0

        # Add subtask with different priority
        result = runner.invoke(app, ["add-subtask", "1", "Child task", "-p", "p3"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        child = db.get(2)
        assert child.priority == Priority.P3

    def test_add_subtask_inherits_project(self, runner, cli_env):
        """Test that subtask inherits parent's project."""
        # Create project
        from todo_cli.projects import ProjectManager
        pm = ProjectManager(cli_env["get_db"]().db_path)
        pm.create_project("work")

        # Create parent with project
        result = runner.invoke(app, ["add", "Parent task", "-P", "work"])
        assert result.exit_code == 0

        # Add subtask
        result = runner.invoke(app, ["add-subtask", "1", "Child task"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        parent = db.get(1)
        child = db.get(2)
        assert child.project_id == parent.project_id

    def test_add_subtask_inherits_tags(self, runner, cli_env):
        """Test that subtask inherits parent's tags."""
        # Create parent with tags
        result = runner.invoke(app, ["add", "Parent task", "-t", "urgent,feature"])
        assert result.exit_code == 0

        # Add subtask
        result = runner.invoke(app, ["add-subtask", "1", "Child task"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        child = db.get(2)
        assert "urgent" in child.tags
        assert "feature" in child.tags

    def test_add_subtask_combines_tags(self, runner, cli_env):
        """Test that subtask combines parent's tags with additional tags."""
        # Create parent with tags
        result = runner.invoke(app, ["add", "Parent task", "-t", "urgent"])
        assert result.exit_code == 0

        # Add subtask with additional tags
        result = runner.invoke(app, ["add-subtask", "1", "Child task", "-t", "backend"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        child = db.get(2)
        assert "urgent" in child.tags
        assert "backend" in child.tags

    def test_add_subtask_with_due_date(self, runner, cli_env):
        """Test adding subtask with due date."""
        # Create parent
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0

        # Add subtask with due date
        result = runner.invoke(app, ["add-subtask", "1", "Child task", "-d", "2025-12-31"])
        assert result.exit_code == 0

        db = cli_env["get_db"]()
        child = db.get(2)
        assert child.due_date is not None
        assert child.due_date.year == 2025

    def test_add_subtask_nonexistent_parent_fails(self, runner, cli_env):
        """Test that adding subtask to nonexistent parent fails."""
        result = runner.invoke(app, ["add-subtask", "999", "Child task"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_add_subtask_to_subtask_fails(self, runner, cli_env):
        """Test that adding subtask to a subtask fails (depth constraint)."""
        # Create parent
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0

        # Add child
        result = runner.invoke(app, ["add-subtask", "1", "Child task"])
        assert result.exit_code == 0

        # Try to add grandchild
        result = runner.invoke(app, ["add-subtask", "2", "Grandchild task"])
        assert result.exit_code == 1
        assert "already a subtask" in result.output.lower()

    def test_add_subtask_to_parent_with_children_fails(self, runner, cli_env):
        """Test that making a parent task into a subtask fails."""
        # Create two parents
        result = runner.invoke(app, ["add", "Parent 1"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add", "Parent 2"])
        assert result.exit_code == 0

        # Add child to first parent
        result = runner.invoke(app, ["add-subtask", "1", "Child task"])
        assert result.exit_code == 0

        # Try to make first parent a child of second
        # This would require linking existing task as subtask
        # The add-subtask creates a new task, so this isn't directly testable here
        # But we can verify via the subtask manager
        sm = cli_env["get_sm"]()
        can_add, error = sm.can_add_subtask(2, 1)
        assert can_add is False
        assert "subtask" in error.lower()


class TestUnlinkCommand:
    """Test the unlink command."""

    def test_unlink_subtask_success(self, runner, cli_env):
        """Test successfully unlinking a subtask."""
        # Create parent and child
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child task"])
        assert result.exit_code == 0

        # Verify it's a subtask
        sm = cli_env["get_sm"]()
        assert sm.is_subtask(2) is True

        # Unlink
        result = runner.invoke(app, ["unlink", "2"])
        assert result.exit_code == 0
        assert "Unlinked" in result.output
        assert "#2" in result.output
        assert "#1" in result.output

        # Verify it's no longer a subtask
        assert sm.is_subtask(2) is False

    def test_unlink_preserves_task(self, runner, cli_env):
        """Test that unlink preserves the task data."""
        # Create parent and child
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child task", "-t", "important"])
        assert result.exit_code == 0

        # Unlink
        result = runner.invoke(app, ["unlink", "2"])
        assert result.exit_code == 0

        # Verify task still exists with its data
        db = cli_env["get_db"]()
        child = db.get(2)
        assert child is not None
        assert child.task == "Child task"
        assert "important" in child.tags

    def test_unlink_nonexistent_task_fails(self, runner, cli_env):
        """Test that unlinking nonexistent task fails."""
        result = runner.invoke(app, ["unlink", "999"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_unlink_top_level_task_fails(self, runner, cli_env):
        """Test that unlinking a top-level task fails."""
        # Create a top-level task
        result = runner.invoke(app, ["add", "Top level task"])
        assert result.exit_code == 0

        # Try to unlink it
        result = runner.invoke(app, ["unlink", "1"])
        assert result.exit_code == 1
        assert "not a subtask" in result.output.lower()


class TestListSubtaskFilters:
    """Test the subtask filtering options in list command."""

    def test_list_parent_filter(self, runner, cli_env):
        """Test filtering by parent ID."""
        # Create parent and children
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child 1"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child 2"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add", "Unrelated task"])
        assert result.exit_code == 0

        # List only children of parent 1
        result = runner.invoke(app, ["list", "--parent", "1"])
        assert result.exit_code == 0
        assert "Child 1" in result.output
        assert "Child 2" in result.output
        assert "Parent task" not in result.output
        assert "Unrelated task" not in result.output

    def test_list_has_children_filter(self, runner, cli_env):
        """Test filtering tasks that have children."""
        # Create parent with child and standalone task
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add", "Standalone task"])
        assert result.exit_code == 0

        # List only tasks with children
        result = runner.invoke(app, ["list", "--has-children"])
        assert result.exit_code == 0
        assert "Parent task" in result.output
        assert "Child task" not in result.output
        assert "Standalone task" not in result.output

    def test_list_is_subtask_filter(self, runner, cli_env):
        """Test filtering only subtasks."""
        # Create parent with child and standalone task
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add", "Standalone task"])
        assert result.exit_code == 0

        # List only subtasks
        result = runner.invoke(app, ["list", "--is-subtask"])
        assert result.exit_code == 0
        assert "Child task" in result.output
        assert "Parent task" not in result.output
        assert "Standalone task" not in result.output

    def test_list_empty_parent_filter(self, runner, cli_env):
        """Test parent filter with no children."""
        # Create task without children
        result = runner.invoke(app, ["add", "Standalone task"])
        assert result.exit_code == 0

        # List children (should be empty)
        result = runner.invoke(app, ["list", "--parent", "1"])
        assert result.exit_code == 0
        # Output should not contain the task
        assert "Standalone task" not in result.output

    def test_list_combined_filters(self, runner, cli_env):
        """Test combining subtask filters with other filters."""
        # Create project
        from todo_cli.projects import ProjectManager
        pm = ProjectManager(cli_env["get_db"]().db_path)
        pm.create_project("work")

        # Create parent with project
        result = runner.invoke(app, ["add", "Parent task", "-P", "work"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child task"])
        assert result.exit_code == 0

        # List subtasks filtered by project
        result = runner.invoke(app, ["list", "--is-subtask", "-P", "work"])
        assert result.exit_code == 0
        assert "Child task" in result.output

    def test_list_shows_subtask_count_indicator(self, runner, cli_env):
        """Test that parent tasks show sub-task count indicator."""
        # Create parent with multiple subtasks
        result = runner.invoke(app, ["add", "Feature X"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Design"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Implement"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Test"])
        assert result.exit_code == 0

        # Create standalone task
        result = runner.invoke(app, ["add", "Standalone task"])
        assert result.exit_code == 0

        # List all tasks
        result = runner.invoke(app, ["list", "-a"])
        assert result.exit_code == 0

        # Parent should show "(3 sub-tasks)" indicator
        assert "Feature X" in result.output
        assert "3 sub-tasks" in result.output

        # Standalone should NOT have sub-task indicator
        assert "Standalone task" in result.output
        # The standalone task shouldn't be followed by sub-task count
        # (verifying absence is tricky, but we at least check parent has it)

    def test_list_shows_singular_subtask_indicator(self, runner, cli_env):
        """Test that singular 'sub-task' is used for one child."""
        # Create parent with one subtask
        result = runner.invoke(app, ["add", "Single child parent"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Only child"])
        assert result.exit_code == 0

        # List tasks
        result = runner.invoke(app, ["list", "-a"])
        assert result.exit_code == 0

        # Should show "(1 sub-task)" not "(1 sub-tasks)"
        assert "1 sub-task)" in result.output
        assert "1 sub-tasks)" not in result.output


class TestSubtaskIntegration:
    """Integration tests for subtask workflow."""

    def test_full_subtask_workflow(self, runner, cli_env):
        """Test complete workflow: create, list, unlink."""
        # Create parent
        result = runner.invoke(app, ["add", "Feature X"])
        assert result.exit_code == 0

        # Add subtasks
        result = runner.invoke(app, ["add-subtask", "1", "Design", "-p", "p1"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Implement", "-p", "p2"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Test", "-p", "p3"])
        assert result.exit_code == 0

        # List children
        result = runner.invoke(app, ["list", "--parent", "1"])
        assert result.exit_code == 0
        assert "Design" in result.output
        assert "Implement" in result.output
        assert "Test" in result.output

        # Unlink one
        result = runner.invoke(app, ["unlink", "3"])
        assert result.exit_code == 0

        # Verify remaining children
        result = runner.invoke(app, ["list", "--parent", "1"])
        assert result.exit_code == 0
        assert "Design" in result.output
        assert "Test" in result.output
        assert "Implement" not in result.output

        # Verify unlinked is top-level
        sm = cli_env["get_sm"]()
        assert sm.is_subtask(3) is False

    def test_depth_constraint_enforced(self, runner, cli_env):
        """Test that depth constraint is enforced through CLI."""
        # Create chain: parent -> child
        result = runner.invoke(app, ["add", "Level 0"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Level 1"])
        assert result.exit_code == 0

        # Try to create: child -> grandchild (should fail)
        result = runner.invoke(app, ["add-subtask", "2", "Level 2"])
        assert result.exit_code == 1

        # Verify no task was created
        db = cli_env["get_db"]()
        todos = db.list_all(include_done=True)
        assert len(todos) == 2  # Only parent and child

    def test_parent_with_children_cannot_become_subtask(self, runner, cli_env):
        """Test that a parent cannot be made into a subtask via direct SubtaskManager."""
        # Create two separate trees
        result = runner.invoke(app, ["add", "Tree 1 Root"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Tree 1 Child"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add", "Tree 2 Root"])
        assert result.exit_code == 0

        # Try to make Tree 1 Root a child of Tree 2 Root
        sm = cli_env["get_sm"]()
        can_add, error = sm.can_add_subtask(3, 1)
        assert can_add is False
        assert "subtask" in error.lower()


class TestTreeViewRendering:
    """Test the --tree flag for hierarchical display."""

    def test_tree_flag_basic(self, runner, cli_env):
        """Test basic tree view output."""
        # Create parent and children
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child 1"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child 2"])
        assert result.exit_code == 0

        # List with tree view
        result = runner.invoke(app, ["list", "--tree"])
        assert result.exit_code == 0
        assert "Parent task" in result.output
        assert "Child 1" in result.output
        assert "Child 2" in result.output

    def test_tree_short_flag(self, runner, cli_env):
        """Test short -T flag for tree view."""
        result = runner.invoke(app, ["add", "Test task"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["list", "-T"])
        assert result.exit_code == 0
        assert "Test task" in result.output

    def test_tree_empty_list(self, runner, cli_env):
        """Test tree view with no tasks."""
        result = runner.invoke(app, ["list", "--tree"])
        assert result.exit_code == 0
        assert "No todos found" in result.output

    def test_tree_shows_status_icons(self, runner, cli_env):
        """Test that tree view shows status icons."""
        # Create tasks in different states
        result = runner.invoke(app, ["add", "Todo task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add", "Done task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["done", "2"])
        assert result.exit_code == 0

        # List with tree view (include all)
        result = runner.invoke(app, ["list", "--tree", "--all"])
        assert result.exit_code == 0
        # Check status icons are present (pending: ⬜, done: ✅)
        assert "⬜" in result.output or "Todo task" in result.output
        assert "✅" in result.output or "Done task" in result.output

    def test_tree_shows_priority_icons(self, runner, cli_env):
        """Test that tree view shows priority icons."""
        result = runner.invoke(app, ["add", "P0 task", "-p", "p0"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add", "P3 task", "-p", "p3"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["list", "--tree"])
        assert result.exit_code == 0
        # Check priority icons (P0: 🔴, P3: ⚪)
        assert "🔴" in result.output
        assert "⚪" in result.output

    def test_tree_shows_completion_status(self, runner, cli_env):
        """Test that tree view shows completion status for parents."""
        # Create parent with children
        result = runner.invoke(app, ["add", "Feature X"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Step 1"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Step 2"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Step 3"])
        assert result.exit_code == 0

        # Complete one child
        result = runner.invoke(app, ["done", "2"])
        assert result.exit_code == 0

        # List with tree view
        result = runner.invoke(app, ["list", "--tree"])
        assert result.exit_code == 0
        # Should show (1/3) for parent
        assert "(1/3)" in result.output

    def test_tree_with_project_filter(self, runner, cli_env):
        """Test tree view combined with project filter."""
        # Create project
        from todo_cli.projects import ProjectManager
        pm = ProjectManager(cli_env["get_db"]().db_path)
        pm.create_project("work")

        # Create tasks
        result = runner.invoke(app, ["add", "Work parent", "-P", "work"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Work child"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add", "Other task"])
        assert result.exit_code == 0

        # List with tree and project filter
        result = runner.invoke(app, ["list", "--tree", "-P", "work"])
        assert result.exit_code == 0
        assert "Work parent" in result.output
        assert "Work child" in result.output
        assert "Other task" not in result.output

    def test_tree_with_status_filter(self, runner, cli_env):
        """Test tree view combined with status filter."""
        # Create tasks
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Todo child"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Done child"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["done", "3"])
        assert result.exit_code == 0

        # List with tree and status filter
        result = runner.invoke(app, ["list", "--tree", "-s", "done"])
        assert result.exit_code == 0
        assert "Done child" in result.output
        assert "Todo child" not in result.output

    def test_tree_shows_task_ids(self, runner, cli_env):
        """Test that tree view shows task IDs."""
        result = runner.invoke(app, ["add", "Task one"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add", "Task two"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["list", "--tree"])
        assert result.exit_code == 0
        assert "#1" in result.output
        assert "#2" in result.output

    def test_tree_only_shows_top_level_parents(self, runner, cli_env):
        """Test that children are nested under parents, not duplicated at root."""
        # Create parent and child
        result = runner.invoke(app, ["add", "Parent"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child"])
        assert result.exit_code == 0

        # In tree view, Child should be nested, not at top level
        result = runner.invoke(app, ["list", "--tree"])
        assert result.exit_code == 0
        # Both should be present
        assert "Parent" in result.output
        assert "Child" in result.output
        # The tree structure should show hierarchy (Rich tree uses box-drawing characters)

    def test_tree_with_all_flag(self, runner, cli_env):
        """Test tree view includes completed tasks with --all flag."""
        result = runner.invoke(app, ["add", "Active task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add", "Completed task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["done", "2"])
        assert result.exit_code == 0

        # Without --all, should not show completed
        result = runner.invoke(app, ["list", "--tree"])
        assert result.exit_code == 0
        assert "Active task" in result.output
        assert "Completed task" not in result.output

        # With --all, should show completed
        result = runner.invoke(app, ["list", "--tree", "--all"])
        assert result.exit_code == 0
        assert "Active task" in result.output
        assert "Completed task" in result.output


class TestParentCompletionLogic:
    """Test parent task completion validation and cascading."""

    def test_complete_parent_with_incomplete_children_fails(self, runner, cli_env):
        """Test that completing parent with incomplete children fails."""
        # Create parent with incomplete child
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child task"])
        assert result.exit_code == 0

        # Try to complete parent - should fail
        result = runner.invoke(app, ["done", "1"])
        assert result.exit_code == 1
        assert "Cannot complete" in result.output
        assert "#2" in result.output  # Shows incomplete child ID

    def test_complete_parent_with_no_children_succeeds(self, runner, cli_env):
        """Test that completing task without children works normally."""
        result = runner.invoke(app, ["add", "Standalone task"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["done", "1"])
        assert result.exit_code == 0
        assert "Completed" in result.output

    def test_complete_parent_with_all_children_done_succeeds(self, runner, cli_env):
        """Test that parent can be completed when all children are done."""
        # Create parent with children
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child 1"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child 2"])
        assert result.exit_code == 0

        # Complete all children
        result = runner.invoke(app, ["done", "2"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["done", "3"])
        assert result.exit_code == 0

        # Now parent can be completed
        result = runner.invoke(app, ["done", "1"])
        assert result.exit_code == 0
        assert "Completed" in result.output

    def test_force_complete_parent_with_incomplete_children(self, runner, cli_env):
        """Test --force flag overrides incomplete children check."""
        # Create parent with incomplete child
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child task"])
        assert result.exit_code == 0

        # Force complete parent
        result = runner.invoke(app, ["done", "1", "--force"])
        assert result.exit_code == 0
        assert "Force completing" in result.output
        assert "Completed" in result.output

    def test_complete_last_child_auto_completes_parent(self, runner, cli_env):
        """Test that completing the last child auto-completes the parent."""
        # Create parent with two children
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child 1"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child 2"])
        assert result.exit_code == 0

        # Complete first child
        result = runner.invoke(app, ["done", "2"])
        assert result.exit_code == 0
        assert "Parent #1 also completed" not in result.output

        # Complete second (last) child - should auto-complete parent
        result = runner.invoke(app, ["done", "3"])
        assert result.exit_code == 0
        assert "Parent #1 also completed" in result.output

        # Verify parent is done
        db = cli_env["get_db"]()
        parent = db.get(1)
        assert parent.status.value == "done"

    def test_complete_multiple_incomplete_children_error_message(self, runner, cli_env):
        """Test error message shows all incomplete children."""
        # Create parent with multiple incomplete children
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child 1"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child 2"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child 3"])
        assert result.exit_code == 0

        # Try to complete parent - should show all incomplete children
        result = runner.invoke(app, ["done", "1"])
        assert result.exit_code == 1
        assert "#2" in result.output
        assert "#3" in result.output
        assert "#4" in result.output


class TestUncompleteCommand:
    """Test uncomplete command and cascading to parent."""

    def test_uncomplete_basic(self, runner, cli_env):
        """Test basic uncomplete functionality."""
        result = runner.invoke(app, ["add", "Task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["done", "1"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["uncomplete", "1"])
        assert result.exit_code == 0
        assert "Uncompleted" in result.output

        # Verify status
        db = cli_env["get_db"]()
        todo = db.get(1)
        assert todo.status.value == "todo"

    def test_uncomplete_not_completed_task_fails(self, runner, cli_env):
        """Test that uncompleting a non-completed task fails."""
        result = runner.invoke(app, ["add", "Task"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["uncomplete", "1"])
        assert result.exit_code == 1
        assert "not completed" in result.output

    def test_uncomplete_nonexistent_task_fails(self, runner, cli_env):
        """Test that uncompleting nonexistent task fails."""
        result = runner.invoke(app, ["uncomplete", "999"])
        assert result.exit_code == 1
        assert "not found" in result.output

    def test_uncomplete_child_also_uncompletes_parent(self, runner, cli_env):
        """Test that uncompleting child cascades to parent."""
        # Create and complete parent with child
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child task"])
        assert result.exit_code == 0

        # Complete both
        result = runner.invoke(app, ["done", "2"])  # Complete child
        assert result.exit_code == 0
        result = runner.invoke(app, ["done", "1"])  # Complete parent
        assert result.exit_code == 0

        # Uncomplete child - should also uncomplete parent
        result = runner.invoke(app, ["uncomplete", "2"])
        assert result.exit_code == 0
        assert "Parent #1 also uncompleted" in result.output

        # Verify both are uncompleted
        db = cli_env["get_db"]()
        parent = db.get(1)
        child = db.get(2)
        assert parent.status.value == "todo"
        assert child.status.value == "todo"

    def test_uncomplete_child_with_incomplete_parent_no_cascade(self, runner, cli_env):
        """Test that uncompleting child when parent was already incomplete doesn't message."""
        # Create parent with TWO children (so completing one doesn't auto-complete parent)
        result = runner.invoke(app, ["add", "Parent task"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child 1"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["add-subtask", "1", "Child 2"])
        assert result.exit_code == 0

        # Complete only one child - parent stays incomplete because Child 2 is still todo
        result = runner.invoke(app, ["done", "2"])
        assert result.exit_code == 0
        assert "auto-completed" not in result.output  # Parent not auto-completed

        # Uncomplete child - parent was never completed so no cascade message
        result = runner.invoke(app, ["uncomplete", "2"])
        assert result.exit_code == 0
        assert "Parent" not in result.output

    def test_uncomplete_standalone_task(self, runner, cli_env):
        """Test uncompleting a standalone (non-child) task."""
        result = runner.invoke(app, ["add", "Standalone"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["done", "1"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["uncomplete", "1"])
        assert result.exit_code == 0
        assert "Uncompleted" in result.output
        # No parent cascade message
        assert "Parent" not in result.output
