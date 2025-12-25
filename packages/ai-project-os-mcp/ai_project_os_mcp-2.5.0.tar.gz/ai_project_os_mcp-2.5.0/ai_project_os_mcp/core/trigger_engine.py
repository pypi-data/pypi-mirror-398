"""
Trigger Engine - Evaluates events and detects violations
"""

from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from enum import Enum

from .events import _EventType as EventType, _GovernanceEvent as GovernanceEvent
from .violation import _GovernanceViolation as GovernanceViolation, _ViolationLevel as ViolationLevel


class _TriggerCondition(BaseModel):
    """Trigger condition definition"""
    event: EventType = Field(..., description="Type of event to trigger on")
    condition: str = Field(..., description="Condition expression to evaluate")


class _GovernanceTrigger(BaseModel):
    """Governance trigger definition"""
    id: str = Field(..., description="Unique trigger ID")
    when: _TriggerCondition = Field(..., description="When to trigger")
    violation: ViolationLevel = Field(..., description="Violation level when triggered")
    message: str = Field(..., description="Violation message")
    enabled: bool = Field(default=True, description="Whether the trigger is enabled")


class _TriggerEngine:
    """
    Trigger Engine - Evaluates events and detects violations
    
    This is a private module - do not use directly outside governance_engine.py
    """
    
    def __init__(self, caller):
        if caller.__class__.__name__ != "GovernanceEngine":
            raise RuntimeError("Unauthorized access to TriggerEngine")
        self.caller = caller
        self.triggers = self._load_default_triggers()
    
    def _load_default_triggers(self) -> List[_GovernanceTrigger]:
        """Load default governance triggers"""
        return [
            _GovernanceTrigger(
                id="code_outside_s5",
                when=_TriggerCondition(
                    event=EventType.CODE_GENERATION,
                    condition="stage != 'S5'"
                ),
                violation=ViolationLevel.CRITICAL,
                message="Code generation outside S5 stage",
                enabled=True
            ),
            _GovernanceTrigger(
                id="audit_missing",
                when=_TriggerCondition(
                    event=EventType.AUDIT_MISSING,
                    condition="audit_required == True"
                ),
                violation=ViolationLevel.MAJOR,
                message="Audit required but missing",
                enabled=True
            ),
            _GovernanceTrigger(
                id="arch_violation",
                when=_TriggerCondition(
                    event=EventType.ARCH_VIOLATION,
                    condition="true"
                ),
                violation=ViolationLevel.MINOR,
                message="Architecture violation detected",
                enabled=True
            )
        ]
    
    def evaluate(self, event: GovernanceEvent, state: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Evaluate event against triggers to determine if any should fire
        
        Args:
            event: Governance event to evaluate
            state: Current project state
            
        Returns:
            Tuple[bool, List[str]]: (是否触发，匹配的触发条件ID列表)
        """
        trigger_ids = []
        
        for trigger in self.triggers:
            if not trigger.enabled:
                continue
            
            if self._should_trigger(trigger, event, state):
                trigger_ids.append(trigger.id)
        
        return len(trigger_ids) > 0, trigger_ids
    
    def detect_violations(self, event: GovernanceEvent, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect violations based on event and state
        
        Args:
            event: Governance event to evaluate
            state: Current project state
            
        Returns:
            List of detected violations
        """
        violations = []
        
        for trigger in self.triggers:
            if not trigger.enabled:
                continue
            
            if self._should_trigger(trigger, event, state):
                violation = self._create_violation(trigger, event)
                violations.append(violation.model_dump())
        
        return violations
    
    def _should_trigger(self, trigger: _GovernanceTrigger, event: GovernanceEvent, state: Dict[str, Any]) -> bool:
        """
        Check if a trigger should fire for the given event and state
        
        Args:
            trigger: Governance trigger to check
            event: Governance event to evaluate
            state: Current project state
            
        Returns:
            True if the trigger should fire, False otherwise
        """
        # Check event type match
        if trigger.when.event != event.event_type:
            return False
        
        # Check condition using safe structured comparison
        condition = trigger.when.condition
        
        # Get context from event and state
        context = {
            "event_type": event.event_type,
            "actor_id": event.actor.id,
            "actor_role": event.actor.role,
            "actor_role_type": event.actor.source,  # Use source as role_type for now
            **state,  # Add state to context
            **event.payload  # Add event payload to context
        }
        
        # Safe condition evaluation using structured comparison
        return self._safe_condition_eval(condition, context)
    
    def _safe_condition_eval(self, condition: str, context: Dict[str, Any]) -> bool:
        """
        Safe condition evaluation using structured comparison
        
        治理不变量：条件不明确=fail-closed，禁止静默绕过
        
        Args:
            condition: Condition string to evaluate (e.g., "stage != S5")
            context: Context dictionary for evaluation
            
        Returns:
            True if condition is met, False otherwise
            
        Raises:
            RuntimeError: If condition evaluation fails due to missing context, triggering governance violation
        """
        # Remove whitespace
        condition = condition.strip()
        
        # Split condition into parts, check multi-character operators first
        if "!=" in condition:
            left, right = condition.split("!=")
            operator = "!="
        elif "==" in condition:
            left, right = condition.split("==")
            operator = "=="
        elif ">=" in condition:
            left, right = condition.split(">=")
            operator = ">="
        elif "<=" in condition:
            left, right = condition.split("<=")
            operator = "<="
        elif ">" in condition:
            left, right = condition.split(">")
            operator = ">"
        elif "<" in condition:
            left, right = condition.split("<")
            operator = "<"
        else:
            # Unknown condition format, fail closed
            raise RuntimeError(f"Governance invariant violation: Invalid condition format: '{condition}'")
        
        # Trim whitespace
        left = left.strip()
        right = right.strip().strip("'\"").strip()  # Remove quotes
        
        # Get left value from context
        if left not in context:
            # 治理不变量：条件依赖的上下文缺失，视为治理失败，触发fail-closed
            raise RuntimeError(f"Governance invariant violation: Missing context for condition '{condition}' - '{left}' not in context")
        
        left_value = context[left]
        
        # Compare values
        if operator == "!=":
            return left_value != right
        elif operator == "==":
            return left_value == right
        elif operator == ">":
            try:
                return float(left_value) > float(right)
            except (ValueError, TypeError):
                raise RuntimeError(f"Governance invariant violation: Invalid numeric comparison for condition '{condition}'")
        elif operator == "<":
            try:
                return float(left_value) < float(right)
            except (ValueError, TypeError):
                raise RuntimeError(f"Governance invariant violation: Invalid numeric comparison for condition '{condition}'")
        elif operator == ">=":
            try:
                return float(left_value) >= float(right)
            except (ValueError, TypeError):
                raise RuntimeError(f"Governance invariant violation: Invalid numeric comparison for condition '{condition}'")
        elif operator == "<=":
            try:
                return float(left_value) <= float(right)
            except (ValueError, TypeError):
                raise RuntimeError(f"Governance invariant violation: Invalid numeric comparison for condition '{condition}'")
        
        return False
    
    def _create_violation(self, trigger: _GovernanceTrigger, event: GovernanceEvent) -> GovernanceViolation:
        """Create a violation object from a trigger and event"""
        return GovernanceViolation(
            level=trigger.violation,
            rule_id=trigger.id,
            event_id=event.id,
            actor_id=event.actor.id,
            message=trigger.message
        )
    
    def get_triggers(self) -> List[Dict[str, Any]]:
        """Get list of registered triggers"""
        return [trigger.model_dump() for trigger in self.triggers]
    
    def add_trigger(self, trigger: _GovernanceTrigger):
        """Add a new trigger"""
        self.triggers.append(trigger)
    
    def remove_trigger(self, trigger_id: str):
        """Remove a trigger by ID"""
        self.triggers = [t for t in self.triggers if t.id != trigger_id]


__all__ = []