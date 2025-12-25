"""Tests for YAML parsers."""
import pytest
from pathlib import Path

from planecompose.parser.plane_yaml import parse_plane_yaml
from planecompose.parser.types_yaml import parse_types_yaml
from planecompose.parser.workflows_yaml import parse_workflows_yaml
from planecompose.parser.labels_yaml import parse_labels_yaml
from planecompose.parser.work_yaml import parse_work_items


class TestPlaneYamlParser:
    """Tests for plane.yaml parser."""
    
    def test_parse_plane_yaml(self, temp_project):
        """Test parsing plane.yaml."""
        config = parse_plane_yaml(temp_project / "plane.yaml")
        
        assert config.workspace == "test-workspace"
        assert config.project_key == "TEST"
        assert config.project_name == "Test Project"
        assert config.default_type == "task"
    
    def test_parse_plane_yaml_with_uuid(self, tmp_path):
        """Test parsing plane.yaml with UUID."""
        plane_yaml = """
workspace: myteam
project:
  key: PROJ
  uuid: abc-123-def-456
  name: My Project
"""
        yaml_path = tmp_path / "plane.yaml"
        yaml_path.write_text(plane_yaml)
        
        config = parse_plane_yaml(yaml_path)
        
        assert config.project_uuid == "abc-123-def-456"
    
    def test_parse_plane_yaml_minimal(self, tmp_path):
        """Test parsing minimal plane.yaml."""
        plane_yaml = """
workspace: test
project:
  key: T
"""
        yaml_path = tmp_path / "plane.yaml"
        yaml_path.write_text(plane_yaml)
        
        config = parse_plane_yaml(yaml_path)
        
        assert config.workspace == "test"
        assert config.project_key == "T"


class TestTypesYamlParser:
    """Tests for types.yaml parser."""
    
    def test_parse_types_yaml(self, temp_project):
        """Test parsing types.yaml."""
        types = parse_types_yaml(temp_project / "schema" / "types.yaml")
        
        assert len(types) == 2
        
        task_type = next(t for t in types if t.name == "task")
        assert task_type.description == "A single unit of work"
        assert task_type.workflow == "standard"
    
    def test_parse_types_yaml_with_fields(self, tmp_path):
        """Test parsing types with custom fields."""
        types_yaml = """
feature:
  description: A feature request
  workflow: standard
  fields:
    - name: title
      type: string
      required: true
    - name: priority
      type: enum
      options: [low, medium, high]
"""
        yaml_path = tmp_path / "types.yaml"
        yaml_path.write_text(types_yaml)
        
        types = parse_types_yaml(yaml_path)
        
        assert len(types) == 1
        assert types[0].name == "feature"
        assert len(types[0].fields) == 2
        assert types[0].fields[1].options == ["low", "medium", "high"]
    
    def test_parse_types_yaml_empty(self, tmp_path):
        """Test parsing empty types.yaml."""
        yaml_path = tmp_path / "types.yaml"
        yaml_path.write_text("")
        
        types = parse_types_yaml(yaml_path)
        
        assert types == []


class TestWorkflowsYamlParser:
    """Tests for workflows.yaml parser."""
    
    def test_parse_workflows_yaml(self, temp_project):
        """Test parsing workflows.yaml."""
        workflows = parse_workflows_yaml(temp_project / "schema" / "workflows.yaml")
        
        assert len(workflows) == 1
        assert workflows[0].name == "standard"
        assert workflows[0].initial == "backlog"
        assert "done" in workflows[0].terminal
    
    def test_parse_workflows_yaml_states(self, temp_project):
        """Test parsing workflow states."""
        workflows = parse_workflows_yaml(temp_project / "schema" / "workflows.yaml")
        
        states = workflows[0].states
        assert len(states) == 3
        
        backlog = next(s for s in states if s.name == "backlog")
        assert backlog.group == "unstarted"
        assert backlog.color == "#858585"
    
    def test_parse_workflows_yaml_empty(self, tmp_path):
        """Test parsing empty workflows.yaml."""
        yaml_path = tmp_path / "workflows.yaml"
        yaml_path.write_text("")
        
        workflows = parse_workflows_yaml(yaml_path)
        
        assert workflows == []


class TestLabelsYamlParser:
    """Tests for labels.yaml parser."""
    
    def test_parse_labels_yaml_groups(self, temp_project):
        """Test parsing labels.yaml with groups."""
        labels = parse_labels_yaml(temp_project / "schema" / "labels.yaml")
        
        assert len(labels) == 2
        
        frontend_label = next(l for l in labels if l.name == "frontend")
        assert frontend_label.color == "#3b82f6"
    
    def test_parse_labels_yaml_flat(self, tmp_path):
        """Test parsing flat labels.yaml."""
        labels_yaml = """
- name: bug
  color: "#ef4444"
- name: feature
  color: "#22c55e"
"""
        yaml_path = tmp_path / "labels.yaml"
        yaml_path.write_text(labels_yaml)
        
        labels = parse_labels_yaml(yaml_path)
        
        assert len(labels) == 2
        assert labels[0].name == "bug"
    
    def test_parse_labels_yaml_empty(self, tmp_path):
        """Test parsing empty labels.yaml."""
        yaml_path = tmp_path / "labels.yaml"
        yaml_path.write_text("")
        
        labels = parse_labels_yaml(yaml_path)
        
        assert labels == []


class TestWorkYamlParser:
    """Tests for work/*.yaml parser."""
    
    def test_parse_work_items_empty(self, temp_project):
        """Test parsing empty work items."""
        items = list(parse_work_items(temp_project / "work"))
        
        assert len(items) == 0
    
    def test_parse_work_items_list(self, tmp_path):
        """Test parsing list of work items."""
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        
        work_yaml = """
- title: First task
  type: task
  state: backlog

- title: Second task
  type: bug
  priority: high
"""
        (work_dir / "inbox.yaml").write_text(work_yaml)
        
        items = list(parse_work_items(work_dir, tmp_path))
        
        assert len(items) == 2
        assert items[0].item.title == "First task"
        assert items[1].item.priority == "high"
    
    def test_parse_work_items_with_ids(self, tmp_path):
        """Test parsing work items with stable IDs."""
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        
        work_yaml = """
- id: task-001
  title: Task with ID
  type: task

- title: Task without ID
  type: task
"""
        (work_dir / "inbox.yaml").write_text(work_yaml)
        
        items = list(parse_work_items(work_dir, tmp_path))
        
        assert items[0].item.id == "task-001"
        assert items[1].item.id is None
    
    def test_parse_work_items_metadata(self, tmp_path):
        """Test that parser captures source metadata."""
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        
        work_yaml = """
- title: Test task
  type: task
"""
        (work_dir / "inbox.yaml").write_text(work_yaml)
        
        items = list(parse_work_items(work_dir, tmp_path))
        
        assert items[0].source_file == "work/inbox.yaml"
        assert items[0].index == 0
    
    def test_parse_work_items_multiple_files(self, tmp_path):
        """Test parsing work items from multiple files."""
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        
        (work_dir / "a_features.yaml").write_text("- title: Feature 1\n  type: task")
        (work_dir / "b_bugs.yaml").write_text("- title: Bug 1\n  type: bug")
        
        items = list(parse_work_items(work_dir, tmp_path))
        
        assert len(items) == 2
        # Should be sorted by filename
        assert items[0].item.title == "Feature 1"
        assert items[1].item.title == "Bug 1"

