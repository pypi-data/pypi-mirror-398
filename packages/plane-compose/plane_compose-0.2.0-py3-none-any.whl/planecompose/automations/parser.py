"""
YAML parser for automation definitions.

Handles loading, parsing, and validation of automation files.
"""

from pathlib import Path
from typing import Any
import yaml

from .models import AutomationDefinition, TriggerConfig


def parse_automation_file(file_path: Path) -> AutomationDefinition:
    """
    Parse a single automation YAML file.
    
    Args:
        file_path: Path to the .yaml file
        
    Returns:
        Parsed AutomationDefinition
        
    Raises:
        ValueError: If parsing fails
    """
    content = file_path.read_text()
    data = yaml.safe_load(content)
    
    if data is None:
        raise ValueError(f"Empty automation file: {file_path}")
    
    # Handle YAML quirk: 'on' is parsed as boolean True
    # Convert True key back to "on"
    if True in data:
        data["on"] = data.pop(True)
    if False in data:
        data["off"] = data.pop(False)  # Just in case
    
    # Normalize trigger format
    if isinstance(data.get("on"), str):
        # Simple form: on: work_item.created
        # Keep as string, model handles it
        pass
    elif isinstance(data.get("on"), dict):
        # Expanded form: on: { event: ..., fields: [...] }
        if "event" not in data["on"] and "schedule" not in data["on"]:
            raise ValueError(f"Trigger must have 'event' or 'schedule': {file_path}")
    
    # Normalize 'do' actions
    if "do" in data and data["do"]:
        data["do"] = _normalize_actions(data["do"])
    
    try:
        automation = AutomationDefinition(**data)
        automation.source_file = str(file_path)
        return automation
    except Exception as e:
        raise ValueError(f"Error parsing {file_path}: {e}")


def _normalize_actions(actions: list) -> list:
    """Normalize action definitions."""
    normalized = []
    
    for action in actions:
        if isinstance(action, dict):
            # Handle add_labels -> add_label normalization
            if "add_labels" in action and "add_label" not in action:
                action["add_label"] = action.pop("add_labels")
            if "remove_labels" in action and "remove_label" not in action:
                action["remove_label"] = action.pop("remove_labels")
            normalized.append(action)
        else:
            normalized.append(action)
    
    return normalized


def load_automations(automations_dir: Path) -> list[AutomationDefinition]:
    """
    Load all automations from a directory.
    
    Args:
        automations_dir: Path to automations/ directory
        
    Returns:
        List of parsed automations
    """
    automations = []
    
    if not automations_dir.exists():
        return automations
    
    for file_path in sorted(automations_dir.glob("*.yaml")):
        # Skip files starting with underscore (partials/includes)
        if file_path.name.startswith("_"):
            continue
        
        try:
            automation = parse_automation_file(file_path)
            automations.append(automation)
        except Exception as e:
            raise ValueError(f"Error loading {file_path.name}: {e}")
    
    return automations


def validate_automation(automation: AutomationDefinition) -> list[str]:
    """
    Validate an automation definition.
    
    Args:
        automation: The automation to validate
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Must have a name
    if not automation.name or not automation.name.strip():
        errors.append("Automation must have a 'name'")
    
    # Must have trigger
    if not automation.on:
        errors.append("Automation must have 'on' trigger")
    
    # Must have either 'do' or 'script' (but not both)
    has_do = automation.do is not None and len(automation.do) > 0
    has_script = automation.script is not None
    
    if not has_do and not has_script:
        errors.append("Automation must have either 'do' actions or 'script'")
    
    if has_do and has_script:
        errors.append("Automation cannot have both 'do' and 'script'")
    
    # Validate script path exists
    if has_script and automation.source_file:
        script_path = Path(automation.source_file).parent / automation.script
        if not script_path.exists():
            errors.append(f"Script not found: {automation.script}")
    
    # Validate trigger event
    valid_events = {
        "work_item.created", "work_item.updated", "work_item.deleted",
        "work_item.assigned", "work_item.state_changed",
        "comment.created", "schedule", "manual"
    }
    
    trigger_event = automation.trigger_event
    if trigger_event not in valid_events:
        # Allow schedule with cron
        if not (isinstance(automation.on, dict) and "schedule" in automation.on):
            errors.append(f"Unknown trigger event: {trigger_event}")
    
    return errors


def validate_all(automations: list[AutomationDefinition]) -> dict[str, list[str]]:
    """
    Validate multiple automations.
    
    Returns:
        Dict mapping automation name to list of errors
    """
    results = {}
    
    for auto in automations:
        errors = validate_automation(auto)
        results[auto.name] = errors
    
    return results

