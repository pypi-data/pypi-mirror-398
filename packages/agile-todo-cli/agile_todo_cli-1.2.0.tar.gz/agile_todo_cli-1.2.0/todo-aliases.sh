# Todo CLI shortcuts - source this in your .zshrc or .bashrc
# Usage: source ~/dev/todo-cli/todo-aliases.sh

# Quick access
alias t='todo list'                    # List all todos
alias tt='todo list -s todo'           # Only "todo" status (not done)
alias tp='todo list -P'                # List by project: tp myproject
alias ta='todo add'                    # Add: ta "task" -p p1 -P project
alias td='todo done'                   # Done: td 1
alias ts='todo start'                  # Start timer: ts 1
alias tx='todo stop'                   # Stop timer
alias ti='todo interactive'            # Interactive mode
alias tw='todo active'                 # What am I working on?
alias tstat='todo stats'               # Statistics

# Quick add with priority
alias t0='todo add -p p0'              # Urgent: t0 "task"
alias t1='todo add -p p1'              # High: t1 "task"
alias t2='todo add -p p2'              # Normal: t2 "task"

# Reports
alias trd='todo report daily'          # Daily report
alias trw='todo report weekly'         # Weekly report

# Quick view function - show top 5 P0/P1 tasks
top() {
    echo "🔴 P0 - Urgent:"
    todo list | grep "🔴" | head -5
    echo ""
    echo "🟡 P1 - High:"
    todo list | grep "🟡" | head -5
}

# What's next? Show first undone task
next() {
    todo list -s todo | head -20
}
