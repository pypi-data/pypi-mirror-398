"""
Human Sovereignty Models - Define human intervention and sovereignty models

These models ensure that when system governance conflicts with human judgment,
we can clearly answer: Who has sovereignty, how to intervene, whether to take responsibility,
and how to be audited and arbitrated.
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
import uuid

from .stage_models import _RoleType as RoleType


class _SovereigntyMode(str, Enum):
    """主权模式枚举
    
    定义系统的不同主权状态
    """
    SYSTEM_PRIMARY = "system_primary"      # 默认：系统为主权主体
    HUMAN_SUPERVISORY = "human_supervisory" # 人类监督：系统为主权主体，人类有监督权
    HUMAN_OVERRIDE = "human_override"      # 人类主权接管：人类为主权主体，系统退化为执行代理
    ARBITRATION = "arbitration"             # 仲裁模式：主权冻结，等待仲裁


class _HumanIntervention(BaseModel):
    """人类介入模型
    
    记录人类介入系统决策的详细信息
    确保所有人类行为都可审计、可重放
    """
    intervention_id: str = Field(default_factory=lambda: f"intervention-{uuid.uuid4()}", description="介入ID")
    actor_id: str = Field(..., description="介入者ID")
    role: RoleType = Field(..., description="介入者角色")
    mode: _SovereigntyMode = Field(..., description="主权模式")
    target_event_id: str = Field(..., description="目标事件ID")
    reason: str = Field(..., description="介入原因")
    timestamp: datetime = Field(default_factory=datetime.now, description="介入时间")
    responsibility_takeover: bool = Field(default=True, description="是否接管责任")
    original_decision: Optional[Dict[str, Any]] = Field(None, description="原始决策")
    intervention_decision: Optional[Dict[str, Any]] = Field(None, description="介入后的决策")
    sovereignty_context: Dict[str, Any] = Field(..., description="介入时的主权上下文")
    
    class Config:
        frozen = True  # 介入记录不可修改，确保审计完整性
        use_enum_values = True  # 序列化时使用枚举值而非名称


class _SovereigntySwitch(BaseModel):
    """主权切换模型
    
    记录主权从一个主体切换到另一个主体的过程
    """
    switch_id: str = Field(default_factory=lambda: f"switch-{uuid.uuid4()}", description="切换ID")
    from_mode: _SovereigntyMode = Field(..., description="切换前主权模式")
    to_mode: _SovereigntyMode = Field(..., description="切换后主权限模式")
    reason: str = Field(..., description="切换原因")
    timestamp: datetime = Field(default_factory=datetime.now, description="切换时间")
    triggered_by: str = Field(..., description="触发者ID")
    triggered_by_role: RoleType = Field(..., description="触发者角色")
    context: Dict[str, Any] = Field(..., description="切换上下文")
    
    class Config:
        frozen = True  # 主权切换记录不可修改
        use_enum_values = True  # 序列化时使用枚举值而非名称


__all__ = []
