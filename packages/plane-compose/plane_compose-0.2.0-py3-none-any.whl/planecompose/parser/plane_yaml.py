"""Parser for plane.yaml configuration file."""
import yaml
from pathlib import Path
from planecompose.core.models import ProjectConfig


def parse_plane_yaml(path: Path) -> ProjectConfig:
    """Parse plane.yaml into ProjectConfig model."""
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    project_data = data.get('project', {})
    
    return ProjectConfig(
        workspace=data['workspace'],
        project_key=project_data.get('key', data.get('project_key', '')),
        project_uuid=project_data.get('uuid'),  # Optional UUID field
        project_name=project_data.get('name'),
        api_url=data.get('api_url', 'https://api.plane.so'),
        default_type=data.get('defaults', {}).get('type', 'task'),
    )



