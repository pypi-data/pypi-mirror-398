"""
Sovereignty Context - Define sovereignty context models for governance

This module implements the core sovereignty context models ensuring that every governance outcome
can answer: "Who has sovereignty, under what conditions, and which agents are active?"
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class _SovereigntyContext(BaseModel):
    """主权上下文模型
    
    确保每一个事件、决策、动作都绑定一个主权上下文
    支持主权上下文快照，用于审计与回放
    确保Replay时严格一致
    
    治理不变量：
    - 任一时刻只能存在一个Primary Sovereign
    - 多Agent ≠ 多主权
    - 每一个事件、决策、动作都必须绑定一个SovereigntyContext
    - Replay时必须严格一致
    """
    primary_sovereign: Literal["system", "human", "arbitration"] = Field(..., description="主要主权主体")
    active_agents: List[str] = Field(default_factory=list, description="当前活跃的Agent列表")
    stage: str = Field(..., description="当前治理阶段")
    governance_version: str = Field(..., description="治理引擎版本")
    policy_version: str = Field(..., description="策略版本")
    timestamp: datetime = Field(default_factory=datetime.now, description="上下文创建时间")
    
    class Config:
        frozen = True  # 主权上下文不可修改，确保审计完整性
        use_enum_values = True  # 序列化时使用枚举值而非名称


class _SovereigntyContextSnapshot(_SovereigntyContext):
    """主权上下文快照
    
    用于审计和回放，确保历史主权状态可追溯
    """
    snapshot_id: str = Field(..., description="快照ID")
    event_id: str = Field(..., description="关联的事件ID")
    decision_id: Optional[str] = Field(None, description="关联的决策ID")
    action_id: Optional[str] = Field(None, description="关联的动作ID")
    
    class Config:
        frozen = True  # 快照不可修改，确保审计完整性
        use_enum_values = True  # 序列化时使用枚举值而非名称


__all__ = []
