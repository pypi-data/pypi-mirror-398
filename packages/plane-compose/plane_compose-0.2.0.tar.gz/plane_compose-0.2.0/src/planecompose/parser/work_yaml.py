"""Parser for work/*.yaml files - Terraform-style clean parsing."""
import yaml
from pathlib import Path
from typing import Iterator, NamedTuple
from planecompose.core.models import WorkItem


class WorkItemWithMeta(NamedTuple):
    """Work item with metadata about its source (for tracking)."""
    item: WorkItem
    source_file: str  # Relative path
    index: int  # Index in the file


def parse_work_items(path: Path, root_path: Path = None) -> Iterator[WorkItemWithMeta]:
    """Parse work items from YAML files without modifying them."""
    if root_path is None:
        root_path = path.parent if path.is_file() else path
    
    if path.is_file():
        yield from _parse_work_file(path, root_path)
    else:
        for file_path in sorted(path.glob("*.yaml")):
            yield from _parse_work_file(file_path, root_path)


def _parse_work_file(path: Path, root_path: Path) -> Iterator[WorkItemWithMeta]:
    """Parse a single work YAML file."""
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    if not data:
        return
    
    # Get relative path for source tracking
    try:
        relative_path = str(path.relative_to(root_path))
    except ValueError:
        relative_path = str(path)
    
    if isinstance(data, list):
        for index, item_data in enumerate(data):
            if item_data:  # Skip empty items
                item = _parse_work_item(item_data)
                yield WorkItemWithMeta(item, relative_path, index)
    elif isinstance(data, dict):
        item = _parse_work_item(data)
        yield WorkItemWithMeta(item, relative_path, 0)


def _parse_work_item(data: dict, parent_id: str = None) -> WorkItem:
    """
    Parse a single work item dictionary.
    
    CLEAN approach: Only read what's in the file, don't add metadata.
    """
    children = []
    for child_data in data.get('children', []):
        child = _parse_work_item(child_data, data.get('id'))
        children.append(child)
    
    return WorkItem(
        id=data.get('id'),  # Optional user-provided ID
        title=data['title'],
        description=data.get('description'),
        type=data.get('type', 'task'),
        state=data.get('state'),
        priority=data.get('priority'),
        labels=data.get('labels', []),
        start_date=data.get('start_date'),
        due_date=data.get('due_date'),
        parent=parent_id or data.get('parent'),  # Use parent_id from hierarchy or explicit parent
        children=children,
        assignees=data.get('assignees', []),
        watchers=data.get('watchers', []),
        blocked_by=data.get('blocked_by', []),
        blocking=data.get('blocking', []),
        duplicate_of=data.get('duplicate_of'),
        relates_to=data.get('relates_to', []),
        properties=data.get('properties', {}),  # Custom properties
    )



