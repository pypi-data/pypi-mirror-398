# Automation Examples

Real-world examples you can copy and customize.

---

## Bug Triage

Automatically categorize and route bugs based on labels.

```yaml
name: Bug triage
description: Route bugs to the right team based on labels

on: work_item.created

when:
  type: bug

do:
  # Critical bugs get immediate attention
  - when: labels contains "critical"
    set:
      priority: urgent
      state: in_progress
    assign: oncall@example.com
    notify:
      channel: "#critical-bugs"
      message: "🚨 Critical bug needs attention: ${{ title }}"

  # Security issues go to security team
  - when: labels contains "security"
    set:
      priority: urgent
    add_label: security-review
    assign: security-team@example.com
    notify:
      channel: "#security"
      message: "🔒 Security issue: ${{ title }}"

  # Frontend bugs
  - when: labels contains "frontend"
    set:
      priority: high
    assign: frontend-lead@example.com

  # Backend bugs
  - when: labels contains "backend"
    set:
      priority: high
    assign: backend-lead@example.com

  # Everything else goes to backlog
  - otherwise: true
    set:
      state: backlog
    add_label: needs-triage
```

**Test it:**
```bash
plane automations test "Bug triage" --type bug --labels critical
plane automations test "Bug triage" --type bug --labels security
plane automations test "Bug triage" --type bug --labels frontend
plane automations test "Bug triage" --type bug --labels random
```

---

## SLA Due Dates

Set due dates based on priority.

```yaml
name: SLA due dates
description: Automatically set due dates based on priority level

on: work_item.created

do:
  # Urgent = 1 day
  - when: priority == "urgent"
    set:
      due_date: ${{ today + days(1) }}
    comment: "⏰ SLA: Due in 1 day (urgent priority)"

  # High = 3 days
  - when: priority == "high"
    set:
      due_date: ${{ today + days(3) }}
    comment: "⏰ SLA: Due in 3 days (high priority)"

  # Medium = 7 days
  - when: priority == "medium"
    set:
      due_date: ${{ today + days(7) }}
    comment: "⏰ SLA: Due in 7 days (medium priority)"

  # Low = 14 days
  - when: priority == "low"
    set:
      due_date: ${{ today + days(14) }}
```

**Test it:**
```bash
plane automations test "SLA due dates" --priority urgent
plane automations test "SLA due dates" --priority high
```

---

## Auto-Assign by Team

Route work to team members based on labels.

```yaml
name: Auto-assign by team
description: Assign work items to team leads based on area labels

on: work_item.created

do:
  - when: "'frontend' in work_item.labels || 'ui' in work_item.labels || 'react' in work_item.labels"
    assign: frontend@example.com
    comment: "👋 Assigned to Frontend team"

  - when: "'backend' in work_item.labels || 'api' in work_item.labels || 'database' in work_item.labels"
    assign: backend@example.com
    comment: "👋 Assigned to Backend team"

  - when: "'devops' in work_item.labels || 'infra' in work_item.labels || 'ci' in work_item.labels"
    assign: devops@example.com
    comment: "👋 Assigned to DevOps team"

  - when: "'mobile' in work_item.labels || 'ios' in work_item.labels || 'android' in work_item.labels"
    assign: mobile@example.com
    comment: "👋 Assigned to Mobile team"
```

---

## Notify on Completion

Alert the team when important items are done.

```yaml
name: Notify on done
description: Send notifications when high-priority items are completed

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
    comment: "🎉 Great work closing this high-priority item!"
```

**Test it:**
```bash
# This should match - state changed to done
plane automations test "Notify on done" --priority high --state done

# This should not match - wrong priority
plane automations test "Notify on done" --priority low --state done
```

---

## Welcome New Assignees

Send a welcome message when someone is assigned.

```yaml
name: Welcome assignee
description: Welcome message when someone is assigned to an item

on: work_item.assigned

do:
  - comment: |
      👋 Hi ${{ assignee }}! You've been assigned to this item.
      
      **Quick links:**
      - [Team Guidelines](https://wiki.example.com/guidelines)
      - [How to Update Status](https://wiki.example.com/status)
      
      Let us know if you have questions!
```

---

## Blocker Alert

Alert when items are marked as blocked.

```yaml
name: Blocker alert
description: Notify team when items are blocked

on:
  event: work_item.labeled

do:
  - when: labels contains "blocked"
    notify:
      channel: "#blockers"
      message: "🚫 Blocked: ${{ title }}"
    comment: |
      ⚠️ This item has been marked as blocked.
      
      Please add a comment explaining what's blocking progress.
```

---

## PR Linked Status

Update status based on linked PR.

```yaml
name: PR linked
description: Update state when PR is linked

on:
  event: work_item.updated
  fields: [links]

do:
  - when: "'pr' in work_item.labels || 'has-pr' in work_item.labels"
    set:
      state: in_review
    comment: "🔗 PR linked - moving to review"
```

---

## Stale Item Detection (Script)

Complex logic using TypeScript.

**automations/stale-check.yaml:**
```yaml
name: Stale check
description: Find and label items that haven't been updated

on:
  schedule: "0 9 * * MON"  # Every Monday at 9am

script: ./scripts/stale-check.ts
```

**automations/scripts/stale-check.ts:**
```typescript
interface Context {
  workItem: {
    id: string;
    title: string;
    state: string;
    labels: string[];
    updatedAt: string;
  };
}

interface Action {
  type: string;
  [key: string]: any;
}

export default function run(context: Context): Action[] {
  const { workItem } = context;
  const actions: Action[] = [];

  // Skip if already done or already marked stale
  if (workItem.state === 'done' || workItem.labels.includes('stale')) {
    return actions;
  }

  // Calculate days since last update
  const updatedAt = new Date(workItem.updatedAt);
  const now = new Date();
  const daysSinceUpdate = Math.floor(
    (now.getTime() - updatedAt.getTime()) / (1000 * 60 * 60 * 24)
  );

  // Mark as stale if no updates in 14 days
  if (daysSinceUpdate > 14) {
    actions.push(
      { type: 'addLabel', label: 'stale' },
      {
        type: 'comment',
        text: `⚠️ This item hasn't been updated in ${daysSinceUpdate} days. Is it still relevant?`
      }
    );
  }

  // Warn if approaching stale (10+ days)
  else if (daysSinceUpdate > 10) {
    actions.push({
      type: 'comment',
      text: `📅 Reminder: This item hasn't been updated in ${daysSinceUpdate} days.`
    });
  }

  return actions;
}
```

---

## SLA Escalation (Script)

Escalate items that breach SLA.

**automations/escalation.yaml:**
```yaml
name: SLA escalation
description: Escalate items that breach SLA thresholds

on:
  schedule: "*/30 * * * *"  # Every 30 minutes

script: ./scripts/escalation.ts
```

**automations/scripts/escalation.ts:**
```typescript
interface Context {
  workItem: {
    id: string;
    title: string;
    priority: string;
    state: string;
    labels: string[];
    createdAt: string;
  };
}

interface Action {
  type: string;
  [key: string]: any;
}

// SLA thresholds in hours
const SLA_HOURS: Record<string, number> = {
  urgent: 4,
  high: 24,
  medium: 72,
  low: 168  // 1 week
};

export default function run(context: Context): Action[] {
  const { workItem } = context;
  const actions: Action[] = [];

  // Skip completed items
  if (workItem.state === 'done' || workItem.state === 'cancelled') {
    return actions;
  }

  // Skip already escalated
  if (workItem.labels.includes('escalated')) {
    return actions;
  }

  // Calculate hours since creation
  const createdAt = new Date(workItem.createdAt);
  const hoursSinceCreated = (Date.now() - createdAt.getTime()) / (1000 * 60 * 60);

  // Get SLA threshold
  const threshold = SLA_HOURS[workItem.priority] || SLA_HOURS.medium;

  // Check for breach
  if (hoursSinceCreated > threshold) {
    actions.push(
      { type: 'addLabel', label: 'escalated' },
      { type: 'addLabel', label: 'sla-breach' },
      {
        type: 'notify',
        channel: '#escalations',
        message: `🚨 SLA BREACH: "${workItem.title}" exceeded ${threshold}h threshold (${Math.floor(hoursSinceCreated)}h)`
      },
      {
        type: 'comment',
        text: `⚠️ **SLA Breach**\n\nThis ${workItem.priority} priority item has been open for ${Math.floor(hoursSinceCreated)} hours, exceeding the ${threshold}-hour SLA.`
      }
    );
  }

  return actions;
}
```

---

## Smart Labeling (Script)

Auto-label based on content analysis.

**automations/smart-labeler.yaml:**
```yaml
name: Smart labeler
description: Auto-label based on title and description keywords

on: work_item.created

script: ./scripts/smart-labeler.ts
```

**automations/scripts/smart-labeler.ts:**
```typescript
interface Context {
  workItem: {
    title: string;
    description: string;
    labels: string[];
  };
}

interface Action {
  type: string;
  [key: string]: any;
}

// Keyword patterns for auto-labeling
const PATTERNS: Array<{ keywords: string[]; label: string }> = [
  { keywords: ['crash', 'error', 'exception', 'fail'], label: 'bug' },
  { keywords: ['security', 'vulnerability', 'cve', 'auth'], label: 'security' },
  { keywords: ['performance', 'slow', 'timeout', 'memory'], label: 'performance' },
  { keywords: ['ui', 'button', 'layout', 'css', 'style'], label: 'frontend' },
  { keywords: ['api', 'endpoint', 'database', 'query'], label: 'backend' },
  { keywords: ['docs', 'documentation', 'readme'], label: 'documentation' },
  { keywords: ['test', 'testing', 'coverage'], label: 'testing' },
];

export default function run(context: Context): Action[] {
  const { workItem } = context;
  const actions: Action[] = [];

  // Combine title and description for analysis
  const content = `${workItem.title} ${workItem.description || ''}`.toLowerCase();

  // Check each pattern
  for (const pattern of PATTERNS) {
    // Skip if already has this label
    if (workItem.labels.includes(pattern.label)) {
      continue;
    }

    // Check if any keyword matches
    const hasMatch = pattern.keywords.some(keyword => content.includes(keyword));

    if (hasMatch) {
      actions.push({ type: 'addLabel', label: pattern.label });
    }
  }

  return actions;
}
```

---

## Tips for Writing Automations

### 1. Test incrementally

```bash
# Test each condition separately
plane automations test "My auto" --labels critical
plane automations test "My auto" --labels security
plane automations test "My auto" --labels random
```

### 2. Use visualization

```bash
# See the flow
plane automations viz "My auto"

# Generate docs
plane automations viz-all -f html
```

### 3. Start with YAML, move to scripts

Most automations don't need scripts. Only use TypeScript when you need:
- Complex date/time calculations
- External data lookups
- Multi-step conditional logic
- Custom algorithms

### 4. Keep it DRY

If you're repeating patterns, consider:
- Using config values: `${{ config.team.lead }}`
- Creating reusable scripts
- Breaking into smaller automations


