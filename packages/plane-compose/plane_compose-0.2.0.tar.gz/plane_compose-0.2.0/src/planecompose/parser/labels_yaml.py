"""Parser for schema/labels.yaml."""
import yaml
from pathlib import Path
from planecompose.core.models import LabelDefinition


def parse_labels_yaml(path: Path) -> list[LabelDefinition]:
    """Parse labels.yaml into LabelDefinition models."""
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    if not data:
        return []
    
    labels = []
    
    # Handle groups structure
    if 'groups' in data:
        for group_name, group_data in data['groups'].items():
            group_color = group_data.get('color')
            for label_data in group_data.get('labels', []):
                labels.append(LabelDefinition(
                    name=label_data['name'],
                    color=label_data.get('color', group_color),
                ))
    else:
        # Handle flat list
        for label_data in data:
            labels.append(LabelDefinition(
                name=label_data['name'],
                color=label_data.get('color'),
            ))
    
    return labels



