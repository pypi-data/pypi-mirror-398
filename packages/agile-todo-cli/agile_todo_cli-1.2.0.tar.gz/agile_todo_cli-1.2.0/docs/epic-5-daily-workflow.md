# Epic 5: Daily Workflow

**Version**: v1.2.0
**Theme**: Recurring Tasks, Due Date Management, Calendar View
**Status**: Planning

## Overview

Epic 5 focuses on enhancing daily productivity workflows with recurring task automation, improved due date visibility, and a calendar view for time-based planning.

## Goals

1. Automate repetitive task creation with recurrence patterns
2. Surface urgent and overdue tasks more effectively
3. Provide a calendar-based view for planning

---

## Story 5.1: Recurring Task Database Schema

**As a** developer
**I want** a database schema for recurring task patterns
**So that** I can store and manage recurrence rules

### Acceptance Criteria

- [ ] New `recurrence_rules` table with columns:
  - `id` (primary key)
  - `task_id` (foreign key to todos)
  - `pattern` (daily, weekly, monthly, yearly, custom)
  - `interval` (every N days/weeks/months)
  - `days_of_week` (for weekly: Mon,Tue,Wed...)
  - `day_of_month` (for monthly: 1-31)
  - `end_date` (optional end date)
  - `max_occurrences` (optional limit)
  - `created_at`, `updated_at`
- [ ] Migration v3 created and tested
- [ ] Backward compatibility maintained
- [ ] Index on `task_id` for performance

### Technical Notes

```sql
CREATE TABLE recurrence_rules (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES todos(id) ON DELETE CASCADE,
    pattern TEXT NOT NULL CHECK(pattern IN ('daily', 'weekly', 'monthly', 'yearly', 'custom')),
    interval INTEGER DEFAULT 1,
    days_of_week TEXT,  -- JSON array: ["mon", "wed", "fri"]
    day_of_month INTEGER,
    end_date TEXT,
    max_occurrences INTEGER,
    occurrences_created INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## Story 5.2: Add Recurring Task via CLI

**As a** user
**I want** to add a task with a recurrence pattern
**So that** it automatically creates new instances

### Acceptance Criteria

- [ ] `todo add "Task" --recur daily` creates daily recurring task
- [ ] `todo add "Task" --recur weekly` creates weekly recurring task
- [ ] `todo add "Task" --recur monthly` creates monthly recurring task
- [ ] `todo add "Task" --recur "every 2 days"` supports interval
- [ ] `todo add "Task" --recur "every mon,wed,fri"` supports specific days
- [ ] `todo add "Task" --recur daily --until 2025-03-01` supports end date
- [ ] Recurrence indicator shown in task list output
- [ ] Error handling for invalid recurrence patterns

### Examples

```bash
# Daily standup
todo add "Daily standup" --recur daily -p p1

# Weekly review every Friday
todo add "Weekly review" --recur "every fri"

# Bi-weekly sprint planning
todo add "Sprint planning" --recur "every 2 weeks"

# Monthly report on the 1st
todo add "Monthly report" --recur "monthly on 1"

# Custom: Mon, Wed, Fri
todo add "Exercise" --recur "every mon,wed,fri"
```

---

## Story 5.3: Recurrence Manager Module

**As a** developer
**I want** a RecurrenceManager class
**So that** I can handle recurrence logic cleanly

### Acceptance Criteria

- [ ] `RecurrenceManager` class in `todo_cli/recurrence.py`
- [ ] `parse_pattern(pattern: str) -> RecurrenceRule` parses user input
- [ ] `get_next_occurrence(rule: RecurrenceRule, from_date: date) -> date`
- [ ] `should_create_occurrence(rule: RecurrenceRule) -> bool`
- [ ] `create_occurrence(task_id: int) -> Todo` creates next instance
- [ ] Handles edge cases (month end, leap years)
- [ ] 95%+ test coverage for recurrence logic

### Technical Notes

```python
@dataclass
class RecurrenceRule:
    pattern: str  # daily, weekly, monthly, yearly, custom
    interval: int = 1
    days_of_week: list[str] | None = None
    day_of_month: int | None = None
    end_date: date | None = None
    max_occurrences: int | None = None
```

---

## Story 5.4: Automatic Occurrence Generation

**As a** user
**I want** recurring tasks to automatically generate new instances
**So that** I don't have to manually recreate them

### Acceptance Criteria

- [ ] When a recurring task is marked done, next occurrence is created
- [ ] New occurrence has same properties (priority, project, tags)
- [ ] New occurrence has calculated due date based on pattern
- [ ] `todo recur generate` manually triggers occurrence generation
- [ ] Occurrences respect `end_date` and `max_occurrences` limits
- [ ] Notification shown when new occurrence is created

### Behavior

```bash
$ todo done 5
✓ Task #5 marked as done (30m tracked)
↻ Created next occurrence: Task #12 (due: 2025-01-03)
```

---

## Story 5.5: List and Manage Recurring Tasks

**As a** user
**I want** to see and manage my recurring tasks
**So that** I can modify or stop recurrence patterns

### Acceptance Criteria

- [ ] `todo recur list` shows all recurring task templates
- [ ] `todo recur show <id>` shows recurrence details
- [ ] `todo recur edit <id> --interval 2` modifies pattern
- [ ] `todo recur stop <id>` stops future occurrences
- [ ] `todo recur delete <id>` removes rule (keeps existing tasks)
- [ ] Recurring tasks show indicator in regular `todo list`

### Output Example

```
$ todo recur list
Recurring Tasks:
  #1 Daily standup      [daily]           Next: 2025-01-02
  #3 Weekly review      [every fri]       Next: 2025-01-03
  #7 Sprint planning    [every 2 weeks]   Next: 2025-01-13

$ todo recur show 1
Task #1: Daily standup
  Pattern: daily
  Interval: 1
  Created: 15 occurrences
  Next due: 2025-01-02
  End date: none
```

---

## Story 5.6: Due Date Filtering

**As a** user
**I want** to filter tasks by due date
**So that** I can focus on what's urgent

### Acceptance Criteria

- [ ] `todo list --due today` shows tasks due today
- [ ] `todo list --due tomorrow` shows tasks due tomorrow
- [ ] `todo list --due week` shows tasks due this week
- [ ] `todo list --overdue` shows all overdue tasks
- [ ] `todo list --due 2025-01-15` shows tasks due on specific date
- [ ] `todo list --due-before 2025-01-15` shows tasks due before date
- [ ] `todo list --due-after 2025-01-15` shows tasks due after date
- [ ] Overdue tasks highlighted in red in output

### Examples

```bash
# Morning routine: what's due today?
todo list --due today

# Planning: what's coming this week?
todo list --due week

# Catch up: what did I miss?
todo list --overdue

# Specific date
todo list --due 2025-01-15
```

---

## Story 5.7: Overdue Task Notifications

**As a** user
**I want** to see overdue task warnings
**So that** I don't forget urgent items

### Acceptance Criteria

- [ ] `todo list` shows overdue count in header when > 0
- [ ] `todo stats` includes overdue task count
- [ ] Overdue tasks show days overdue (e.g., "2d overdue")
- [ ] `todo list --all` still shows overdue tasks prominently
- [ ] KANBAN board shows overdue indicator (red !)

### Output Example

```
$ todo list
⚠️  3 tasks overdue

  ID  Task                 Priority  Due         Status
  ──  ────                 ────────  ───         ──────
  #2  Submit report        P0        2d overdue  todo
  #5  Review PR            P1        1d overdue  todo
  #8  Update docs          P2        today       todo
  #3  Plan sprint          P1        tomorrow    doing
```

---

## Story 5.8: Calendar View

**As a** user
**I want** a calendar view of my tasks
**So that** I can visualize my schedule

### Acceptance Criteria

- [ ] `todo calendar` shows current month with task counts
- [ ] `todo calendar --month 2025-02` shows specific month
- [ ] `todo calendar --week` shows current week view
- [ ] Days with tasks show task count or indicator
- [ ] Today highlighted
- [ ] Overdue days highlighted in red
- [ ] Can navigate with `--prev` and `--next` flags

### Output Example

```
$ todo calendar
         January 2025
  Su  Mo  Tu  We  Th  Fr  Sa
            1   2   3   4
               [2] [1]
   5   6   7   8   9  10  11
      [3]         [1]
  12  13  14  15  16  17  18
  [TODAY]    [2]
  19  20  21  22  23  24  25

  26  27  28  29  30  31
                  [1]

[n] = n tasks due that day
```

---

## Story 5.9: Calendar Interactive Mode

**As a** user
**I want** to navigate the calendar interactively
**So that** I can explore and manage tasks by date

### Acceptance Criteria

- [ ] `todo calendar -i` launches interactive calendar TUI
- [ ] Arrow keys navigate between days
- [ ] Enter on a day shows tasks due that day
- [ ] `a` adds task with selected date as due date
- [ ] `n`/`p` moves to next/previous month
- [ ] `t` jumps to today
- [ ] `q` quits

### Technical Notes

- Use Textual framework (already a dependency)
- Calendar widget with task integration
- Modal for day detail view

---

## Dependencies

```
Story 5.1 (Schema)
    ↓
Story 5.3 (Manager) ──→ Story 5.2 (CLI Add)
    ↓
Story 5.4 (Auto-generate) ──→ Story 5.5 (List/Manage)

Story 5.6 (Due Filtering) ──→ Story 5.7 (Notifications)
    ↓
Story 5.8 (Calendar View) ──→ Story 5.9 (Interactive)
```

## Implementation Order

### Phase 1: Recurring Tasks Foundation
1. Story 5.1 - Database Schema
2. Story 5.3 - Recurrence Manager
3. Story 5.2 - CLI Add with --recur

### Phase 2: Recurring Task Operations
4. Story 5.4 - Auto-generate occurrences
5. Story 5.5 - List and manage recurring

### Phase 3: Due Date Enhancements
6. Story 5.6 - Due date filtering
7. Story 5.7 - Overdue notifications

### Phase 4: Calendar
8. Story 5.8 - Calendar view
9. Story 5.9 - Interactive calendar

---

## Estimates

| Story | Complexity | Est. Tests |
|-------|------------|------------|
| 5.1 Schema | Low | 10 |
| 5.2 CLI Add | Medium | 20 |
| 5.3 Manager | High | 40 |
| 5.4 Auto-gen | Medium | 25 |
| 5.5 List/Manage | Medium | 20 |
| 5.6 Due Filter | Low | 15 |
| 5.7 Notifications | Low | 10 |
| 5.8 Calendar | Medium | 20 |
| 5.9 Interactive | High | 25 |

**Total**: ~185 new tests

---

## Success Metrics

- [ ] Users can create recurring tasks with common patterns
- [ ] Overdue tasks are immediately visible
- [ ] Calendar view renders correctly for any month
- [ ] All existing tests continue to pass
- [ ] Performance: calendar renders < 100ms
