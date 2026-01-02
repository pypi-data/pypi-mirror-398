# Story 2.1: Parent-Child Task Relationship Model

## Story Overview

| Field | Value |
|-------|-------|
| Epic | 2 - Hierarchical Task Organization |
| Story | 2.1 - Parent-Child Task Relationship Model |
| Priority | Must Have (Core MVP) |
| Estimated Effort | 3-4 hours |
| Dependencies | Epic 1 Complete (database foundation exists) |

## User Story

**As a** developer,
**I want** to define parent-child relationships between tasks in the database,
**So that** I can represent feature breakdowns and track granular progress without losing context of the larger goal.

---

## Brownfield Context

### Existing System State

**Database Foundation (Epic 1 Complete):**
- `subtasks` table already created by migration v0→v1 in `migrations.py`
- Schema: `parent_id`, `child_id`, `position`, `created_at`
- Indexes: `idx_subtasks_parent`, `idx_subtasks_child`
- CHECK constraint: `parent_id != child_id`
- Foreign keys with CASCADE on delete

**Current Schema (from migrations.py:573-585):**
```sql
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
```

**Existing Files to Extend:**
- `todo_cli/database.py` - Add subtask query methods
- `todo_cli/main.py` - CLI commands (Story 2.2)

**New File to Create:**
- `todo_cli/subtasks.py` - SubtaskManager business logic (per architecture.md)

### Integration Points

| Integration | Mechanism | Notes |
|-------------|-----------|-------|
| Database Layer | `Database` class in database.py | Follow existing context manager pattern |
| Migration System | Already complete | subtasks table exists |
| Project Module | `projects.py` pattern | Use as reference for SubtaskManager |
| Display Layer | `display.py` | Future: tree rendering (Story 2.3) |

---

## Acceptance Criteria

### AC1: Database Query Support
```gherkin
Given the subtasks table exists in the database
When I query for parent-child relationships
Then I can:
  - Get all children of a parent task
  - Get the parent of a child task
  - Check if a task has children
  - Check if a task is a subtask
```

**Implementation:**
- Add methods to `Database` class or create `SubtaskManager`

### AC2: Circular Reference Prevention
```gherkin
Given task A is a parent of task B
When I attempt to make task A a child of task B
Then the operation fails with error "Circular reference detected"
```

**Implementation:**
- Application-level check before INSERT

### AC3: Depth Constraint (1 Level Max)
```gherkin
Given task A is a parent of task B (B is a subtask)
When I attempt to add task C as a child of task B
Then the operation fails with error "Cannot add subtask to a task that is already a subtask (max depth: 1)"
```

**Implementation:**
- Check if proposed parent is already a child in subtasks table

### AC4: Parent Cannot Become Child
```gherkin
Given task A has children (is a parent)
When I attempt to make task A a child of another task
Then the operation fails with error "Cannot make a parent task into a subtask (has N children)"
```

**Implementation:**
- Check if proposed child has existing children

### AC5: Cascade Delete Behavior
```gherkin
Given task A (parent) has children B and C
When task A is deleted
Then:
  - Tasks B and C remain as top-level tasks
  - Relationships in subtasks table are removed (CASCADE)
```

**Already Implemented:** Foreign key CASCADE on delete handles this automatically.

---

## Technical Design

### SubtaskManager Class (subtasks.py)

```python
# todo_cli/subtasks.py
"""Hierarchical task relationship management."""

from typing import Optional
from .database import Database
from .models import Todo


class SubtaskManager:
    """Manages parent-child task relationships."""

    def __init__(self, db: Database):
        self.db = db

    def add_subtask(self, parent_id: int, child_id: int, position: int = 0) -> tuple[bool, str]:
        """
        Create parent-child relationship with validation.

        Returns:
            (success: bool, message: str)
        """
        # Validation sequence:
        # 1. Both tasks exist
        # 2. parent_id != child_id (DB constraint handles this too)
        # 3. Child is not already a subtask (depth constraint)
        # 4. Parent is not already a subtask (depth constraint)
        # 5. No circular reference (A->B->A)
        pass

    def remove_subtask(self, parent_id: int, child_id: int) -> tuple[bool, str]:
        """Remove relationship (child becomes top-level)."""
        pass

    def get_children(self, parent_id: int) -> list[Todo]:
        """Get all children of parent task, ordered by position."""
        pass

    def get_parent(self, child_id: int) -> Optional[Todo]:
        """Get parent of child task, or None if top-level."""
        pass

    def is_subtask(self, task_id: int) -> bool:
        """Check if task is a sub-task (has a parent)."""
        pass

    def has_children(self, task_id: int) -> bool:
        """Check if task has children."""
        pass

    def get_child_count(self, task_id: int) -> int:
        """Get number of children for a task."""
        pass

    def can_add_subtask(self, parent_id: int, child_id: int) -> tuple[bool, str]:
        """
        Validate if sub-task can be added.

        Checks:
        - Both tasks exist
        - Self-reference prevention
        - Depth constraint (neither can already be in hierarchy)
        - Circular reference prevention

        Returns:
            (can_add: bool, error_message: str)
        """
        pass

    def reorder_children(self, parent_id: int, child_ids: list[int]) -> bool:
        """Reorder children by updating position values."""
        pass
```

### Database Queries

**Get children of parent:**
```sql
SELECT t.* FROM todos t
JOIN subtasks s ON t.id = s.child_id
WHERE s.parent_id = ?
ORDER BY s.position, t.created_at
```

**Get parent of child:**
```sql
SELECT t.* FROM todos t
JOIN subtasks s ON t.id = s.parent_id
WHERE s.child_id = ?
```

**Check if task is subtask:**
```sql
SELECT 1 FROM subtasks WHERE child_id = ? LIMIT 1
```

**Check if task has children:**
```sql
SELECT 1 FROM subtasks WHERE parent_id = ? LIMIT 1
```

**Count children:**
```sql
SELECT COUNT(*) FROM subtasks WHERE parent_id = ?
```

---

## Testing Requirements

### Unit Tests (tests/test_subtasks.py)

```python
# Test Categories:

# 1. Basic Operations
def test_add_subtask_success():
    """Adding valid subtask creates relationship."""

def test_get_children_returns_ordered_list():
    """Children returned in position order."""

def test_get_parent_returns_parent_task():
    """Getting parent of subtask returns correct task."""

def test_get_parent_returns_none_for_top_level():
    """Top-level tasks have no parent."""

# 2. Validation - Depth Constraint
def test_cannot_add_subtask_to_subtask():
    """Task already a child cannot have children (depth=1 max)."""

def test_cannot_make_parent_into_subtask():
    """Task with children cannot become a child."""

# 3. Validation - Circular Reference
def test_self_reference_prevented():
    """Task cannot be its own parent."""

def test_circular_reference_prevented():
    """A->B then B->A prevented."""

# 4. Cascade Behavior
def test_delete_parent_orphans_children():
    """Deleting parent leaves children as top-level."""

def test_delete_child_removes_relationship():
    """Deleting child removes from subtasks table."""

# 5. Edge Cases
def test_add_subtask_nonexistent_parent():
    """Adding to nonexistent parent fails gracefully."""

def test_add_subtask_nonexistent_child():
    """Adding nonexistent child fails gracefully."""

def test_reorder_children():
    """Position updates correctly order children."""
```

---

## Implementation Checklist

### Phase 1: SubtaskManager Core
- [ ] Create `todo_cli/subtasks.py` with `SubtaskManager` class
- [ ] Implement `can_add_subtask()` validation method
- [ ] Implement `add_subtask()` with full validation
- [ ] Implement `remove_subtask()` (unlink operation)
- [ ] Implement query methods: `get_children()`, `get_parent()`, `is_subtask()`, `has_children()`

### Phase 2: Testing
- [ ] Create `tests/test_subtasks.py`
- [ ] Write tests for basic operations
- [ ] Write tests for depth constraint
- [ ] Write tests for circular reference prevention
- [ ] Write tests for cascade behavior
- [ ] Write edge case tests

### Phase 3: Integration
- [ ] Verify foreign key CASCADE works correctly
- [ ] Test with existing todo data
- [ ] Run full test suite to ensure no regressions

---

## Definition of Done

- [ ] All acceptance criteria pass
- [ ] SubtaskManager class implemented with all methods
- [ ] Unit tests written and passing (>90% coverage for subtasks.py)
- [ ] No regressions in existing tests
- [ ] Code follows project patterns (type hints, docstrings)
- [ ] Linting passes (`ruff check`)
- [ ] Type checking passes (`mypy`)

---

## Out of Scope (Future Stories)

- CLI commands for subtasks (Story 2.2)
- Tree view rendering (Story 2.3)
- Subtask listing/filtering (Story 2.4)
- Parent completion logic (Story 2.5)
- Subtask deletion commands (Story 2.6)

---

## References

- PRD: `docs/prd.md` (Story 2.1 section)
- Architecture: `docs/architecture.md` (Section 2.1, 4.2)
- Existing Pattern: `todo_cli/projects.py` (ProjectManager class)
- Migration: `todo_cli/migrations.py` (_migrate_v0_to_v1)
