# Examples

This directory contains example projects and automation configurations to help you get started with Plane Compose.

## 📁 Directory Structure

### `hello/`
A complete example project demonstrating the basic structure of a Plane Compose project:
- **`plane.yaml`** - Project configuration
- **`schema/`** - Work item types, workflows, and labels definitions
- **`work/`** - Sample work items
- **`automations/`** - Example automation rules

This is a ready-to-use template. You can copy this folder and customize it for your own projects.

### `automations/`
A collection of automation examples demonstrating various use cases:
- **Auto-assignment rules** - Automatically assign work items based on labels or teams
- **Blocker alerts** - Notify teams when work items are blocked
- **Due date SLA management** - Track and escalate items approaching deadlines
- **Smart labeling** - Auto-categorize work items using ML
- **Stale issue checks** - Identify and manage inactive work items
- **PR linking** - Connect work items with pull requests
- **Triage workflows** - Automate bug triage processes

Each automation includes:
- YAML configuration files
- TypeScript scripts for complex logic
- HTML documentation pages

## 🚀 Getting Started

### Use the hello project as a template:

```bash
# Copy the example project
cp -r examples/hello my-project
cd my-project

# Edit configuration
vim plane.yaml

# Authenticate
plane auth login

# Push schema and work items
plane schema push
plane push
```

### Use automation examples:

```bash
# Copy specific automations to your project
cp examples/automations/auto-assign.yaml my-project/automations/
cp examples/automations/scripts/example.ts my-project/automations/scripts/

# Customize the automation rules in the YAML files
vim my-project/automations/auto-assign.yaml
```

## 📚 Learn More

- [Automations Documentation](../docs/automations/README.md) - Comprehensive guide to automations
- [Quick Reference](../docs/automations/quick-reference.md) - Automation syntax reference
- [Examples Guide](../docs/examples.md) - More usage examples

## 💡 Tips

1. **Start simple** - Begin with the `hello/` project and gradually add automations
2. **Customize schemas** - Modify work item types and workflows to match your process
3. **Test locally** - Use `--dry-run` flags to preview changes before applying
4. **Version control** - Keep your project configurations in Git for tracking changes
