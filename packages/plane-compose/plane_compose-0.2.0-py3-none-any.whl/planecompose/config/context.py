"""Project context management."""
import json
from pathlib import Path
from dataclasses import dataclass
from planecompose.core.models import (
    ProjectConfig,
    WorkItemTypeDefinition,
    WorkflowDefinition,
    StateDefinition,
    LabelDefinition,
    SyncState,
)
from planecompose.parser.plane_yaml import parse_plane_yaml
from planecompose.parser.types_yaml import parse_types_yaml
from planecompose.parser.workflows_yaml import parse_workflows_yaml
from planecompose.parser.labels_yaml import parse_labels_yaml


@dataclass
class ProjectContext:
    """Context for a Plane project."""
    root_path: Path
    config: ProjectConfig
    types: list[WorkItemTypeDefinition]
    workflows: list[WorkflowDefinition]
    labels: list[LabelDefinition]
    state: SyncState
    api_key: str
    
    @property
    def schema_path(self) -> Path:
        return self.root_path / "schema"
    
    @property
    def work_path(self) -> Path:
        return self.root_path / "work"
    
    @property
    def state_path(self) -> Path:
        return self.root_path / ".plane" / "state.json"
    
    @property
    def states(self) -> list[StateDefinition]:
        """Get all states from all workflows."""
        states = []
        for workflow in self.workflows:
            states.extend(workflow.states)
        return states
    
    def save_state(self):
        """Save sync state to disk."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, 'w') as f:
            json.dump(self.state.model_dump(), f, indent=2)


def load_project_context(path: Path = None) -> ProjectContext:
    """
    Load project context from a directory.
    
    ONLY checks the specified directory (or current directory if not specified).
    Does NOT search parent directories.
    
    Args:
        path: Directory to check for plane.yaml (defaults to current directory)
    
    Returns:
        ProjectContext: The loaded project context
        
    Raises:
        FileNotFoundError: If plane.yaml is not found in the specified directory
    """
    if path is None:
        path = Path.cwd()
    
    # ONLY check the specified directory (no parent directory search!)
    root_path = path.resolve()
    plane_yaml_path = root_path / "plane.yaml"
    
    if not plane_yaml_path.exists():
        raise FileNotFoundError(
            f"Not a Plane project (no plane.yaml found in {root_path})"
        )
    
    # Load configuration
    config = parse_plane_yaml(root_path / "plane.yaml")
    
    # Load schema
    types = parse_types_yaml(root_path / "schema" / "types.yaml")
    workflows = parse_workflows_yaml(root_path / "schema" / "workflows.yaml")
    labels = parse_labels_yaml(root_path / "schema" / "labels.yaml")
    
    # Load sync state
    state_path = root_path / ".plane" / "state.json"
    if state_path.exists():
        with open(state_path, 'r') as f:
            state_data = json.load(f)
        state = SyncState(**state_data)
    else:
        state = SyncState()
    
    # Load API key (and server URL for validation)
    # Import here to avoid circular dependency
    from planecompose.cli.auth import CONFIG_FILE, TOKEN_FILE
    
    api_key = None
    if CONFIG_FILE.exists():
        try:
            import json as json_module
            config_data = json_module.loads(CONFIG_FILE.read_text())
            api_key = config_data.get("api_key")
        except (json_module.JSONDecodeError, KeyError):
            pass
    
    # Fall back to TOKEN_FILE for backward compatibility
    if not api_key and TOKEN_FILE.exists():
        api_key = TOKEN_FILE.read_text().strip()
    
    if not api_key:
        raise FileNotFoundError("Not authenticated. Run 'plane auth login' first")
    
    return ProjectContext(
        root_path=root_path,
        config=config,
        types=types,
        workflows=workflows,
        labels=labels,
        state=state,
        api_key=api_key,
    )


