"""Tests for core domain models."""
import pytest
from pydantic import ValidationError

from planecompose.core.models import (
    WorkItem,
    WorkItemTypeDefinition,
    StateDefinition,
    LabelDefinition,
    ProjectConfig,
    SyncState,
    WorkItemState,
    FieldDefinition,
    FieldType,
)


class TestWorkItem:
    """Tests for WorkItem model."""
    
    def test_work_item_minimal(self):
        """Test creating work item with minimal fields."""
        item = WorkItem(title="Test Task")
        
        assert item.title == "Test Task"
        assert item.type == "task"  # Default
        assert item.id is None
        assert item.description is None
        assert item.labels == []
    
    def test_work_item_full(self, sample_work_item):
        """Test work item with all fields."""
        assert sample_work_item.id == "test-item-001"
        assert sample_work_item.title == "Test Work Item"
        assert sample_work_item.type == "task"
        assert sample_work_item.state == "backlog"
        assert sample_work_item.priority == "high"
        assert "frontend" in sample_work_item.labels
    
    def test_work_item_with_properties(self):
        """Test work item with custom properties."""
        item = WorkItem(
            title="Feature Task",
            type="task",
            properties={"platform": "iOS", "severity": "critical"}
        )
        
        assert item.properties["platform"] == "iOS"
        assert item.properties["severity"] == "critical"
    
    def test_work_item_requires_title(self):
        """Test that title is required."""
        with pytest.raises(ValidationError):
            WorkItem()
    
    def test_work_item_with_children(self):
        """Test work item with nested children."""
        parent = WorkItem(
            id="parent-001",
            title="Parent Task",
            children=[
                WorkItem(title="Child 1"),
                WorkItem(title="Child 2"),
            ]
        )
        
        assert len(parent.children) == 2
        assert parent.children[0].title == "Child 1"


class TestWorkItemTypeDefinition:
    """Tests for WorkItemTypeDefinition model."""
    
    def test_type_definition_basic(self, sample_type_definition):
        """Test basic type definition."""
        assert sample_type_definition.name == "task"
        assert sample_type_definition.workflow == "standard"
    
    def test_type_definition_with_fields(self):
        """Test type definition with custom fields."""
        type_def = WorkItemTypeDefinition(
            name="feature",
            description="A feature request",
            workflow="standard",
            fields=[
                FieldDefinition(name="title", type=FieldType.TEXT, required=True),
                FieldDefinition(name="priority", type=FieldType.OPTION, options=["low", "high"]),
            ]
        )
        
        assert len(type_def.fields) == 2
        assert type_def.fields[0].required is True
        assert type_def.fields[1].options == ["low", "high"]


class TestStateDefinition:
    """Tests for StateDefinition model."""
    
    def test_state_definition_basic(self, sample_state_definition):
        """Test basic state definition."""
        assert sample_state_definition.name == "backlog"
        assert sample_state_definition.group == "unstarted"
        assert sample_state_definition.color == "#858585"
    
    def test_state_definition_defaults(self):
        """Test state definition with defaults."""
        state = StateDefinition(name="new")
        
        assert state.group == "unstarted"  # Default
        assert state.color is None


class TestLabelDefinition:
    """Tests for LabelDefinition model."""
    
    def test_label_definition_basic(self, sample_label_definition):
        """Test basic label definition."""
        assert sample_label_definition.name == "frontend"
        assert sample_label_definition.color == "#3b82f6"


class TestProjectConfig:
    """Tests for ProjectConfig model."""
    
    def test_project_config_basic(self, sample_project_config):
        """Test basic project configuration."""
        assert sample_project_config.workspace == "test-workspace"
        assert sample_project_config.project_key == "TEST"
        assert sample_project_config.api_url == "https://api.plane.so"
    
    def test_project_config_defaults(self):
        """Test project config with defaults."""
        config = ProjectConfig(
            workspace="myteam",
            project_key="PROJ",
        )
        
        assert config.api_url == "https://api.plane.so"
        assert config.default_type == "task"


class TestSyncState:
    """Tests for SyncState model."""
    
    def test_sync_state_empty(self):
        """Test empty sync state."""
        state = SyncState()
        
        assert state.last_sync is None
        assert state.types == {}
        assert state.states == {}
        assert state.labels == {}
        assert state.work_items == {}
    
    def test_sync_state_with_data(self, sample_sync_state):
        """Test sync state with data."""
        assert sample_sync_state.types["task"] == "type-uuid-1"
        assert sample_sync_state.states["backlog"] == "state-uuid-1"
        assert sample_sync_state.labels["frontend"] == "label-uuid-1"


class TestWorkItemState:
    """Tests for WorkItemState model."""
    
    def test_work_item_state(self):
        """Test work item state tracking."""
        item_state = WorkItemState(
            remote_id="item-uuid-123",
            content_hash="abc123def456",
            source="work/inbox.yaml:0",
            last_synced="2024-01-01T00:00:00Z",
        )
        
        assert item_state.remote_id == "item-uuid-123"
        assert item_state.content_hash == "abc123def456"
        assert "inbox.yaml" in item_state.source


class TestFieldType:
    """Tests for FieldType enum."""
    
    def test_field_type_values(self):
        """Test field type enum values."""
        assert FieldType.TEXT.value == "text"
        assert FieldType.NUMBER.value == "number"
        assert FieldType.OPTION.value == "option"
        assert FieldType.DATE.value == "date"
    
    def test_field_type_aliases(self):
        """Test field type aliases for backwards compatibility."""
        assert FieldType.STRING.value == "string"
        assert FieldType.ENUM.value == "enum"
        assert FieldType.USER.value == "user"

