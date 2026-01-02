# Product Requirements Document (PRD)
**Project:** Todo-CLI Feature Expansion - Advanced Project Management
**Version:** 1.0
**Date:** 2024-12-25
**Status:** Ready for Architecture Phase
**PM Checklist:** ✅ PASS (94% Complete)

---

## Table of Contents

1. [Goals and Background Context](#1-goals-and-background-context)
2. [Requirements](#2-requirements)
3. [UI Goals](#3-ui-goals)
4. [Technical Assumptions](#4-technical-assumptions)
5. [Epic List](#5-epic-list)
6. [Epic Details](#6-epic-details)
7. [PM Checklist Results](#7-pm-checklist-results)
8. [Next Steps](#8-next-steps)

---

## 1. Goals and Background Context

### Project Overview

Todo-CLI Feature Expansion transforms the existing command-line todo manager into a comprehensive, terminal-native project management system by adding four integrated capabilities: enhanced project grouping, hierarchical task organization (sub-tasks), ASCII KANBAN board visualization, and Linear-inspired cycle management. This enhancement addresses the needs of CLI power users who require sophisticated project organization without leaving their development environment, positioning todo-cli as "Linear for the terminal."

### Problem Statement

**Current Challenge:** CLI-focused developers and technical professionals spend 80%+ of their time in the terminal but must constantly context-switch to GUI-based project management tools (Jira, Trello, Asana, Linear) for essential project organization tasks. This context switching causes:

- **Flow state disruption:** Developers report losing 15-30 minutes per day switching between terminal and browser-based PM tools
- **Data duplication:** Teams maintain tasks in both CLI (personal tracking) and GUI PM tool (team visibility), leading to sync errors
- **Reduced CLI adoption:** Power users abandon todo-cli for complex projects because it can't scale beyond simple task lists
- **Lost automation opportunities:** Without terminal-native PM features, users cannot script project workflows or integrate with CI/CD pipelines

**Existing todo-cli Limitations:**
- No task hierarchies - large features cannot be broken into sub-tasks
- Limited project visualization - tasks are list-based only, no KANBAN board view
- No iteration planning - cannot organize work into sprints/cycles
- Weak project grouping - projects exist as tags but lack dedicated project-centric operations

**Why Existing Solutions Fall Short:**
- **GUI PM tools:** Require mouse interaction, slow to navigate, cannot be scripted, break terminal-centric workflows
- **Other CLI task managers:** Tools like taskwarrior or todo.txt lack modern PM features (KANBAN, cycles)
- **Hybrid approaches:** Using CLI for tasks + GUI for PM means maintaining two systems with manual synchronization

### Business Objectives

**Primary Goals:**
- Increase user adoption by 40% within 3 months of release (measured by active weekly users)
- Achieve 60% feature adoption rate among existing users within 6 months
- Reduce user churn by 25% (decrease monthly attrition)
- Establish todo-cli as "go-to" CLI PM tool (top 3 in search results, GitHub stars)
- Enable enterprise use cases (support 5-10 person engineering teams)

**User Success Metrics:**
- Users report 50%+ reduction in daily switches to GUI PM tools
- Daily active usage increases to 10+ interactions per day (up from 5-7)
- 70% of users who adopt KANBAN also adopt cycles (feature integration validation)
- New users create first project with sub-tasks and KANBAN view within 15 minutes
- 40% of users integrate todo-cli commands into scripts/aliases/automation within first month
- Users complete 20%+ more tasks per sprint when using cycle management

**Key Performance Indicators:**
- Weekly Active Users (WAU): 40% increase within 3 months post-release
- Feature Adoption Rate: Projects (80%), Sub-tasks (70%), KANBAN (60%), Cycles (50%)
- Commands per Session: Target 15+ (indicating deep engagement)
- Retention Rate (28-day): Target 70%+
- Net Promoter Score (NPS): Target 40+ (industry good)
- Export/Integration Usage: 30% of users leverage export commands
- Time in KANBAN View: Average 10+ minutes daily

### Target Users

**Primary Segment: Terminal-Native Software Developers**
- **Role:** Software engineers, backend developers, full-stack developers
- **Experience:** Intermediate to senior (3+ years), comfortable with CLI tools
- **Environment:** Remote-first teams, multiple projects simultaneously
- **Tech stack:** Git, Docker, Kubernetes, Vim/Neovim/VSCode terminal, tmux/screen
- **OS:** macOS, Linux, Windows WSL
- **Behaviors:** 6-8 hours daily in terminal, context-switch to browser PM tools 5-15 times/day

**Pain Points:**
- Context switching fatigue breaking flow state
- Cannot organize work into hierarchical breakdowns without leaving CLI
- No sprint planning in terminal
- Poor visibility into workflow state without GUI tool
- Manual synchronization between personal CLI tracker and team PM tool
- Cannot automate project workflows (cycle creation, reports, status updates)

**Goals:**
- Minimize context switching to maintain deep work
- Manage personal and team projects entirely from terminal
- Plan and track sprint/cycle progress without opening browser
- Automate project management tasks via scripts
- Visualize project health and workflow state in terminal dashboards
- Share project status with team via simple text exports

**Secondary Segment: Technical Project Managers & DevOps Engineers**
- **Role:** Engineering managers, technical PMs, DevOps/SRE engineers, team leads
- **Split time:** 40-60% terminal, 40-60% GUI PM tools
- **Responsibilities:** Multi-project management, team coordination, stakeholder reporting

**Additional Pain Points:**
- Reporting overhead (manually extracting data from PM tools)
- Multi-project visibility needs
- Planning complexity with current CLI tools
- Bridging gap between terminal-native teams and stakeholder reporting

### Value Proposition

**Core Differentiation:**
- **Integrated, not bolted-on:** All features share the same data model and work seamlessly together
- **Terminal-native visualization:** KANBAN boards render beautifully in terminal using box-drawing characters and color
- **Scriptable PM workflows:** Every feature accessible via commands, enabling automation
- **Existing workflow preservation:** Backwards compatible - current users can adopt features incrementally
- **Linear's cycle model:** Modern iteration paradigm (fixed-length, auto-rolling cycles) familiar to developers

**Vision:** Todo-cli becomes the "Linear for the terminal" - a complete project management system that developers never need to leave their shell to use.

### Success Criteria

**MVP is successful if:**
1. Users can manage a complete software project using only todo-cli without GUI PM tool for basic workflows
2. All four core features work seamlessly together (not siloed)
3. 80%+ of current users can upgrade and use new features within 30 minutes with minimal documentation
4. KANBAN board provides sufficient visibility and is preferred to list view for project overview
5. Cycles drive better planning and completion rates vs. unstructured task lists
6. At least 20% of users create custom scripts/aliases leveraging new commands within first month
7. Technical quality meets existing standards (sub-second execution, no corruption, 80%+ test coverage)
8. Export enables team sharing via Markdown/JSON exports

**MVP is NOT successful if it requires:**
- More than 5 new CLI commands to access core features (complexity threshold)
- GUI tool or external service to be fully functional
- Breaking changes to existing data or commands
- More than 10 hours of development time to learn and adopt for experienced CLI users

---

## 2. Requirements

### 2.1 Functional Requirements

**FR-001: Enhanced Project Management**
- **Description:** Users can create, list, update, and delete projects as first-class entities (not just tags). Projects have metadata (description, status, created date) and support dedicated project-centric views.
- **Priority:** Must Have (Core MVP)
- **User Story:** "As a developer, I want to create dedicated projects so that I can organize my tasks by codebase or initiative rather than using generic tags."
- **Acceptance Criteria:**
  - Users can create projects with name and optional description
  - Users can list all projects with task counts and status
  - Users can filter all commands by project (`--project` flag)
  - Project metadata is persisted in database
  - Projects can be archived/deleted
- **Dependencies:** Database schema extension, migration framework

**FR-002: Project-Centric Views**
- **Description:** Users can view all tasks grouped by project with dedicated commands and filtering across all existing todo-cli operations.
- **Priority:** Must Have (Core MVP)
- **User Story:** "As a developer managing multiple codebases, I want to see all tasks for a specific project at once so that I can focus on one project context without mental overhead."
- **Acceptance Criteria:**
  - `todo projects` command lists all projects with summary stats
  - `todo list --project <name>` filters tasks by project
  - `todo kanban --project <name>` shows project-specific KANBAN board
  - Project filtering works across all commands (add, list, complete, etc.)

**FR-003: Hierarchical Sub-Task System**
- **Description:** Users can create parent-child task relationships (1 level deep for MVP) allowing feature breakdown into manageable sub-tasks.
- **Priority:** Must Have (Core MVP)
- **User Story:** "As a developer, I want to break down large features into sub-tasks so that I can track granular progress without losing sight of the larger goal."
- **Acceptance Criteria:**
  - Users can add sub-tasks to any existing task
  - Sub-tasks appear indented under parent in list view
  - Parent task completion requires all sub-tasks complete
  - Sub-tasks inherit project from parent by default
  - Maximum 1 level of nesting enforced (no grandchildren)

**FR-004: Tree Visualization for Hierarchical Tasks**
- **Description:** Users can view tasks in hierarchical tree format showing parent-child relationships clearly.
- **Priority:** Must Have (Core MVP)
- **User Story:** "As a developer, I want to see my task breakdown visually so that I can understand feature scope and progress at a glance."
- **Acceptance Criteria:**
  - `todo list --tree` displays hierarchical view using Rich library
  - Tree view uses box-drawing characters for visual hierarchy
  - Completion status visible for parent and children
  - Tree view supports project filtering
  - Collapsible branches for large hierarchies (optional)

**FR-005: ASCII KANBAN Board Rendering**
- **Description:** Terminal-rendered KANBAN board with configurable columns displaying tasks in workflow states using box-drawing characters and color coding.
- **Priority:** Must Have (Core MVP)
- **User Story:** "As a developer, I want to visualize my workflow state in the terminal so that I can see what's in progress, what's blocked, and what's completed without opening a GUI tool."
- **Acceptance Criteria:**
  - `todo kanban` command renders board in terminal using Rich panels
  - Default columns: Backlog, Todo, In Progress, Review, Done
  - Tasks display with ID, title, priority color coding
  - Board supports filtering by project (`--project` flag)
  - Board renders in <500ms for 1000+ tasks
  - Board fits within standard 80-column terminal (with horizontal scrolling if needed)

**FR-006: KANBAN Column Management**
- **Description:** Users can move tasks between KANBAN columns to update workflow state.
- **Priority:** Must Have (Core MVP)
- **User Story:** "As a developer, I want to move tasks between workflow states (Todo → In Progress → Done) using keyboard commands so that I can update my board without mouse interaction."
- **Acceptance Criteria:**
  - `todo move <task-id> <column>` updates task's KANBAN column
  - Column names are case-insensitive
  - Invalid column names show error with available options
  - Task history tracks column changes (optional)
  - Moving to "Done" auto-completes the task

**FR-007: KANBAN Interactive Mode**
- **Description:** Real-time refreshing KANBAN board view with keyboard navigation for quick updates (optional enhancement).
- **Priority:** Should Have (Post-MVP)
- **User Story:** "As a developer, I want to interact with my KANBAN board using arrow keys so that I can quickly update task states without typing multiple commands."
- **Acceptance Criteria:**
  - `todo kanban --interactive` launches TUI mode
  - Arrow keys navigate between tasks and columns
  - Enter key moves selected task to focused column
  - ESC exits interactive mode
  - Board updates in <50ms on state change

**FR-008: Basic Cycle Creation and Management**
- **Description:** Users can create fixed-length cycles (iterations/sprints) with start/end dates following Linear's cycle model.
- **Priority:** Must Have (Core MVP)
- **User Story:** "As a developer, I want to plan my work in time-boxed iterations so that I can scope releases and track velocity without using a GUI tool."
- **Acceptance Criteria:**
  - `todo cycle create <name> --duration <weeks>` creates new cycle
  - Cycle has start date, end date, status (active, closed)
  - Only one active cycle at a time (MVP constraint)
  - Cycles are persisted in database
  - `todo cycle list` shows all cycles with dates and task counts

**FR-009: Cycle Task Assignment**
- **Description:** Users can assign tasks to cycles for sprint planning.
- **Priority:** Must Have (Core MVP)
- **User Story:** "As a developer, I want to assign tasks to the current cycle so that I can plan what I'll complete this sprint."
- **Acceptance Criteria:**
  - `todo cycle assign <task-id>` assigns task to active cycle
  - `todo cycle assign <task-id> --cycle <name>` assigns to specific cycle
  - `todo list --cycle <name>` shows all tasks in cycle
  - Task can only be in one cycle at a time
  - Unassigning tasks supported (`todo cycle unassign <task-id>`)

**FR-010: Cycle Progress Tracking**
- **Description:** Users can view current cycle status including completed vs. incomplete tasks.
- **Priority:** Must Have (Core MVP)
- **User Story:** "As a developer, I want to see my cycle progress so that I can understand if I'm on track to complete my sprint goals."
- **Acceptance Criteria:**
  - `todo cycle current` shows active cycle with progress summary
  - Progress shows: total tasks, completed, remaining, completion percentage
  - Displays cycle start/end dates and days remaining
  - Highlights overdue cycles (past end date but still active)

**FR-011: Cycle Reporting**
- **Description:** Users can generate cycle summary reports in multiple formats for sharing with team or stakeholders.
- **Priority:** Must Have (Core MVP)
- **User Story:** "As a technical PM, I want to export cycle summaries as Markdown or JSON so that I can share sprint results with my team via Slack or documentation."
- **Acceptance Criteria:**
  - `todo cycle report [--format md|json]` generates cycle report
  - Markdown format: human-readable with task lists, completion stats, burndown summary
  - JSON format: machine-readable for tool integration
  - Report includes: cycle name, dates, task completion stats, list of completed/incomplete tasks
  - Report can be piped to file or clipboard

**FR-012: Cycle Closing and Auto-Rolling**
- **Description:** Users can close completed cycles and automatically create next cycle following Linear's auto-rolling model.
- **Priority:** Should Have (Post-MVP)
- **User Story:** "As a developer, I want to close the current cycle and automatically start the next one so that I don't have to manually manage iteration transitions."
- **Acceptance Criteria:**
  - `todo cycle close` marks current cycle as closed
  - Incomplete tasks can be moved to next cycle or backlog (user choice)
  - `todo cycle close --auto-next` closes current and creates next cycle with same duration
  - Closed cycles are archived but queryable for historical reporting

**FR-013: Task Filtering and Search**
- **Description:** Users can filter tasks across all views by project, cycle, status, priority, and tags.
- **Priority:** Must Have (Core MVP)
- **User Story:** "As a developer, I want to filter my task list by multiple criteria so that I can focus on high-priority items for my current project and cycle."
- **Acceptance Criteria:**
  - `todo list --project <name> --cycle <cycle> --status <status>` supports combined filtering
  - Filter by priority (`--priority high|medium|low`)
  - Filter by tags (`--tag <tag>`)
  - Filters work across list, KANBAN, and tree views
  - Multiple tags/projects supported (OR logic)

**FR-014: Backwards Compatibility**
- **Description:** All existing todo-cli commands, data, and workflows continue working unchanged after upgrade.
- **Priority:** Must Have (Critical)
- **User Story:** "As an existing user, I want to upgrade to the new version without losing data or having to change my existing workflows."
- **Acceptance Criteria:**
  - Existing `todo add`, `todo list`, `todo complete`, etc. work identically
  - Existing database files auto-migrate to new schema
  - Migration is reversible (rollback supported if issues)
  - New columns/tables have sensible defaults for existing tasks
  - Help text updated but command syntax unchanged

**FR-015: Export Enhancements**
- **Description:** Existing export functionality extended to support projects, sub-tasks, cycles, and KANBAN state.
- **Priority:** Must Have (Core MVP)
- **User Story:** "As a developer, I want to export my project data including hierarchy and cycle assignments so that I can integrate with other tools or create backups."
- **Acceptance Criteria:**
  - JSON export includes sub-task relationships, project metadata, cycle assignments
  - Markdown export formats hierarchical tasks with indentation
  - CSV export includes new columns (project_id, parent_id, cycle_id, kanban_column)
  - Export respects filtering (e.g., export only current cycle)

**FR-016: Configuration Management**
- **Description:** Users can configure KANBAN columns, default cycle duration, and display preferences via YAML config.
- **Priority:** Should Have (Post-MVP)
- **User Story:** "As a developer, I want to customize my KANBAN column names and default cycle length so that the tool matches my team's workflow."
- **Acceptance Criteria:**
  - `~/.config/todo-cli/config.yaml` stores user preferences
  - Configure KANBAN columns (names, order, colors)
  - Set default cycle duration (1, 2, or 4 weeks)
  - Color scheme customization for priorities and KANBAN
  - Config changes apply immediately without restart

**FR-017: Help and Documentation**
- **Description:** Comprehensive inline help for all new commands and updated command examples.
- **Priority:** Must Have (Core MVP)
- **User Story:** "As a new user, I want to learn how to use projects, sub-tasks, KANBAN, and cycles via `--help` flags so that I don't need to read external documentation."
- **Acceptance Criteria:**
  - All new commands have detailed `--help` output
  - Examples included for common workflows
  - README updated with feature documentation
  - Migration guide for existing users
  - Troubleshooting section for common issues

### 2.2 Non-Functional Requirements

**NFR-001: Performance - Command Execution Speed**
- **Requirement:** All list/display operations complete in <100ms, KANBAN rendering in <500ms for datasets up to 10,000 tasks.
- **Rationale:** CLI tools must feel instant - any lag breaks the terminal-native experience.
- **Measurement:** Execution time logging, performance benchmarks in CI/CD
- **Priority:** Critical

**NFR-002: Performance - Database Query Optimization**
- **Requirement:** Complex queries (KANBAN with filters, hierarchical tree views) use appropriate indexes and complete within performance targets.
- **Rationale:** SQLite performance degrades without proper indexing as datasets grow.
- **Measurement:** EXPLAIN QUERY PLAN analysis, query duration logging
- **Priority:** High

**NFR-003: Performance - Interactive KANBAN Refresh**
- **Requirement:** Interactive KANBAN mode updates display in <50ms on state changes for responsive UX.
- **Rationale:** Interactive TUI must feel real-time, not laggy.
- **Measurement:** Frame timing logs, user perception testing
- **Priority:** Medium (Post-MVP feature)

**NFR-004: Scalability - Large Dataset Support**
- **Requirement:** Tool remains performant with 10,000+ tasks, 100+ projects, 50+ cycles without degradation.
- **Rationale:** Power users accumulate large task histories over time.
- **Measurement:** Performance benchmarks with synthetic large datasets
- **Priority:** High

**NFR-005: Reliability - Data Integrity**
- **Requirement:** Database operations are ACID-compliant, with no data corruption or loss during crashes/interruptions.
- **Rationale:** Task data is critical - users cannot tolerate data loss.
- **Measurement:** Crash recovery testing, transaction rollback validation
- **Priority:** Critical

**NFR-006: Reliability - Migration Robustness**
- **Requirement:** Database migrations succeed for 100% of existing todo-cli installations with automatic rollback on failure.
- **Rationale:** Breaking existing users' data is unacceptable.
- **Measurement:** Migration testing with diverse existing database versions
- **Priority:** Critical

**NFR-007: Compatibility - Cross-Platform Support**
- **Requirement:** Tool works identically on macOS, Linux, and Windows WSL without platform-specific code paths (where possible).
- **Rationale:** Target users span multiple platforms.
- **Measurement:** CI/CD testing on all platforms, platform-specific bug reports
- **Priority:** High

**NFR-008: Compatibility - Terminal Emulator Support**
- **Requirement:** KANBAN board renders correctly on major terminal emulators (iTerm2, Alacritty, Kitty, GNOME Terminal, Windows Terminal) with graceful degradation for limited terminals.
- **Rationale:** Users have diverse terminal preferences - can't assume advanced Unicode support.
- **Measurement:** Manual testing across terminals, fallback to ASCII mode for unsupported features
- **Priority:** High

**NFR-009: Compatibility - Python Version**
- **Requirement:** Requires Python 3.10+ with no support for older versions.
- **Rationale:** Modern Python features (type hints, match statements) improve code quality.
- **Measurement:** Python version check on startup
- **Priority:** Medium

**NFR-010: Security - SQL Injection Prevention**
- **Requirement:** All database queries use parameterized statements with zero direct string interpolation.
- **Rationale:** Prevent data corruption or exploitation via malicious input.
- **Measurement:** Code review, security linting
- **Priority:** High

**NFR-011: Security - File Permissions**
- **Requirement:** Database file created with 600 permissions (user-only read/write) by default.
- **Rationale:** Task data may be sensitive and should not be readable by other system users.
- **Measurement:** File permission checks on database creation
- **Priority:** Medium

**NFR-012: Usability - Backwards Compatibility**
- **Requirement:** Existing commands work identically post-upgrade, no breaking changes to CLI interface.
- **Rationale:** Non-negotiable to avoid alienating existing user base.
- **Measurement:** Regression testing of all existing commands
- **Priority:** Critical

**NFR-013: Usability - Discoverability**
- **Requirement:** New features are discoverable via `--help`, with inline examples and progressive disclosure (basic → advanced).
- **Rationale:** Users should learn features naturally without external docs.
- **Measurement:** User testing, onboarding time tracking
- **Priority:** High

**NFR-014: Maintainability - Test Coverage**
- **Requirement:** Maintain 80%+ code coverage with pytest, all new features fully tested.
- **Rationale:** High test coverage prevents regressions and enables confident refactoring.
- **Measurement:** pytest-cov reports in CI/CD
- **Priority:** High

**NFR-015: Maintainability - Code Quality**
- **Requirement:** Code follows existing style (type hints, docstrings, modular architecture), passes linting (flake8/black).
- **Rationale:** Consistent code quality makes maintenance and contributions easier.
- **Measurement:** Linting in CI/CD, code review standards
- **Priority:** Medium

---

## 3. UI Goals

### Terminal-Specific UX Principles

**3.1 Keyboard-First Interaction**
- **Goal:** All features accessible via keyboard commands with zero mouse dependency
- **Rationale:** Terminal users expect keyboard-driven workflows - mouse interaction breaks CLI paradigm
- **Requirements:**
  - No drag-and-drop interactions (use keyboard commands: `todo move <id> <column>`)
  - Arrow key navigation in interactive modes (KANBAN TUI)
  - Tab completion for commands, projects, cycles (shell integration)
  - Keyboard shortcuts discoverable via help text

**3.2 Visual Hierarchy with ASCII/Unicode**
- **Goal:** Use box-drawing characters, color, and spacing to create clear visual hierarchy in terminal
- **Rationale:** Text-only interface needs structure to be scannable and usable
- **Requirements:**
  - KANBAN board uses Rich panels with box-drawing borders
  - Tree view uses └─, ├─, │ characters for parent-child relationships
  - Color coding: High priority (red), Medium (yellow), Low (blue), Completed (green)
  - Consistent spacing and alignment for tables/lists

**3.3 Information Density Optimization**
- **Goal:** Maximize information density without overwhelming user - balance completeness with scannability
- **Rationale:** Terminal has limited screen real estate (80x24 common), every character counts
- **Requirements:**
  - KANBAN board shows task ID, title (truncated), priority indicator
  - List view shows status icon, ID, title, project, tags, due date (all in one line)
  - Tree view shows indentation, completion status, title
  - Verbose mode (`-v`) for full details when needed

**3.4 Graceful Degradation for Limited Terminals**
- **Goal:** Tool works on basic terminals without Unicode/color support, with degraded but functional UI
- **Rationale:** Some environments (screen, old SSH sessions) lack advanced terminal features
- **Requirements:**
  - Detect terminal capabilities (TERM variable, Rich detection)
  - Fallback to ASCII-only box drawing if Unicode unsupported
  - Fallback to no color if ANSI color unsupported
  - Core functionality unaffected by display limitations

**3.5 Accessibility Considerations**
- **Goal:** Tool is usable with screen readers and accessible to users with visual impairments
- **Rationale:** Terminal tools should be inclusive and standards-compliant
- **Requirements:**
  - Screen reader compatibility (avoid ASCII art that doesn't read well)
  - High contrast color schemes (user-configurable)
  - Text-based output as default (visual embellishments optional)
  - Descriptive error messages and status indicators

**3.6 Responsive Feedback**
- **Goal:** Users receive immediate, clear feedback for all actions
- **Rationale:** CLI users expect instant confirmation that commands succeeded/failed
- **Requirements:**
  - Success messages with clear action confirmation ("Task moved to In Progress")
  - Error messages with actionable guidance ("Invalid column 'WIP'. Valid: backlog, todo, in-progress, review, done")
  - Progress indicators for long operations (>500ms)
  - Status codes (exit 0 for success, non-zero for errors) for scripting

**3.7 Scriptability and Automation**
- **Goal:** All commands designed for both interactive and programmatic use
- **Rationale:** CLI power users script workflows - UI must support automation
- **Requirements:**
  - Machine-readable output formats (JSON, CSV) alongside human-readable (tables, Markdown)
  - Silent mode (`--quiet`) suppresses progress/decoration for piping
  - Exit codes indicate success/failure for scripting error handling
  - Idempotent commands where possible (running twice has same effect as once)

**3.8 Progressive Disclosure**
- **Goal:** Basic commands are simple, advanced features revealed via flags or sub-commands
- **Rationale:** Avoid overwhelming new users while providing power user capabilities
- **Requirements:**
  - `todo list` shows basic view, `todo list --tree` shows hierarchy
  - `todo kanban` shows default board, `--project` filters, `--interactive` enables TUI
  - Help text shows common options first, advanced options in separate section
  - Examples in help demonstrate common workflows before edge cases

### Terminal Rendering Specifications

**3.9 KANBAN Board Layout**
```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│   Backlog    │     Todo     │ In Progress  │    Review    │     Done     │
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ 🔴 #42 Fix   │ 🟡 #15 API   │ 🟡 #8 KANBAN │ 🟢 #3 Tests  │ 🟢 #1 Setup  │
│    auth bug  │    endpoint  │    rendering │    passing   │    complete  │
│              │              │              │              │              │
│ 🔴 #35 Add   │ 🔵 #12 Docs  │              │              │ 🟢 #2 Schema │
│    sub-tasks │    update    │              │              │    migrated  │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```
- **Width:** Dynamically adjusts to terminal width, minimum 80 columns
- **Colors:** Priority-based emoji or ANSI color codes
- **Truncation:** Task titles truncated with "..." if too long for column width
- **Scrolling:** Vertical scrolling if tasks exceed terminal height

**3.10 Tree View Layout**
```
📁 Project: todo-cli-features
  ├─ 🟡 #10 Epic 1: Foundation
  │   ├─ 🟢 #11 Database schema design [done]
  │   ├─ 🟡 #12 Migration framework [in progress]
  │   └─ ⚪ #13 Testing setup
  ├─ 🟡 #20 Epic 2: Sub-tasks
  │   ├─ 🟡 #21 Parent-child relationships [in progress]
  │   └─ ⚪ #22 Tree view command
  └─ ⚪ #30 Epic 3: KANBAN
      ├─ ⚪ #31 Board rendering
      └─ ⚪ #32 Interactive mode
```
- **Icons:** Emoji or ASCII symbols for status, priority
- **Indentation:** 2-4 spaces per level, consistent
- **Collapsing:** Optional `--collapsed` flag to show only top-level (post-MVP)

---

## 4. Technical Assumptions

### 4.1 Technology Stack

**Programming Language:**
- **Assumption:** Python 3.10+ is acceptable for CLI tool performance
- **Validation:** Current todo-cli uses Python successfully; no performance complaints from users
- **Risk:** If Python proves too slow for KANBAN rendering, may need Rust/Go rewrite (low probability)

**Database:**
- **Assumption:** SQLite can handle 10,000+ tasks with acceptable query performance
- **Validation:** SQLite powers applications with millions of rows; proper indexing should suffice
- **Risk:** Complex KANBAN queries with filters may be slow; mitigation via query optimization and caching

**Terminal Rendering:**
- **Assumption:** Rich library provides sufficient capabilities for KANBAN and tree rendering without full TUI framework
- **Validation:** Rich has proven box-drawing, panel, and tree components used in other CLI tools
- **Risk:** May need Textual (Rich's TUI framework) for interactive KANBAN; adds complexity

**Cross-Platform:**
- **Assumption:** Python/SQLite/Rich combo works identically on macOS, Linux, WSL without platform-specific code
- **Validation:** Current todo-cli already cross-platform; libraries used are platform-agnostic
- **Risk:** Terminal emulator differences (box-drawing, Unicode) may require fallback rendering

### 4.2 User Environment

**Terminal Emulators:**
- **Assumption:** Target users run modern terminals (iTerm2, Alacritty, Kitty, GNOME Terminal, Windows Terminal) with Unicode and ANSI color support
- **Validation:** Survey of target demographic shows 90%+ use modern terminals
- **Risk:** Legacy terminal users (screen, basic SSH) may have degraded experience; acceptable with graceful fallback

**Python Installation:**
- **Assumption:** Users have Python 3.10+ installed or can install it
- **Validation:** Python 3.10 released Oct 2021, widely available in package managers
- **Risk:** Some enterprise environments stuck on older Python; acceptable - they can stay on old todo-cli version

**Disk Space:**
- **Assumption:** SQLite database growth (with projects, sub-tasks, cycles) remains under 50MB for typical use (10k tasks, 100 projects)
- **Validation:** Text-based task data compresses well; SQLite overhead is minimal
- **Risk:** None - disk space is non-issue for modern systems

**Network:**
- **Assumption:** No network required (local-only tool)
- **Validation:** Design explicitly avoids cloud sync for MVP
- **Risk:** None

### 4.3 Development Environment

**Testing Framework:**
- **Assumption:** pytest with pytest-cov is sufficient for comprehensive testing
- **Validation:** Current todo-cli uses pytest successfully; industry-standard for Python
- **Risk:** None - pytest is mature and well-documented

**CI/CD:**
- **Assumption:** GitHub Actions free tier provides adequate CI/CD for testing and PyPI publishing
- **Validation:** Many open-source Python projects use GitHub Actions successfully
- **Risk:** Build time limits on free tier (acceptable for small project)

**Distribution:**
- **Assumption:** PyPI package distribution via `pip install todo-cli` is primary installation method
- **Validation:** Current distribution method, widely understood by target users
- **Risk:** May want Homebrew/apt packages later for easier installation; deferrable to post-MVP

### 4.4 Performance Assumptions

**Command Execution:**
- **Assumption:** <100ms execution for list operations achievable with Python/SQLite
- **Validation:** Current todo-cli meets this target; new features shouldn't drastically increase overhead
- **Risk:** KANBAN rendering may take 200-500ms; acceptable if under 500ms threshold

**KANBAN Rendering:**
- **Assumption:** <500ms rendering for 1000+ task KANBAN board is achievable with query optimization
- **Validation:** Rich rendering is fast (uses ANSI escape codes); database query is bottleneck
- **Risk:** May need query result caching for very large boards; acceptable optimization

**Interactive Mode:**
- **Assumption:** <50ms refresh for interactive KANBAN is achievable with differential rendering
- **Validation:** Textual framework (if used) has proven performance for TUIs
- **Risk:** May require optimization or defer to post-MVP if too complex

### 4.5 Data Model Assumptions

**Task Volume:**
- **Assumption:** Users will have 100-5,000 tasks typically, with power users reaching 10,000+
- **Validation:** Anecdotal data from taskwarrior, org-mode users
- **Risk:** If users exceed 10k tasks regularly, may need database optimization or archival features

**Hierarchy Depth:**
- **Assumption:** 1-level parent-child hierarchy (MVP) satisfies 80%+ of use cases
- **Validation:** Most PM tools show features broken into tasks (2 levels), not deeper
- **Risk:** Users may demand 2-3 level nesting; acceptable to defer to post-MVP

**Cycle Duration:**
- **Assumption:** 1-4 week cycles cover typical sprint lengths (1 week, 2 week, 1 month)
- **Validation:** Linear, Scrum, and agile literature support these durations
- **Risk:** Some teams use non-standard cycles (3 weeks, 6 weeks); acceptable - configurable in post-MVP

**Concurrent Cycles:**
- **Assumption:** Users only need one active cycle at a time (MVP)
- **Validation:** Linear's model (one cycle at a time) is simpler and popular
- **Risk:** Multi-team users may want parallel cycles; deferrable to post-MVP

### 4.6 Migration Assumptions

**Schema Evolution:**
- **Assumption:** Database migrations can be handled via simple Python scripts without Alembic or complex migration framework
- **Validation:** Schema changes are additive (new tables, new columns with defaults) for MVP
- **Risk:** Future breaking changes may require migration framework; acceptable to add later

**Backwards Compatibility:**
- **Assumption:** All existing todo-cli data and commands can remain functional with new schema
- **Validation:** New tables are separate; existing todos table gets new columns with defaults
- **Risk:** If existing commands conflict with new features, may need careful design; mitigated by design review

**User Adoption:**
- **Assumption:** Users will upgrade to new version voluntarily via `pip install --upgrade todo-cli`
- **Validation:** Standard Python package upgrade process
- **Risk:** Users may not upgrade; acceptable - old version continues working

### 4.7 Dependency Assumptions

**Rich Library:**
- **Assumption:** Rich library is stable and maintained, suitable for production use
- **Validation:** Rich is widely used, actively maintained, 47k+ GitHub stars
- **Risk:** Rich API changes could break rendering; mitigated by pinning version ranges

**python-dateutil:**
- **Assumption:** python-dateutil provides adequate date/time manipulation for cycle management
- **Validation:** Industry-standard library for Python date operations
- **Risk:** None - extremely stable library

**Minimal Dependencies:**
- **Assumption:** Limiting dependencies to Typer, Rich, python-dateutil (+ existing pyyaml) minimizes installation friction and security surface
- **Validation:** Fewer dependencies = faster installs, less breakage
- **Risk:** May need additional libraries for advanced features; acceptable to add selectively

---

## 5. Epic List

### Epic 1: Foundation & Enhanced Project Management
**Goal:** Establish the architectural foundation for new features and implement first-class project support.

**Scope:**
- Database schema extensions (projects, sub-tasks, cycles, cycle_tasks tables)
- Migration framework for schema evolution
- Project CRUD operations (create, read, update, delete)
- Project-centric filtering across existing commands
- Testing framework extensions

**Success Criteria:**
- Database migrations run successfully on existing todo-cli installations
- Users can create and manage projects via CLI
- All existing commands support `--project` filtering
- Test coverage maintained at 80%+

**Dependencies:** None (foundation for all other epics)

**Estimated Effort:** 5 stories, ~15-20 hours total

---

### Epic 2: Hierarchical Task Organization
**Goal:** Enable users to break down large features into manageable sub-tasks with visual hierarchy.

**Scope:**
- Parent-child task relationships (1 level deep)
- Sub-task CRUD operations (add, list, delete)
- Tree visualization using Rich library
- Parent task completion logic (requires all children complete)
- Hierarchical filtering and display

**Success Criteria:**
- Users can create sub-tasks under any task
- Tree view renders clearly with box-drawing characters
- Parent-child relationships preserved in database
- Sub-task operations feel intuitive and fast

**Dependencies:** Epic 1 (database foundation)

**Estimated Effort:** 6 stories, ~18-24 hours total

---

### Epic 3: KANBAN Board Visualization
**Goal:** Provide terminal-based visual workflow representation with KANBAN board rendering.

**Scope:**
- KANBAN board rendering using Rich panels and box-drawing
- Column management (move tasks between workflow states)
- Board filtering (by project, priority, tags)
- Performance optimization for large boards (1000+ tasks)
- Optional interactive mode with keyboard navigation (TUI)

**Success Criteria:**
- KANBAN board renders clearly in standard 80-column terminal
- Board renders in <500ms for 1000+ tasks
- Users prefer KANBAN view for project overview (user survey)
- Column movements are intuitive and fast

**Dependencies:** Epic 1 (project filtering), Epic 2 (optional: show sub-tasks in board)

**Estimated Effort:** 7 stories, ~21-28 hours total

---

### Epic 4: Cycle Management & Reporting
**Goal:** Enable Linear-style iteration planning with cycle creation, task assignment, and progress reporting.

**Scope:**
- Cycle CRUD operations (create, list, close)
- Task assignment to cycles
- Cycle progress tracking (tasks completed/remaining)
- Cycle reporting (Markdown, JSON export)
- Auto-rolling cycle transitions (post-MVP)

**Success Criteria:**
- Users can plan and track sprints entirely in CLI
- Cycle reports provide valuable team visibility
- Export formats integrate with existing tools (Slack, docs)
- Cycles drive measurable improvement in task completion rates

**Dependencies:** Epic 1 (database foundation), Epic 3 (optional: KANBAN filtered by cycle)

**Estimated Effort:** 7 stories, ~21-28 hours total

---

### Epic Sequencing

**Sequence Rationale:**
1. **Epic 1 first** - Foundation is prerequisite for all features
2. **Epic 2 or Epic 3 next** - Can be done in parallel or either order:
   - Epic 2 (Sub-tasks) is simpler, good for early validation
   - Epic 3 (KANBAN) is higher user-visible value
3. **Epic 4 last** - Depends on Epic 1, enhanced by Epic 3 (KANBAN filtered by cycle)

**Iterative Releases:**
- **Alpha:** Epic 1 only (foundation + projects)
- **Beta:** Epics 1-2 (projects + sub-tasks)
- **RC:** Epics 1-3 (projects + sub-tasks + KANBAN)
- **v1.0:** All 4 epics (full MVP)

---

## 6. Epic Details

### Epic 1: Foundation & Enhanced Project Management

**Epic Goal:** Establish the architectural foundation for new features and implement first-class project support, enabling users to organize tasks by project with dedicated project-centric commands and filtering.

#### Story 1.1: Database Schema Design & Migration Framework

**As a** developer,
**I want** the database schema extended to support projects, sub-tasks, and cycles with a robust migration framework,
**So that** I can add new features without breaking existing user data and ensure schema evolution is safe and reversible.

**Acceptance Criteria:**
1. New tables created:
   - `projects` (id, name, description, status, created_at)
   - `subtasks` (parent_id, child_id, position)
   - `cycles` (id, name, start_date, end_date, status, created_at)
   - `cycle_tasks` (cycle_id, task_id)
2. `todos` table extended with `kanban_column` (default 'backlog')
3. Foreign key constraints enforced (CASCADE on delete)
4. Indexes created for:
   - `projects.name` (UNIQUE)
   - `todos.kanban_column`
   - `subtasks.parent_id`, `subtasks.child_id`
   - `cycles.status`
   - `cycle_tasks.cycle_id`, `cycle_tasks.task_id`
5. Migration script detects existing database version and applies migrations
6. Migration is idempotent (running twice is safe)
7. Rollback capability exists if migration fails
8. All tests pass with new schema

**Technical Notes:**
- Use SQLite `PRAGMA user_version` for version tracking
- Migration scripts in `todo_cli/migrations/` directory
- Each migration is a Python function: `def migrate_v1_to_v2(conn):`
- Transaction-wrapped migrations (rollback on error)

**Testing Requirements:**
- Test migration from empty database (new install)
- Test migration from existing v1 database
- Test migration rollback on simulated failure
- Test foreign key constraint enforcement

**Estimated Effort:** 3-4 hours

---

#### Story 1.2: Project CRUD Operations

**As a** developer,
**I want** to create, list, update, and delete projects via CLI commands,
**So that** I can organize my tasks into logical groupings that match my codebases or initiatives.

**Acceptance Criteria:**
1. `todo project create <name> [--description <text>]` creates new project
2. `todo project list` shows all projects with:
   - Project name
   - Task count (total, active, completed)
   - Status (active, archived)
   - Created date
3. `todo project show <name>` displays project details and all associated tasks
4. `todo project update <name> [--description <text>] [--status <active|archived>]` updates metadata
5. `todo project delete <name>` removes project (with confirmation prompt)
6. Deleting project does NOT delete tasks (tasks become unassigned)
7. Project names are unique and case-insensitive
8. Error handling:
   - Duplicate project name
   - Project not found
   - Invalid status

**Technical Notes:**
- New module: `todo_cli/projects.py`
- Database operations in `database.py` extended
- Use Rich tables for project list display

**Testing Requirements:**
- Test CRUD operations
- Test uniqueness constraint
- Test task count calculations
- Test deletion behavior (tasks persist)

**Estimated Effort:** 2-3 hours

---

#### Story 1.3: Project Filtering Across Commands

**As a** developer,
**I want** to filter all todo commands by project using `--project` flag,
**So that** I can focus on tasks for a specific codebase or initiative without seeing unrelated tasks.

**Acceptance Criteria:**
1. `--project <name>` flag added to:
   - `todo add` (assign task to project on creation)
   - `todo list` (show only project tasks)
   - `todo complete` (complete tasks in project)
   - All existing commands that operate on tasks
2. `todo list --project myapp` shows only tasks assigned to "myapp" project
3. `todo add "Fix bug" --project myapp` creates task in project
4. Project filtering can combine with other filters (status, priority, tags)
5. Invalid project name shows error with available projects
6. Empty result set shows clear message: "No tasks found for project 'myapp'"

**Technical Notes:**
- Extend CLI argument parsing in `main.py`
- Update database query functions to accept `project` filter
- Project filtering uses JOIN or WHERE clause on `todos.project` column

**Testing Requirements:**
- Test filtering with single project
- Test combining filters (project + status + priority)
- Test error handling (invalid project)
- Test empty result sets

**Estimated Effort:** 2-3 hours

---

#### Story 1.4: Performance Benchmarking & Optimization

**As a** developer,
**I want** to validate that database performance meets requirements with realistic datasets,
**So that** I can identify and fix performance bottlenecks before they affect users.

**Acceptance Criteria:**
1. Test dataset created with:
   - 10,000 tasks
   - 100 projects
   - 50 cycles
   - Realistic distribution (80% complete, 20% active)
2. Benchmark script measures:
   - `todo list` execution time
   - `todo list --project <name>` execution time
   - Project list with task counts
   - KANBAN query performance (Epic 3 dependency)
3. All queries complete within performance targets:
   - `todo list`: <100ms
   - `todo list --project`: <100ms
   - `todo project list`: <200ms
4. Slow queries identified via SQLite EXPLAIN QUERY PLAN
5. Indexes added as needed to meet performance targets
6. Benchmark results documented in `docs/performance.md`

**Technical Notes:**
- Benchmark script: `tests/benchmark.py`
- Use `time` module for execution timing
- Run benchmarks in CI/CD on each release

**Testing Requirements:**
- Benchmark with 1k, 5k, 10k, 50k task datasets
- Validate index usage via EXPLAIN QUERY PLAN
- Confirm no performance regression vs. baseline

**Estimated Effort:** 3-4 hours

---

#### Story 1.5: Testing Framework Extensions

**As a** developer,
**I want** comprehensive test coverage for all new features with clear testing patterns,
**So that** I can prevent regressions and maintain code quality as the project grows.

**Acceptance Criteria:**
1. New test modules created:
   - `tests/test_projects.py` (project CRUD, filtering)
   - `tests/test_migrations.py` (schema migration, rollback)
   - `tests/test_performance.py` (benchmarking)
2. Test fixtures for:
   - Empty database (new install)
   - Populated database (existing tasks)
   - Large database (10k tasks for performance tests)
3. Test helpers:
   - `create_project(name, **kwargs)` fixture
   - `create_task_batch(count, project=None)` fixture
   - `assert_migration_success(from_version, to_version)` helper
4. All tests pass with coverage >80% for new code
5. CI/CD runs full test suite on Python 3.10, 3.11, 3.12
6. Tests run in <30 seconds locally (excluding performance benchmarks)

**Technical Notes:**
- Use pytest fixtures in `tests/conftest.py`
- Mock database operations where appropriate for speed
- Separate performance tests into `tests/benchmark/` (run separately)

**Testing Requirements:**
- Test isolation (each test has clean database)
- Test performance (suite completes in <30s)
- Test cross-platform (macOS, Linux via CI/CD)

**Estimated Effort:** 2-3 hours

---

### Epic 2: Hierarchical Task Organization

**Epic Goal:** Enable users to break down large features into manageable sub-tasks with visual hierarchy, supporting 1-level parent-child relationships and tree visualization.

#### Story 2.1: Parent-Child Task Relationship Model

**As a** developer,
**I want** to define parent-child relationships between tasks in the database,
**So that** I can represent feature breakdowns and track granular progress without losing context of the larger goal.

**Acceptance Criteria:**
1. `subtasks` table enforces:
   - Foreign key: `parent_id` → `todos.id`
   - Foreign key: `child_id` → `todos.id`
   - CHECK constraint: `parent_id != child_id` (no self-reference)
   - Unique constraint: `(parent_id, child_id)`
2. Database queries support:
   - Get all children of parent: `SELECT * FROM todos JOIN subtasks ON todos.id = subtasks.child_id WHERE parent_id = ?`
   - Get parent of child: `SELECT * FROM todos JOIN subtasks ON todos.id = subtasks.parent_id WHERE child_id = ?`
   - Check if task has children: `SELECT COUNT(*) FROM subtasks WHERE parent_id = ?`
3. Circular references prevented (no A → B → A chains)
4. Nesting depth limited to 1 level (MVP constraint):
   - Task with children cannot become a child itself
   - Error if attempting to add sub-task to task that's already a sub-task
5. Cascade delete: deleting parent removes relationships (but children remain as top-level tasks)

**Technical Notes:**
- Trigger or application logic prevents depth >1
- `position` column allows ordering children (for future use)
- Circular reference check via recursive query (deferred to post-MVP if complex)

**Testing Requirements:**
- Test parent-child creation
- Test depth constraint enforcement
- Test circular reference prevention
- Test cascade delete behavior

**Estimated Effort:** 3-4 hours

---

#### Story 2.2: Sub-Task Creation Command

**As a** developer,
**I want** to add sub-tasks to an existing task via CLI command,
**So that** I can break down large features into smaller, manageable pieces.

**Acceptance Criteria:**
1. `todo add-subtask <parent-id> "<description>" [flags]` creates sub-task
2. Sub-task inherits properties from parent by default:
   - Project (can be overridden with `--project`)
   - Tags (can be extended with `--tag`)
3. Sub-task has its own:
   - Priority (default: same as parent, overridable with `--priority`)
   - Status (default: pending)
   - Due date (optional, independent of parent)
4. Command validates:
   - Parent task exists
   - Parent is not already a sub-task (depth constraint)
5. Success message: "Sub-task #42 added under #10 'Implement KANBAN'"
6. Error handling:
   - Parent task not found
   - Parent is a sub-task (cannot nest deeper)

**Technical Notes:**
- New command in `main.py`: `@app.command("add-subtask")`
- Validation logic in `subtasks.py` module
- Database insert: both `todos` and `subtasks` tables (transaction-wrapped)

**Testing Requirements:**
- Test sub-task creation with various flags
- Test inheritance of project/tags
- Test depth constraint enforcement
- Test error cases (invalid parent, already sub-task)

**Estimated Effort:** 2-3 hours

---

#### Story 2.3: Tree View Rendering

**As a** developer,
**I want** to view my tasks in a hierarchical tree format,
**So that** I can see parent-child relationships visually and understand feature breakdown at a glance.

**Acceptance Criteria:**
1. `todo list --tree` renders tasks in hierarchical format using Rich Tree
2. Tree structure shows:
   - Parent tasks at root level
   - Children indented with box-drawing characters (`└─`, `├─`, `│`)
   - Status icons (emoji or symbols): ✅ complete, 🟡 in progress, ⬜ pending
   - Task ID, title, priority indicator
3. Tree view supports filtering:
   - `--project <name>`: Show only project tasks in tree
   - `--status <status>`: Filter by status (applies to all levels)
4. Completion status propagation:
   - Parent shows "(2/5)" children completed
   - Parent marked complete only if all children complete
5. Tree renders quickly (<200ms for 1000+ tasks)

**Technical Notes:**
- Use `rich.tree.Tree` for rendering
- Recursive query to build tree structure: parent → children
- Color coding: priority colors, completion status colors

**Testing Requirements:**
- Test tree rendering with various depths
- Test filtering (project, status)
- Test completion status display
- Test performance with large datasets

**Estimated Effort:** 3-4 hours

---

#### Story 2.4: Sub-Task Listing and Filtering

**As a** developer,
**I want** to list all sub-tasks for a specific parent or filter sub-tasks globally,
**So that** I can review task breakdowns and find specific sub-tasks quickly.

**Acceptance Criteria:**
1. `todo list --parent <parent-id>` shows only children of specified parent
2. `todo list --has-children` shows only parent tasks (tasks with sub-tasks)
3. `todo list --is-subtask` shows only sub-tasks (children of other tasks)
4. Default `todo list` shows:
   - Option A: All tasks flat (no hierarchy)
   - Option B: Parent tasks with indented children (mini-tree)
5. Sub-task count indicator: "Feature X (3 sub-tasks)"
6. Filtering combines with existing filters (project, status, priority)

**Technical Notes:**
- Add `--parent`, `--has-children`, `--is-subtask` flags
- Database queries use `subtasks` JOIN
- Consider default display: flat vs. hierarchical (user feedback needed)

**Testing Requirements:**
- Test parent filtering
- Test has-children filtering
- Test is-subtask filtering
- Test combined filters

**Estimated Effort:** 2-3 hours

---

#### Story 2.5: Parent Task Completion Logic

**As a** developer,
**I want** parent tasks to auto-complete only when all sub-tasks are complete,
**So that** I have accurate high-level progress tracking without manual status management.

**Acceptance Criteria:**
1. `todo complete <parent-id>` validates:
   - If task has incomplete children → error: "Cannot complete #10. Incomplete sub-tasks: #11, #12"
   - If task has no children → completes normally
   - If all children complete → completes parent
2. Completing last child auto-completes parent:
   - `todo complete <child-id>` checks if it's the last incomplete child
   - If yes, auto-completes parent and shows message: "Task #42 completed. Parent #10 also completed."
3. `todo complete --force <parent-id>` overrides and completes parent regardless (with warning)
4. Uncompleting child auto-uncompletes parent:
   - `todo uncomplete <child-id>` also uncompletes parent if parent was complete
   - Message: "Task #42 uncompleted. Parent #10 also uncompleted."

**Technical Notes:**
- Completion validation in `database.py` or `subtasks.py`
- Trigger or application logic for auto-completion
- Transaction-wrapped (parent + child updates)

**Testing Requirements:**
- Test completion with incomplete children (error)
- Test auto-completion of parent
- Test force completion
- Test uncomplete cascade

**Estimated Effort:** 3-4 hours

---

#### Story 2.6: Sub-Task Deletion and Orphan Handling

**As a** developer,
**I want** to delete sub-tasks or break parent-child relationships,
**So that** I can reorganize task structures as my project evolves.

**Acceptance Criteria:**
1. `todo delete <sub-task-id>` deletes sub-task and relationship:
   - Sub-task removed from `todos` table
   - Relationship removed from `subtasks` table
   - Parent task unaffected
2. `todo delete <parent-id>` deletes parent:
   - Children remain as top-level tasks (orphaned)
   - Relationships removed from `subtasks` table
   - Message: "Task #10 deleted. 3 sub-tasks promoted to top-level."
3. `todo unlink <child-id>` breaks parent-child relationship without deleting:
   - Relationship removed from `subtasks`
   - Child becomes top-level task
   - Message: "Task #42 unlinked from parent #10"
4. Confirmation prompts for:
   - Deleting parent with children
   - Unlinking sub-tasks

**Technical Notes:**
- Cascade behavior controlled by foreign key ON DELETE CASCADE
- `unlink` command is new, separate from `delete`
- Transaction-wrapped for consistency

**Testing Requirements:**
- Test sub-task deletion
- Test parent deletion (orphaning children)
- Test unlink operation
- Test confirmation prompts

**Estimated Effort:** 2-3 hours

---

### Epic 3: KANBAN Board Visualization

**Epic Goal:** Provide terminal-based visual workflow representation with KANBAN board rendering, enabling users to see task status at a glance and move tasks between columns via keyboard commands.

#### Story 3.1: KANBAN Board Rendering Engine

**As a** developer,
**I want** to render a KANBAN board in the terminal using box-drawing characters and Rich panels,
**So that** I can visualize workflow state (Backlog, Todo, In Progress, Review, Done) without leaving the CLI.

**Acceptance Criteria:**
1. `todo kanban` renders board with 5 default columns:
   - Backlog, Todo, In Progress, Review, Done
2. Board layout:
   - Columns are Rich Panel objects with borders
   - Each task shows: ID, title (truncated to fit), priority indicator
   - Priority color coding: 🔴 High, 🟡 Medium, 🔵 Low, 🟢 Completed
3. Board adapts to terminal width:
   - Minimum 80 columns
   - Columns dynamically sized (equal width or weighted)
   - Horizontal scrolling if needed (or wrap to multiple rows)
4. Vertical scrolling:
   - If tasks exceed terminal height, show "... X more tasks" footer
   - Optional: scroll with arrow keys in interactive mode (future)
5. Performance:
   - Renders in <500ms for 1000 tasks
   - Renders in <200ms for 100 tasks
6. Empty columns show placeholder: "(no tasks)"

**Technical Notes:**
- Use `rich.layout.Layout` or `rich.columns.Columns` for column arrangement
- Use `rich.panel.Panel` for each column
- Query: `SELECT * FROM todos ORDER BY kanban_column, priority, created_at`
- Rendering logic in `todo_cli/kanban.py`

**Testing Requirements:**
- Test rendering with various task counts (0, 10, 100, 1000)
- Test terminal width adaptation (80, 120, 160 columns)
- Test empty columns
- Test performance benchmarks

**Estimated Effort:** 4-5 hours

---

#### Story 3.2: KANBAN Column Movement

**As a** developer,
**I want** to move tasks between KANBAN columns via CLI command,
**So that** I can update task workflow state quickly without opening a GUI tool.

**Acceptance Criteria:**
1. `todo move <task-id> <column>` updates task's `kanban_column`
2. Valid column names (case-insensitive):
   - backlog, todo, in-progress (or in_progress), review, done
3. Moving to "done" auto-completes task:
   - Sets `status = 'completed'`
   - Sets `completed_at = NOW()`
   - Message: "Task #42 moved to Done and marked complete"
4. Moving from "done" to other column uncompletes task:
   - Sets `status = 'pending'`
   - Clears `completed_at`
   - Message: "Task #42 moved to In Progress and marked incomplete"
5. Error handling:
   - Invalid column name → show valid options
   - Task not found → clear error message
6. Success message: "Task #42 'Fix auth bug' moved to In Progress"

**Technical Notes:**
- Update query: `UPDATE todos SET kanban_column = ? WHERE id = ?`
- Status synchronization logic (done ↔ completed)
- Validation: `kanban_column IN ('backlog', 'todo', 'in-progress', 'review', 'done')`

**Testing Requirements:**
- Test moving between all columns
- Test auto-completion on "done"
- Test uncomplete on move from "done"
- Test error handling (invalid column, task not found)

**Estimated Effort:** 2-3 hours

---

#### Story 3.3: KANBAN Filtering (Project, Priority, Tags)

**As a** developer,
**I want** to filter the KANBAN board by project, priority, or tags,
**So that** I can focus on specific work contexts and reduce visual noise.

**Acceptance Criteria:**
1. `todo kanban --project <name>` shows only tasks in specified project
2. `todo kanban --priority <high|medium|low>` shows only tasks with specified priority
3. `todo kanban --tag <tag>` shows only tasks with specified tag
4. Filters can be combined:
   - `todo kanban --project myapp --priority high`
   - Shows high-priority tasks in "myapp" project
5. Filtered board shows counts: "KANBAN Board (Project: myapp, Priority: high) - 15 tasks"
6. Empty filter results show: "No tasks match filters. Remove filters to see all tasks."

**Technical Notes:**
- Extend `kanban.py` to accept filter parameters
- Database query: `WHERE project = ? AND priority = ? AND tags LIKE ?`
- Filter combination uses AND logic (all must match)

**Testing Requirements:**
- Test single filters (project, priority, tag)
- Test combined filters
- Test empty results
- Test filter counts displayed correctly

**Estimated Effort:** 2-3 hours

---

#### Story 3.4: KANBAN Performance Optimization

**As a** developer,
**I want** KANBAN board rendering to be fast even with large datasets,
**So that** the tool remains responsive and usable as my task list grows to 1000+ items.

**Acceptance Criteria:**
1. Benchmark rendering with datasets:
   - 100 tasks: <100ms
   - 1,000 tasks: <300ms
   - 5,000 tasks: <500ms
   - 10,000 tasks: <1000ms (acceptable degradation)
2. Optimization techniques applied:
   - Database indexes on `kanban_column`, `project`, `priority`
   - Limit tasks per column (show top 20 + "... X more" link)
   - Lazy loading for large columns (future: interactive mode)
3. Query optimization:
   - Use single query to fetch all tasks: `SELECT * FROM todos WHERE ... ORDER BY kanban_column`
   - Group tasks by column in Python (fast in-memory operation)
   - Avoid N+1 queries (one query per column)
4. EXPLAIN QUERY PLAN shows index usage
5. Performance regression tests in CI/CD

**Technical Notes:**
- Add indexes: `CREATE INDEX idx_kanban_column ON todos(kanban_column)`
- Consider result caching for repeated `todo kanban` calls (future)
- Pagination for columns with >20 tasks (show top 20, hide rest)

**Testing Requirements:**
- Benchmark with large datasets
- Validate index usage via EXPLAIN QUERY PLAN
- Test pagination/truncation for large columns
- Regression testing in CI/CD

**Estimated Effort:** 3-4 hours

---

#### Story 3.5: KANBAN Sub-Task Display (Optional)

**As a** developer,
**I want** to see sub-tasks indented under parent tasks in KANBAN columns,
**So that** I can understand task breakdown without switching to tree view.

**Acceptance Criteria:**
1. KANBAN board shows parent tasks with children indented:
   ```
   In Progress
   ├─────────────────┤
   │ #10 Feature X   │
   │   ├─ #11 Part A │
   │   └─ #12 Part B │
   │ #20 Feature Y   │
   └─────────────────┘
   ```
2. Sub-tasks appear in parent's column (not independently placed)
3. Sub-task completion indicator: "Feature X (2/3 done)"
4. Option to collapse sub-tasks: `todo kanban --collapsed` shows only parents
5. Performance: sub-task display adds <100ms overhead

**Technical Notes:**
- Query with JOIN to fetch parent-child relationships
- Rendering logic in `kanban.py` to indent children
- Use `rich.tree.Tree` within panel for hierarchical display (or simple indentation)

**Testing Requirements:**
- Test sub-task display in board
- Test collapsed mode
- Test performance with hierarchical tasks
- Test empty sub-task lists

**Estimated Effort:** 3-4 hours

---

#### Story 3.6: KANBAN Interactive Mode (TUI) [Optional]

**As a** developer,
**I want** to interact with the KANBAN board using arrow keys and keyboard shortcuts,
**So that** I can update task states quickly without typing multiple commands.

**Acceptance Criteria:**
1. `todo kanban --interactive` launches TUI mode using Textual
2. Keyboard navigation:
   - Arrow keys: navigate between tasks and columns
   - Enter: move selected task to focused column
   - Tab: switch between columns
   - ESC: exit interactive mode
3. Real-time updates:
   - Board refreshes on task movement (<50ms)
   - Highlighting shows selected task and focused column
4. Actions available:
   - Move task to column
   - View task details (popup)
   - Edit task inline (future)
5. TUI supports filtering (project, priority) via command-line flags

**Technical Notes:**
- Use Textual framework (Rich's TUI extension)
- Event handlers for keyboard input
- Differential rendering for performance
- Graceful fallback if Textual not installed (optional dependency)

**Testing Requirements:**
- Test keyboard navigation
- Test task movement
- Test refresh performance
- Test filtering in interactive mode

**Estimated Effort:** 4-5 hours (deferred to post-MVP if time-constrained)

---

#### Story 3.7: KANBAN Configuration (Column Customization) [Post-MVP]

**As a** developer,
**I want** to customize KANBAN column names and ordering via config file,
**So that** the board matches my team's workflow terminology (e.g., "Doing" instead of "In Progress").

**Acceptance Criteria:**
1. Config file: `~/.config/todo-cli/config.yaml` defines columns:
   ```yaml
   kanban:
     columns:
       - backlog
       - todo
       - doing
       - review
       - done
   ```
2. Custom column names used in board rendering
3. `todo move <task-id> <custom-column>` works with custom names
4. Default columns used if config file missing
5. Invalid config shows error with default fallback

**Technical Notes:**
- Load config via PyYAML
- Validate column names (no duplicates, no spaces)
- Update database schema to support custom columns (or map to fixed internal columns)

**Testing Requirements:**
- Test custom column names
- Test invalid config handling
- Test default fallback
- Test move command with custom columns

**Estimated Effort:** 2-3 hours (deferred to post-MVP)

---

### Epic 4: Cycle Management & Reporting

**Epic Goal:** Enable Linear-style iteration planning with cycle creation, task assignment, progress tracking, and reporting, allowing users to plan sprints and track velocity entirely from the CLI.

#### Story 4.1: Cycle Creation and Listing

**As a** developer,
**I want** to create fixed-length cycles (iterations/sprints) with start and end dates,
**So that** I can time-box my work and plan releases in structured iterations.

**Acceptance Criteria:**
1. `todo cycle create <name> --duration <weeks>` creates new cycle:
   - Start date: today (or specified with `--start-date`)
   - End date: calculated from duration (1, 2, or 4 weeks)
   - Status: active
2. `todo cycle create <name> --start-date 2025-01-01 --end-date 2025-01-14` creates custom dates
3. `todo cycle list` shows all cycles:
   - Cycle name
   - Start date, end date
   - Status (active, closed)
   - Task count (total, completed)
   - Days remaining (for active cycles)
4. Only one active cycle at a time (MVP constraint):
   - Creating new cycle while one is active → error or auto-close previous (user choice)
5. Cycle names are unique

**Technical Notes:**
- Use `python-dateutil` for date calculations
- Duration stored as weeks (1, 2, 4)
- Status: 'active' or 'closed'
- Query: `SELECT * FROM cycles ORDER BY start_date DESC`

**Testing Requirements:**
- Test cycle creation with various durations
- Test custom date ranges
- Test uniqueness constraint
- Test active cycle limit

**Estimated Effort:** 3-4 hours

---

#### Story 4.2: Task Assignment to Cycles

**As a** developer,
**I want** to assign tasks to the current or a specific cycle,
**So that** I can plan what work I'll complete in this iteration.

**Acceptance Criteria:**
1. `todo cycle assign <task-id>` assigns task to active cycle
2. `todo cycle assign <task-id> --cycle <name>` assigns to specific cycle
3. `todo add "Task" --cycle <name>` creates task and assigns to cycle
4. `todo cycle unassign <task-id>` removes task from cycle (returns to backlog)
5. Task can only be in one cycle at a time:
   - Assigning to new cycle removes from previous cycle
   - Warning message: "Task #42 moved from 'Sprint 1' to 'Sprint 2'"
6. `todo list --cycle <name>` shows all tasks in cycle
7. Cycle assignment visible in `todo list` output: "[Sprint 2]"

**Technical Notes:**
- Insert into `cycle_tasks` table: `(cycle_id, task_id)`
- Unique constraint on `task_id` ensures single cycle assignment
- Query: `SELECT * FROM todos JOIN cycle_tasks ON todos.id = cycle_tasks.task_id WHERE cycle_id = ?`

**Testing Requirements:**
- Test assignment to active cycle
- Test assignment to specific cycle
- Test unassignment
- Test single-cycle constraint
- Test list filtering by cycle

**Estimated Effort:** 2-3 hours

---

#### Story 4.3: Cycle Progress Tracking

**As a** developer,
**I want** to view the current cycle's progress (tasks completed vs. remaining),
**So that** I can understand if I'm on track to complete my sprint goals.

**Acceptance Criteria:**
1. `todo cycle current` shows active cycle overview:
   - Cycle name, start/end dates
   - Days elapsed / Days remaining
   - Tasks: total, completed, remaining
   - Completion percentage
   - List of incomplete tasks (top 10 + "... X more")
2. Visual progress bar:
   ```
   Sprint 2 (Jan 1 - Jan 14)
   Progress: [████████░░░░░░░░░░] 40% (4/10 tasks)
   Days: 5 elapsed, 9 remaining
   ```
3. Warning for overdue cycles:
   - If today > end_date and status = active → "⚠️  Cycle overdue by 3 days"
4. No active cycle → message: "No active cycle. Create one with 'todo cycle create'"

**Technical Notes:**
- Calculate progress: `(completed / total) * 100`
- Date math: `(end_date - today).days`
- Use Rich progress bar for visual display

**Testing Requirements:**
- Test progress calculation
- Test date calculations (elapsed, remaining)
- Test overdue warning
- Test no active cycle case

**Estimated Effort:** 2-3 hours

---

#### Story 4.4: Cycle Reporting (Markdown Export)

**As a** developer,
**I want** to generate a Markdown report of cycle results,
**So that** I can share sprint summaries with my team via Slack, GitHub, or documentation.

**Acceptance Criteria:**
1. `todo cycle report` generates Markdown report for active cycle:
   ```markdown
   # Sprint 2 Report (Jan 1 - Jan 14)

   **Status:** Active (9 days remaining)
   **Completion:** 40% (4/10 tasks)

   ## Completed Tasks
   - ✅ #42 Fix auth bug (High)
   - ✅ #35 Add sub-tasks (Medium)

   ## Remaining Tasks
   - ⬜ #15 API endpoint (High)
   - ⬜ #8 KANBAN rendering (Medium)

   ## Summary
   - Velocity: 0.8 tasks/day
   - At current pace, will complete 7/10 tasks by end date
   ```
2. `todo cycle report --cycle <name>` generates report for specific cycle
3. `todo cycle report --format md` outputs Markdown (default)
4. Report can be piped to file: `todo cycle report > sprint2.md`
5. Report includes:
   - Cycle metadata (name, dates, status)
   - Completion stats
   - Completed tasks list (with priority)
   - Remaining tasks list
   - Velocity calculation (tasks/day)
   - Forecast (projected completion)

**Technical Notes:**
- Template in `todo_cli/templates/cycle_report.md.j2` (Jinja2) or f-strings
- Velocity: `completed_tasks / days_elapsed`
- Forecast: `total_tasks / velocity`

**Testing Requirements:**
- Test Markdown generation
- Test velocity calculation
- Test forecast accuracy
- Test piping to file

**Estimated Effort:** 3-4 hours

---

#### Story 4.5: Cycle Reporting (JSON Export)

**As a** developer,
**I want** to export cycle data as JSON,
**So that** I can integrate with scripts, dashboards, or external tools.

**Acceptance Criteria:**
1. `todo cycle report --format json` outputs structured JSON:
   ```json
   {
     "cycle": {
       "name": "Sprint 2",
       "start_date": "2025-01-01",
       "end_date": "2025-01-14",
       "status": "active",
       "days_elapsed": 5,
       "days_remaining": 9
     },
     "progress": {
       "total_tasks": 10,
       "completed": 4,
       "remaining": 6,
       "completion_percentage": 40,
       "velocity": 0.8
     },
     "completed_tasks": [
       {"id": 42, "title": "Fix auth bug", "priority": "high"},
       {"id": 35, "title": "Add sub-tasks", "priority": "medium"}
     ],
     "remaining_tasks": [
       {"id": 15, "title": "API endpoint", "priority": "high"},
       {"id": 8, "title": "KANBAN rendering", "priority": "medium"}
     ]
   }
   ```
2. JSON is valid and parseable
3. JSON can be piped to file or tools: `todo cycle report --format json | jq '.progress.completion_percentage'`

**Technical Notes:**
- Use Python `json` module for serialization
- Ensure dates serialized as ISO 8601 strings

**Testing Requirements:**
- Test JSON validity
- Test piping to jq
- Test all fields present
- Test date serialization

**Estimated Effort:** 1-2 hours

---

#### Story 4.6: Cycle Closing and Archival

**As a** developer,
**I want** to close completed cycles and handle incomplete tasks,
**So that** I can transition to the next iteration cleanly without losing work.

**Acceptance Criteria:**
1. `todo cycle close` closes active cycle:
   - Status changed to 'closed'
   - Incomplete tasks handling options:
     a. **Prompt user:** "5 tasks incomplete. Move to next cycle (y), backlog (b), or leave assigned (n)?"
     b. **Default:** Move to backlog (unassign)
     c. **Flag:** `--move-to-next` auto-assigns to next cycle (if exists)
2. `todo cycle close --cycle <name>` closes specific cycle
3. Closing cycle generates summary:
   ```
   Sprint 2 closed (Jan 1 - Jan 14)
   Completed: 7/10 tasks (70%)
   Incomplete tasks moved to backlog
   ```
4. Closed cycles remain queryable:
   - `todo cycle list` shows closed cycles (grayed out)
   - `todo cycle report --cycle "Sprint 2"` works for closed cycles
5. Cannot assign tasks to closed cycle (error message)

**Technical Notes:**
- Update: `UPDATE cycles SET status = 'closed' WHERE id = ?`
- Unassign incomplete tasks: `DELETE FROM cycle_tasks WHERE cycle_id = ? AND task_id IN (SELECT id FROM todos WHERE status != 'completed')`

**Testing Requirements:**
- Test closing with complete tasks
- Test closing with incomplete tasks
- Test move-to-next flag
- Test queryability of closed cycles

**Estimated Effort:** 3-4 hours

---

#### Story 4.7: Auto-Rolling Cycle Transitions [Post-MVP]

**As a** developer,
**I want** to automatically create the next cycle when closing the current one,
**So that** I follow Linear's seamless iteration model without manual setup overhead.

**Acceptance Criteria:**
1. `todo cycle close --auto-next` closes current and creates next:
   - New cycle name: auto-incremented ("Sprint 3" if current is "Sprint 2")
   - Duration: same as previous cycle
   - Start date: today (or next business day)
   - End date: calculated from duration
2. Incomplete tasks auto-assigned to next cycle (optional flag)
3. Cycle naming patterns:
   - Detect pattern: "Sprint X", "Cycle X", "Iteration X"
   - Auto-increment number
   - If no pattern, prompt for name
4. `todo cycle config` sets default auto-rolling behavior:
   ```yaml
   cycles:
     auto_roll: true
     naming_pattern: "Sprint {number}"
     default_duration: 2
   ```

**Technical Notes:**
- Regex pattern matching for cycle names
- Config stored in `~/.config/todo-cli/config.yaml`
- Transaction-wrapped (close + create)

**Testing Requirements:**
- Test auto-increment naming
- Test duration inheritance
- Test incomplete task assignment
- Test config-driven behavior

**Estimated Effort:** 2-3 hours (deferred to post-MVP)

---

## 7. PM Checklist Results

### Executive Summary

**Overall PRD Completeness:** 94% Complete

- **MVP Scope Appropriateness:** Just Right (well-bounded, achievable)
- **Readiness for Architecture Phase:** ✅ Ready with Minor Enhancements
- **Most Critical Gaps:** User flow documentation, validation of user research assumptions

---

### Category Analysis

| Category | Status | Critical Issues |
|----------|--------|-----------------|
| 1. Problem Definition & Context | PARTIAL (85%) | User research is assumption-based; needs validation interviews with 5-10 actual users |
| 2. MVP Scope Definition | PASS (100%) | None - scope is well-defined and appropriately bounded |
| 3. User Experience Requirements | PARTIAL (80%) | Missing explicit user journey flows and decision tree diagrams |
| 4. Functional Requirements | PASS (100%) | None - requirements are comprehensive and testable |
| 5. Non-Functional Requirements | PASS (100%) | None - performance, security, reliability well-defined |
| 6. Epic & Story Structure | PASS (100%) | None - 25 stories well-sized and sequenced |
| 7. Technical Guidance | PASS (100%) | None - architecture and implementation guidance clear |
| 8. Cross-Functional Requirements | PASS (100%) | None - data, integration, operations covered |
| 9. Clarity & Communication | PASS (95%) | Would benefit from user flow diagrams (visual aid) |

---

### Top Issues by Priority

#### BLOCKERS (Must Fix Before Architect Proceeds)
**None** - PRD is ready for architecture phase.

#### HIGH (Should Fix for Quality)

**1. User Flow Documentation Missing**
- **Issue:** Primary user journeys not explicitly mapped end-to-end
- **Impact:** Architect may make assumptions about interaction patterns
- **Recommendation:** Add 3-5 primary flows:
  1. Create project & KANBAN view
  2. Break down feature into sub-tasks
  3. Plan cycle & assign tasks
  4. Generate cycle report
  5. Migrate existing task list to projects
- **Effort:** 2-3 hours to document and diagram

**2. User Research Validation Needed**
- **Issue:** Pain points and needs are logical but assumption-based (not validated with actual users)
- **Impact:** Risk of building features users don't actually want or use
- **Recommendation:** Conduct 5-10 brief user interviews before or during Epic 1 implementation to validate:
  - KANBAN terminal usability assumptions
  - Sub-task hierarchy depth needs (1-level vs. 2-3 levels)
  - Cycle model fit (Linear-style vs. traditional sprints)
  - Reporting granularity requirements
- **Effort:** 1-2 weeks (can overlap with Epic 1 development)

#### MEDIUM (Would Improve Clarity)

**3. Missing User Flow Diagrams**
- **Issue:** No visual representation of user journeys or system state transitions
- **Impact:** Harder for architect to visualize interaction patterns
- **Recommendation:** Create ASCII/Mermaid diagrams for:
  - KANBAN column state transitions
  - Task lifecycle with sub-tasks
  - Cycle workflow (create → assign → track → report → close)
- **Effort:** 1-2 hours

**4. Competitive Analysis Depth**
- **Issue:** Competitive landscape is high-level comparison, not detailed feature matrix
- **Impact:** May miss lessons learned from other CLI PM tools
- **Recommendation:** Deep dive into taskwarrior, org-mode feature sets to identify pitfalls and opportunities
- **Effort:** 4-6 hours research and documentation

#### LOW (Nice to Have)

**5. Export Format Examples**
- **Issue:** JSON/CSV/Markdown export mentioned but not detailed
- **Impact:** Architect must design formats without user input
- **Recommendation:** Provide sample export formats for:
  - Cycle report in Markdown
  - Project summary in JSON
  - Task list in CSV
- **Effort:** 1 hour

---

### MVP Scope Assessment

#### ✅ Scope is Appropriate

**Well-Scoped Features:**
- **1-level sub-task hierarchy:** Delivers 80% of value with minimal complexity
- **Fixed KANBAN columns:** Avoids customization complexity while providing core value
- **Basic cycle management:** Time-boxing and assignment without advanced analytics
- **Backwards compatibility:** Critical for existing user adoption

**Nothing Should Be Cut:** The 4 core features (projects, sub-tasks, KANBAN, cycles) are minimal and integrated. Removing any one would undermine the "comprehensive PM experience" value proposition.

**Nothing Missing:** Out-of-scope list is comprehensive. MVP is truly minimal while remaining viable.

#### Timeline Realism

**Realistic for Target:** 3-4 months with 10-20 hrs/week (120-320 total hours) for 25 stories averaging 2-4 hours each (50-100 implementation hours) plus testing, documentation, and iteration buffer is achievable.

**Risk Factor:** Scope creep during implementation. KANBAN rendering and migration strategy could balloon if not carefully managed.

---

### Technical Readiness

#### Clarity of Technical Constraints ✅
- **Database:** SQLite well-understood, schema documented
- **Performance:** Specific targets defined (<100ms, <500ms)
- **Platform:** Python 3.10+, macOS/Linux/WSL clear
- **Libraries:** Typer, Rich, python-dateutil identified

#### Identified Technical Risks ✅
- **SQLite performance** with complex KANBAN queries (10k+ tasks)
- **Terminal compatibility** across emulators (box-drawing, Unicode)
- **ASCII KANBAN usability** (might not be as useful as theory suggests)
- **Migration strategy** complexity (backwards compatibility)

#### Areas Needing Architect Investigation 🔍

1. **KANBAN Query Optimization**
   - How to efficiently render filtered/grouped KANBAN views with sub-tasks
   - Index strategy for performance targets
   - Caching layer for interactive KANBAN mode

2. **Tree Rendering Algorithm**
   - Efficient parent-child traversal for hierarchical display
   - Handling circular references (should be prevented by constraints)
   - Rich.tree library integration patterns

3. **Migration Framework Design**
   - Zero-downtime database schema evolution
   - Rollback strategy if migration fails
   - Version detection and auto-migration triggers

4. **Terminal Compatibility Layer**
   - Graceful degradation for terminals without box-drawing support
   - ANSI color fallbacks
   - Unicode detection and ASCII-only mode

5. **Cycle Auto-Rolling Logic**
   - Linear-style automatic cycle transitions
   - Incomplete task handling (move to next cycle? backlog?)
   - Notification/warning system for cycle boundaries

---

### Recommendations

#### For PM (Before Architect Handoff)

1. **✅ OPTIONAL: Add User Flow Documentation** (2-3 hours)
   - Create 3-5 primary user journey maps with entry/exit points
   - Document decision trees for key interactions
   - Include in PRD as "User Journeys" section

2. **⚠️ RECOMMENDED: Validate User Research** (1-2 weeks, can overlap with Epic 1)
   - Interview 5-10 existing todo-cli users or target personas
   - Validate KANBAN terminal usability assumptions
   - Confirm sub-task hierarchy depth needs
   - Test cycle model terminology and concepts

3. **✅ OPTIONAL: Add Export Format Examples** (1 hour)
   - Provide sample Markdown cycle report
   - Define JSON project summary structure
   - Show CSV task list format

#### For Architect (During Design Phase)

1. **Performance Benchmarking** (Epic 1, Story 1.3)
   - Create test dataset with 10k tasks, 100 projects, 20 cycles
   - Benchmark KANBAN query performance before and after optimization
   - Validate <500ms target or adjust architecture accordingly

2. **Terminal Compatibility Testing** (Epic 3, Story 3.1)
   - Test KANBAN rendering across 5+ terminal emulators
   - Implement graceful degradation for limited terminals
   - Document minimum terminal requirements

3. **Migration Strategy Prototyping** (Epic 1, Story 1.2)
   - Design version detection mechanism
   - Implement rollback capability
   - Test migration with sample existing databases

#### For Developer (During Implementation)

1. **Prototype Early** (Epic 3, Story 3.1)
   - Build ASCII KANBAN proof-of-concept before full implementation
   - Get user feedback on usability (not just visual appeal)
   - Iterate on layout, colors, information density

2. **Incremental Releases** (Throughout)
   - Ship Epic 1 separately for user testing
   - Gather feedback before committing to Epic 2-4
   - Validate integration between features as you go

3. **Performance Monitoring** (Throughout)
   - Add execution time logging to all commands
   - Track query counts and duration during testing
   - Profile KANBAN rendering with increasing task counts

---

### Final Decision

**✅ READY FOR ARCHITECT**

The PRD and epics are comprehensive, properly structured, and ready for architectural design. The identified gaps (user flow documentation, research validation) are quality improvements, not blockers.

**Architect can proceed with confidence that:**
- Requirements are clear, testable, and implementable
- MVP scope is appropriate and achievable
- Technical constraints and risks are well-understood
- Epic/story structure provides logical implementation sequence
- Non-functional requirements provide clear quality gates

**PM should address HIGH priority items during Epic 1:**
- User flow documentation can be added as architect designs system
- User research validation can happen in parallel with early development

The PRD provides a solid foundation for building "Linear for the terminal."

---

## 8. Next Steps

### For Product Manager (PM)

**Immediate Actions:**

1. **Review and Finalize PRD** (Now)
   - Read through complete PRD
   - Confirm all sections are accurate and complete
   - Sign off on requirements and scope

2. **Optional Enhancements** (Before Architect Handoff)
   - Add user flow documentation (3-5 primary journeys)
   - Add export format examples (Markdown, JSON, CSV samples)
   - Create ASCII/Mermaid diagrams for workflows

3. **User Research Validation** (During Epic 1)
   - Contact 5-10 existing todo-cli users via GitHub
   - Validate KANBAN usability assumptions
   - Confirm sub-task depth needs
   - Test cycle model fit

**Next Phase Transition:**

The PRD is now ready for handoff to the System Architect. Use the following prompt to transition to architecture phase:

**Prompt for UX Expert (Optional, if user flows needed):**
```
Review this PRD and create 3-5 primary user journey flows with entry/exit points and decision trees:
1. Create project & view KANBAN board
2. Break down feature into sub-tasks
3. Plan cycle & assign tasks
4. Generate and share cycle report
5. Migrate existing task list to projects

For each flow, document:
- User goal and context
- Step-by-step actions
- Decision points and branches
- Success criteria and exit points
- Error states and recovery paths

Output as Mermaid flowchart diagrams and narrative descriptions.
```

**Prompt for System Architect:**
```
Review this PRD for todo-cli feature expansion (Projects, Sub-tasks, KANBAN, Cycles).

Based on the requirements, epics, and stories:

1. **System Architecture Design**
   - Confirm or refine the layered architecture (CLI → Logic → Data → Display)
   - Design database schema with indexes for performance targets
   - Plan migration framework for backwards compatibility
   - Identify integration points between features

2. **Technical Investigation**
   - KANBAN query optimization strategy for <500ms rendering
   - Tree rendering algorithm for hierarchical tasks
   - Terminal compatibility layer design
   - Migration rollback mechanism

3. **Technology Validation**
   - Confirm Rich library capabilities for KANBAN/tree rendering
   - Validate SQLite performance for 10k+ tasks
   - Assess Textual framework for interactive KANBAN (optional)
   - Plan testing strategy (unit, integration, performance)

4. **Risk Mitigation**
   - Address identified technical risks (SQLite perf, terminal compat, ASCII KANBAN usability)
   - Design graceful degradation for limited terminals
   - Plan performance benchmarking approach

5. **Epic 1 Detailed Design**
   - Database schema SQL with indexes
   - Migration script architecture
   - Module structure for new features

Deliverable: Architecture Design Document (ADD) with:
- System architecture diagram
- Database schema with DDL
- Migration framework design
- Technology stack validation
- Risk mitigation strategies
- Epic 1 implementation blueprint
```

---

### For System Architect

**Upon Receiving This PRD:**

1. **Review Requirements Thoroughly**
   - Understand functional and non-functional requirements
   - Note performance targets (<100ms, <500ms, <50ms)
   - Review database schema design in Technical Assumptions
   - Study epic/story breakdown for implementation sequence

2. **Investigate Technical Unknowns**
   - **KANBAN Query Optimization:** Design query strategy for filtered/grouped views
   - **Tree Rendering:** Plan efficient parent-child traversal algorithm
   - **Migration Framework:** Design version detection and rollback mechanism
   - **Terminal Compatibility:** Research graceful degradation patterns
   - **Cycle Auto-Rolling:** Design state transition logic

3. **Create Architecture Design Document (ADD)**
   - System architecture diagram (layers, modules, data flow)
   - Database schema DDL with indexes
   - Migration framework architecture
   - Technology stack validation (Rich, SQLite, python-dateutil)
   - Performance optimization strategy
   - Testing approach (unit, integration, benchmarking)

4. **Prototype Critical Paths**
   - ASCII KANBAN proof-of-concept (validate usability)
   - Performance benchmarks with large datasets
   - Terminal compatibility testing across emulators

5. **Hand Off to Developer**
   - Deliver ADD with implementation blueprints
   - Provide Epic 1 detailed design (database schema, migration scripts, module structure)
   - Document technology decisions and rationale

---

### For Developer

**Upon Receiving Architecture Design:**

1. **Set Up Development Environment**
   - Clone todo-cli repository
   - Install dependencies (Python 3.10+, pytest, Rich, python-dateutil)
   - Set up testing framework extensions
   - Configure CI/CD for automated testing

2. **Implement Epic 1: Foundation & Enhanced Project Management**
   - Follow story sequence (1.1 → 1.2 → 1.3 → 1.4 → 1.5)
   - Write tests first (TDD approach)
   - Maintain 80%+ test coverage
   - Run performance benchmarks
   - Document new commands in README

3. **Incremental Release Strategy**
   - **Alpha Release:** Epic 1 only (foundation + projects)
   - Get user feedback on project management features
   - Validate database migration approach
   - **Beta Release:** Epics 1-2 (projects + sub-tasks)
   - Test hierarchical task usage patterns
   - Validate tree view usability
   - **Release Candidate:** Epics 1-3 (projects + sub-tasks + KANBAN)
   - Prototype KANBAN board for user feedback
   - Validate rendering across terminals
   - **v1.0 Release:** All 4 epics (full MVP)

4. **User Feedback Integration**
   - Ship early, ship often
   - Gather feedback via GitHub issues
   - Iterate on UX based on actual usage
   - Adjust scope if features don't deliver expected value

---

### Stakeholder Approvals

**Sign-Off Required:**
- [ ] Product Manager: PRD approved and finalized
- [ ] System Architect: ADD completed and reviewed
- [ ] Lead Developer: Implementation plan accepted

**Timeline Milestones:**
- **Week 0:** PRD finalized, architecture design begins
- **Week 2:** ADD completed, Epic 1 development starts
- **Week 4:** Epic 1 alpha release
- **Week 8:** Epic 2 beta release
- **Week 12:** Epic 3 RC release
- **Week 16:** v1.0 MVP release

---

### Success Metrics Tracking

**Post-Launch Monitoring:**
- Weekly Active Users (WAU)
- Feature adoption rates (projects, sub-tasks, KANBAN, cycles)
- Commands per session
- User retention (28-day)
- GitHub stars, forks, issues
- Export/integration usage
- Performance metrics (command execution times)

**User Research:**
- User satisfaction surveys (NPS)
- Usability testing (KANBAN board, tree view)
- Feature value assessment (which features drive adoption?)
- Workflow integration validation (scripting, automation usage)

---

**End of Product Requirements Document**

---

**Document Status:** ✅ Ready for Architecture Phase
**Last Updated:** 2024-12-25
**PM Checklist Status:** PASS (94% Complete)
**Next Phase:** System Architecture Design
