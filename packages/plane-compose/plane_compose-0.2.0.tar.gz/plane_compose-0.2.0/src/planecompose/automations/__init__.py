"""
Plane Automations - Event-driven automation system.

Define automations in YAML, run them locally or on server.
"""

from .models import (
    AutomationDefinition,
    ExecutionContext,
    ExecutionResult,
    Action,
)
from .engine import AutomationEngine
from .parser import load_automations, parse_automation_file

__all__ = [
    "AutomationDefinition",
    "ExecutionContext", 
    "ExecutionResult",
    "Action",
    "AutomationEngine",
    "load_automations",
    "parse_automation_file",
]

