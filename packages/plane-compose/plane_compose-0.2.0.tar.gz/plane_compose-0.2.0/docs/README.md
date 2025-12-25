# 📚 Plane Compose Documentation

Welcome to the Plane Compose documentation! This guide helps you get the most out of this project as code framework.

## Quick Links

| Document | Description |
|----------|-------------|
| [Installation](INSTALL.md) | Installation via pipx |
| [Architecture](architecture.md) | System design and technical overview |
| [Development](development.md) | Contributing guide and development setup |
| [Examples](examples.md) | Common workflows and usage patterns |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |
| [Work Item Fields](WORK_ITEM_FIELDS.md) | Available fields and properties |
| [Automations](automations/README.md) | Automation system documentation |

## Getting Started

The fastest way to get started is in the main [README](../README.md).

```bash
# Install
pipx install plane-compose

# Initialize a project
plane init my-project --workspace myteam --project PROJ

# Authenticate
plane auth login

# Push your schema
plane schema push

# Push work items
plane push
```

## Command Reference

```bash
plane --help              # Show all commands
plane <command> --help    # Show command help

# Core Commands
plane init [path]         # Initialize new project
plane schema push         # Push schema to Plane
plane push                # Push work items
plane pull                # Pull work items from Plane
plane status              # Show sync status
plane sync                # Push schema + work items

# Advanced
plane apply               # Declarative sync (with delete)
plane clone <uuid>        # Clone existing project

# Auth
plane auth login          # Authenticate with API key
plane auth whoami         # Show current user
plane auth logout         # Remove credentials

# Monitoring
plane rate stats          # Show rate limit statistics
plane rate reset          # Reset rate limit counters

# Global Options
--version, -V             # Show version
--verbose, -v             # Verbose output
--debug                   # Debug logging
```

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/makeplane/compose/issues)
- **API Docs**: [Plane API Documentation](https://docs.plane.so/api)

