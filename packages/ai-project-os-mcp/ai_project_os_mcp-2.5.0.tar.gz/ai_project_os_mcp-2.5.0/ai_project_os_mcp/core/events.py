"""
Governance Events - Enhanced Event Model with Agent Identity
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, List, Literal
import uuid


class _EventStatus(str, Enum):
    """Status of governance events"""
    OPEN = "OPEN"           # Event is open and being processed
    IN_PROGRESS = "IN_PROGRESS"  # Event is being processed
    CLOSED = "CLOSED"       # Event has been processed and closed
    ERROR = "ERROR"         # Event processing failed with error


class _EventType(str, Enum):
    """Types of governance events"""
    STAGE_CHANGE = "STAGE_CHANGE"
    CODE_GENERATION = "CODE_GENERATION"
    ARCH_VIOLATION = "ARCH_VIOLATION"
    AUDIT_MISSING = "AUDIT_MISSING"
    TOOL_CALL = "TOOL_CALL"
    FREEZE_REQUEST = "FREEZE_REQUEST"
    UNFREEZE = "UNFREEZE"
    STATUS = "STATUS"
    POLICY_CHANGE = "POLICY_CHANGE"
    VIOLATION = "VIOLATION"
    SCORE_UPDATE = "SCORE_UPDATE"
    APPROVAL = "APPROVAL"
    OVERRIDE = "OVERRIDE"
    RESPONSIBILITY_TRANSFER = "RESPONSIBILITY_TRANSFER"
    HUMAN_INTERVENTION = "HUMAN_INTERVENTION"           # 人类介入事件
    SOVEREIGNTY_SWITCH = "SOVEREIGNTY_SWITCH"           # 主权切换事件
    ARBITRATION_REQUEST = "ARBITRATION_REQUEST"         # 仲裁请求事件
    ARBITRATION_RESOLUTION = "ARBITRATION_RESOLUTION"   # 仲裁决议事件
    
    # Agent Governance Events
    AGENT_REGISTRATION = "AGENT_REGISTRATION"           # Agent注册事件
    AGENT_UPDATE = "AGENT_UPDATE"                       # Agent更新事件
    AGENT_DEACTIVATION = "AGENT_DEACTIVATION"           # Agent停用事件
    AGENT_PROPOSAL = "AGENT_PROPOSAL"                   # Agent提议事件
    AGENT_CONFLICT = "AGENT_CONFLICT"                   # Agent冲突事件
    AGENT_DECISION = "AGENT_DECISION"                   # Agent决策事件
    AGENT_COORDINATION = "AGENT_COORDINATION"           # Agent协同事件
    AGENT_REPLAY_FAILED = "AGENT_REPLAY_FAILED"         # Agent提议重放失败事件


class _Actor(BaseModel):
    """
    Accountable entity for governance events
    
    Actor represents the accountable entity, not necessarily a human.
    """
    id: str = Field(..., description="Unique identifier for the actor")
    role: Literal["planner", "coder", "reviewer", "system"] = Field(..., description="Role of the actor")
    role_type: Literal["AI", "HUMAN", "SYSTEM"] = Field(..., description="Type of actor")
    source: Literal["claude", "cursor", "trae", "api"] = Field(..., description="Source of the actor")
    name: Optional[str] = Field(None, description="Human-readable name of the actor")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class _GovernanceEvent(BaseModel):
    """Enhanced governance event with agent identity"""
    event_type: _EventType = Field(..., description="Type of governance event")
    actor: _Actor = Field(..., description="Actor who triggered the event")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event-specific payload")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique event identifier")
    status: _EventStatus = Field(default=_EventStatus.OPEN, description="Event status")
    
    class _Config:
        extra = "forbid"  # Strict validation, no extra fields allowed
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


__all__ = []