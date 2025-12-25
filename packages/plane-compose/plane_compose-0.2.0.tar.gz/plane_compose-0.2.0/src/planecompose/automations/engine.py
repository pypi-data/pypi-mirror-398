"""
Automation execution engine.

The main orchestrator that loads, matches, and executes automations.
"""

from __future__ import annotations
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Any, TYPE_CHECKING

from .models import (
    AutomationDefinition, 
    ExecutionContext, 
    ExecutionResult,
    ActionResult,
)
from .parser import load_automations, validate_automation
from .evaluator import ExpressionEvaluator
from .runner import ScriptRunner
from .actions import ActionExecutor, format_action

if TYPE_CHECKING:
    from planecompose.backend.base import Backend


class AutomationEngine:
    """
    Load, match, and execute automations.
    
    This is the main entry point for the automation system.
    
    Example:
        engine = AutomationEngine(project_root, backend, config)
        engine.load()
        
        # Check for matching automations
        matched = engine.match(event)
        
        # Execute
        for auto in matched:
            result = await engine.execute(auto, event)
    """
    
    def __init__(
        self, 
        project_root: Path, 
        backend: "Backend | None" = None,
        config: dict[str, Any] | None = None,
    ):
        """
        Initialize the automation engine.
        
        Args:
            project_root: Root of the planecompose project
            backend: Plane backend for API calls (optional for dry-run)
            config: Project config from plane.yaml
        """
        self.project_root = Path(project_root)
        self.backend = backend
        self.config = config or {}
        
        # Automations
        self.automations: list[AutomationDefinition] = []
        
        # Components
        self.runner = ScriptRunner(project_root)
        
        # Options
        self.dry_run = False
    
    # =========================================================================
    # LOADING
    # =========================================================================
    
    def load(self) -> int:
        """
        Load automations from the project.
        
        Returns:
            Number of automations loaded
        """
        automations_dir = self.project_root / "automations"
        self.automations = load_automations(automations_dir)
        return len(self.automations)
    
    def get(self, name: str) -> AutomationDefinition | None:
        """Get automation by name."""
        for auto in self.automations:
            if auto.name == name:
                return auto
        return None
    
    # =========================================================================
    # VALIDATION
    # =========================================================================
    
    def validate_all(self) -> dict[str, list[str]]:
        """
        Validate all loaded automations.
        
        Returns:
            Dict mapping automation name to list of errors
        """
        results = {}
        
        for auto in self.automations:
            errors = validate_automation(auto)
            
            # Also validate script if present
            if auto.script:
                script_errors = self.runner.validate(auto.script)
                errors.extend(script_errors)
            
            results[auto.name] = errors
        
        return results
    
    # =========================================================================
    # MATCHING
    # =========================================================================
    
    def match(self, event: dict[str, Any]) -> list[AutomationDefinition]:
        """
        Find automations matching an event.
        
        Args:
            event: Event dict with 'type' and 'payload'
            
        Returns:
            List of matching automations
        """
        matched = []
        event_type = event.get("type", "")
        payload = event.get("payload", {})
        
        for auto in self.automations:
            if not auto.enabled:
                continue
            
            # Check trigger event matches
            if not self._matches_trigger(auto, event_type):
                continue
            
            # Check 'when' conditions
            if auto.when:
                if not self._matches_conditions(auto.when, payload):
                    continue
            
            matched.append(auto)
        
        return matched
    
    def _matches_trigger(self, auto: AutomationDefinition, event_type: str) -> bool:
        """Check if automation trigger matches event type."""
        trigger_event = auto.trigger_event
        
        # Direct match
        if trigger_event == event_type:
            return True
        
        # Schedule triggers match "schedule" events
        if isinstance(auto.on, dict) and "schedule" in auto.on:
            return event_type == "schedule"
        
        return False
    
    def _matches_conditions(self, when: dict[str, Any], payload: dict[str, Any]) -> bool:
        """Check if payload matches 'when' conditions."""
        work_item = payload.get("work_item", payload)
        
        evaluator = ExpressionEvaluator({
            "work_item": work_item,
            "trigger": payload.get("trigger", {}),
            "config": self.config,
        })
        
        for field, expected in when.items():
            # Handle operator-style conditions
            if " " in field:
                # e.g., "labels contains" -> evaluate as condition
                condition = f"{field} {expected}"
                if not evaluator.evaluate_condition(condition):
                    return False
            else:
                # Simple field match
                actual = evaluator._get_field(field)
                
                if isinstance(expected, list):
                    # Value should be in list
                    if actual not in expected:
                        return False
                else:
                    # Exact match
                    if actual != expected:
                        return False
        
        return True
    
    # =========================================================================
    # EXECUTION
    # =========================================================================
    
    async def execute(
        self, 
        automation: AutomationDefinition, 
        event: dict[str, Any]
    ) -> ExecutionResult:
        """
        Execute a single automation.
        
        Args:
            automation: The automation to execute
            event: The triggering event
            
        Returns:
            ExecutionResult with success/failure and actions
        """
        start = datetime.now()
        payload = event.get("payload", {})
        work_item = payload.get("work_item", {})
        
        # Build context
        context = ExecutionContext(
            work_item=work_item,
            trigger={
                "type": event.get("type"),
                "timestamp": event.get("timestamp", datetime.now().isoformat()),
                "changes": payload.get("changes"),
            },
            config=self.config,
        )
        
        try:
            # Get actions
            if automation.script:
                actions = await self._run_script(automation, context)
            else:
                actions = self._evaluate_yaml_actions(automation, context)
            
            # Execute actions
            executor = ActionExecutor(self.backend, dry_run=self.dry_run)
            work_item_id = work_item.get("id", "unknown")
            
            action_results = await executor.execute(work_item_id, actions)
            
            duration = int((datetime.now() - start).total_seconds() * 1000)
            
            return ExecutionResult(
                automation=automation.name,
                success=True,
                actions=action_results,
                duration_ms=duration,
                dry_run=self.dry_run,
            )
            
        except Exception as e:
            duration = int((datetime.now() - start).total_seconds() * 1000)
            
            return ExecutionResult(
                automation=automation.name,
                success=False,
                error=str(e),
                duration_ms=duration,
                dry_run=self.dry_run,
            )
    
    async def _run_script(
        self, 
        automation: AutomationDefinition, 
        context: ExecutionContext
    ) -> list[dict[str, Any]]:
        """Run a script-based automation."""
        if not automation.script:
            return []
        
        return await self.runner.run(
            automation.script,
            context.model_dump(),
        )
    
    def _evaluate_yaml_actions(
        self, 
        automation: AutomationDefinition,
        context: ExecutionContext,
    ) -> list[dict[str, Any]]:
        """
        Evaluate YAML-defined actions.
        
        Handles conditional branching:
        - Actions with 'when' only execute if condition is true
        - 'otherwise' only executes if NO previous 'when' conditions matched
        - Actions without conditions always execute
        """
        if not automation.do:
            return []
        
        evaluator = ExpressionEvaluator(context.model_dump())
        actions = []
        any_when_matched = False
        
        for action_def in automation.do:
            # Handle dict form
            if isinstance(action_def, dict):
                action_dict = action_def.copy()
            else:
                action_dict = action_def.model_dump(exclude_none=True)
            
            # Check condition
            condition = action_dict.pop("when", None)
            is_otherwise = action_dict.pop("otherwise", False)
            
            # Determine if this action should execute
            should_execute = False
            
            if condition:
                # Conditional action - only execute if condition is true
                if evaluator.evaluate_condition(condition):
                    should_execute = True
                    any_when_matched = True
            elif is_otherwise:
                # Otherwise block - only execute if no 'when' matched
                should_execute = not any_when_matched
            else:
                # Unconditional action - always execute
                should_execute = True
            
            if not should_execute:
                continue
            
            # Extract actions from the definition
            for key in ["set", "assign", "unassign", "add_label", "add_labels", 
                       "remove_label", "remove_labels", "comment", "notify", "create"]:
                if key in action_dict:
                    value = action_dict[key]
                    
                    # Evaluate expressions in values
                    value = self._evaluate_value(value, evaluator)
                    
                    actions.append({key: value})
        
        return actions
    
    def _evaluate_value(self, value: Any, evaluator: ExpressionEvaluator) -> Any:
        """Recursively evaluate expressions in a value."""
        if isinstance(value, str):
            return evaluator.evaluate_template(value)
        elif isinstance(value, dict):
            return {k: self._evaluate_value(v, evaluator) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._evaluate_value(v, evaluator) for v in value]
        return value
    
    # =========================================================================
    # BATCH EXECUTION
    # =========================================================================
    
    async def process_events(
        self, 
        events: list[dict[str, Any]]
    ) -> list[ExecutionResult]:
        """
        Process multiple events.
        
        Args:
            events: List of events to process
            
        Returns:
            List of all execution results
        """
        results = []
        
        for event in events:
            matched = self.match(event)
            
            for auto in matched:
                result = await self.execute(auto, event)
                results.append(result)
        
        return results


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_event(
    event_type: str,
    work_item: dict[str, Any],
    changes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create an event dict for testing.
    
    Args:
        event_type: Event type like "work_item.created"
        work_item: Work item data
        changes: Field changes (for update events)
        
    Returns:
        Event dict
    """
    return {
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
        "payload": {
            "work_item": work_item,
            "changes": changes,
        }
    }


def create_sample_work_item(
    id: str = "test-123",
    title: str = "Test work item",
    type: str = "bug",
    state: str = "backlog",
    priority: str = "medium",
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Create a sample work item for testing."""
    return {
        "id": id,
        "title": title,
        "type": type,
        "state": state,
        "priority": priority,
        "labels": labels or [],
        "assignees": [],
        "properties": {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }

