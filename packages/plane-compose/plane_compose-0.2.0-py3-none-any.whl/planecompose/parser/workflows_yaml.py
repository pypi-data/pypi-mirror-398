"""Parser for schema/workflows.yaml."""
import yaml
from pathlib import Path
from planecompose.core.models import WorkflowDefinition, StateDefinition


def parse_workflows_yaml(path: Path) -> list[WorkflowDefinition]:
    """Parse workflows.yaml into WorkflowDefinition models."""
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    if not data:
        return []
    
    workflows = []
    for name, config in data.items():
        states = []
        for state_data in config.get('states', []):
            states.append(StateDefinition(
                name=state_data['name'],
                description=state_data.get('description'),
                color=state_data.get('color'),
                group=state_data.get('group', 'unstarted'),
            ))
        
        workflows.append(WorkflowDefinition(
            name=name,
            states=states,
            initial=config['initial'],
            terminal=config.get('terminal', []),
        ))
    
    return workflows



