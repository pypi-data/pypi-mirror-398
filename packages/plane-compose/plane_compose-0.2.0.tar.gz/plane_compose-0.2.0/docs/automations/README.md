# Plane Automations

Automate your workflow with simple YAML files. No code required for common tasks, TypeScript available for complex logic.

## Quick Start

### 1. Create your first automation

```bash
# Navigate to your project
cd my-project

# Create an automation
plane automations new "Auto-assign bugs"
```

This creates `automations/auto-assign-bugs.yaml`:

```yaml
name: Auto-assign bugs
description: TODO - Add description

on: work_item.created

when:
  type: bug

do:
  - set:
      priority: high
```

### 2. Test it

```bash
plane automations test "Auto-assign bugs" --type bug
```

### 3. Validate all automations

```bash
plane automations validate
```

---

## Table of Contents

1. [Concepts](#concepts)
2. [Triggers](#triggers)
3. [Conditions](#conditions)
4. [Actions](#actions)
5. [Expressions](#expressions)
6. [Scripts](#scripts)
7. [CLI Reference](#cli-reference)
8. [Examples](#examples)

---

## Concepts

An automation has four parts:

```yaml
name: Bug triage                    # 1. Name
on: work_item.created               # 2. Trigger (when to run)
when:                               # 3. Conditions (filter)
  type: bug
do:                                 # 4. Actions (what to do)
  - set:
      priority: high
```

### File Structure

```
my-project/
├── plane.yaml                 # Project config
├── automations/
│   ├── bug-triage.yaml        # Automation definitions
│   ├── auto-assign.yaml
│   └── scripts/               # TypeScript for complex logic
│       └── escalation.ts
```

---

## Triggers

Triggers define **when** an automation runs.

### Available Triggers

| Trigger | Description |
|---------|-------------|
| `work_item.created` | New work item created |
| `work_item.updated` | Work item modified |
| `work_item.deleted` | Work item deleted |
| `work_item.state_changed` | State changed (todo → done) |
| `work_item.assigned` | Assignee added |
| `work_item.unassigned` | Assignee removed |
| `work_item.labeled` | Label added |
| `work_item.unlabeled` | Label removed |
| `comment.created` | Comment added |
| `schedule` | Cron-based schedule |

### Examples

```yaml
# Simple trigger
on: work_item.created

# Trigger on specific field changes
on:
  event: work_item.updated
  fields: [priority, state]

# Scheduled trigger (cron)
on:
  schedule: "0 9 * * MON"  # Every Monday at 9am
```

---

## Conditions

Conditions filter **which** items trigger the automation.

### Simple Conditions (in `when:`)

```yaml
# Single condition
when:
  type: bug

# Multiple conditions (AND)
when:
  type: bug
  priority: high

# Value in list
when:
  state: [todo, backlog]

# Check for null
when:
  assignee: null
```

### Advanced Conditions (CEL expressions)

For complex logic, use [CEL (Common Expression Language)](https://cel.dev):

```yaml
# In 'do' block actions
do:
  - when: work_item.priority == 'high' && 'critical' in work_item.labels
    set:
      state: in_progress

  - when: size(work_item.labels) == 0
    add_label: needs-triage

  - when: work_item.assignee == null
    assign: default@example.com
```

### CEL Syntax Reference

| Operation | Syntax | Example |
|-----------|--------|---------|
| Equals | `==` | `work_item.type == 'bug'` |
| Not equals | `!=` | `work_item.state != 'done'` |
| Contains | `in` | `'critical' in work_item.labels` |
| Size | `size()` | `size(work_item.labels) > 0` |
| AND | `&&` | `a == 'x' && b == 'y'` |
| OR | `\|\|` | `a == 'x' \|\| a == 'y'` |
| NOT | `!` | `!(work_item.state == 'done')` |
| Null check | `== null` | `work_item.assignee == null` |

### Legacy Shorthand (also supported)

```yaml
do:
  - when: type == bug              # Same as: work_item.type == 'bug'
  - when: labels contains critical # Same as: 'critical' in work_item.labels
  - when: priority != low          # Same as: work_item.priority != 'low'
```

---

## Actions

Actions define **what** happens when conditions match.

### Available Actions

| Action | Description | Example |
|--------|-------------|---------|
| `set` | Update fields | `set: { priority: high }` |
| `assign` | Add assignee | `assign: user@example.com` |
| `unassign` | Remove assignee | `unassign: user@example.com` |
| `add_label` | Add label | `add_label: needs-review` |
| `remove_label` | Remove label | `remove_label: stale` |
| `comment` | Add comment | `comment: "Hello!"` |
| `notify` | Send notification | `notify: { channel: #team }` |
| `create` | Create new item | `create: { title: "..." }` |

### Examples

```yaml
do:
  # Update multiple fields
  - set:
      priority: urgent
      state: in_progress

  # Assign user
  - assign: alice@example.com

  # Add labels
  - add_label: needs-review
  - add_label: [urgent, security]  # Multiple labels

  # Add comment with template
  - comment: "Assigned to ${{ assignee }} for triage"

  # Send notification
  - notify:
      channel: "#bugs"
      message: "🐛 New bug: ${{ title }}"
```

### Conditional Actions

Use `when:` to make actions conditional:

```yaml
do:
  - when: labels contains "critical"
    set:
      priority: urgent
    assign: oncall@example.com

  - when: labels contains "security"
    add_label: security-review
    notify:
      channel: "#security"

  - otherwise: true  # Default case
    set:
      state: backlog
```

---

## Expressions

Use `${{ }}` for dynamic values in actions.

### Available Variables

| Variable | Description |
|----------|-------------|
| `title` | Work item title |
| `description` | Work item description |
| `type` | Work item type |
| `state` | Current state |
| `priority` | Priority level |
| `labels` | Array of labels |
| `assignee` | First assignee |
| `assignees` | All assignees |

### Date Functions

| Function | Result |
|----------|--------|
| `${{ today }}` | `2025-12-01` |
| `${{ now }}` | `2025-12-01T14:30:00` |
| `${{ today + days(3) }}` | `2025-12-04` |
| `${{ today + weeks(1) }}` | `2025-12-08` |

### Examples

```yaml
do:
  - comment: "Hi ${{ assignee }}, this is assigned to you!"
  
  - set:
      due_date: ${{ today + days(3) }}
  
  - notify:
      message: "🔔 ${{ title }} - Priority: ${{ priority }}"
```

---

## Scripts

For complex logic that YAML can't express, use TypeScript:

### Create a Script

```bash
plane automations new "SLA escalation" --script
```

This creates two files:

**automations/sla-escalation.yaml:**
```yaml
name: SLA escalation
on: work_item.updated
script: ./scripts/sla-escalation.ts
```

**automations/scripts/sla-escalation.ts:**
```typescript
interface Context {
  workItem: {
    id: string;
    title: string;
    type: string;
    state: string;
    priority: string;
    labels: string[];
    createdAt: string;
    updatedAt: string;
  };
  trigger: {
    event: string;
    changes?: Record<string, { from: any; to: any }>;
  };
}

interface Action {
  type: string;
  [key: string]: any;
}

export default function run(context: Context): Action[] {
  const { workItem } = context;
  const actions: Action[] = [];
  
  // Your logic here
  if (workItem.priority === 'urgent') {
    const hoursSinceCreated = /* calculate */;
    
    if (hoursSinceCreated > 4) {
      actions.push({
        type: 'notify',
        channel: '#escalations',
        message: `⚠️ SLA breach: ${workItem.title}`
      });
    }
  }
  
  return actions;
}
```

### Script Requirements

1. **Default export** - Must export a `run` function
2. **Returns actions** - Return an array of action objects
3. **Pure function** - No side effects (API calls, file writes)
4. **Sandboxed** - Runs in Deno with limited permissions

### Action Types from Scripts

```typescript
// Set fields
{ type: 'set', priority: 'urgent', state: 'in_progress' }

// Assign
{ type: 'assign', user: 'alice@example.com' }

// Add label
{ type: 'addLabel', label: 'escalated' }

// Comment
{ type: 'comment', text: 'SLA breach detected' }

// Notify
{ type: 'notify', channel: '#team', message: 'Alert!' }
```

---

## CLI Reference

### Commands

```bash
# List all automations
plane automations list

# Validate automations
plane automations validate

# Test an automation
plane automations test "Name" [options]

# Show automation details
plane automations show "Name"

# Get automation info
plane automations info "Name"

# Create new automation
plane automations new "Name" [--script]

# Visualize automation flow
plane automations viz "Name" [--format ascii|mermaid|html|png]

# Generate docs for all automations
plane automations viz-all --format html
```

### Test Command Options

```bash
plane automations test "Bug triage" \
  --type bug \
  --state todo \
  --priority high \
  --labels "critical,frontend" \
  --title "Login broken"
```

| Option | Description |
|--------|-------------|
| `--type` | Work item type |
| `--state` | Current state |
| `--priority` | Priority level |
| `--labels` | Comma-separated labels |
| `--title` | Work item title |
| `--input` | JSON file with full context |

### Visualization Options

```bash
# ASCII flowchart in terminal
plane automations viz "Bug triage"

# Mermaid diagram (for docs)
plane automations viz "Bug triage" -f mermaid -o flow.md

# Interactive HTML
plane automations viz "Bug triage" -f html --open

# PNG image
plane automations viz "Bug triage" -f png -o flow.png
```

---

## Examples

### Auto-Triage Bugs

```yaml
name: Bug triage
description: Automatically triage new bugs based on labels

on: work_item.created

when:
  type: bug

do:
  - when: labels contains "critical"
    set:
      priority: urgent
      state: in_progress
    assign: oncall@example.com
    notify:
      channel: "#critical"
      message: "🚨 Critical bug: ${{ title }}"

  - when: labels contains "security"
    set:
      priority: urgent
    add_label: security-review

  - otherwise: true
    set:
      state: backlog
    add_label: needs-triage
```

### SLA Due Dates

```yaml
name: SLA due dates
description: Set due dates based on priority

on: work_item.created

do:
  - when: priority == "urgent"
    set:
      due_date: ${{ today + days(1) }}

  - when: priority == "high"
    set:
      due_date: ${{ today + days(3) }}

  - when: priority == "medium"
    set:
      due_date: ${{ today + days(7) }}
```

### Notify on Completion

```yaml
name: Notify on done
description: Notify team when high-priority items are completed

on:
  event: work_item.updated
  fields: [state]

when:
  priority: [urgent, high]

do:
  - when: state changed_to: done
    notify:
      channel: "#releases"
      message: "✅ Completed: ${{ title }}"
    comment: "🎉 Great work closing this!"
```

### Stale Item Check (with Script)

```yaml
name: Stale check
description: Find and label stale items

on:
  schedule: "0 9 * * MON"  # Every Monday at 9am

script: ./scripts/stale-check.ts
```

```typescript
// scripts/stale-check.ts
export default function run(context: Context): Action[] {
  const { workItem } = context;
  const actions: Action[] = [];
  
  const updatedAt = new Date(workItem.updatedAt);
  const daysSinceUpdate = (Date.now() - updatedAt.getTime()) / (1000 * 60 * 60 * 24);
  
  if (daysSinceUpdate > 14 && workItem.state !== 'done') {
    actions.push(
      { type: 'addLabel', label: 'stale' },
      { type: 'comment', text: `⚠️ This item hasn't been updated in ${Math.floor(daysSinceUpdate)} days.` }
    );
  }
  
  return actions;
}
```

---

## Best Practices

### 1. Start Simple

Begin with basic YAML automations. Only use scripts when needed.

```yaml
# Good: Simple and clear
do:
  - set:
      priority: high

# Avoid: Over-engineering
script: ./scripts/set-priority.ts  # Don't use scripts for simple tasks
```

### 2. Use Meaningful Names

```yaml
# Good
name: Auto-assign critical bugs to on-call

# Bad
name: automation1
```

### 3. Test Before Deploying

```bash
# Always test with realistic data
plane automations test "My automation" --type bug --labels critical
```

### 4. Use `otherwise` for Default Cases

```yaml
do:
  - when: priority == "urgent"
    assign: urgent-team@example.com

  - when: priority == "high"
    assign: high-priority@example.com

  - otherwise: true  # Catch-all
    add_label: needs-assignment
```

### 5. Keep Scripts Focused

```typescript
// Good: Single responsibility
export default function run(context: Context): Action[] {
  // One clear purpose
}

// Bad: Too much in one script
export default function run(context: Context): Action[] {
  // Triage + escalation + notification + reporting...
}
```

### 6. Document Your Automations

```yaml
name: Bug triage
description: |
  Automatically triage new bugs:
  - Critical bugs → urgent priority, assign on-call
  - Security bugs → security-review label
  - Others → backlog state
```

---

## Troubleshooting

### Automation Not Triggering

1. **Check the trigger:**
   ```bash
   plane automations info "My automation"
   ```

2. **Verify conditions match:**
   ```bash
   plane automations test "My automation" --type bug
   ```

3. **Check if enabled:**
   ```yaml
   enabled: true  # Must be true (default)
   ```

### Script Errors

1. **Validate syntax:**
   ```bash
   plane automations validate
   ```

2. **Check Deno is installed:**
   ```bash
   deno --version
   ```

3. **Test the script:**
   ```bash
   plane automations test "My automation" --type bug
   ```

### Expression Errors

Use native CEL syntax for complex conditions:

```yaml
# Instead of this (may have issues):
when: labels contains critical and priority == high

# Use this (explicit CEL):
when: "'critical' in work_item.labels && work_item.priority == 'high'"
```

---

## Next Steps

- [Full CEL Reference](https://github.com/google/cel-spec)
- [Automation Examples](./examples/)
- [API Integration Guide](../api/webhooks.md)


