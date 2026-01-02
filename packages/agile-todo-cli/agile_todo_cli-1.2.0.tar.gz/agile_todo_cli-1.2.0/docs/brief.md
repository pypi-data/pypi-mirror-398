# Project Brief: Todo-CLI Feature Expansion

**Project:** Todo-CLI - Advanced Project Management Features
**Version:** 1.0
**Date:** 2024-12-25
**Status:** Draft

---

## Executive Summary

**Todo-CLI Feature Expansion** extends the existing command-line todo manager with advanced project management capabilities, bringing KANBAN workflows, hierarchical task organization, and sprint-based iteration management to the terminal. The enhancement addresses the growing needs of CLI power users who require sophisticated project organization without leaving their development environment, transforming a simple task tracker into a comprehensive productivity system that rivals GUI-based project management tools while maintaining the speed and scriptability of the command line.

**Primary problem:** CLI users currently lack integrated project management features (task hierarchies, visual workflows, sprint planning) and must context-switch to separate GUI tools, breaking their development flow.

**Target market:** Software developers, DevOps engineers, technical project managers, and power users who live in the terminal and prefer keyboard-driven workflows over mouse-based interfaces.

**Key value proposition:** A unified, terminal-native project management experience combining KANBAN visualization, hierarchical task breakdown, and Linear-style cycles—all accessible via fast CLI commands and scriptable for automation.

---

## Problem Statement

### Current State and Pain Points

CLI-focused developers and technical professionals currently face a fragmented productivity workflow. While they spend 80%+ of their time in the terminal environment, they must constantly context-switch to GUI-based project management tools (Jira, Trello, Asana, Linear) for essential project organization tasks. The existing todo-cli tool provides basic task management but lacks critical features for managing complex projects:

- **No task hierarchies:** Large features cannot be broken into sub-tasks, forcing users to maintain mental models or external documentation
- **Limited project visualization:** Tasks are list-based only—no KANBAN board view to understand workflow states at a glance
- **No iteration planning:** Cannot organize work into sprints/cycles, making it impossible to plan releases or track velocity
- **Weak project grouping:** While projects exist as tags, there's no dedicated project-centric view or operations

### Impact of the Problem

- **Context switching overhead:** Developers report losing 15-30 minutes per day switching between terminal and browser-based PM tools, disrupting flow state
- **Data duplication:** Teams maintain tasks in both CLI tool (for personal tracking) and GUI PM tool (for team visibility), leading to sync errors and wasted effort
- **Reduced CLI adoption:** Power users abandon todo-cli for complex projects because it can't scale beyond simple task lists, forcing them back to GUI tools they prefer to avoid
- **Lost automation opportunities:** Without terminal-native PM features, users cannot script project workflows, generate reports, or integrate with CI/CD pipelines

### Why Existing Solutions Fall Short

- **GUI PM tools:** Require mouse interaction, slow to navigate, cannot be scripted, break terminal-centric workflows
- **Other CLI task managers:** Tools like `taskwarrior` or `todo.txt` lack modern PM features (KANBAN, cycles); they're still just sophisticated list managers
- **Hybrid approaches:** Using CLI for tasks + GUI for PM means maintaining two systems with manual synchronization

### Urgency and Importance

The rise of remote development and "terminal-first" workflows (Vim/Neovim, tmux, CLI-based IDEs) has created a growing community of developers who want to minimize GUI interaction. Linear's success demonstrated that developers value purpose-built PM tools, but no terminal-native alternative exists. As todo-cli gains traction, users are increasingly requesting these features—without them, the tool risks becoming abandoned for more feature-complete (albeit GUI-based) alternatives.

---

## Proposed Solution

### Core Concept and Approach

Extend todo-cli with four integrated project management capabilities that transform it from a task tracker into a comprehensive, terminal-native project management system:

1. **Project Grouping & Views:** Dedicated project-centric commands and filters that make project context first-class, not just tags
2. **Hierarchical Sub-tasks:** Native parent-child task relationships enabling breakdown of large features into manageable units
3. **KANBAN Board Visualization:** ASCII/Unicode-based board view rendering workflow columns (Backlog, Todo, In Progress, Review, Done) in the terminal
4. **Cycles (Sprint Management):** Linear-inspired iteration planning with cycle creation, task assignment, velocity tracking, and burndown reporting

All features are designed CLI-first: fast command syntax, scriptable operations, pipe-friendly output, and zero mouse interaction required.

### Key Differentiators from Existing Solutions

- **Integrated, not bolted-on:** Unlike using separate CLI task manager + GUI PM tool, all features share the same data model and work seamlessly together
- **Terminal-native visualization:** KANBAN boards render beautifully in the terminal using box-drawing characters and color, no browser required
- **Scriptable PM workflows:** Every feature is accessible via commands, enabling automation (e.g., "close current cycle and create next one" in CI/CD)
- **Existing workflow preservation:** Current todo-cli users can adopt features incrementally without disruption—backwards compatible
- **Linear's cycle model:** Borrowing Linear's iteration concept (fixed-length, auto-rolling cycles) rather than traditional sprints gives developers a familiar, modern PM paradigm

### Why This Solution Will Succeed Where Others Haven't

Most CLI task managers (taskwarrior, todo.txt, etc.) are built on 1990s-era list-based paradigms and haven't adopted modern PM workflows. GUI PM tools are feature-rich but fundamentally incompatible with terminal-centric development. This solution succeeds by:

- **Meeting users where they are:** Building on an existing, working tool that users already trust rather than asking them to switch entirely
- **Focusing on developer workflows:** Features chosen specifically for software teams (cycles, KANBAN) rather than generic PM
- **Maintaining CLI advantages:** Fast, scriptable, keyboard-driven while adding visualization that GUI tools have
- **Learning from Linear:** Adopting proven modern PM patterns instead of reinventing project management

### High-Level Vision for the Product

Todo-cli becomes the **"Linear for the terminal"**—a complete project management system that developers never need to leave their shell to use. Developers can:

- Plan entire releases using cycles
- Break down features into sub-tasks and track them on KANBAN boards
- Generate sprint reports via commands and pipe them into documentation or Slack
- Script project workflows (e.g., "archive completed cycle, create new cycle, import backlog items")
- Visualize project health at a glance with terminal-based dashboards
- Share project state with team members via simple text exports (Markdown, JSON) that integrate with existing tools

The vision is not to replace all PM tools, but to provide a **complete, self-contained PM experience for terminal-native developers** who value speed, scriptability, and keyboard-driven workflows.

---

## Target Users

### Primary User Segment: Terminal-Native Software Developers

**Demographic/Firmographic Profile:**
- **Role:** Software engineers, backend developers, full-stack developers
- **Experience level:** Intermediate to senior (3+ years), comfortable with command-line tools
- **Work environment:** Remote-first or distributed teams, often working in multiple projects simultaneously
- **Tech stack preferences:** Modern development tools (Git, Docker, Kubernetes), IDE preference for Vim/Neovim/VSCode terminal, heavy tmux/screen users
- **Company size:** Startups to mid-size tech companies (10-500 employees), occasionally enterprise developers on platform/infrastructure teams
- **Operating systems:** Primarily macOS and Linux, some WSL users on Windows

**Current Behaviors and Workflows:**
- Spend 6-8 hours daily in terminal environments
- Use multiple terminal tabs/panes for different contexts (development, testing, monitoring)
- Already use todo-cli or similar CLI task managers for personal task tracking
- Context-switch to browser-based PM tools (Linear, Jira, Trello) 5-15 times per day for team coordination
- Maintain personal notes in Markdown files or note-taking tools
- Script repetitive tasks using bash/python/make
- Value keyboard shortcuts and fast command execution over visual polish

**Specific Needs and Pain Points:**
- **Context switching fatigue:** Breaking flow state to check PM tools in browser
- **Lack of project structure:** Cannot organize personal work into hierarchical breakdowns without leaving CLI
- **No sprint planning in terminal:** Want to plan iterations but current CLI tools don't support cycles/sprints
- **Poor visibility into workflow state:** Can't see KANBAN-style "what's in progress" without GUI tool
- **Manual synchronization:** Duplicate task entry between personal CLI tracker and team PM tool
- **Limited scriptability:** Cannot automate project workflows (cycle creation, report generation, status updates)

**Goals They're Trying to Achieve:**
- Minimize context switching to maintain deep work and flow state
- Manage personal and team projects entirely from the terminal
- Plan and track sprint/cycle progress without opening a browser
- Automate project management tasks via scripts
- Visualize project health and workflow state in terminal dashboards
- Integrate task management with development workflows (CI/CD, Git hooks, etc.)
- Share project status with team via simple text exports

### Secondary User Segment: Technical Project Managers & DevOps Engineers

**Demographic/Firmographic Profile:**
- **Role:** Engineering managers, technical PMs, DevOps/SRE engineers, team leads
- **Experience level:** Senior engineers transitioning to leadership or infrastructure specialists
- **Work environment:** Same as primary segment but with more coordination responsibilities
- **Tools:** Heavy CLI users but also interface with stakeholders using traditional PM tools
- **Company context:** Often bridge between engineering teams and business stakeholders

**Current Behaviors and Workflows:**
- Split time between terminal (40-60%) and GUI PM tools (40-60%)
- Manage multiple projects and teams simultaneously
- Generate reports for stakeholders (sprint reviews, velocity tracking, burndown charts)
- Need to track team velocity and plan capacity
- Often responsible for sprint planning and backlog grooming

**Specific Needs and Pain Points:**
- **Reporting overhead:** Manually extracting data from PM tools to generate reports
- **Multi-project visibility:** Need to see status across multiple projects quickly
- **Planning complexity:** Struggle to plan sprints/cycles efficiently with current CLI tools
- **Team coordination:** Want to share project state with team without forcing them into specific tools

**Goals They're Trying to Achieve:**
- Efficiently plan and track multiple projects from terminal
- Generate automated reports for stakeholders (velocity, burndown, cycle summaries)
- Maintain project visibility without constant GUI interaction
- Script project management workflows (close cycles, create reports, notify team)
- Bridge gap between terminal-native teams and stakeholder reporting needs

---

## Goals & Success Metrics

### Business Objectives

- **Increase user adoption by 40% within 3 months of release:** Measured by active weekly users of todo-cli, targeting growth from current baseline to demonstrate feature value drives retention
- **Achieve 60% feature adoption rate among existing users within 6 months:** At least 60% of active users utilize at least one new feature (projects, sub-tasks, KANBAN, or cycles) regularly
- **Reduce user churn by 25%:** Decrease monthly user attrition by retaining users who previously abandoned todo-cli for GUI PM tools
- **Establish todo-cli as "go-to" CLI PM tool:** Appear in top 3 results for "CLI project management" and "terminal todo manager" searches, tracked via GitHub stars and community mentions
- **Enable enterprise use cases:** Support team-based workflows allowing 5-10 person engineering teams to use todo-cli as primary PM tool

### User Success Metrics

- **Context switching reduction:** Users report 50%+ reduction in daily switches to GUI PM tools (measured via user survey)
- **Daily active usage:** Users interact with todo-cli 10+ times per day (up from current 5-7), indicating it's becoming central workflow tool
- **Feature utilization depth:** 70% of users who adopt KANBAN also adopt cycles, indicating features work well together
- **Time to first value:** New users create their first project with sub-tasks and KANBAN view within 15 minutes of feature introduction
- **Workflow integration:** 40% of users integrate todo-cli commands into scripts, aliases, or automation workflows within first month
- **Project completion velocity:** Users complete 20%+ more tasks per sprint when using cycle management vs. unstructured task lists

### Key Performance Indicators (KPIs)

- **Weekly Active Users (WAU):** Track growth from current baseline, target 40% increase within 3 months post-release
- **Feature Adoption Rate:** Percentage of users using each feature (projects: 80%, sub-tasks: 70%, KANBAN: 60%, cycles: 50%)
- **Commands per Session:** Average CLI commands executed per session, target 15+ (indicating deep engagement)
- **Retention Rate (28-day):** Percentage of users active in month N who return in month N+1, target 70%+
- **Net Promoter Score (NPS):** User willingness to recommend todo-cli, target score of 40+ (industry good)
- **GitHub Engagement:** Stars, forks, and community contributions as proxy for adoption and satisfaction
- **Export/Integration Usage:** Percentage of users leveraging export commands (JSON/CSV/Markdown) for tool integration, target 30%
- **Time in KANBAN View:** Average daily time users spend in KANBAN board view, target 10+ minutes (indicating usefulness)

---

## MVP Scope

### Core Features (Must Have)

- **Enhanced Project Grouping:** Dedicated `todo projects` command with project-centric views showing all tasks grouped by project. Project filtering across all commands (`todo list --project myapp`). Project metadata (description, created date, active status). Rationale: Projects already exist as tags but need first-class treatment to be truly useful for organization.

- **Hierarchical Sub-tasks:** Parent-child task relationships allowing any task to have sub-tasks (1 level deep for MVP). Commands: `todo add-subtask <parent-id> "description"`, `todo list --tree` for hierarchical view. Parent task completion requires all sub-tasks complete. Rationale: Single-level hierarchy delivers 80% of the value with minimal complexity—deep nesting can wait for v2.

- **ASCII KANBAN Board View:** Terminal-rendered board with configurable columns (default: Backlog, Todo, In Progress, Review, Done). Command: `todo kanban [--project <name>]` displays board using box-drawing characters. Tasks move between columns via `todo move <id> <column>`. Board supports color coding by priority and filtering by project. Rationale: Visual workflow state is core differentiator—even basic ASCII board provides massive value over list-only view.

- **Basic Cycle Management:** Create fixed-length cycles (iterations/sprints) with start/end dates. Commands: `todo cycle create <name> --duration <weeks>`, `todo cycle assign <task-id>`, `todo cycle current` to view active cycle. Track cycle progress (tasks completed/total). Rationale: Linear's cycle model simplified—focus on time-boxing and assignment first, velocity tracking can be v2 enhancement.

- **Cycle Reporting:** Generate cycle summary reports showing completed vs. incomplete tasks, basic burndown data. Export as Markdown or JSON for sharing. Command: `todo cycle report [--format md|json]`. Rationale: Reporting is essential for team visibility and validates scriptability value proposition.

- **Backwards Compatibility:** All existing todo-cli commands and data continue working unchanged. Users can adopt new features incrementally without migration. Rationale: Non-negotiable to avoid alienating existing user base.

### Out of Scope for MVP

- **Multi-level sub-task nesting:** Limit to 1 level parent-child for MVP; deep hierarchies add complexity without proportional value
- **Drag-and-drop KANBAN interaction:** CLI tool uses keyboard commands to move tasks, not mouse-based dragging
- **Advanced cycle analytics:** Velocity tracking, burndown charts, forecasting deferred to v2
- **Team collaboration features:** No real-time sync, shared boards, or multi-user permissions in MVP—focus on individual/small team use
- **Custom KANBAN columns:** MVP ships with fixed column set; customization adds significant complexity
- **Dependency management:** Task dependencies (blockers, prerequisites) deferred to future release
- **Time tracking integration:** Existing time tracking continues working but won't integrate deeply with cycles/KANBAN in MVP
- **Mobile/web companion app:** Terminal-only for MVP; GUI interfaces are future consideration
- **Advanced filtering/queries:** Basic project filtering only; complex queries (AND/OR, regex) are v2 features
- **Task templates:** Ability to create task templates for common workflows deferred
- **Notifications/reminders:** No active notifications or due date alerts in MVP
- **Integration APIs:** No REST API or webhook support for external tool integration in MVP

### MVP Success Criteria

**The MVP is successful if:**

1. **Users can manage a complete software project** using only todo-cli without GUI PM tool for basic workflows (plan sprint, break down features, track progress, generate report)

2. **All four core features work seamlessly together:** Users can create projects, add tasks with sub-tasks, view them on KANBAN board, assign to cycles, and generate reports—all features integrated, not siloed

3. **Existing users adopt without friction:** 80%+ of current todo-cli users can upgrade and use new features within 30 minutes with minimal documentation

4. **KANBAN board is actually usable:** Users report the ASCII board provides sufficient visibility into workflow state and prefer it to list view for project overview

5. **Cycles drive better planning:** Users report improved sprint planning and completion rates when using cycle management vs. unstructured task lists

6. **Scriptability is validated:** At least 20% of users create custom scripts/aliases leveraging new commands within first month

7. **Technical quality meets existing standards:** New features maintain current performance (sub-second command execution), data integrity (no corruption), and test coverage (80%+)

8. **Export enables team sharing:** Users successfully share cycle reports and project status with team members via Markdown/JSON exports

**MVP is NOT successful if it requires:**
- More than 5 new CLI commands to access core features (complexity threshold)
- GUI tool or external service to be fully functional
- Breaking changes to existing data or commands
- More than 10 hours of development time to learn and adopt for experienced CLI users

---

## Post-MVP Vision

### Phase 2 Features (Next Priority)

**Enhanced Cycle Analytics:**
- Velocity tracking across cycles (average tasks completed per cycle)
- Burndown charts rendered in terminal using ASCII sparklines or bar graphs
- Cycle-over-cycle comparison reports
- Forecasting tools to predict completion dates based on historical velocity
- Rationale: Once basic cycle management proves valuable, users will want deeper analytics for planning and optimization

**Multi-level Sub-task Nesting:**
- Extend hierarchical tasks to support 3-5 levels of nesting
- Improved tree visualization commands with collapsible views
- Bulk operations on task hierarchies (complete all children, move branch)
- Rationale: Users will naturally want deeper breakdowns for complex features once they adopt single-level hierarchy

**Custom KANBAN Workflows:**
- User-defined column names and ordering
- Per-project workflow configurations
- Work-in-progress (WIP) limits per column
- Automated transitions based on task status changes
- Rationale: Different teams have different workflows—flexibility becomes valuable once core KANBAN proves useful

**Task Dependencies & Blocking:**
- Define prerequisite relationships between tasks
- Visualize dependency graphs in terminal
- Automatically update dependent task statuses
- Critical path analysis for cycle planning
- Rationale: Dependencies are essential for complex projects but add significant complexity, better suited for Phase 2

**Team Collaboration (Lightweight):**
- Shared project state via Git-based synchronization
- Export/import project snapshots for team sharing
- Conflict resolution for concurrent updates
- Role-based visibility (personal vs. team tasks)
- Rationale: Start with simple sharing mechanisms before building full multi-user system

### Long-term Vision (1-2 Years)

**Todo-CLI as Complete PM Platform:**

By the 1-2 year mark, todo-cli evolves into a comprehensive project management platform that rivals GUI tools in functionality while maintaining terminal-native advantages. The vision includes:

**Advanced Team Features:**
- Real-time collaboration via lightweight sync server (optional, self-hosted)
- Team dashboards aggregating multiple user boards
- @mentions and task assignment to team members
- Activity feeds and notification system (terminal-based, non-intrusive)
- Sprint planning poker and estimation tools

**Intelligence & Automation:**
- AI-powered task breakdown suggestions (analyze feature description, suggest sub-tasks)
- Automated cycle planning using historical velocity and task estimates
- Smart dependency detection (identify blockers from task descriptions)
- Anomaly detection (cycles at risk, tasks taking too long)
- Template library for common project types (web app, API service, infrastructure)

**Rich Visualization:**
- Timeline/Gantt chart views in terminal
- Interactive TUI mode (terminal user interface) with mouse support for those who want it
- Export to image formats (SVG, PNG) for stakeholder presentations
- Integration with terminal-based data visualization tools

**Ecosystem Integration:**
- REST API for external tool integration (CI/CD, Slack, GitHub, etc.)
- Webhooks for event-driven automation
- Plugin system for community extensions
- Native integrations with popular developer tools (Jira, Linear, GitHub Issues sync)
- CLI companion app for mobile (read-only view of projects/boards)

**Advanced Reporting:**
- Custom report builder with query language
- Scheduled reports (automated cycle summaries via email/Slack)
- Export to multiple formats (PDF, HTML, Confluence, Notion)
- Data warehouse integration for cross-project analytics

**User Experience Enhancements:**
- Natural language input ("add task to deploy feature next Tuesday high priority")
- Smart search across all projects and tasks
- Saved filters and custom views
- Keyboard shortcuts customization
- Themes and color scheme configuration

### Expansion Opportunities

**Adjacent Markets:**
- **Individual Knowledge Workers:** Beyond developers—writers, designers, product managers who value CLI efficiency
- **Academic/Research:** Researchers tracking experiments, papers, and collaborations
- **DevOps/SRE Teams:** Incident management, runbook tracking, on-call task management
- **Open Source Projects:** Public project boards for community-driven development

**Complementary Products:**
- **Todo-CLI Cloud:** Optional hosted sync service for teams who don't want to self-host
- **GUI Companion App:** Desktop app for stakeholders who need visual dashboards (while teams use CLI)
- **Browser Extension:** Quick capture from browser into todo-cli backend
- **Mobile App:** Read-only view with quick task updates on the go

**Platform Plays:**
- **Marketplace:** Plugin and template marketplace for community contributions
- **Training/Certification:** "Terminal-Native PM" courses teaching modern CLI-based project management
- **Enterprise Edition:** Enhanced security, compliance, audit logs, SSO integration

**Technological Evolution:**
- **Language Ports:** Rust or Go rewrite for performance and single-binary distribution
- **Cloud-Native:** Kubernetes operator for team deployments
- **AI Integration:** Deep integration with LLMs for project planning assistance

---

## Technical Considerations

### Platform Requirements

- **Target Platforms:** Cross-platform CLI tool supporting macOS, Linux, and Windows (WSL)
- **Terminal Support:** ANSI color terminals, minimum 80x24 character display, Unicode/box-drawing character support for KANBAN rendering
- **Python Version:** Python 3.10+ (current requirement maintained)
- **Performance Requirements:**
  - Sub-100ms command execution for list/display operations
  - Sub-500ms for KANBAN board rendering (including database queries)
  - Support for 10,000+ tasks per database without degradation
  - Interactive KANBAN view updates in real-time (<50ms refresh)

### Technology Preferences

**Current Stack (Maintained):**
- **Language:** Python 3.10+
- **CLI Framework:** Typer (with Rich for terminal formatting)
- **Database:** SQLite (local file-based storage)
- **Display:** Rich library for terminal formatting, tables, and color
- **Testing:** pytest with pytest-cov for coverage

**New Dependencies for Features:**
- **KANBAN Rendering:**
  - `rich.layout` and `rich.panel` for board visualization (already available)
  - Potentially `textual` for future interactive TUI mode (not MVP)
- **Tree Visualization (Sub-tasks):**
  - `rich.tree` for hierarchical display (already available)
- **Date/Time Handling (Cycles):**
  - `python-dateutil` for cycle scheduling and duration calculations
- **Data Validation:**
  - `pydantic` for data models and validation (optional enhancement)

**Infrastructure:**
- **Hosting:** Not applicable (local CLI tool)
- **Distribution:** PyPI package distribution (existing), potential future Homebrew/apt packages
- **Documentation:** Markdown in repository, potential future MkDocs site

### Architecture Considerations

**Repository Structure:**
- **Monorepo maintained** - All features within existing `todo-cli` repository
- New modules added to `todo_cli/` package structure:
  - `todo_cli/projects.py` - Enhanced project operations
  - `todo_cli/subtasks.py` - Hierarchical task logic
  - `todo_cli/kanban.py` - Board rendering and display
  - `todo_cli/cycles.py` - Cycle management and reporting

**Service Architecture:**
- **Single-process monolith** - No service decomposition needed for CLI tool
- **Database-first design** - SQLite as source of truth, all state persisted
- **Layered architecture maintained:**
  - **CLI Layer:** Typer commands in `main.py`
  - **Business Logic:** Feature modules (projects, subtasks, kanban, cycles)
  - **Data Layer:** Database operations in `database.py` extended with new tables
  - **Display Layer:** Rich-based formatting in `display.py` extended with KANBAN renderer

**Database Schema Extensions:**

```sql
-- New tables for features
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL
);

CREATE TABLE subtasks (
    parent_id INTEGER NOT NULL,
    child_id INTEGER NOT NULL,
    position INTEGER DEFAULT 0,
    PRIMARY KEY (parent_id, child_id),
    FOREIGN KEY (parent_id) REFERENCES todos(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES todos(id) ON DELETE CASCADE
);

CREATE TABLE cycles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL
);

CREATE TABLE cycle_tasks (
    cycle_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    PRIMARY KEY (cycle_id, task_id),
    FOREIGN KEY (cycle_id) REFERENCES cycles(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES todos(id) ON DELETE CASCADE
);

-- Extend todos table with new columns (via migration)
ALTER TABLE todos ADD COLUMN kanban_column TEXT DEFAULT 'backlog';
```

**Integration Requirements:**
- **Export formats:** Extend existing JSON/CSV/Markdown export to support new entities (projects, cycles)
- **Configuration:** YAML-based config extended with KANBAN column definitions, default cycle duration
- **Backwards compatibility:** Database migrations via simple Python scripts (no Alembic needed for MVP)
- **Testing:** Extend existing pytest suite with new test modules per feature

**Security/Compliance:**
- **Local-only data** - No cloud sync in MVP reduces security surface area
- **File permissions:** Ensure database file has appropriate permissions (600) for user-only access
- **SQL injection prevention:** Parameterized queries throughout (existing pattern maintained)
- **No PII concerns:** Task data is user-generated, no built-in PII collection
- **Future consideration:** Encryption at rest if shared/team features added post-MVP

---

## Constraints & Assumptions

### Constraints

**Budget:**
- **Development:** $0 budget - open-source project with volunteer/personal development time
- **Infrastructure:** $0 ongoing costs - local-only CLI tool with no hosting requirements
- **Tools/Services:** Free tier tools only (GitHub, PyPI, free CI/CD via GitHub Actions)
- **Marketing:** Organic growth through GitHub, Reddit, HackerNews - no paid advertising budget

**Timeline:**
- **MVP Target:** 3-4 months from start to initial release (assuming part-time development)
- **Feature Delivery:** Iterative releases rather than big-bang (ship projects first, then sub-tasks, then KANBAN, then cycles)
- **No Hard Deadline:** Open-source project timeline is flexible but target Q2 2025 for MVP completion
- **Maintenance Window:** Ongoing maintenance and bug fixes required post-launch with limited time availability

**Resources:**
- **Development Team:** Solo developer or small team (1-3 contributors max)
- **Time Availability:** 10-20 hours/week development time (part-time/evening work)
- **Skills:** Python expertise required, terminal/CLI UX design skills helpful
- **Community:** Rely on user community for testing, feedback, and potential contributions
- **Documentation:** Limited time for comprehensive docs - focus on README and inline help

**Technical:**
- **Python 3.10+ requirement:** Cannot support older Python versions due to type hints and language features
- **Terminal limitations:** ASCII/Unicode rendering only - no graphical components
- **Local storage only:** SQLite file-based storage, no cloud/server component in MVP
- **Cross-platform compatibility:** Must work on macOS, Linux, WSL without platform-specific dependencies
- **Backwards compatibility:** Cannot break existing user data or command interfaces
- **Performance constraints:** Pure Python limits optimization options vs compiled languages
- **Dependency minimalism:** Prefer standard library and existing dependencies over adding new heavy frameworks

### Key Assumptions

- **User base exists:** Current todo-cli users will adopt new features and provide feedback for iteration
- **Terminal adoption continues:** Developers continue trending toward terminal-first workflows rather than abandoning CLI tools
- **SQLite is sufficient:** Local SQLite database can handle expected data volumes (10k+ tasks) with acceptable performance
- **ASCII KANBAN is valuable:** Users will find terminal-rendered boards useful enough to prefer over GUI alternatives for quick views
- **Linear's cycle model translates:** The cycle/iteration concept works well in CLI context even without GUI's visual calendar
- **Solo development is viable:** Project scope is achievable for 1-3 developers working part-time over 3-4 months
- **Community will contribute:** Open-source community will help with testing, bug reports, and potentially code contributions
- **No team sync needed initially:** Users can coordinate via exports (Markdown/JSON) without real-time collaboration features
- **Export formats sufficient:** JSON, CSV, Markdown exports provide adequate integration with other tools for MVP
- **Incremental adoption:** Users will adopt features gradually (not all at once) allowing time to validate and iterate
- **Performance is acceptable:** Python's performance characteristics are sufficient for CLI tool responsiveness expectations
- **Rich library capabilities:** Rich provides adequate terminal rendering for KANBAN boards without needing full TUI framework
- **Migration paths exist:** Can evolve database schema without breaking existing installations through simple migration scripts
- **Documentation via usage:** Users prefer learning through `--help` and README examples over comprehensive documentation sites
- **Platform coverage:** macOS/Linux/WSL coverage captures 95%+ of target user base (native Windows users minimal)

---

## Risks & Open Questions

### Key Risks

- **Scope Creep / Over-Ambition:** Four major features (projects, sub-tasks, KANBAN, cycles) in one release may be too ambitious for part-time development. Feature complexity could balloon during implementation, causing significant timeline slips or forcing quality compromises. *Impact: High - could delay release by months or result in half-finished features.*

- **ASCII KANBAN Usability:** Terminal-rendered KANBAN boards may look good in theory but prove unusable in practice. Users might find ASCII boards too cluttered, hard to scan, or frustrating compared to GUI drag-and-drop interfaces. If KANBAN isn't genuinely useful, a core value proposition fails. *Impact: High - invalidates key differentiator and user value.*

- **Database Performance Degradation:** SQLite may not handle complex KANBAN queries (filtering, grouping, joining projects/sub-tasks/cycles) efficiently. As task counts grow beyond 1,000+ items, board rendering could slow to unacceptable levels (>1 second), breaking CLI responsiveness expectations. *Impact: Medium - requires architecture changes or optimization work.*

- **User Adoption Resistance:** Existing todo-cli users may resist complexity of new features, preferring simple task lists. New features could overwhelm the interface and alienate current user base while failing to attract new users who are committed to GUI tools. *Impact: Medium - user base stagnates or shrinks.*

- **Backwards Compatibility Challenges:** Database schema changes and new commands may break existing user workflows, scripts, or aliases in unexpected ways. Migration path could fail for edge cases, resulting in data loss or corruption. *Impact: High - destroys user trust and adoption.*

- **Limited Development Resources:** Solo/small team may burn out, lose interest, or face competing priorities. Without dedicated time, project could stall mid-development leaving half-finished features. *Impact: Medium - project abandonment or indefinite delay.*

- **Competition Emergence:** Established CLI tool (taskwarrior, etc.) or new entrant could add similar features while in development, reducing differentiation. Alternatively, GUI tools could add CLI interfaces, eliminating need for todo-cli. *Impact: Low-Medium - reduces market opportunity.*

- **Terminal Ecosystem Fragmentation:** Different terminal emulators handle Unicode, colors, and box-drawing characters inconsistently. KANBAN board may render beautifully on iTerm2 but break on Windows Terminal or older terminals, creating fragmented user experience. *Impact: Medium - limits addressable user base.*

- **Cycle Model Misfit:** Linear's cycle concept may not translate well to CLI context. Without GUI calendar views and drag-drop, users might find cycle management clunky and abandon feature, leaving it unused. *Impact: Medium - wasted development effort on unused feature.*

### Open Questions

- **What is the minimum viable KANBAN board?** How many columns are truly essential? Can we ship with 3 columns (Todo, In Progress, Done) instead of 5? What customization is absolutely required vs. nice-to-have?

- **How deep should sub-task nesting go?** Is 1-level sufficient or will users immediately demand 2-3 levels? What's the use case distribution for deep vs. shallow hierarchies?

- **What's the right default cycle duration?** Should cycles default to 1 week (agile), 2 weeks (scrum standard), or be required user input? Does the Linear model of auto-rolling cycles work without GUI?

- **How do users want to move tasks between KANBAN columns?** Should it be `todo move <id> <column>`, `todo status <id> <column>`, or integrated into existing `todo status` command with column mapping?

- **Should project grouping replace or augment existing project tagging?** Current todo-cli has `-P` project flag. Do we need dedicated project entities or enhance the existing tagging system?

- **What reporting granularity do users actually need?** Is basic "tasks completed/total" sufficient for cycles, or do users require detailed burndown, velocity tracking, and forecasting from day one?

- **How should sub-task completion affect parent tasks?** Must all children complete before parent can be marked done? Or allow parent completion independently? What's the right UX?

- **What's the migration strategy for existing users?** Can we auto-migrate existing tasks to new schema, or require user action? How do we communicate breaking changes effectively?

- **Should KANBAN be project-specific or global?** Do users want one big board, per-project boards, or both? What's the mental model that matches workflows?

- **How do we handle conflicts between features?** If a task is in a cycle but hasn't moved to "In Progress" on KANBAN, what's the source of truth? How do these features integrate coherently?

- **What's the actual market size?** How many CLI power users exist who would use advanced PM features? Is this a 100-user niche or 10,000+ user market?

- **Will users actually script workflows?** Is scriptability a genuine value driver or just a checkbox feature that sounds good but doesn't drive adoption?

### Areas Needing Further Research

- **User Research - KANBAN Usability:** Prototype ASCII KANBAN board designs and test with target users before full implementation. Validate that terminal rendering is actually usable, not just theoretically possible.

- **Performance Benchmarking:** Test SQLite query performance with realistic datasets (5k, 10k, 50k tasks) to validate database choice and identify optimization needs early.

- **Competitive Analysis - Deep Dive:** Comprehensive review of taskwarrior, todo.txt, org-mode, and other CLI PM tools to understand what they got right/wrong with advanced features.

- **Terminal Compatibility Testing:** Survey terminal emulator landscape (iTerm2, Alacritty, Kitty, Windows Terminal, GNOME Terminal, etc.) to understand Unicode/box-drawing support and compatibility challenges.

- **User Workflow Mapping:** Interview 5-10 target users about their current PM workflows to understand how they actually use GUI tools and what CLI translation makes sense.

- **Cycle Model Validation:** Research Linear's cycle implementation deeply and interview Linear users about what makes cycles valuable vs. traditional sprints.

- **Export Format Requirements:** Understand what formats and integrations users actually need (Markdown for docs? JSON for scripts? CSV for Excel? GitHub Issues sync?)

- **Migration Strategy Research:** Study how other CLI tools (Git, npm, etc.) have handled breaking changes and migrations to inform backwards compatibility approach.

- **Community Engagement Assessment:** Analyze similar open-source CLI projects to understand realistic community contribution patterns and engagement strategies.

- **Accessibility Requirements:** Research terminal accessibility for users with visual impairments or other disabilities to ensure inclusive design.

---

## Appendices

### A. Research Summary

**Existing Codebase Analysis:**
- Current todo-cli has solid foundation with SQLite database, Rich terminal rendering, time tracking, and export capabilities
- Clean architecture with separate modules for CLI, business logic, database, and display layers
- Comprehensive test suite with pytest (strong foundation for adding features)
- Active development with recent commits and test coverage

**Competitive Landscape (Preliminary):**
- **taskwarrior:** Feature-rich but complex syntax, no built-in KANBAN or modern cycle management
- **todo.txt:** Minimalist, text-file based, lacks project management features entirely
- **Linear:** GUI-only, sets standard for developer-focused PM but no CLI offering
- **Jira/Trello/Asana:** Enterprise/team PM tools, heavy GUI interfaces, no terminal-native experience
- **org-mode:** Emacs-based, powerful but locked into Emacs ecosystem

**Gap Identified:** No terminal-native PM tool combines KANBAN visualization, hierarchical tasks, and modern cycle management. Todo-cli is positioned to fill this gap.

### B. References

**Relevant Links:**
- Todo-CLI Repository: `/Users/rk/dev/todo-cli`
- Linear Product Approach: https://linear.app (reference for cycle model)
- Rich Terminal Library Docs: https://rich.readthedocs.io
- Python Typer CLI Framework: https://typer.tiangolo.com

**Related Documentation:**
- README.md - Current feature set and usage
- Existing test suite - Reference for testing patterns
- Database schema - Foundation for extensions

---

## Next Steps

### Immediate Actions

1. **Finalize and approve this Project Brief** - Review all sections, make final adjustments, and sign off on direction

2. **Prototype ASCII KANBAN board** - Create quick proof-of-concept rendering to validate usability before committing to full implementation (2-3 hours, high-value risk reduction)

3. **User research outreach** - Contact 5-10 existing todo-cli users (via GitHub issues/discussions) to validate feature priorities and gather workflow insights (1 week)

4. **Database schema design** - Detail the table structures for projects, sub-tasks, cycles with migration strategy (4-6 hours)

5. **Create PRD from this brief** - Use BMad Master agent with PRD template to translate this brief into detailed Product Requirements Document with functional/non-functional requirements and user stories

6. **Set up project tracking** - Initialize GitHub project board or milestone to track feature development progress

7. **Prototype performance testing** - Create test dataset with 10k tasks and benchmark current query performance to establish baseline

### PM Handoff

This Project Brief provides the full context for **Todo-CLI Feature Expansion: Projects, Sub-tasks, KANBAN, and Cycles**.

**Summary:**
We're transforming todo-cli from a simple task tracker into a comprehensive terminal-native project management system by adding four integrated capabilities: enhanced project grouping, hierarchical sub-tasks (1-level), ASCII KANBAN board visualization, and Linear-inspired cycle management. The target users are terminal-native software developers who want to eliminate context-switching to GUI PM tools while maintaining speed, scriptability, and keyboard-driven workflows.

**Key Constraints:**
- Zero budget, open-source development
- Part-time development (10-20 hrs/week)
- 3-4 month MVP timeline
- Must maintain backwards compatibility with existing todo-cli
- Solo or small team (1-3 developers)

**Critical Success Factors:**
- ASCII KANBAN must be genuinely usable (not just a novelty)
- All four features integrate coherently (not siloed capabilities)
- Performance remains CLI-fast (<100ms for most operations)
- Existing users adopt without friction

**Next Phase:**
Please start in **PRD Generation Mode**. Review this brief thoroughly to work with the user to create the PRD section by section as the template indicates, asking for any necessary clarification or suggesting improvements. Focus on translating the MVP scope into detailed functional requirements and well-sequenced user stories that an architect and developer can execute.

The PRD should prioritize:
1. Clear functional requirements for each feature (projects, sub-tasks, KANBAN, cycles)
2. Specific non-functional requirements (performance targets, compatibility)
3. Logical epic sequencing (foundation first, then features)
4. User stories sized for AI agent execution (completable in single focused session)

---

**End of Project Brief**
