"""
Action executor for automations.

Executes actions returned by automation scripts/YAML against the Plane API.
"""

from __future__ import annotations
from typing import Any, TYPE_CHECKING

from .models import ActionResult

if TYPE_CHECKING:
    from planecompose.backend.base import Backend


class ActionExecutor:
    """
    Execute automation actions.
    
    Converts action dicts into Plane API calls.
    Supports dry-run mode for testing.
    """
    
    # Valid action types
    ACTION_TYPES = {
        "set", "assign", "unassign", 
        "add_label", "add_labels", "remove_label", "remove_labels",
        "comment", "notify", "create"
    }
    
    def __init__(self, backend: "Backend | None" = None, dry_run: bool = False):
        """
        Initialize action executor.
        
        Args:
            backend: Plane backend for API calls (None for dry-run only)
            dry_run: If True, don't execute actions, just record them
        """
        self.backend = backend
        self.dry_run = dry_run
        self.executed: list[ActionResult] = []
    
    async def execute(
        self, 
        work_item_id: str, 
        actions: list[dict[str, Any]]
    ) -> list[ActionResult]:
        """
        Execute a list of actions on a work item.
        
        Args:
            work_item_id: ID of the work item to modify
            actions: List of action dicts
            
        Returns:
            List of ActionResult for each action
        """
        results = []
        
        for action in actions:
            result = await self._execute_single(work_item_id, action)
            results.append(result)
            self.executed.append(result)
        
        return results
    
    async def _execute_single(
        self, 
        work_item_id: str, 
        action: dict[str, Any]
    ) -> ActionResult:
        """Execute a single action."""
        action_type = self._get_action_type(action)
        
        if action_type not in self.ACTION_TYPES:
            return ActionResult(
                action="unknown",
                data=action,
                success=False,
                error=f"Unknown action type: {action_type}"
            )
        
        # Dry run mode - just record
        if self.dry_run:
            return ActionResult(
                action=action_type,
                data=action.get(action_type),
                success=True,
                dry_run=True
            )
        
        # No backend - can't execute
        if self.backend is None:
            return ActionResult(
                action=action_type,
                data=action.get(action_type),
                success=False,
                error="No backend configured"
            )
        
        # Execute the action
        try:
            if action_type == "set":
                await self._execute_set(work_item_id, action["set"])
                
            elif action_type == "assign":
                await self._execute_assign(work_item_id, action["assign"])
                
            elif action_type == "unassign":
                await self._execute_unassign(work_item_id, action["unassign"])
                
            elif action_type in ("add_label", "add_labels"):
                labels = action.get("add_label") or action.get("add_labels")
                await self._execute_add_label(work_item_id, labels)
                
            elif action_type in ("remove_label", "remove_labels"):
                labels = action.get("remove_label") or action.get("remove_labels")
                await self._execute_remove_label(work_item_id, labels)
                
            elif action_type == "comment":
                await self._execute_comment(work_item_id, action["comment"])
                
            elif action_type == "notify":
                await self._execute_notify(action["notify"])
                
            elif action_type == "create":
                await self._execute_create(action["create"])
            
            return ActionResult(
                action=action_type,
                data=action.get(action_type),
                success=True
            )
            
        except Exception as e:
            return ActionResult(
                action=action_type,
                data=action.get(action_type),
                success=False,
                error=str(e)
            )
    
    # =========================================================================
    # ACTION IMPLEMENTATIONS
    # =========================================================================
    
    async def _execute_set(self, work_item_id: str, fields: dict[str, Any]) -> None:
        """Set fields on work item."""
        # Filter to allowed fields
        allowed = {"state", "priority", "type", "start_date", "due_date", "properties"}
        update_data = {k: v for k, v in fields.items() if k in allowed or k.startswith("properties.")}
        
        if update_data and self.backend:
            # Convert to WorkItem and update
            from planecompose.core.models import WorkItem
            work_item = WorkItem(title="", **update_data)  # Minimal for update
            await self.backend.update_work_item(work_item_id, work_item)
    
    async def _execute_assign(self, work_item_id: str, assignees: str | list[str]) -> None:
        """Assign work item to user(s)."""
        if isinstance(assignees, str):
            assignees = [assignees]
        
        # Would need backend method for assignment
        # await self.backend.assign_work_item(work_item_id, assignees)
        pass
    
    async def _execute_unassign(self, work_item_id: str, assignees: str | list[str]) -> None:
        """Remove assignee(s) from work item."""
        if isinstance(assignees, str):
            assignees = [assignees]
        
        # Would need backend method
        # await self.backend.unassign_work_item(work_item_id, assignees)
        pass
    
    async def _execute_add_label(self, work_item_id: str, labels: str | list[str]) -> None:
        """Add label(s) to work item."""
        if isinstance(labels, str):
            labels = [labels]
        
        # Would need backend method
        # await self.backend.add_labels(work_item_id, labels)
        pass
    
    async def _execute_remove_label(self, work_item_id: str, labels: str | list[str]) -> None:
        """Remove label(s) from work item."""
        if isinstance(labels, str):
            labels = [labels]
        
        # Would need backend method
        # await self.backend.remove_labels(work_item_id, labels)
        pass
    
    async def _execute_comment(self, work_item_id: str, comment: str) -> None:
        """Add comment to work item."""
        # Would need backend method
        # await self.backend.add_comment(work_item_id, comment)
        pass
    
    async def _execute_notify(self, notification: dict[str, str]) -> None:
        """Send notification (Slack, email, webhook)."""
        channel = notification.get("channel")
        to = notification.get("to")
        message = notification.get("message", "")
        
        # Would integrate with notification service
        # For now, just log
        pass
    
    async def _execute_create(self, work_item_data: dict[str, Any]) -> None:
        """Create a new work item."""
        from planecompose.core.models import WorkItem
        
        work_item = WorkItem(**work_item_data)
        
        if self.backend:
            await self.backend.create_work_item(work_item)
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _get_action_type(self, action: dict) -> str:
        """Get the type of an action dict."""
        for key in self.ACTION_TYPES:
            if key in action:
                return key
        
        # Check for combined keys
        keys = set(action.keys()) - {"when", "otherwise"}
        if keys:
            return list(keys)[0]
        
        return "unknown"
    
    def _normalize_list(self, value: str | list[str]) -> list[str]:
        """Normalize string or list to list."""
        if isinstance(value, str):
            return [value]
        return list(value)


def format_action(action: dict[str, Any]) -> str:
    """Format an action for display."""
    action_type = None
    data = None
    
    for key in ActionExecutor.ACTION_TYPES:
        if key in action:
            action_type = key
            data = action[key]
            break
    
    if action_type is None:
        return str(action)
    
    # Format based on type
    if action_type == "set":
        fields = ", ".join(f"{k}={v}" for k, v in data.items())
        return f"set: {{{fields}}}"
    
    if action_type in ("assign", "add_label", "remove_label"):
        if isinstance(data, list):
            return f"{action_type}: {', '.join(data)}"
        return f"{action_type}: {data}"
    
    if action_type == "comment":
        preview = data[:50] + "..." if len(data) > 50 else data
        return f'comment: "{preview}"'
    
    if action_type == "notify":
        target = data.get("channel") or data.get("to") or "?"
        return f"notify: {target}"
    
    return f"{action_type}: {data}"

