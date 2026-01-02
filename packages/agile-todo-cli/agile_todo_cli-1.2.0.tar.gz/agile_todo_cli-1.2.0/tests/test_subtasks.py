"""Tests for subtask management (parent-child relationships)."""

import pytest
import tempfile
from pathlib import Path

from todo_cli.subtasks import SubtaskManager
from todo_cli.database import Database
from todo_cli.models import Priority


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    # Initialize database with migrations
    db = Database(db_path)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def db(temp_db):
    """Create a Database instance."""
    return Database(temp_db)


@pytest.fixture
def sm(temp_db):
    """Create a SubtaskManager instance."""
    return SubtaskManager(temp_db)


@pytest.fixture
def parent_task(db):
    """Create a parent task for testing."""
    return db.add(task="Parent task", priority=Priority.P1)


@pytest.fixture
def child_task(db):
    """Create a potential child task for testing."""
    return db.add(task="Child task", priority=Priority.P2)


@pytest.fixture
def multiple_tasks(db):
    """Create multiple tasks for testing hierarchies."""
    tasks = [
        db.add(task=f"Task {i}", priority=Priority.P2)
        for i in range(5)
    ]
    return tasks


class TestAddSubtask:
    """Test adding subtasks."""

    def test_add_subtask_success(self, sm, parent_task, child_task):
        """Test successfully adding a subtask."""
        success, message = sm.add_subtask(parent_task.id, child_task.id)

        assert success is True
        assert f"#{child_task.id}" in message
        assert f"#{parent_task.id}" in message

    def test_add_subtask_creates_relationship(self, sm, parent_task, child_task):
        """Test that adding subtask creates correct relationship."""
        sm.add_subtask(parent_task.id, child_task.id)

        children = sm.get_children(parent_task.id)
        assert len(children) == 1
        assert children[0]['id'] == child_task.id

    def test_add_multiple_subtasks(self, sm, db, parent_task):
        """Test adding multiple subtasks to same parent."""
        child1 = db.add(task="Child 1", priority=Priority.P2)
        child2 = db.add(task="Child 2", priority=Priority.P2)
        child3 = db.add(task="Child 3", priority=Priority.P2)

        sm.add_subtask(parent_task.id, child1.id)
        sm.add_subtask(parent_task.id, child2.id)
        sm.add_subtask(parent_task.id, child3.id)

        children = sm.get_children(parent_task.id)
        assert len(children) == 3


class TestValidation:
    """Test validation rules for subtasks."""

    def test_self_reference_prevented(self, sm, parent_task):
        """Test that a task cannot be its own subtask."""
        can_add, error = sm.can_add_subtask(parent_task.id, parent_task.id)

        assert can_add is False
        assert "own subtask" in error.lower()

    def test_self_reference_add_fails(self, sm, parent_task):
        """Test that adding self-reference fails."""
        success, error = sm.add_subtask(parent_task.id, parent_task.id)

        assert success is False
        assert "own subtask" in error.lower()

    def test_nonexistent_parent_fails(self, sm, child_task):
        """Test that adding to nonexistent parent fails."""
        can_add, error = sm.can_add_subtask(99999, child_task.id)

        assert can_add is False
        assert "not found" in error.lower()

    def test_nonexistent_child_fails(self, sm, parent_task):
        """Test that adding nonexistent child fails."""
        can_add, error = sm.can_add_subtask(parent_task.id, 99999)

        assert can_add is False
        assert "not found" in error.lower()

    def test_duplicate_relationship_fails(self, sm, parent_task, child_task):
        """Test that duplicate relationship fails."""
        sm.add_subtask(parent_task.id, child_task.id)

        can_add, error = sm.can_add_subtask(parent_task.id, child_task.id)

        assert can_add is False
        assert "already a subtask" in error.lower()


class TestDepthConstraint:
    """Test depth constraint (max 1 level)."""

    def test_cannot_add_subtask_to_subtask(self, sm, db, parent_task, child_task):
        """Test that a subtask cannot have children (depth = 1 max)."""
        grandchild = db.add(task="Grandchild", priority=Priority.P3)

        # Make child a subtask
        sm.add_subtask(parent_task.id, child_task.id)

        # Try to add grandchild to child
        can_add, error = sm.can_add_subtask(child_task.id, grandchild.id)

        assert can_add is False
        assert "already a subtask" in error.lower()
        assert "max depth" in error.lower()

    def test_cannot_make_parent_into_subtask(self, sm, db, parent_task, child_task):
        """Test that a task with children cannot become a subtask."""
        grandparent = db.add(task="Grandparent", priority=Priority.P0)

        # Make child a subtask of parent
        sm.add_subtask(parent_task.id, child_task.id)

        # Try to make parent a subtask of grandparent
        can_add, error = sm.can_add_subtask(grandparent.id, parent_task.id)

        assert can_add is False
        assert "has" in error.lower() and "subtask" in error.lower()

    def test_subtask_cannot_have_multiple_parents(self, sm, db, child_task):
        """Test that a task can only have one parent."""
        parent1 = db.add(task="Parent 1", priority=Priority.P1)
        parent2 = db.add(task="Parent 2", priority=Priority.P1)

        sm.add_subtask(parent1.id, child_task.id)

        can_add, error = sm.can_add_subtask(parent2.id, child_task.id)

        assert can_add is False
        assert "already a subtask" in error.lower()


class TestQueryMethods:
    """Test query methods."""

    def test_get_children_returns_list(self, sm, db, parent_task):
        """Test that children are returned as a list."""
        children = [
            db.add(task=f"Child {i}", priority=Priority.P2)
            for i in range(3)
        ]

        for child in children:
            sm.add_subtask(parent_task.id, child.id)

        result = sm.get_children(parent_task.id)

        assert len(result) == 3
        child_ids = {c['id'] for c in result}
        assert child_ids == {c.id for c in children}

    def test_get_children_empty_list(self, sm, parent_task):
        """Test getting children of task with no children."""
        children = sm.get_children(parent_task.id)

        assert children == []

    def test_get_parent_returns_parent_task(self, sm, parent_task, child_task):
        """Test getting parent of a subtask."""
        sm.add_subtask(parent_task.id, child_task.id)

        parent = sm.get_parent(child_task.id)

        assert parent is not None
        assert parent['id'] == parent_task.id

    def test_get_parent_returns_none_for_top_level(self, sm, parent_task):
        """Test that top-level tasks have no parent."""
        parent = sm.get_parent(parent_task.id)

        assert parent is None

    def test_is_subtask_true(self, sm, parent_task, child_task):
        """Test is_subtask returns True for subtasks."""
        sm.add_subtask(parent_task.id, child_task.id)

        assert sm.is_subtask(child_task.id) is True

    def test_is_subtask_false(self, sm, parent_task):
        """Test is_subtask returns False for top-level tasks."""
        assert sm.is_subtask(parent_task.id) is False

    def test_has_children_true(self, sm, parent_task, child_task):
        """Test has_children returns True for parents."""
        sm.add_subtask(parent_task.id, child_task.id)

        assert sm.has_children(parent_task.id) is True

    def test_has_children_false(self, sm, parent_task):
        """Test has_children returns False for tasks without children."""
        assert sm.has_children(parent_task.id) is False

    def test_get_child_count(self, sm, db, parent_task):
        """Test getting child count."""
        assert sm.get_child_count(parent_task.id) == 0

        children = [db.add(task=f"Child {i}", priority=Priority.P2) for i in range(3)]
        for child in children:
            sm.add_subtask(parent_task.id, child.id)

        assert sm.get_child_count(parent_task.id) == 3


class TestRemoveSubtask:
    """Test removing subtasks."""

    def test_remove_subtask_success(self, sm, parent_task, child_task):
        """Test successfully removing a subtask."""
        sm.add_subtask(parent_task.id, child_task.id)

        success, message = sm.remove_subtask(parent_task.id, child_task.id)

        assert success is True
        assert "unlinked" in message.lower()

    def test_remove_subtask_makes_top_level(self, sm, parent_task, child_task):
        """Test that removed subtask becomes top-level."""
        sm.add_subtask(parent_task.id, child_task.id)
        sm.remove_subtask(parent_task.id, child_task.id)

        assert sm.is_subtask(child_task.id) is False
        assert sm.get_parent(child_task.id) is None

    def test_remove_nonexistent_relationship_fails(self, sm, parent_task, child_task):
        """Test removing nonexistent relationship fails."""
        success, error = sm.remove_subtask(parent_task.id, child_task.id)

        assert success is False
        assert "not a subtask" in error.lower()


class TestCascadeDelete:
    """Test cascade delete behavior."""

    def test_delete_child_removes_relationship(self, sm, db, parent_task, child_task):
        """Test that deleting child removes from subtasks table."""
        sm.add_subtask(parent_task.id, child_task.id)

        # Delete the child task
        db.delete(child_task.id)

        # Parent should have no children
        assert sm.get_child_count(parent_task.id) == 0

    def test_delete_parent_orphans_children(self, sm, db, parent_task, child_task):
        """Test that deleting parent leaves children as top-level."""
        sm.add_subtask(parent_task.id, child_task.id)

        # Delete the parent task
        db.delete(parent_task.id)

        # Child should now be top-level (not a subtask)
        assert sm.is_subtask(child_task.id) is False

        # Child should still exist
        assert db.get(child_task.id) is not None


class TestCompletionStatus:
    """Test completion status methods."""

    def test_get_children_completion_status(self, sm, db, parent_task):
        """Test getting completion status of children."""
        children = [db.add(task=f"Child {i}", priority=Priority.P2) for i in range(3)]
        for child in children:
            sm.add_subtask(parent_task.id, child.id)

        # Mark one as done
        db.mark_done(children[0].id)

        status = sm.get_children_completion_status(parent_task.id)

        assert status['total'] == 3
        assert status['completed'] == 1
        assert len(status['incomplete_ids']) == 2
        assert children[0].id not in status['incomplete_ids']

    def test_can_complete_parent_no_children(self, sm, parent_task):
        """Test that parent with no children can be completed."""
        can_complete, message = sm.can_complete_parent(parent_task.id)

        assert can_complete is True
        assert "no subtasks" in message.lower()

    def test_can_complete_parent_all_done(self, sm, db, parent_task):
        """Test that parent can be completed when all children done."""
        children = [db.add(task=f"Child {i}", priority=Priority.P2) for i in range(2)]
        for child in children:
            sm.add_subtask(parent_task.id, child.id)
            db.mark_done(child.id)

        can_complete, message = sm.can_complete_parent(parent_task.id)

        assert can_complete is True
        assert "complete" in message.lower()

    def test_cannot_complete_parent_incomplete_children(self, sm, db, parent_task):
        """Test that parent cannot be completed with incomplete children."""
        children = [db.add(task=f"Child {i}", priority=Priority.P2) for i in range(3)]
        for child in children:
            sm.add_subtask(parent_task.id, child.id)

        # Mark only one as done
        db.mark_done(children[0].id)

        can_complete, message = sm.can_complete_parent(parent_task.id)

        assert can_complete is False
        assert "incomplete" in message.lower()
        assert "2" in message  # 2 incomplete children


class TestReorderChildren:
    """Test reordering children (validation only - no position column)."""

    def test_reorder_children_validates(self, sm, db, parent_task):
        """Test that reorder validates child IDs."""
        children = [db.add(task=f"Child {i}", priority=Priority.P2) for i in range(3)]
        for child in children:
            sm.add_subtask(parent_task.id, child.id)

        # Provide all children in different order
        new_order = [children[2].id, children[1].id, children[0].id]
        success, message = sm.reorder_children(parent_task.id, new_order)

        assert success is True
        assert "validated" in message.lower()

    def test_reorder_missing_child_fails(self, sm, db, parent_task):
        """Test that reorder with missing child fails."""
        children = [db.add(task=f"Child {i}", priority=Priority.P2) for i in range(3)]
        for child in children:
            sm.add_subtask(parent_task.id, child.id)

        # Missing one child in reorder
        incomplete_order = [children[0].id, children[1].id]
        success, error = sm.reorder_children(parent_task.id, incomplete_order)

        assert success is False
        assert "missing" in error.lower()

    def test_reorder_invalid_child_fails(self, sm, db, parent_task):
        """Test that reorder with invalid child fails."""
        children = [db.add(task=f"Child {i}", priority=Priority.P2) for i in range(2)]
        for child in children:
            sm.add_subtask(parent_task.id, child.id)

        # Include invalid child
        invalid_order = [children[0].id, children[1].id, 99999]
        success, error = sm.reorder_children(parent_task.id, invalid_order)

        assert success is False
        assert "invalid" in error.lower()


class TestHierarchyInfo:
    """Test hierarchy info method."""

    def test_hierarchy_info_top_level(self, sm, parent_task):
        """Test hierarchy info for top-level task."""
        info = sm.get_task_hierarchy_info(parent_task.id)

        assert info['is_subtask'] is False
        assert info['parent_id'] is None
        assert info['has_children'] is False
        assert info['child_count'] == 0
        assert info['can_have_children'] is True
        assert info['can_become_subtask'] is True

    def test_hierarchy_info_parent(self, sm, parent_task, child_task):
        """Test hierarchy info for parent task."""
        sm.add_subtask(parent_task.id, child_task.id)

        info = sm.get_task_hierarchy_info(parent_task.id)

        assert info['is_subtask'] is False
        assert info['has_children'] is True
        assert info['child_count'] == 1
        assert info['can_have_children'] is True
        assert info['can_become_subtask'] is False  # Has children

    def test_hierarchy_info_child(self, sm, parent_task, child_task):
        """Test hierarchy info for child task."""
        sm.add_subtask(parent_task.id, child_task.id)

        info = sm.get_task_hierarchy_info(child_task.id)

        assert info['is_subtask'] is True
        assert info['parent_id'] == parent_task.id
        assert info['has_children'] is False
        assert info['can_have_children'] is False  # Is a subtask
        assert info['can_become_subtask'] is False  # Already a subtask

    def test_hierarchy_info_nonexistent_task(self, sm):
        """Test hierarchy info for nonexistent task."""
        info = sm.get_task_hierarchy_info(99999)

        assert 'error' in info
        assert "not found" in info['error'].lower()
