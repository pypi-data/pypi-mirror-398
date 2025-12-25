# 🔧 Troubleshooting Guide

## Common Issues

### Authentication Errors

#### Issue: `Authentication failed. Check your API key.`

**Symptoms:**
```
✗ Error: Authentication failed. Check your API key.
```

**Causes:**
- Invalid API key
- Expired API key
- Missing API key

**Solutions:**

1. **Re-authenticate:**
```bash
plane auth logout
plane auth login
# Enter your API key when prompted
```

2. **Verify API key:**
```bash
plane auth whoami
```

3. **Check credentials file:**
```bash
cat ~/.config/plane-compose/credentials
# Should contain valid API key
```

4. **Use environment variable:**
```bash
export PLANE_API_KEY=your_key_here
plane auth whoami
```

---

### Permission Errors

#### Issue: `Permission denied for {resource}`

**Symptoms:**
```
✗ Error: Permission denied for projects
```

**Causes:**
- Insufficient workspace permissions
- Project-level access restrictions
- API key from different workspace

**Solutions:**

1. **Verify workspace access:**
   - Check you have write access to the workspace
   - Ask workspace admin to grant permissions

2. **Check plane.yaml:**
```yaml
workspace: correct-workspace-slug  # Must match your access
```

3. **Verify project access:**
```bash
plane status
# Will show if project is accessible
```

---

### Project Not Found

#### Issue: `Project not found`

**Symptoms:**
```
✗ Error: Project not found
```

**Causes:**
- Wrong project UUID
- Project deleted
- Wrong workspace

**Solutions:**

1. **Verify project UUID:**
```bash
# Check plane.yaml
cat plane.yaml | grep uuid

# If UUID is wrong, remove it
vim plane.yaml
# Delete the uuid line

# Push schema to recreate/find project
plane schema push
```

2. **Check project exists in Plane:**
   - Log in to Plane web app
   - Verify project exists in workspace

3. **Clone project again:**
```bash
# Get fresh copy
plane clone <correct-uuid> --workspace <workspace>
```

---

### Rate Limit Errors

#### Issue: `Rate limit exceeded`

**Symptoms:**
```
✗ Error: Rate limit exceeded. Retry after 60 seconds
```

**Causes:**
- Too many API requests
- Exceeded 50 requests/minute limit

**Solutions:**

1. **Wait and retry:**
```bash
# Wait for the retry-after period
sleep 60
plane push
```

2. **Check rate limit stats:**
```bash
plane rate stats

# Output shows current usage:
# Last Minute: 52 / 50
# Wait a bit and retry
```

3. **Reduce rate limit (for testing):**
```bash
export PLANE_RATE_LIMIT_PER_MINUTE=30
plane push
```

4. **Reset stats:**
```bash
plane rate reset
```

---

### Sync Issues

#### Issue: Duplicate work items being created

**Symptoms:**
```
✓ Created 6 work items
# But you only added 3 new items
```

**Causes:**
- Corrupted state.json
- Items without IDs
- Multiple files with same items

**Solutions:**

1. **Check state.json:**
```bash
cat .plane/state.json
```

2. **Add IDs to work items:**
```yaml
# Before (no stable ID)
- title: "My task"
  type: "task"

# After (with stable ID)
- id: "my-task-001"
  title: "My task"
  type: "task"
```

3. **Reset state if corrupted:**
```bash
# Backup first
cp .plane/state.json .plane/state.json.backup

# Remove state
rm .plane/state.json

# Pull to rebuild state
plane pull

# Check and push
plane status
plane push
```

4. **Organize work files:**
```bash
# Don't duplicate items across files
work/
├── inbox.yaml      # New items
├── backlog.yaml    # Backlog items
└── done.yaml       # Completed items
```

---

#### Issue: Changes not being detected

**Symptoms:**
```
plane status
# Shows: Everything is up to date
# But you made changes
```

**Causes:**
- Content hash unchanged
- State not updated

**Solutions:**

1. **Force push:**
```bash
plane push --force
```

2. **Check file is being read:**
```bash
# Ensure file is in work/ directory
ls work/
```

3. **Verify YAML syntax:**
```bash
# Install yamllint
pip install yamllint

# Check syntax
yamllint work/*.yaml
```

4. **Clear state and re-sync:**
```bash
rm .plane/state.json
plane pull
plane push
```

---

### Schema Errors

#### Issue: `Invalid work item type`

**Symptoms:**
```
✗ Error: Invalid work item type: "featur" (typo)
```

**Causes:**
- Typo in type name
- Type not defined in schema
- Schema not pushed

**Solutions:**

1. **Check schema:**
```bash
cat schema/types.yaml
```

2. **Verify type exists:**
```yaml
# schema/types.yaml must have:
feature:
  description: "..."
  workflow: "standard"
```

3. **Push schema first:**
```bash
plane schema push
```

4. **Fix typo in work item:**
```yaml
# Before
- title: "My task"
  type: "featur"  # Wrong

# After
- title: "My task"
  type: "feature"  # Correct
```

---

#### Issue: `Invalid state`

**Symptoms:**
```
✗ Error: State "in-progress" not found
```

**Causes:**
- State name doesn't match schema
- Wrong workflow

**Solutions:**

1. **Check state name in schema:**
```bash
cat schema/workflows.yaml
```

2. **Use exact state name:**
```yaml
# schema/workflows.yaml has:
standard:
  states:
    - name: "in_progress"  # Note: underscore, not hyphen

# work/inbox.yaml should use:
- title: "My task"
  state: "in_progress"  # Match exactly
```

---

### File Issues

#### Issue: `File not found: plane.yaml`

**Symptoms:**
```
✗ Error: File not found: plane.yaml
```

**Causes:**
- Running command outside project directory
- plane.yaml doesn't exist

**Solutions:**

1. **Check current directory:**
```bash
pwd
ls -la | grep plane.yaml
```

2. **Navigate to project:**
```bash
cd /path/to/your/project
plane status
```

3. **Initialize project if missing:**
```bash
plane init
```

---

#### Issue: `Invalid YAML syntax`

**Symptoms:**
```
✗ Error: Invalid YAML syntax at line 10
```

**Causes:**
- YAML formatting errors
- Wrong indentation
- Missing quotes

**Solutions:**

1. **Validate YAML:**
```bash
# Online: https://www.yamllint.com/
# Or use yamllint:
pip install yamllint
yamllint work/inbox.yaml
```

2. **Common YAML mistakes:**

```yaml
# Wrong: Inconsistent indentation
- title: "Task 1"
   type: "task"  # 3 spaces instead of 2

# Right:
- title: "Task 1"
  type: "task"  # 2 spaces

# Wrong: Special characters without quotes
- title: Task: fix bug  # Colon breaks parsing

# Right:
- title: "Task: fix bug"  # Quoted

# Wrong: Missing hyphen for list item
- title: "Task 1"
  type: "task"
  children:
    title: "Subtask"  # Missing hyphen

# Right:
- title: "Task 1"
  type: "task"
  children:
    - title: "Subtask"  # Has hyphen
```

---

### Network Issues

#### Issue: `Connection timeout`

**Symptoms:**
```
✗ Error: Connection timeout
```

**Causes:**
- Network connectivity issues
- Plane API down
- Firewall blocking requests

**Solutions:**

1. **Check internet connection:**
```bash
ping api.plane.so
```

2. **Verify Plane status:**
   - Check https://plane.so/status
   - Check Plane Discord/Twitter

3. **Check firewall:**
```bash
# Allow HTTPS traffic
# Check corporate firewall settings
```

4. **Increase timeout:**
```bash
export PLANE_API_TIMEOUT=60
plane push
```

---

### Installation Issues

#### Issue: `Command not found: plane`

**Symptoms:**
```bash
plane --help
# bash: plane: command not found
```

**Causes:**
- Not installed globally
- pipx not in PATH

**Solutions:**

1. **Install globally:**
```bash
pipx install plane-cli
```

2. **Check pipx installation:**
```bash
pipx list | grep plane-cli
```

3. **Reinstall:**
```bash
pipx uninstall plane-cli
pipx install plane-cli
```

4. **Check PATH:**
```bash
echo $PATH | grep pipx
# Should include ~/.local/bin
```

---

#### Issue: `Module not found` errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'planecompose'
```

**Causes:**
- Incomplete installation
- Wrong Python environment

**Solutions:**

1. **Reinstall:**
```bash
pipx reinstall plane-cli
```

2. **Install in venv (for development):**
```bash
cd /path/to/compose
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

---

## Debugging

### Enable Debug Logging

```bash
# Method 1: CLI flag
plane --debug push

# Method 2: Environment variable
export PLANE_DEBUG=true
plane push

# View logs
tail -f ~/.config/plane-cli/plane.log
```

### Verbose Output

```bash
plane --verbose push
```

### Check State

```bash
# View current state
cat .plane/state.json | python3 -m json.tool

# View remote items
cat .plane/remote/items.yaml
```

## Getting Help

### Command Help

```bash
# General help
plane --help

# Command-specific help
plane push --help
plane apply --help
```

### Report Issues

When reporting issues, include:

1. **Command run:**
```bash
plane --verbose push
```

2. **Error output:**
```
Copy full error message
```

3. **Environment:**
```bash
plane --version
python3 --version
cat plane.yaml
```

4. **Logs:**
```bash
cat ~/.config/plane-cli/plane.log | tail -50
```

### Community Support

- **GitHub Issues**: https://github.com/makeplane/compose/issues
- **Discord**: Join Plane Discord
- **Documentation**: https://docs.plane.so

---

## Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Auth failed | `plane auth logout && plane auth login` |
| Rate limit | `plane rate stats` and wait |
| Duplicates | Add `id` field to items |
| Not found | Check `plane.yaml` workspace/UUID |
| Permission denied | Verify workspace access |
| Sync issues | `rm .plane/state.json && plane pull` |
| Type errors | `plane schema push` first |
| YAML errors | Use YAML validator |
| Network timeout | Check connectivity, increase timeout |
| Command not found | `pipx install plane-cli` |

---

## Preventive Measures

### Best Practices

1. **Always use IDs:**
```yaml
- id: "unique-id"
  title: "..."
```

2. **Push schema first:**
```bash
plane schema push  # Before pushing work items
```

3. **Pull before push:**
```bash
plane pull  # Get latest
plane push  # Then push changes
```

4. **Commit state:**
```bash
git add .plane/state.json
git commit -m "Update state"
```

5. **Use version control:**
```bash
git add work/ schema/ plane.yaml
git commit -m "Update work items"
```

6. **Regular backups:**
```bash
cp -r .plane .plane.backup
```

