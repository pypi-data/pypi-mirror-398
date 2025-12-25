# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-15

### Added
- Initial release of Plane Compose
- **Core Features:**
  - Local-first workflow with YAML-based project definitions
  - Bidirectional sync between local files and Plane platform
  - Auto-create projects during schema push
  - Secure API key authentication
  - Beautiful CLI with Rich terminal UI

- **Schema Management:**
  - Work item types with custom properties
  - Workflow definitions with states and transitions
  - Label management with groups and colors
  - Schema validation and push commands

- **Work Item Management:**
  - Collaborative mode (`plane push`) - additive-only, team-friendly
  - Declarative mode (`plane apply`) - domain-scoped single source of truth
  - Intelligent content-based change detection
  - Stable ID support via user-defined IDs or content hashing
  - State tracking with `.plane/state.json`

- **CLI Commands:**
  - `plane init` - Initialize new project structure
  - `plane auth login/logout/whoami` - Authentication management
  - `plane schema validate/push` - Schema operations
  - `plane push/pull/sync` - Work item synchronization
  - `plane apply` - Declarative sync with delete support
  - `plane clone` - Clone existing projects from Plane
  - `plane status` - Show sync status
  - `plane rate stats/reset` - Rate limit monitoring

- **Advanced Features:**
  - Built-in rate limiting (50 req/min by default)
  - Respects Plane API rate limits with automatic throttling
  - Debug mode with comprehensive logging
  - Environment variable configuration support
  - Project cloning with schema and work items
  - Dry-run support for preview before changes

- **Documentation:**
  - Comprehensive README with quick start guide
  - Architecture documentation
  - Development guide
  - Troubleshooting guide
  - Example workflows and patterns

### Technical Details
- Python 3.10+ support
- Built with Typer, Rich, Pydantic, and Plane SDK
- Clean architecture with separation of concerns
- Full test coverage with pytest
- Type hints throughout codebase
- Formatted with Black, linted with Ruff

[0.1.0]: https://github.com/makeplane/compose/releases/tag/v0.1.0

[0.2.0]:
- Added support for selfhosted editions