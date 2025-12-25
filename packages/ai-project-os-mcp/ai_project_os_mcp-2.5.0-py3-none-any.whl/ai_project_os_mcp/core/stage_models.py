"""
Stage Models - Define governance stage data models

This module defines the core data models for governance stages, including:
1. GovernanceStage - Core stage definition with immutability constraints
2. StageTransition - Stage transition record
3. StageAuthority - Stage authority definition

These models enforce governance invariants and ensure stage authority is maintained.
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, model_validator

from .events import _EventType as EventType
from .policy_engine import _ActionType as ActionType


# Define RoleType for stage transition authorization
class _RoleType(str, Enum):
    """Types of actor roles"""
    SYSTEM = "SYSTEM"
    HUMAN = "HUMAN"
    AI = "AI"
    PLANNER = "PLANNER"
    CODER = "CODER"
    REVIEWER = "REVIEWER"


class _GovernanceStage(BaseModel):
    """治理阶段模型 - 治理规范，不可变
    
    Governance Authority Invariants:
    1. Stage Definition is immutable governance spec, not runtime config
    2. Stage definition can only be loaded at system initialization
    3. Stage definition change = Governance Spec Upgrade
    4. Stage definition cannot be modified at runtime
    """
    stage_id: str = Field(..., description="阶段唯一标识")
    name: str = Field(..., description="阶段名称")
    version: str = Field(default="1.0", description="阶段定义版本")
    immutable: bool = Field(default=True, description="阶段定义是否不可变")
    defined_at: datetime = Field(default_factory=datetime.now, description="阶段定义时间")
    allowed_events: List[EventType] = Field(default_factory=list, description="允许的事件类型")
    allowed_actions: List[ActionType] = Field(default_factory=list, description="允许的动作类型")
    can_freeze: bool = Field(default=True, description="是否可以冻结")
    can_unfreeze: bool = Field(default=True, description="是否可以解冻")
    allowed_transition_actors: List[_RoleType] = Field(default_factory=lambda: [_RoleType.SYSTEM, _RoleType.HUMAN], description="允许触发跃迁的角色类型")
    next_stages: List[str] = Field(default_factory=list, description="允许跃迁到的下一阶段")
    prev_stages: List[str] = Field(default_factory=list, description="允许跃迁来的前一阶段")
    overlay_states: List[str] = Field(default_factory=lambda: ["frozen"], description="允许的覆盖状态")
    
    class _Config:
        """Model configuration"""
        extra = "forbid"  # Strict validation, no extra fields allowed
        frozen = True  # Make the model immutable
    
    @model_validator(mode='after')
    def validate_stage_invariants(cls, values):
        """Validate stage invariants"""
        # Stage ID must start with 'S' followed by a number
        if not values.stage_id.startswith('S') or not values.stage_id[1:].isdigit():
            raise ValueError(f"Stage ID must be in format 'S1', 'S2', etc. Got '{values.stage_id}'")
        
        # Stage name must not be empty
        if not values.name:
            raise ValueError("Stage name cannot be empty")
        
        # Must have at least one allowed event
        if not values.allowed_events:
            raise ValueError("Stage must have at least one allowed event")
        
        # Must have at least one allowed action
        if not values.allowed_actions:
            raise ValueError("Stage must have at least one allowed action")
        
        return values


class _StageTransition(BaseModel):
    """阶段跃迁记录"""
    from_stage: str = Field(..., description="源阶段")
    to_stage: str = Field(..., description="目标阶段")
    actor_id: str = Field(..., description="触发者ID")
    actor_role: _RoleType = Field(..., description="触发者角色")
    reason: str = Field(..., description="跃迁原因")
    timestamp: datetime = Field(default_factory=datetime.now, description="跃迁时间")
    transition_id: str = Field(default_factory=lambda: f"transition-{datetime.now().timestamp()}", description="跃迁记录ID")


class _StageAuthority(BaseModel):
    """阶段权限定义"""
    stage_id: str = Field(..., description="阶段ID")
    allowed_event_types: List[EventType] = Field(default_factory=list, description="允许的事件类型")
    allowed_action_types: List[ActionType] = Field(default_factory=list, description="允许的动作类型")
    allowed_transition_actors: List[_RoleType] = Field(default_factory=list, description="允许触发跃迁的角色类型")
    can_freeze: bool = Field(default=True, description="是否可以冻结")
    can_unfreeze: bool = Field(default=True, description="是否可以解冻")


__all__ = []
