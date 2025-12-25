"""Parser for schema/types.yaml."""
import yaml
from pathlib import Path
from planecompose.core.models import WorkItemTypeDefinition, FieldDefinition, FieldType, LogoProps


def parse_types_yaml(path: Path) -> list[WorkItemTypeDefinition]:
    """
    Parse types.yaml into WorkItemTypeDefinition models.
    
    Supports both 'fields' and 'properties' keys for backward compatibility.
    Reads rich metadata: logo_props, is_epic, level, display_name, is_multi, is_active.
    """
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    if not data:
        return []
    
    types = []
    
    # Handle both list format (from plane schema pull) and dict format (legacy)
    items_to_parse = []
    if isinstance(data, list):
        # New format: list of type definitions
        items_to_parse = [(item.get('name'), item) for item in data]
    elif isinstance(data, dict):
        # Old format: dict with type names as keys
        items_to_parse = list(data.items())
    else:
        raise ValueError(f"Invalid types.yaml format: expected list or dict, got {type(data)}")
    
    for name, config in items_to_parse:
        # Read both 'properties' (from clone) and 'fields' (legacy) for compatibility
        field_list = config.get('properties', config.get('fields', []))
        fields = []
        
        for field_data in field_list:
            # Normalize type to lowercase for enum matching
            field_type_str = field_data['type'].lower()
            
            fields.append(FieldDefinition(
                name=field_data['name'],
                display_name=field_data.get('display_name', field_data['name']),
                type=FieldType(field_type_str),
                required=field_data.get('required', False),
                default=field_data.get('default'),
                options=field_data.get('options'),
                is_multi=field_data.get('is_multi', False),
                is_active=field_data.get('is_active', True),
            ))
        
        # Parse logo_props (icon and color)
        logo_props = None
        if 'logo_props' in config:
            logo_data = config['logo_props']
            logo_props = LogoProps(
                icon=logo_data.get('icon'),
                background_color=logo_data.get('background_color', logo_data.get('color')),
                emoji=logo_data.get('emoji'),
            )
        elif 'icon' in config:
            # Legacy format: icon directly in config
            icon_data = config['icon']
            if isinstance(icon_data, dict):
                logo_props = LogoProps(
                    icon=icon_data.get('name'),
                    background_color=icon_data.get('color'),
                )
        
        types.append(WorkItemTypeDefinition(
            name=name,
            description=config.get('description'),
            workflow=config.get('workflow', 'standard'),  # Default to 'standard' if not specified
            parent_types=config.get('parent_types', []),
            fields=fields,
            logo_props=logo_props,
            is_epic=config.get('is_epic', False),
            level=config.get('level', 0.0),
            is_default=config.get('is_default', False),
        ))
    
    return types



