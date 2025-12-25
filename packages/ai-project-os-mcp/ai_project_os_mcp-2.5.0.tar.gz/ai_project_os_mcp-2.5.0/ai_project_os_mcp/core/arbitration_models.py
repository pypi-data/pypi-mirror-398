"""
Arbitration Models - Define arbitration case models

These models ensure that when conflicts arise between system governance and human judgment,
we have a structured way to resolve them with clear accountability and auditability.
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
import uuid

from .stage_models import _RoleType as RoleType
from .human_sovereignty_models import _SovereigntyMode as SovereigntyMode


class _ArbitrationCase(BaseModel):
    """仲裁案例模型
    
    记录仲裁案例的完整信息，包括冲突决策、仲裁员、最终决策和责任承担者
    确保仲裁过程可审计、可重放，责任可追溯
    """
    case_id: str = Field(default_factory=lambda: f"arbitration-{uuid.uuid4()}", description="仲裁案例ID")
    trigger_reason: str = Field(..., description="触发仲裁的原因")
    involved_entities: List[str] = Field(..., description="涉及的实体ID列表")
    conflicting_decisions: List[Dict[str, Any]] = Field(..., description="冲突的决策列表")
    arbitrators: List[str] = Field(..., description="仲裁员ID列表")
    arbitrator_id: str = Field(..., description="主仲裁员ID（必填）")
    arbitrator_role: RoleType = Field(..., description="主仲裁员角色（必填）")
    decision_rationale: str = Field(..., description="仲裁决策理由（必填）")
    final_decision: Optional[Dict[str, Any]] = Field(None, description="最终决策")
    final_responsibility_holder: Optional[str] = Field(..., description="最终责任承担者（必填）")
    final_sovereignty_mode: Optional[SovereigntyMode] = Field(None, description="最终主权模式")
    status: Literal["open", "resolved"] = Field(default="open", description="仲裁状态")
    created_at: datetime = Field(default_factory=datetime.now, description="案例创建时间")
    resolved_at: Optional[datetime] = Field(None, description="案例解决时间")
    context: Dict[str, Any] = Field(..., description="仲裁上下文")
    sovereignty_context: Dict[str, Any] = Field(..., description="仲裁时的主权上下文")
    
    class Config:
        frozen = True  # 仲裁案例不可修改，确保审计完整性
        use_enum_values = True  # 序列化时使用枚举值而非名称


class _ArbitrationResolution(BaseModel):
    """仲裁决议模型
    
    记录仲裁的最终决议，包括主权归属和责任分配
    """
    resolution_id: str = Field(default_factory=lambda: f"resolution-{uuid.uuid4()}", description="仲裁决议ID")
    case_id: str = Field(..., description="关联的仲裁案例ID")
    arbitrator_id: str = Field(..., description="仲裁员ID")
    arbitrator_role: RoleType = Field(..., description="仲裁员角色")
    resolution: Dict[str, Any] = Field(..., description="仲裁决议内容")
    rationale: str = Field(..., description="决议理由")
    final_responsibility_holder: str = Field(..., description="最终责任承担者")
    new_sovereignty_mode: SovereigntyMode = Field(..., description="新的主权模式")
    timestamp: datetime = Field(default_factory=datetime.now, description="决议时间")
    
    class Config:
        frozen = True  # 仲裁决议不可修改
        use_enum_values = True  # 序列化时使用枚举值而非名称


class _ArbitrationRequest(BaseModel):
    """仲裁请求模型
    
    记录请求仲裁的详细信息
    """
    request_id: str = Field(default_factory=lambda: f"request-{uuid.uuid4()}", description="仲裁请求ID")
    requester_id: str = Field(..., description="请求者ID")
    requester_role: RoleType = Field(..., description="请求者角色")
    reason: str = Field(..., description="请求仲裁的原因")
    conflicting_event_ids: List[str] = Field(..., description="冲突事件ID列表")
    context: Dict[str, Any] = Field(..., description="请求上下文")
    timestamp: datetime = Field(default_factory=datetime.now, description="请求时间")
    
    class Config:
        frozen = True  # 仲裁请求不可修改
        use_enum_values = True  # 序列化时使用枚举值而非名称


__all__ = []
