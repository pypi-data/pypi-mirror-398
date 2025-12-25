# Automations Quick Reference

One-page reference for Plane automations.

---

## Basic Structure

```yaml
name: My automation              # Required
description: What it does        # Optional
enabled: true                    # Default: true

on: work_item.created            # Trigger

when:                            # Filter conditions
  type: bug

do:                              # Actions
  - set:
      priority: high
```

---

## Triggers

| Trigger | When |
|---------|------|
| `work_item.created` | Item created |
| `work_item.updated` | Item updated |
| `work_item.deleted` | Item deleted |
| `work_item.state_changed` | State changed |
| `work_item.assigned` | Assignee added |
| `comment.created` | Comment added |
| `schedule: "0 9 * * MON"` | Cron schedule |

---

## Conditions

### In `when:` block (simple matching)

```yaml
when:
  type: bug                    # Equals
  state: [todo, backlog]       # In list
  assignee: null               # Is null
```

### In `do:` block (CEL expressions)

```yaml
do:
  - when: work_item.priority == 'high'
  - when: 'critical' in work_item.labels
  - when: size(work_item.labels) > 0
  - when: work_item.assignee == null
  - otherwise: true            # Default case
```

---

## CEL Operators

| Operator | Example |
|----------|---------|
| `==` | `work_item.type == 'bug'` |
| `!=` | `work_item.state != 'done'` |
| `in` | `'bug' in work_item.labels` |
| `size()` | `size(work_item.labels) > 0` |
| `&&` | `a == 'x' && b == 'y'` |
| `\|\|` | `a == 'x' \|\| a == 'y'` |
| `!` | `!(state == 'done')` |

---

## Actions

```yaml
# Set fields
- set:
    priority: high
    state: in_progress

# Assign/unassign
- assign: user@example.com
- unassign: user@example.com

# Labels
- add_label: needs-review
- add_label: [urgent, bug]
- remove_label: stale

# Comment
- comment: "Hello ${{ assignee }}!"

# Notify
- notify:
    channel: "#team"
    message: "New: ${{ title }}"
```

---

## Expressions `${{ }}`

| Expression | Result |
|------------|--------|
| `${{ title }}` | Work item title |
| `${{ priority }}` | Priority value |
| `${{ assignee }}` | First assignee |
| `${{ today }}` | `2025-12-01` |
| `${{ today + days(3) }}` | `2025-12-04` |
| `${{ today + weeks(1) }}` | `2025-12-08` |

---

## CLI Commands

```bash
# List automations
plane automations list

# Validate
plane automations validate

# Test
plane automations test "Name" --type bug --labels critical

# Create new
plane automations new "Name"
plane automations new "Name" --script

# Show details
plane automations show "Name"
plane automations info "Name"

# Visualize
plane automations viz "Name"
plane automations viz "Name" -f png -o flow.png
```

---

## Complete Example

```yaml
name: Bug triage
description: Auto-triage bugs based on labels

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
      message: "🚨 ${{ title }}"

  - when: labels contains "security"
    set:
      priority: urgent
    add_label: security-review

  - otherwise: true
    set:
      state: backlog
    add_label: needs-triage
```

---

## Script Template

```typescript
// automations/scripts/my-script.ts

interface Context {
  workItem: {
    id: string;
    title: string;
    type: string;
    state: string;
    priority: string;
    labels: string[];
  };
}

interface Action {
  type: string;
  [key: string]: any;
}

export default function run(context: Context): Action[] {
  const { workItem } = context;
  const actions: Action[] = [];
  
  if (workItem.priority === 'urgent') {
    actions.push({
      type: 'notify',
      channel: '#alerts',
      message: `Urgent: ${workItem.title}`
    });
  }
  
  return actions;
}
```

Reference in YAML:
```yaml
name: My script automation
on: work_item.created
script: ./scripts/my-script.ts
```


