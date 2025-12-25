# 🏗️ Plane Compose Architecture

## Overview

Plane Compose is a project as code framework for scaffolding and syncing projects with Plane.so. It follows a clean layered architecture with clear separation of concerns.

```
┌─────────────────────────────────────────────────────┐
│                  CLI Layer (Typer)                   │
│        User Commands: init, push, pull, apply        │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              Business Logic Layer                    │
│      Sync, Diff, Validation, State Management        │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              Backend Abstraction Layer               │
│         (Backend interface + implementations)        │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                  External APIs                       │
│              (Plane SDK, HTTP Client)                │
└─────────────────────────────────────────────────────┘
```

## Layers

### 1. CLI Layer (`src/planecompose/cli/`)

**Purpose**: Presentation layer for user interaction

**Responsibilities**:
- Parse command-line arguments
- Display rich output to users
- Handle interactive prompts
- Coordinate business logic

**Key Files**:
- `root.py` - Main CLI entry point
- `init.py` - Project scaffolding
- `push.py` - Push work items to Plane
- `pull.py` - Pull work items from Plane
- `apply.py` - Declarative state management
- `schema.py` - Schema synchronization
- `auth.py` - Authentication
- `status.py` - Sync status display

### 2. Business Logic Layer (`src/planecompose/`)

**Purpose**: Core domain logic

**Responsibilities**:
- Work item diff calculation
- State synchronization
- Validation rules
- Content hashing
- Conflict resolution

**Key Modules**:
- `sync/` - Sync orchestration
- `diff/` - Change detection
- `validation/` - Input validation
- `parser/` - YAML parsing
- `utils/` - Shared utilities

### 3. Backend Layer (`src/planecompose/backend/`)

**Purpose**: Data access abstraction

**Responsibilities**:
- Abstract API interactions
- Rate limiting
- Error handling
- Type/state/label/work item CRUD

**Key Files**:
- `base.py` - Abstract Backend interface
- `plane.py` - Plane SDK implementation

**Design Pattern**: Strategy pattern for swappable backends

```python
class Backend(ABC):
    @abstractmethod
    async def create_work_item(self, item: WorkItem) -> str:
        pass

class PlaneBackend(Backend):
    # Real implementation using Plane SDK
    pass

class MockBackend(Backend):
    # Test implementation
    pass
```

### 4. Data Layer (`src/planecompose/core/`)

**Purpose**: Domain models and data structures

**Responsibilities**:
- Define all data models
- Type validation with Pydantic
- Serialization/deserialization

**Key File**:
- `models.py` - All Pydantic models

## Key Concepts

### State Management

PlaneCompose uses a **Terraform-style state file** (`.plane/state.json`) to track:
- Remote IDs for local entities
- Content hashes for change detection
- Last sync timestamps
- Mapping between local and remote identifiers

**Why?**
- Keeps local YAML files clean (no metadata pollution)
- Enables efficient change detection
- Supports collaborative workflows

### Declarative vs. Collaborative

PlaneCompose supports **two modes**:

1. **Collaborative Mode** (`plane push`):
   - Additive only (create/update, no delete)
   - Safe for team collaboration
   - Multiple sources of truth

2. **Declarative Mode** (`plane apply`):
   - Domain-scoped (by labels, assignee, ID prefix)
   - Can delete items not in local files
   - Single source of truth for the scope

### Rate Limiting

All API interactions go through a **token bucket rate limiter**:
- 50 requests per minute
- Automatic throttling
- HTTP 429 handling
- Statistics tracking

### Content Hashing

Work items are tracked by:
1. **User-provided ID** (if specified in YAML)
2. **Content hash** (fallback)

This enables:
- Stable tracking across renames
- Duplicate detection
- Change detection

## Data Flow

### Push Flow

```
Local YAML Files
      │
      ▼
Parse + Validate
      │
      ▼
Load State (.plane/state.json)
      │
      ▼
Calculate Diff (create/update)
      │
      ▼
Rate-Limited API Calls
      │
      ▼
Update State + Save
```

### Pull Flow

```
API Request (rate-limited)
      │
      ▼
Fetch Work Items
      │
      ▼
Transform to Local Format
      │
      ▼
Write to .plane/remote/items.yaml
      │
      ▼
Update State
```

### Apply Flow

```
Load Scope Definition
      │
      ▼
Fetch Remote Items in Scope
      │
      ▼
Parse Local Files
      │
      ▼
Calculate Diff (create/update/delete)
      │
      ▼
Confirm with User
      │
      ▼
Execute Changes (rate-limited)
      │
      ▼
Update State
```

## Design Principles

### 1. Dependency Inversion

High-level modules (CLI) don't depend on low-level modules (API). Both depend on abstractions (Backend interface).

### 2. Single Responsibility

Each module has one clear purpose:
- `cli/` - User interaction
- `backend/` - API calls
- `parser/` - YAML parsing
- `diff/` - Change detection

### 3. Type Safety

- Pydantic models everywhere
- Type hints on all functions
- Runtime validation

### 4. Separation of Concerns

- Configuration in `config/`
- Logging in `utils/logger.py`
- Rate limiting in `utils/rate_limit.py`
- Error handling via custom exceptions

### 5. Testability

- Mock backend for testing
- Fixtures for test data
- No global state (except singletons like logger/settings)

## Configuration

### Settings (`config/settings.py`)

All settings support environment variables:

```bash
PLANE_API_URL=https://custom.plane.so
PLANE_RATE_LIMIT_PER_MINUTE=30
PLANE_DEBUG=true
```

### Project Config (`plane.yaml`)

```yaml
workspace: my-workspace
project:
  key: PROJ      # User-defined identifier
  uuid: abc-123  # Plane API UUID (auto-added)
  name: My Project
defaults:
  type: task
  workflow: standard
```

## Error Handling

Custom exception hierarchy:

```
PlaneComposeError (base)
├── APIError
│   ├── RateLimitError (429)
│   ├── AuthenticationError (401)
│   ├── PermissionError (403)
│   └── NotFoundError (404)
├── ConfigError
├── ValidationError
├── StateError
├── NetworkError
└── ParserError
```

All exceptions include:
- Clear error messages
- Contextual details
- Proper HTTP status codes (for API errors)

## Extension Points

### Adding New Commands

1. Create file in `cli/` (e.g., `cli/export.py`)
2. Define command using Typer
3. Register in `cli/root.py`

### Adding New Backends

1. Implement `Backend` interface
2. Add to `backend/` directory
3. Update CLI to support selection

### Adding New Parsers

1. Add parser in `parser/` directory
2. Update models in `core/models.py` if needed
3. Integrate into sync flow

## Performance Considerations

### Bottlenecks

1. **API Rate Limit**: 50 req/min
   - Solution: Batch operations, caching

2. **Sequential Operations**: One at a time
   - Solution: Parallel API calls where safe

3. **Large YAML Files**: Can be slow to parse
   - Solution: Consider splitting into multiple files

### Scalability

- **Current**: Handles projects with ~1000s work items
- **Future**: SQLite state store for huge projects

## Security

### API Key Storage

- Stored in `~/.config/plane-cli/credentials`
- Permissions: 600 (owner read/write only)
- Never logged or displayed

### Rate Limiting

- Prevents API abuse
- Respects Plane's limits
- Automatic backoff

### Input Validation

- All user input validated with Pydantic
- YAML parsing with safe loader
- No arbitrary code execution

## Future Enhancements

### Planned

- [ ] Caching layer for read operations
- [ ] Parallel API calls for independent operations
- [ ] SQLite state store for large projects
- [ ] Offline mode
- [ ] Conflict resolution UI
- [ ] Team collaboration features
- [ ] Custom property support in schema push

### Under Consideration

- [ ] Git integration (track changes)
- [ ] Import from other tools (Jira, Asana)
- [ ] Export to various formats
- [ ] Webhooks for real-time sync
- [ ] Desktop app with GUI

## Contributing

See `docs/development.md` for:
- Setting up development environment
- Running tests
- Code style guidelines
- Pull request process

