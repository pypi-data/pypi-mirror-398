# 📚 Plane Compose Examples

## Basic Workflows

### 1. Starting a New Project

```bash
# Initialize project structure
plane init my-project
cd my-project

# Edit plane.yaml with your workspace
vim plane.yaml

# Authenticate
plane auth login

# Push schema to create project in Plane
plane schema push

# Add work items in work/inbox.yaml
vim work/inbox.yaml

# Push work items
plane push

# Check status
plane status
```

### 2. Cloning an Existing Project

```bash
# Clone project from Plane by UUID
plane clone ba251175-682e-4e59-aa0c-0d37f59f1a54 --workspace my-workspace

# Navigate to cloned project
cd <project-name>

# Check what was pulled
cat .plane/remote/items.yaml

# Make changes
vim work/inbox.yaml

# Push changes
plane push
```

### 3. Collaborative Workflow

```bash
# Pull latest items from Plane
plane pull

# Make local changes
vim work/features.yaml

# Preview changes
plane status

# Push only your changes (collaborative mode)
plane push
```

## Advanced Examples

### 4. Declarative Project Management

```bash
# Define scope in plane.yaml
cat >> plane.yaml << EOF
apply_scope:
  labels: ["frontend"]
  assignee: "dev@example.com"
EOF

# Apply declarative changes
plane apply

# This will:
# - Create/update items in work/*.yaml
# - DELETE remote items with label "frontend" not in local files
```

### 5. Schema Management

#### Define Custom Work Item Types

```yaml
# schema/types.yaml
feature:
  description: "Large user-facing feature"
  workflow: "standard"
  parent_types: []
  fields:
    - name: "target_release"
      display_name: "Target Release"
      type: "text"
      required: false
    - name: "priority"
      display_name: "Priority"
      type: "option"
      required: true
      options: ["p0", "p1", "p2", "p3"]

bug:
  description: "Software defect"
  workflow: "bugfix"
  fields:
    - name: "severity"
      type: "option"
      options: ["critical", "major", "minor"]
      required: true
    - name: "affected_version"
      type: "text"
```

#### Define Workflows

```yaml
# schema/workflows.yaml
standard:
  states:
    - name: "backlog"
      group: "backlog"
      color: "#94a3b8"
    - name: "todo"
      group: "unstarted"
      color: "#3b82f6"
    - name: "in_progress"
      group: "started"
      color: "#f59e0b"
    - name: "review"
      group: "started"
      color: "#8b5cf6"
    - name: "done"
      group: "completed"
      color: "#22c55e"
  initial: "backlog"
  terminal: ["done"]

bugfix:
  states:
    - name: "reported"
      group: "backlog"
      color: "#ef4444"
    - name: "investigating"
      group: "started"
      color: "#f59e0b"
    - name: "fixing"
      group: "started"
      color: "#3b82f6"
    - name: "testing"
      group: "started"
      color: "#8b5cf6"
    - name: "verified"
      group: "completed"
      color: "#22c55e"
  initial: "reported"
  terminal: ["verified"]
```

#### Define Labels

```yaml
# schema/labels.yaml
groups:
  priority:
    color: "#ef4444"
    labels:
      - name: "urgent"
      - name: "high"
      - name: "medium"
      - name: "low"
  
  team:
    color: "#3b82f6"
    labels:
      - name: "frontend"
      - name: "backend"
      - name: "mobile"
      - name: "devops"
  
  status:
    color: "#8b5cf6"
    labels:
      - name: "blocked"
      - name: "needs-review"
      - name: "ready"
```

### 6. Complex Work Item Structures

#### Epic with Child Tasks

```yaml
# work/features.yaml
- id: "feat-auth"
  title: "User Authentication System"
  description: |
    Implement complete user authentication with OAuth2,
    email verification, and password reset.
  type: "epic"
  state: "in_progress"
  priority: "high"
  labels: ["backend", "security"]
  assignee: "tech-lead@example.com"
  watchers:
    - "pm@example.com"
    - "qa@example.com"
  
  children:
    - id: "task-auth-oauth"
      title: "Implement OAuth2 login"
      description: "Add Google, GitHub OAuth"
      type: "task"
      state: "in_progress"
      priority: "high"
      assignee: "dev1@example.com"
      labels: ["backend"]
    
    - id: "task-auth-email"
      title: "Email verification flow"
      type: "task"
      state: "todo"
      priority: "high"
      assignee: "dev2@example.com"
      labels: ["backend"]
    
    - id: "task-auth-reset"
      title: "Password reset functionality"
      type: "task"
      state: "todo"
      priority: "medium"
      labels: ["backend"]
```

#### Bugs with Rich Metadata

```yaml
# work/bugs.yaml
- id: "bug-001"
  title: "Login fails on Safari"
  description: |
    ## Steps to Reproduce
    1. Open Safari browser
    2. Navigate to /login
    3. Enter credentials
    4. Click Login button
    
    ## Expected
    User should be logged in
    
    ## Actual
    Error message: "Network request failed"
    
    ## Environment
    - Safari 17.0
    - macOS Sonoma
  type: "bug"
  state: "investigating"
  priority: "urgent"
  labels: ["frontend", "urgent", "safari"]
  assignee: "frontend-lead@example.com"
  watchers:
    - "qa@example.com"
    - "pm@example.com"
  
  # Custom fields (if defined in schema)
  severity: "critical"
  affected_version: "1.2.3"
  reported_by: "user@example.com"
```

### 7. Team-Based Workflows

#### Frontend Team

```yaml
# work/frontend.yaml
- id: "fe-001"
  title: "Redesign dashboard UI"
  type: "feature"
  state: "in_progress"
  labels: ["frontend", "ui/ux"]
  assignee: "designer@example.com"
  priority: "high"

- id: "fe-002"
  title: "Add dark mode support"
  type: "feature"
  state: "todo"
  labels: ["frontend", "accessibility"]
  assignee: "fe-dev@example.com"
  priority: "medium"
```

#### Backend Team

```yaml
# work/backend.yaml
- id: "be-001"
  title: "Optimize database queries"
  type: "improvement"
  state: "in_progress"
  labels: ["backend", "performance"]
  assignee: "backend-dev@example.com"
  priority: "high"

- id: "be-002"
  title: "Add API rate limiting"
  type: "feature"
  state: "todo"
  labels: ["backend", "security"]
  assignee: "backend-lead@example.com"
  priority: "high"
```

### 8. Using Labels for Organization

```yaml
# work/sprint-current.yaml
- title: "Implement user profile page"
  type: "feature"
  state: "in_progress"
  labels: ["sprint-23", "frontend", "high"]
  assignee: "dev1@example.com"

- title: "Fix memory leak in background worker"
  type: "bug"
  state: "in_progress"
  labels: ["sprint-23", "backend", "urgent"]
  assignee: "dev2@example.com"

- title: "Update API documentation"
  type: "task"
  state: "todo"
  labels: ["sprint-23", "documentation", "low"]
  assignee: "tech-writer@example.com"
```

### 9. Declarative Scope Management

```yaml
# plane.yaml - Define what you control
apply_scope:
  # Control all items with these labels
  labels: ["automated", "ci/cd"]
  
  # Or control items assigned to you
  assignee: "devops@example.com"
  
  # Or control items with ID prefix
  id_prefix: "AUTO-"

# work/automated.yaml
- id: "AUTO-001"
  title: "Run nightly tests"
  type: "task"
  state: "done"
  labels: ["automated", "ci/cd"]

- id: "AUTO-002"
  title: "Generate weekly reports"
  type: "task"
  state: "in_progress"
  labels: ["automated"]
```

```bash
# Apply declarative scope
# This will DELETE remote items matching scope not in local files
plane apply

# Preview before applying
plane apply --dry-run
```

### 10. Rate Limit Management

```bash
# Check rate limit statistics
plane rate stats

# Output:
# Rate Limit Statistics
# ┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
# ┃ Metric              ┃ Value  ┃
# ┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
# │ Total Requests      │ 145    │
# │ Last Minute         │ 12     │
# │ Last Hour           │ 145    │
# │ Rate Limit (minute) │ 50     │
# │ Rate Limit (hour)   │ 3000   │
# │ Utilization (min)   │ 24%    │
# │ Total Wait Time     │ 2.3s   │
# └─────────────────────┴────────┘

# Reset stats
plane rate reset

# Configure via environment
export PLANE_RATE_LIMIT_PER_MINUTE=30
plane push
```

## Common Patterns

### Pattern 1: Feature Branch Workflow

```bash
# Create feature branch
git checkout -b feature/new-dashboard

# Add work items for feature
cat > work/dashboard.yaml << EOF
- id: "dash-001"
  title: "Design dashboard mockups"
  type: "task"
  state: "done"
  
- id: "dash-002"
  title: "Implement dashboard components"
  type: "task"
  state: "in_progress"
EOF

# Push to Plane
plane push

# When feature is done, merge to main
git checkout main
git merge feature/new-dashboard
```

### Pattern 2: Sprint Planning

```bash
# Pull all items at start of sprint
plane pull

# Review remote items
cat .plane/remote/items.yaml

# Move items to sprint file
vim work/sprint-24.yaml

# Push sprint items
plane push

# Track sprint status
plane status
```

### Pattern 3: Bug Triage

```bash
# Pull latest bugs
plane pull

# Create bugs file
cat > work/bugs-nov.yaml << EOF
- id: "bug-nov-001"
  title: "..."
  state: "reported"
  priority: "urgent"
  labels: ["bug", "urgent"]
EOF

# Push bugs
plane push

# Track bug resolution
watch plane status
```

### Pattern 4: Release Management

```bash
# Tag release items
cat > work/v1.2.0.yaml << EOF
- title: "Feature A"
  labels: ["release-1.2.0", "feature"]
  
- title: "Feature B"
  labels: ["release-1.2.0", "feature"]
EOF

# Push release items
plane push

# Track release progress
plane status | grep "release-1.2.0"
```

## Environment Variables

```bash
# API Configuration
export PLANE_API_URL="https://custom.plane.so"
export PLANE_API_TIMEOUT=60

# Rate Limiting
export PLANE_RATE_LIMIT_PER_MINUTE=30

# Debugging
export PLANE_DEBUG=true
export PLANE_VERBOSE=true

# Logging
export PLANE_LOG_TO_FILE=true
```

## Tips & Tricks

### Tip 1: Use Descriptive IDs

```yaml
# Good
- id: "auth-oauth-google"
  title: "Add Google OAuth"

# Better than
- id: "task-001"
  title: "Add Google OAuth"
```

### Tip 2: Organize by Feature/Team

```
work/
├── auth/
│   ├── oauth.yaml
│   └── sessions.yaml
├── frontend/
│   ├── dashboard.yaml
│   └── profile.yaml
└── backend/
    ├── api.yaml
    └── database.yaml
```

### Tip 3: Use Templates

```bash
# Create template
cat > .templates/feature.yaml << EOF
- id: "CHANGE_ME"
  title: ""
  description: ""
  type: "feature"
  state: "backlog"
  priority: "medium"
  labels: []
  assignee: ""
EOF

# Use template
cp .templates/feature.yaml work/new-feature.yaml
vim work/new-feature.yaml
```

### Tip 4: Automate with Scripts

```bash
#!/bin/bash
# daily-sync.sh

# Pull latest
plane pull

# Push changes
plane push

# Check status
plane status

# Commit state
git add .plane/state.json work/
git commit -m "Daily sync: $(date)"
```

### Tip 5: Use Watchers for Visibility

```yaml
# Add stakeholders as watchers
- title: "Launch new feature"
  type: "feature"
  watchers:
    - "pm@example.com"      # Product manager
    - "qa@example.com"      # QA lead
    - "marketing@example.com"  # Marketing
```

## Troubleshooting Examples

### Issue: Duplicate Work Items

```bash
# Check state
cat .plane/state.json

# Reset state if corrupted
rm .plane/state.json
plane init  # Reinitialize

# Push again
plane push --force
```

### Issue: Sync Conflicts

```bash
# Pull latest
plane pull

# Review conflicts
diff work/inbox.yaml .plane/remote/items.yaml

# Resolve manually
vim work/inbox.yaml

# Push resolved
plane push
```

### Issue: Rate Limit Errors

```bash
# Check rate limit
plane rate stats

# Wait or reduce rate
export PLANE_RATE_LIMIT_PER_MINUTE=20

# Retry
plane push
```

