# Work Item Fields - Complete Reference

## Overview

Work items in `plane-cli` now support all essential Plane fields including dates, relationships, and multiple assignees.

---

## ✨ Supported Fields

### Basic Fields

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `title` | string | ✅ Yes | Work item title | `"Fix login bug"` |
| `description` | string | No | Detailed description (supports markdown/HTML) | `"Users cannot log in..."` |
| `type` | string | No | Work item type | `"Bug"`, `"Task"`, `"Feature"` |
| `state` | string | No | Current state | `"Backlog"`, `"In Progress"`, `"Done"` |
| `priority` | string | No | Priority level | `"urgent"`, `"high"`, `"medium"`, `"low"`, `"none"` |
| `labels` | list[string] | No | Labels/tags | `["bug", "frontend"]` |

### 📅 Date Fields (NEW!)

| Field | Type | Format | Description | Example |
|-------|------|--------|-------------|---------|
| `start_date` | string | YYYY-MM-DD | When work starts | `"2024-01-15"` |
| `due_date` | string | YYYY-MM-DD | When work is due | `"2024-01-31"` |

### 🔗 Relationship Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `parent` | string | Parent work item | `"PROJ-123"` or UUID |
| `children` | list[WorkItem] | Child work items (nested) | See hierarchy example below |

### 👥 Assignment Fields (NEW!)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `assignees` | list[string] | Assigned users (supports multiple!) | `["alice@example.com", "bob@example.com"]` |
| `watchers` | list[string] | Users watching this item | `["manager@example.com"]` |
| `assignee` | string | ⚠️ Deprecated (use `assignees` instead) | `"alice@example.com"` |

### 🎨 Custom Properties

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `properties` | dict | Custom properties defined in schema | `{"browser": ["Chrome", "Safari"], "severity": "high"}` |

---

## 📝 YAML Examples

### Complete Work Item

```yaml
- title: "Fix critical login bug"
  description: |
    Users are unable to log in when using social auth.
    This is blocking production deployment.
  type: Bug
  state: In Progress
  priority: urgent
  labels:
    - bug
    - security
    - frontend
  
  # Dates
  start_date: "2024-01-15"
  due_date: "2024-01-20"
  
  # Assignments (multiple assignees supported!)
  assignees:
    - alice@company.com
    - bob@company.com
  watchers:
    - manager@company.com
  
  # Parent relationship
  parent: "PROJ-42"  # Parent work item
  
  # Custom properties
  properties:
    browser:
      - Chrome
      - Safari
    severity: critical
    found_in_version: "2.1.0"
```

### Simple Work Item

```yaml
- title: "Update documentation"
  type: Task
  due_date: "2024-02-01"
  assignees:
    - tech-writer@company.com
```

### Work Item with Hierarchy

```yaml
- title: "Launch new feature"
  type: Epic
  start_date: "2024-01-01"
  due_date: "2024-03-31"
  assignees:
    - product-lead@company.com
  children:
    - title: "Design mockups"
      type: Task
      assignees:
        - designer@company.com
    - title: "Implement backend"
      type: Task
      assignees:
        - backend-dev@company.com
    - title: "Implement frontend"
      type: Task
      assignees:
        - frontend-dev@company.com
```

### Multiple Assignees

```yaml
# Team collaboration on a large task
- title: "Migrate database to PostgreSQL"
  type: Task
  priority: high
  start_date: "2024-02-01"
  due_date: "2024-02-15"
  assignees:
    - dba@company.com
    - backend-lead@company.com
    - devops@company.com
  watchers:
    - cto@company.com
    - product-manager@company.com
```

### Sprint Planning

```yaml
# Sprint items with dates and assignments
- title: "User authentication MVP"
  type: Feature
  state: Backlog
  start_date: "2024-02-01"
  due_date: "2024-02-14"
  assignees:
    - alice@company.com
  labels:
    - sprint-5
    - mvp

- title: "API rate limiting"
  type: Feature
  state: Backlog
  start_date: "2024-02-01"
  due_date: "2024-02-14"
  assignees:
    - bob@company.com
  labels:
    - sprint-5
    - infrastructure
```

---

## 🔄 Backwards Compatibility

### `assignee` → `assignees`

The old `assignee` field (singular) is still supported for backwards compatibility:

```yaml
# Old way (still works)
- title: "Old task"
  assignee: alice@company.com

# New way (recommended)
- title: "New task"
  assignees:
    - alice@company.com
```

**When both are present:**
- `assignees` takes precedence
- `assignee` is ignored if `assignees` is provided

---

## 🚀 Usage

### Creating Work Items with Dates

```yaml
# work/sprint-items.yaml
- title: "Implement user profile"
  type: Feature
  start_date: "2024-02-01"
  due_date: "2024-02-07"
  assignees:
    - developer@company.com
```

```bash
$ plane push
✓ Created 1 work items
  Completed in 8.5s
```

### Cloning with All Fields

```bash
$ plane clone <project-uuid> --workspace myteam
```

The cloned `items.yaml` will include all fields:
```yaml
- id: PROJ-123
  title: "Fix login bug"
  type: Bug
  state: In Progress
  start_date: "2024-01-15"
  due_date: "2024-01-20"
  assignees:
    - alice@company.com
    - bob@company.com
  parent: PROJ-100
  properties:
    severity: critical
```

---

## 📊 Field Behavior

### Date Formats

**Input (YAML):**
```yaml
start_date: "2024-01-15"  # ISO format: YYYY-MM-DD
due_date: "2024-01-31"
```

**API Mapping:**
- `start_date` → `start_date` (Plane API)
- `due_date` → `target_date` (Plane API)

### Parent Relationships

**Supported formats:**
```yaml
# Work item ID (e.g., "PROJ-123")
parent: "PROJ-42"

# UUID (less common, but supported)
parent: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Note:** When using work item ID format, ensure the parent exists in Plane.

### Assignees vs User IDs

**Current implementation:**
- Pass email addresses or user IDs directly
- **TODO:** Automatic resolution of emails to Plane user IDs

```yaml
# Works now
assignees:
  - alice@company.com
  - user-uuid-123

# Future improvement: automatic resolution
assignees:
  - alice  # Will resolve to alice@company.com or user ID
```

---

## 🔍 Checking API Response

To see what fields Plane returns for work items:

```bash
# Enable debug logging
$ plane --debug pull

# Check the log file
$ cat ~/.config/plane-cli/plane.log
```

**Common fields from Plane API:**
- `name` → `title`
- `description_html` → `description`
- `target_date` → `due_date`
- `start_date` → `start_date`
- `parent_id` → `parent`
- `assignees` → `assignees`
- `priority` → `priority`
- `labels` → `labels`
- `state` → `state`
- `type_id` → `type` (resolved to name)

---

## 🎯 Best Practices

### 1. Use Multiple Assignees for Collaboration

```yaml
- title: "Cross-functional project"
  assignees:
    - frontend-dev@company.com
    - backend-dev@company.com
    - designer@company.com
  watchers:
    - product-manager@company.com
```

### 2. Set Dates for Planning

```yaml
- title: "Q1 Feature Launch"
  start_date: "2024-01-01"
  due_date: "2024-03-31"
```

### 3. Use Parent for Epics

```yaml
# Epic
- id: PROJ-100
  title: "New Dashboard"
  type: Epic
  
# Subtasks (in separate file or same file)
- title: "Dashboard API"
  parent: "PROJ-100"
  
- title: "Dashboard UI"
  parent: "PROJ-100"
```

### 4. Track Watchers for Notifications

```yaml
- title: "Production deployment"
  assignees:
    - devops@company.com
  watchers:
    - cto@company.com
    - product-lead@company.com
    - qa-lead@company.com
```

---

## 🐛 Troubleshooting

### Assignees Not Showing

**Problem:** Assignees are not visible in Plane after push.

**Solutions:**
1. Ensure email addresses are correct
2. Verify users exist in the workspace
3. Check if you have permission to assign users

### Parent Not Linking

**Problem:** Parent relationship not created.

**Solutions:**
1. Ensure parent work item exists
2. Use correct format: `"PROJ-123"` or UUID
3. Parent must be created before children

### Dates Not Saving

**Problem:** Dates not showing in Plane.

**Solutions:**
1. Use ISO format: `"YYYY-MM-DD"`
2. Ensure dates are quoted strings in YAML
3. Check Plane API permissions

---

## 📖 Summary

**New Fields Added:**
- ✅ `start_date` - When work starts
- ✅ `due_date` - When work is due
- ✅ `assignees` (plural) - Multiple assignees support
- ✅ `parent` - Parent work item relationship
- ✅ Full field extraction during clone/pull

**All Commands Updated:**
- ✅ `plane push` - Creates/updates with all fields
- ✅ `plane pull` - Fetches all fields
- ✅ `plane clone` - Includes all fields
- ✅ Parser - Extracts all fields from YAML

**Next Steps:**
1. Update your YAML files with dates and assignees
2. Run `plane push` to sync
3. Verify in Plane UI

---

**Status**: ✅ All essential work item fields now supported!

