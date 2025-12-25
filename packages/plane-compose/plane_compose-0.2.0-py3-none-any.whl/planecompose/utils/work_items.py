"""Work item utilities - Terraform-style clean state management."""
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from planecompose.core.models import WorkItem, WorkItemState


def generate_id_from_title(title: str) -> str:
    """Generate a stable ID from title (if user doesn't provide one)."""
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    
    # Limit length
    if len(slug) > 50:
        slug = slug[:50].rstrip('-')
    
    return slug or "item"


def calculate_content_hash(item: WorkItem) -> str:
    """
    Calculate content hash for change detection (like Git).
    
    This is used to detect if an item was modified locally.
    """
    # Create a stable string representation of the item's content
    content = f"{item.title}|{item.description or ''}|{item.type}|{item.state or ''}|{item.priority or ''}|{','.join(sorted(item.labels))}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def get_tracking_key(item: WorkItem, source: str, index: int) -> str:
    """
    Get the tracking key for a work item.
    
    Strategy:
    1. If item has user-provided `id`, use that (stable across changes)
    2. Otherwise, use content hash (like Git)
    
    Returns: tracking key for state.json
    """
    if item.id:
        return item.id
    
    # Use content hash as fallback
    content_hash = calculate_content_hash(item)
    return f"hash:{content_hash}"


def make_work_item_state(remote_id: str, item: WorkItem, source: str, index: int) -> WorkItemState:
    """Create a WorkItemState for tracking."""
    return WorkItemState(
        remote_id=remote_id,
        content_hash=calculate_content_hash(item),
        source=f"{source}:{index}",
        last_synced=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    )

