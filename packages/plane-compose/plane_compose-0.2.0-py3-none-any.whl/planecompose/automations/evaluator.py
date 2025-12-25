"""
Expression evaluator for automation conditions and templates.

Uses CEL (Common Expression Language) for safe, standard expression evaluation.
Also supports ${{ }} template syntax for familiar GitHub Actions-like experience.
"""

from __future__ import annotations
import re
from typing import Any
from datetime import datetime, timedelta
import logging

# CEL imports
import celpy
from celpy.adapter import json_to_cel
from celpy import CELParseError, CELEvalError

logger = logging.getLogger(__name__)


class ExpressionEvaluator:
    """
    Expression evaluator using CEL (Common Expression Language).
    
    CEL is Google's standard expression language used in:
    - Firebase Security Rules
    - Kubernetes admission policies
    - Cloud IAM conditions
    
    Supports:
    - CEL conditions: work_item.priority == 'high'
    - CEL operators: &&, ||, !, in, size()
    - Template syntax: ${{ title }}, ${{ today + days(3) }}
    
    Documentation: https://github.com/google/cel-spec
    """
    
    # Pattern for ${{ expression }}
    TEMPLATE_PATTERN = re.compile(r'\$\{\{\s*(.+?)\s*\}\}')
    
    # CEL environment (reused for performance)
    _cel_env: celpy.Environment | None = None
    
    def __init__(self, context: dict[str, Any]):
        """
        Initialize evaluator with context.
        
        Args:
            context: Dict with work_item, trigger, config
        """
        self.context = context
        self.work_item = context.get("work_item", {})
        self.trigger = context.get("trigger", {})
        self.config = context.get("config", {})
        
        # Build CEL activation context
        self._cel_context = self._build_cel_context()
    
    @classmethod
    def _get_cel_env(cls) -> celpy.Environment:
        """Get or create CEL environment (singleton for performance)."""
        if cls._cel_env is None:
            cls._cel_env = celpy.Environment()
        return cls._cel_env
    
    def _build_cel_context(self) -> dict:
        """
        Build the context object for CEL evaluation.
        
        Makes fields accessible as:
        - work_item.priority
        - work_item.labels
        - trigger.changes.state.to
        - config.teams.frontend.lead
        """
        return {
            "work_item": self.work_item,
            "trigger": self.trigger,
            "config": self.config,
            # Convenience shortcuts
            "item": self.work_item,
            "changes": self.trigger.get("changes", {}),
        }
    
    # =========================================================================
    # TEMPLATE EVALUATION
    # =========================================================================
    
    def evaluate_template(self, template: str) -> str:
        """
        Evaluate a template string with ${{ }} expressions.
        
        Example:
            "Hello ${{ work_item.assignee }}, task ${{ work_item.title }} is yours"
        """
        if not isinstance(template, str):
            return template
        
        def replacer(match: re.Match) -> str:
            expr = match.group(1).strip()
            try:
                result = self._evaluate_template_expr(expr)
                return str(result) if result is not None else ""
            except Exception as e:
                logger.debug(f"Template expression failed: {expr} - {e}")
                return match.group(0)  # Keep original on error
        
        return self.TEMPLATE_PATTERN.sub(replacer, template)
    
    def _evaluate_template_expr(self, expr: str) -> Any:
        """
        Evaluate a template expression.
        
        Handles both CEL expressions and convenience shortcuts.
        """
        # Date literals
        if expr == "today":
            return datetime.now().strftime("%Y-%m-%d")
        
        if expr == "now":
            return datetime.now().isoformat()
        
        # Date arithmetic: today + days(n)
        if "today + days(" in expr:
            match = re.search(r'days\((\d+)\)', expr)
            if match:
                days = int(match.group(1))
                return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        if "today + weeks(" in expr:
            match = re.search(r'weeks\((\d+)\)', expr)
            if match:
                weeks = int(match.group(1))
                return (datetime.now() + timedelta(weeks=weeks)).strftime("%Y-%m-%d")
        
        # Shortcut: bare field names -> work_item.field
        if self._is_simple_field(expr):
            return self._get_simple_field(expr)
        
        # Try CEL evaluation for complex expressions
        try:
            return self._evaluate_cel(expr)
        except Exception:
            # Fallback to simple field lookup
            return self._get_simple_field(expr)
    
    # =========================================================================
    # CONDITION EVALUATION (CEL)
    # =========================================================================
    
    def evaluate_condition(self, condition: str) -> bool:
        """
        Evaluate a condition expression using CEL.
        
        CEL Examples:
            work_item.type == 'bug'
            work_item.priority == 'high'
            'critical' in work_item.labels
            size(work_item.labels) > 0
            work_item.assignee == null
            work_item.priority == 'high' && 'bug' in work_item.labels
        
        Legacy Syntax (auto-converted to CEL):
            type == bug              -> work_item.type == 'bug'
            labels contains critical -> 'critical' in work_item.labels
        """
        condition = condition.strip()
        
        # Convert legacy syntax to CEL
        cel_expr = self._convert_to_cel(condition)
        
        try:
            result = self._evaluate_cel(cel_expr)
            return bool(result)
        except (CELParseError, CELEvalError) as e:
            logger.warning(f"CEL evaluation failed for '{cel_expr}': {e}")
            # Fallback to legacy evaluation
            return self._legacy_evaluate_condition(condition)
        except Exception as e:
            logger.error(f"Unexpected error evaluating '{cel_expr}': {e}")
            return False
    
    def _evaluate_cel(self, expr: str) -> Any:
        """Evaluate a CEL expression."""
        env = self._get_cel_env()
        ast = env.compile(expr)
        prog = env.program(ast)
        activation = json_to_cel(self._cel_context)
        return prog.evaluate(activation)
    
    def _convert_to_cel(self, condition: str) -> str:
        """
        Convert legacy/shorthand syntax to CEL.
        
        Conversions:
            type == bug          -> work_item.type == 'bug'
            priority == "high"   -> work_item.priority == 'high'
            labels contains x    -> 'x' in work_item.labels
            labels not_contains  -> !('x' in work_item.labels)
            state changed_to: x  -> trigger.changes.state.to == 'x'
            assignee: null       -> work_item.assignee == null
        """
        # Already looks like native CEL (has work_item., trigger., size(), !, etc.)
        cel_indicators = [
            "work_item.", "trigger.", "config.", "item.",
            "size(", "has(", "!(", "&&", "||",
            "' in ", "\" in ",
        ]
        if any(indicator in condition for indicator in cel_indicators):
            return condition
        
        # Starts with negation
        if condition.startswith("!"):
            return condition
        
        # Handle "labels contains value"
        if " contains " in condition and " contains_any" not in condition:
            parts = condition.split(" contains ", 1)
            field = parts[0].strip()
            value = self._normalize_value(parts[1].strip())
            return f"{value} in work_item.{field}"
        
        # Handle "labels not_contains value"
        if " not_contains " in condition:
            parts = condition.split(" not_contains ", 1)
            field = parts[0].strip()
            value = self._normalize_value(parts[1].strip())
            return f"!({value} in work_item.{field})"
        
        # Handle "labels contains_any: [a, b, c]" - complex, use helper
        if " contains_any:" in condition:
            parts = condition.split(" contains_any:", 1)
            field = parts[0].strip()
            values = self._parse_list(parts[1].strip())
            # Build OR expression: 'a' in field || 'b' in field
            clauses = [f"'{v}' in work_item.{field}" for v in values]
            return " || ".join(clauses)
        
        # Handle "state changed_to: done"
        if " changed_to:" in condition:
            parts = condition.split(" changed_to:", 1)
            field = parts[0].strip()
            value = self._normalize_value(parts[1].strip())
            return f"trigger.changes.{field}.to == {value}"
        
        # Handle "state changed_from: backlog"
        if " changed_from:" in condition:
            parts = condition.split(" changed_from:", 1)
            field = parts[0].strip()
            value = self._normalize_value(parts[1].strip())
            return f"trigger.changes.{field}.from == {value}"
        
        # Handle "field == value"
        if " == " in condition:
            parts = condition.split(" == ", 1)
            field = parts[0].strip()
            value = self._normalize_value(parts[1].strip())
            return f"work_item.{field} == {value}"
        
        # Handle "field != value"
        if " != " in condition:
            parts = condition.split(" != ", 1)
            field = parts[0].strip()
            value = self._normalize_value(parts[1].strip())
            return f"work_item.{field} != {value}"
        
        # Handle "field: null" (is null)
        if condition.endswith(": null"):
            field = condition[:-6].strip()
            return f"work_item.{field} == null"
        
        # Handle "field: [a, b, c]" (value in list)
        if ": [" in condition:
            parts = condition.split(": ", 1)
            field = parts[0].strip()
            values = self._parse_list(parts[1].strip())
            # Build OR: field == 'a' || field == 'b'
            clauses = [f"work_item.{field} == '{v}'" for v in values]
            return " || ".join(clauses)
        
        # Assume it's already valid CEL or a simple truthy check
        if self._is_simple_field(condition):
            return f"work_item.{condition} != null && work_item.{condition} != ''"
        
        return condition
    
    def _normalize_value(self, value: str) -> str:
        """Normalize a value for CEL (add quotes if needed)."""
        value = value.strip()
        
        # Already quoted
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            # Normalize to single quotes for CEL
            return f"'{value[1:-1]}'"
        
        # Special values
        if value in ("null", "None"):
            return "null"
        if value in ("true", "True"):
            return "true"
        if value in ("false", "False"):
            return "false"
        
        # Numbers
        if value.isdigit():
            return value
        
        try:
            float(value)
            return value
        except ValueError:
            pass
        
        # String - add quotes
        return f"'{value}'"
    
    # =========================================================================
    # LEGACY FALLBACK (for backwards compatibility)
    # =========================================================================
    
    def _legacy_evaluate_condition(self, condition: str) -> bool:
        """Legacy condition evaluation as fallback."""
        condition = condition.strip()
        
        # Handle "labels contains value"
        if " contains " in condition and " contains_any" not in condition:
            parts = condition.split(" contains ", 1)
            field = parts[0].strip()
            value = self._parse_literal(parts[1].strip())
            field_value = self._get_simple_field(field)
            
            if isinstance(field_value, list):
                return value in field_value
            if isinstance(field_value, str):
                return value in field_value
            return False
        
        # Handle "field == value"
        if " == " in condition:
            parts = condition.split(" == ", 1)
            field = parts[0].strip()
            expected = self._parse_literal(parts[1].strip())
            actual = self._get_simple_field(field)
            return actual == expected
        
        # Handle "field != value"
        if " != " in condition:
            parts = condition.split(" != ", 1)
            field = parts[0].strip()
            expected = self._parse_literal(parts[1].strip())
            actual = self._get_simple_field(field)
            return actual != expected
        
        # Simple field check (truthy)
        value = self._get_simple_field(condition)
        return bool(value)
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _is_simple_field(self, name: str) -> bool:
        """Check if this is a simple work_item field name."""
        simple_fields = {
            "id", "title", "description", "type", "state", "priority",
            "labels", "assignees", "assignee", "properties",
            "created_at", "updated_at", "createdAt", "updatedAt",
            "due_date", "dueDate", "name"
        }
        return name in simple_fields
    
    # Alias for backward compatibility
    def _get_field(self, path: str) -> Any:
        """Alias for _get_simple_field (backward compatibility)."""
        return self._get_simple_field(path)
    
    def _get_simple_field(self, path: str) -> Any:
        """Get a field value from work_item by path."""
        path = path.strip()
        
        # Direct work item field
        if self._is_simple_field(path):
            value = self.work_item.get(path)
            
            # Handle assignee as first of assignees
            if path == "assignee" and value is None:
                assignees = self.work_item.get("assignees", [])
                return assignees[0] if assignees else None
            
            return value
        
        # Config access: config.teams.frontend.lead
        if path.startswith("config."):
            return self._get_nested(self.config, path[7:])
        
        # Properties access: properties.severity
        if path.startswith("properties."):
            props = self.work_item.get("properties", {})
            return self._get_nested(props, path[11:])
        
        # Work item nested access
        if path.startswith("work_item."):
            return self._get_nested(self.work_item, path[10:])
        
        # Try nested work_item access
        return self._get_nested(self.work_item, path)
    
    def _get_nested(self, obj: Any, path: str) -> Any:
        """Get nested value from dict using dot notation."""
        if obj is None:
            return None
        
        parts = path.split(".")
        current = obj
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
        
        return current
    
    def _parse_literal(self, value: str) -> Any:
        """Parse a literal value from string."""
        value = value.strip()
        
        # Quoted string
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        
        # Special values
        if value in ("null", "None"):
            return None
        if value in ("true", "True"):
            return True
        if value in ("false", "False"):
            return False
        
        # Numbers
        if value.isdigit():
            return int(value)
        
        try:
            return float(value)
        except ValueError:
            pass
        
        # Plain string
        return value
    
    def _parse_list(self, value: str) -> list:
        """Parse a list literal: [a, b, c]."""
        value = value.strip()
        
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1]
            items = [item.strip() for item in inner.split(",")]
            return [self._parse_literal(item) for item in items if item]
        
        # Single value
        return [self._parse_literal(value)]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def evaluate_template(template: str, context: dict[str, Any]) -> str:
    """Convenience function to evaluate a template."""
    evaluator = ExpressionEvaluator(context)
    return evaluator.evaluate_template(template)


def evaluate_condition(condition: str, context: dict[str, Any]) -> bool:
    """Convenience function to evaluate a condition."""
    evaluator = ExpressionEvaluator(context)
    return evaluator.evaluate_condition(condition)


def cel_evaluate(expr: str, context: dict[str, Any]) -> Any:
    """
    Directly evaluate a CEL expression.
    
    Example:
        cel_evaluate(
            "work_item.priority == 'high' && 'bug' in work_item.labels",
            {"work_item": {"priority": "high", "labels": ["bug"]}}
        )
    """
    env = celpy.Environment()
    ast = env.compile(expr)
    prog = env.program(ast)
    activation = json_to_cel(context)
    return prog.evaluate(activation)
