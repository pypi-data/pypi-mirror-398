"""Pytest fixtures for planecompose tests."""
import json
import pytest
from pathlib import Path
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

from planecompose.core.models import (
    WorkItem,
    WorkItemTypeDefinition,
    StateDefinition,
    LabelDefinition,
    ProjectConfig,
    SyncState,
)
from planecompose.backend.base import Backend


# -----------------------------------------------------------------------------
# Fixtures: Project Structure
# -----------------------------------------------------------------------------

@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project structure for testing."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()
    
    # Create directories
    (project_path / "schema").mkdir()
    (project_path / "work").mkdir()
    (project_path / ".plane").mkdir()
    
    # Create plane.yaml
    plane_yaml = """
workspace: test-workspace
project:
  key: TEST
  name: Test Project

defaults:
  type: task
  workflow: standard
"""
    (project_path / "plane.yaml").write_text(plane_yaml)
    
    # Create schema/types.yaml
    types_yaml = """
task:
  description: A single unit of work
  workflow: standard
  fields:
    - name: title
      type: string
      required: true

bug:
  description: A defect requiring fix
  workflow: standard
  fields:
    - name: title
      type: string
      required: true
"""
    (project_path / "schema" / "types.yaml").write_text(types_yaml)
    
    # Create schema/workflows.yaml
    workflows_yaml = """
standard:
  states:
    - name: backlog
      group: unstarted
      color: "#858585"
    - name: in_progress
      group: started
      color: "#f59e0b"
    - name: done
      group: completed
      color: "#22c55e"
  initial: backlog
  terminal: [done]
"""
    (project_path / "schema" / "workflows.yaml").write_text(workflows_yaml)
    
    # Create schema/labels.yaml
    labels_yaml = """
groups:
  area:
    color: "#3b82f6"
    labels:
      - name: frontend
      - name: backend
"""
    (project_path / "schema" / "labels.yaml").write_text(labels_yaml)
    
    # Create empty work/inbox.yaml
    (project_path / "work" / "inbox.yaml").write_text("[]")
    
    # Create .plane/state.json
    state = {
        "last_sync": None,
        "types": {},
        "states": {},
        "labels": {},
        "work_items": {}
    }
    (project_path / ".plane" / "state.json").write_text(json.dumps(state))
    
    return project_path


@pytest.fixture
def temp_credentials(tmp_path: Path) -> Path:
    """Create temporary credentials file."""
    config_dir = tmp_path / ".config" / "plane-compose"
    config_dir.mkdir(parents=True)
    credentials_file = config_dir / "credentials"
    credentials_file.write_text("test-api-key-1234567890")
    return credentials_file


# -----------------------------------------------------------------------------
# Fixtures: Domain Models
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_work_item() -> WorkItem:
    """Create a sample work item for testing."""
    return WorkItem(
        id="test-item-001",
        title="Test Work Item",
        description="This is a test description",
        type="task",
        state="backlog",
        priority="high",
        labels=["frontend", "feature"],
    )


@pytest.fixture
def sample_work_items() -> list[WorkItem]:
    """Create a list of sample work items."""
    return [
        WorkItem(
            id="item-001",
            title="First task",
            type="task",
            state="backlog",
        ),
        WorkItem(
            id="item-002",
            title="Second task",
            type="bug",
            state="in_progress",
            priority="high",
        ),
        WorkItem(
            title="Third task (no ID)",
            type="task",
            labels=["backend"],
        ),
    ]


@pytest.fixture
def sample_type_definition() -> WorkItemTypeDefinition:
    """Create a sample work item type definition."""
    return WorkItemTypeDefinition(
        name="task",
        description="A single unit of work",
        workflow="standard",
    )


@pytest.fixture
def sample_state_definition() -> StateDefinition:
    """Create a sample state definition."""
    return StateDefinition(
        name="backlog",
        group="unstarted",
        color="#858585",
    )


@pytest.fixture
def sample_label_definition() -> LabelDefinition:
    """Create a sample label definition."""
    return LabelDefinition(
        name="frontend",
        color="#3b82f6",
    )


@pytest.fixture
def sample_project_config() -> ProjectConfig:
    """Create a sample project configuration."""
    return ProjectConfig(
        workspace="test-workspace",
        project_key="TEST",
        project_uuid="test-uuid-1234",
        project_name="Test Project",
    )


@pytest.fixture
def sample_sync_state() -> SyncState:
    """Create a sample sync state."""
    return SyncState(
        last_sync="2024-01-01T00:00:00Z",
        types={"task": "type-uuid-1", "bug": "type-uuid-2"},
        states={"backlog": "state-uuid-1", "done": "state-uuid-2"},
        labels={"frontend": "label-uuid-1"},
        work_items={},
    )


# -----------------------------------------------------------------------------
# Fixtures: Mock Backend
# -----------------------------------------------------------------------------

class MockBackend(Backend):
    """Mock backend for testing without API calls."""
    
    def __init__(self):
        self._connected = False
        self._types: dict[str, WorkItemTypeDefinition] = {}
        self._states: dict[str, StateDefinition] = {}
        self._labels: dict[str, LabelDefinition] = {}
        self._work_items: dict[str, WorkItem] = {}
        self._counter = 0
    
    async def connect(self, config: ProjectConfig, api_key: str) -> None:
        self._connected = True
        self._config = config
    
    async def disconnect(self) -> None:
        self._connected = False
    
    async def list_types(self) -> list[WorkItemTypeDefinition]:
        return list(self._types.values())
    
    async def create_type(self, type_def: WorkItemTypeDefinition) -> str:
        self._counter += 1
        type_id = f"type-{self._counter}"
        type_def.remote_id = type_id
        self._types[type_id] = type_def
        return type_id
    
    async def list_states(self) -> list[StateDefinition]:
        return list(self._states.values())
    
    async def create_state(self, state: StateDefinition) -> str:
        self._counter += 1
        state_id = f"state-{self._counter}"
        state.remote_id = state_id
        self._states[state_id] = state
        return state_id
    
    async def list_labels(self) -> list[LabelDefinition]:
        return list(self._labels.values())
    
    async def create_label(self, label: LabelDefinition) -> str:
        self._counter += 1
        label_id = f"label-{self._counter}"
        label.remote_id = label_id
        self._labels[label_id] = label
        return label_id
    
    async def create_work_item(self, work_item: WorkItem) -> str:
        self._counter += 1
        item_id = f"item-{self._counter}"
        self._work_items[item_id] = work_item
        return item_id
    
    async def update_work_item(self, remote_id: str, work_item: WorkItem) -> None:
        if remote_id in self._work_items:
            self._work_items[remote_id] = work_item
    
    async def list_work_items(self) -> list[WorkItem]:
        return list(self._work_items.values())


@pytest.fixture
def mock_backend() -> MockBackend:
    """Create a mock backend instance."""
    return MockBackend()


# -----------------------------------------------------------------------------
# Fixtures: CLI Testing
# -----------------------------------------------------------------------------

@pytest.fixture
def cli_runner():
    """Create a CLI test runner."""
    from typer.testing import CliRunner
    return CliRunner()


# -----------------------------------------------------------------------------
# Async Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

