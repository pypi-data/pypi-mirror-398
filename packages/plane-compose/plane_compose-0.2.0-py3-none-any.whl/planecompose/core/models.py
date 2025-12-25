"""Core domain models."""
# See CURSOR_PROMPT.md for full implementation
from pydantic import BaseModel, Field
from typing import Any
from enum import Enum
from datetime import date


class FieldType(str, Enum):
    """Field types matching Plane API's property types."""
    # Primary types (match Plane SDK PropertyType)
    TEXT = "text"
    NUMBER = "number"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    OPTION = "option"  # Dropdown/select
    RELATION = "relation"  # User/member picker
    BOOLEAN = "boolean"
    URL = "url"  # URL field
    EMAIL = "email"  # Email field
    FILE = "file"  # File attachment
    
    # Aliases for backward compatibility
    STRING = "string"  # Maps to TEXT in backend
    ENUM = "enum"      # Maps to OPTION in backend
    USER = "user"      # Maps to RELATION in backend


class FieldDefinition(BaseModel):
    name: str
    display_name: str | None = None  # Human-readable name
    type: FieldType
    required: bool = False
    default: Any = None
    options: list[str] | None = None  # For enum/dropdown types
    is_multi: bool = False  # Multi-select for options
    is_active: bool = True  # Whether field is active
    relation_type: str | None = None  # For RELATION: "user" or "issue"
    remote_id: str | None = None  # Property ID from Plane


class LogoProps(BaseModel):
    """Logo/icon configuration for work item types."""
    icon: str | None = None  # Icon name (e.g., "Activity", "Bug")
    background_color: str | None = None  # Hex color
    emoji: str | None = None  # Alternative emoji


class WorkItemTypeDefinition(BaseModel):
    name: str
    description: str | None = None
    workflow: str
    parent_types: list[str] = Field(default_factory=list)
    fields: list[FieldDefinition] = Field(default_factory=list)
    remote_id: str | None = None
    # Rich metadata from Plane
    logo_props: LogoProps | None = None
    is_epic: bool = False
    is_default: bool = False
    level: float = 0.0  # Hierarchy level


class StateDefinition(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None
    group: str = "unstarted"
    remote_id: str | None = None


class WorkflowDefinition(BaseModel):
    name: str
    states: list[StateDefinition]
    initial: str
    terminal: list[str]


class LabelDefinition(BaseModel):
    name: str
    color: str | None = None
    remote_id: str | None = None


class WorkItem(BaseModel):
    """Work item - kept clean, no metadata pollution."""
    id: str | None = None  # Optional stable ID for tracking (user-provided)
    title: str
    description: str | None = None
    type: str = "task"
    state: str | None = None
    priority: str | None = None
    labels: list[str] = Field(default_factory=list)
    
    # Dates
    start_date: str | None = None  # ISO format: YYYY-MM-DD
    due_date: str | None = None    # ISO format: YYYY-MM-DD
    
    # Hierarchy
    parent: str | None = None  # Parent work item ID (e.g., "PROJ-123")
    children: list["WorkItem"] = Field(default_factory=list)
    
    # Assignments
    assignees: list[str] = Field(default_factory=list)  # List of emails or user IDs
    watchers: list[str] = Field(default_factory=list)   # Collaborators to notify
    
    # Dependencies & Relationships (for dependency charts)
    blocked_by: list[str] = Field(default_factory=list)  # Work items blocking this one
    blocking: list[str] = Field(default_factory=list)    # Work items this one blocks
    duplicate_of: str | None = None                      # Original work item if this is a duplicate
    relates_to: list[str] = Field(default_factory=list)  # Related work items
    
    # Custom properties
    properties: dict[str, Any] = Field(default_factory=dict)  # Custom properties (e.g., {"platform": "iOS", "severity": "critical"})


class ProjectConfig(BaseModel):
    workspace: str
    project_key: str  # Short identifier like "MYPROJ"
    project_uuid: str | None = None  # Actual UUID from Plane
    project_name: str | None = None
    api_url: str = "https://api.plane.so"
    default_type: str = "task"


class WorkItemState(BaseModel):
    """State tracking for a single work item."""
    remote_id: str
    content_hash: str
    source: str  # e.g., "work/inbox.yaml:0" (file path + index)
    last_synced: str
    

class SyncState(BaseModel):
    last_sync: str | None = None
    types: dict[str, str] = Field(default_factory=dict)  # name -> remote_id
    states: dict[str, str] = Field(default_factory=dict)  # name -> remote_id
    labels: dict[str, str] = Field(default_factory=dict)  # name -> remote_id
    work_items: dict[str, WorkItemState] = Field(default_factory=dict)  # id/hash -> state
