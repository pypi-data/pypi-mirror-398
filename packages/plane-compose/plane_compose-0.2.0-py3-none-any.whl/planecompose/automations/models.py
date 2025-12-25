"""
Automation data models.

Clean, typed models for automation definitions and execution.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any, Literal
from enum import Enum
from datetime import datetime


# =============================================================================
# TRIGGER EVENTS
# =============================================================================

class TriggerEvent(str, Enum):
    """Available trigger events."""
    
    # Work item events
    WORK_ITEM_CREATED = "work_item.created"
    WORK_ITEM_UPDATED = "work_item.updated"
    WORK_ITEM_DELETED = "work_item.deleted"
    WORK_ITEM_ASSIGNED = "work_item.assigned"
    WORK_ITEM_STATE_CHANGED = "work_item.state_changed"
    
    # Comment events
    COMMENT_CREATED = "comment.created"
    
    # Scheduled
    SCHEDULE = "schedule"
    
    # Manual trigger
    MANUAL = "manual"


# =============================================================================
# ACTION TYPES
# =============================================================================

class SetAction(BaseModel):
    """Set fields on work item."""
    set: dict[str, Any]


class AssignAction(BaseModel):
    """Assign work item to user(s)."""
    assign: str | list[str]


class UnassignAction(BaseModel):
    """Remove assignee(s) from work item."""
    unassign: str | list[str]


class AddLabelAction(BaseModel):
    """Add label(s) to work item."""
    add_label: str | list[str]


class RemoveLabelAction(BaseModel):
    """Remove label(s) from work item."""
    remove_label: str | list[str]


class CommentAction(BaseModel):
    """Add comment to work item."""
    comment: str


class NotifyAction(BaseModel):
    """Send notification."""
    notify: dict[str, str]  # channel, to, message


class CreateAction(BaseModel):
    """Create a new work item."""
    create: dict[str, Any]


# Union type for all actions
Action = (
    SetAction | AssignAction | UnassignAction | 
    AddLabelAction | RemoveLabelAction | 
    CommentAction | NotifyAction | CreateAction |
    dict[str, Any]  # Fallback for flexibility
)


# =============================================================================
# AUTOMATION DEFINITION
# =============================================================================

class TriggerConfig(BaseModel):
    """Trigger configuration."""
    event: str | None = None  # Event type (optional if schedule is provided)
    fields: list[str] | None = None  # For updated events: which fields trigger
    schedule: str | None = None  # Cron expression for scheduled triggers
    
    def model_post_init(self, __context: Any) -> None:
        """Validate that either event or schedule is provided."""
        if not self.event and not self.schedule:
            raise ValueError("Trigger must have either 'event' or 'schedule'")


class ConditionalAction(BaseModel):
    """Action with optional condition."""
    when: str | None = None  # Condition expression
    otherwise: bool = False  # Is this the 'otherwise' branch?
    
    # Actions (any combination)
    set: dict[str, Any] | None = None
    assign: str | list[str] | None = None
    unassign: str | list[str] | None = None
    add_label: str | list[str] | None = None
    add_labels: list[str] | None = None  # Alias
    remove_label: str | list[str] | None = None
    comment: str | None = None
    notify: dict[str, str] | None = None
    create: dict[str, Any] | None = None


class RateLimitConfig(BaseModel):
    """Rate limiting configuration."""
    max_per_hour: int = 100
    cooldown: str = "5s"  # e.g., "5s", "1m"


class AutomationDefinition(BaseModel):
    """
    Complete automation definition.
    
    This is what gets parsed from a YAML file.
    """
    # Identity
    name: str
    description: str | None = None
    enabled: bool = True
    
    # Trigger: when does this run?
    on: str | TriggerConfig
    
    # Filter: which items does this apply to?
    when: dict[str, Any] | None = None
    
    # Actions: what to do (choose one)
    do: list[ConditionalAction | dict[str, Any]] | None = None  # YAML actions
    script: str | None = None  # TypeScript script path
    
    # Options
    rate_limit: RateLimitConfig | None = None
    
    # Metadata (set during parsing)
    source_file: str | None = None
    
    @property
    def trigger_event(self) -> str:
        """Get the trigger event name."""
        if isinstance(self.on, str):
            return self.on
        if isinstance(self.on, TriggerConfig):
            if self.on.schedule:
                return "schedule"
            return self.on.event or ""
        if isinstance(self.on, dict):
            if "schedule" in self.on:
                return "schedule"
            return self.on.get("event", "")
        return ""
    
    @property
    def is_script_based(self) -> bool:
        """Check if this automation uses a script."""
        return self.script is not None
    
    def model_post_init(self, __context: Any) -> None:
        """Validate after initialization."""
        if self.do is None and self.script is None:
            # Allow empty automations for now (will be caught in validation)
            pass
        if self.do is not None and self.script is not None:
            raise ValueError("Automation cannot have both 'do' and 'script'")


# =============================================================================
# EXECUTION CONTEXT
# =============================================================================

class WorkItemContext(BaseModel):
    """Work item data passed to automations."""
    id: str
    title: str
    description: str | None = None
    type: str
    state: str
    priority: str | None = None
    labels: list[str] = Field(default_factory=list)
    assignees: list[str] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    updated_at: str | None = None
    
    # Computed
    @property
    def assignee(self) -> str | None:
        """Get first assignee."""
        return self.assignees[0] if self.assignees else None


class TriggerContext(BaseModel):
    """Trigger information."""
    type: str
    timestamp: str
    changes: dict[str, dict[str, Any]] | None = None  # field -> {from, to}


class ExecutionContext(BaseModel):
    """
    Context passed to automation scripts.
    
    This is what your TypeScript script receives.
    """
    work_item: dict[str, Any]  # WorkItemContext as dict for JS compatibility
    trigger: dict[str, Any]
    config: dict[str, Any]  # From plane.yaml
    
    @classmethod
    def create(
        cls,
        work_item: WorkItemContext | dict,
        trigger_type: str,
        changes: dict | None = None,
        config: dict | None = None,
    ) -> "ExecutionContext":
        """Create execution context."""
        if isinstance(work_item, WorkItemContext):
            work_item = work_item.model_dump()
        
        return cls(
            work_item=work_item,
            trigger={
                "type": trigger_type,
                "timestamp": datetime.now().isoformat(),
                "changes": changes,
            },
            config=config or {},
        )


# =============================================================================
# EXECUTION RESULT
# =============================================================================

class ActionResult(BaseModel):
    """Result of a single action."""
    action: str  # set, assign, add_label, etc.
    data: Any
    success: bool = True
    error: str | None = None
    dry_run: bool = False


class ExecutionResult(BaseModel):
    """Result of automation execution."""
    automation: str
    success: bool
    actions: list[ActionResult] = Field(default_factory=list)
    error: str | None = None
    duration_ms: int = 0
    dry_run: bool = False
    
    @property
    def action_count(self) -> int:
        """Number of actions executed."""
        return len(self.actions)
    
    def summary(self) -> str:
        """Get a summary string."""
        if self.success:
            return f"{self.action_count} action{'s' if self.action_count != 1 else ''}"
        return f"failed: {self.error}"

