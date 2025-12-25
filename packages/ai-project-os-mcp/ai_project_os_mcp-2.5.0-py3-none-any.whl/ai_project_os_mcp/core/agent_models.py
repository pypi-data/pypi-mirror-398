"""
Agent Governance Models - Define governance models for multi-agent systems

This module implements the core agent governance models ensuring that in a multi-agent environment:
- Sovereignty is not diluted
- Accountability is not fragmented
- Arbitration is not bypassed

Key Governance Invariants:
1. Sovereignty Singularity: Only one Primary Sovereign at any time
2. Non-Fragmentable Accountability: Results can be attributed to clear accountability entities
3. Non-Bypassable Arbitration: Agent conflicts must enter governance pipeline
4. Single Gate holds for multi-agent: All agent actions through GovernanceEngine
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Literal, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid


class _GovernanceAgent(BaseModel):
    """Agent治理模型
    
    定义Agent的身份、权限、责任域和注册信息
    确保Agent永远不是Sovereign，只能在被授权的责任域内行动
    
    治理规则：
    - Agent永远不是Sovereign
    - Agent只能在被授权的责任域内行动
    - Agent Registry是append-only的，任何变更都会创建新的Agent版本
    - 历史事件绑定到Agent版本，而不仅仅是Agent ID
    """
    agent_id: str = Field(..., description="Agent唯一标识")
    agent_type: Literal["system", "assistant", "tool", "external"] = Field(..., description="Agent类型")
    authority_scope: List[str] = Field(default_factory=list, description="Agent被授权的权限范围")
    responsibility_scope: List[str] = Field(default_factory=list, description="Agent被授权的责任域")
    delegation_allowed: bool = Field(default=False, description="是否允许责任委托")
    registered_by: str = Field(..., description="注册该Agent的实体ID")
    version: str = Field(default_factory=lambda: f"v1-{uuid.uuid4()}", description="Agent版本，每次变更创建新的版本")
    created_at: datetime = Field(default_factory=datetime.now, description="Agent注册时间")
    is_active: bool = Field(default=True, description="Agent是否活跃")
    
    class Config:
        frozen = True  # Agent信息一旦创建不可修改，只能创建新版本
        use_enum_values = True  # 序列化时使用枚举值而非名称


class _AgentProposal(BaseModel):
    """Agent决策建议模型
    
    用于收集Agent的决策建议，确保Agent决策可审计、可回放
    
    治理规则：
    - Agent决策 ≠ Action
    - Agent决策不得直接生成Action，必须经过统一Policy Resolution
    - 如果AgentProposal在Replay时不一致，Replay必须失败
    """
    proposal_id: str = Field(default_factory=lambda: f"proposal-{uuid.uuid4()}", description="决策建议ID")
    agent_id: str = Field(..., description="提出建议的Agent ID")
    agent_version: str = Field(..., description="提出建议的Agent版本")
    content: Dict[str, Any] = Field(..., description="决策建议内容")
    responsibility_scope: List[str] = Field(..., description="建议涉及的责任域")
    timestamp: datetime = Field(default_factory=datetime.now, description="建议提出时间")
    confidence: Optional[float] = Field(None, description="建议的置信度")
    dependencies: List[str] = Field(default_factory=list, description="建议依赖的其他建议ID")
    replay_context: Dict[str, Any] = Field(default_factory=dict, description="用于回放验证的上下文信息")
    
    class Config:
        frozen = True  # 决策建议一旦创建不可修改，确保Replay一致性
        use_enum_values = True  # 序列化时使用枚举值而非名称


class _AgentConflict(BaseModel):
    """Agent冲突模型
    
    用于记录Agent间的冲突，确保所有冲突都能被治理流水线处理
    
    治理规则：
    - 多Agent冲突不得私下解决
    - 必须进入治理流水线并可被仲裁
    - 不允许"Agent A一部分、Agent B一部分"的责任逃逸
    """
    conflict_id: str = Field(default_factory=lambda: f"conflict-{uuid.uuid4()}", description="冲突ID")
    conflicting_proposals: List[str] = Field(..., description="冲突的决策建议ID列表")
    conflict_scope: str = Field(..., description="冲突涉及的责任域")
    resolution_required: bool = Field(default=True, description="是否需要仲裁解决")
    timestamp: datetime = Field(default_factory=datetime.now, description="冲突检测时间")
    conflict_type: Literal["permission", "decision", "scope"] = Field(..., description="冲突类型")
    severity: Literal["low", "medium", "high"] = Field(default="medium", description="冲突严重程度")
    description: Optional[str] = Field(None, description="冲突描述")
    
    class Config:
        frozen = True  # 冲突记录一旦创建不可修改，确保审计完整性
        use_enum_values = True  # 序列化时使用枚举值而非名称


class _AgentVersion(BaseModel):
    """Agent版本模型
    
    用于管理Agent的版本信息，确保Agent Registry是append-only的
    """
    agent_id: str = Field(..., description="Agent ID")
    version: str = Field(..., description="Agent版本")
    parent_version: Optional[str] = Field(None, description="父版本ID")
    created_at: datetime = Field(default_factory=datetime.now, description="版本创建时间")
    created_by: str = Field(..., description="创建该版本的实体ID")
    change_log: Dict[str, Any] = Field(default_factory=dict, description="版本变更日志")
    
    class Config:
        frozen = True  # 版本信息一旦创建不可修改
        use_enum_values = True  # 序列化时使用枚举值而非名称


class _AgentRegistration(BaseModel):
    """Agent注册请求模型
    
    用于处理Agent的注册请求，确保所有Agent都经过严格的注册流程
    """
    agent_id: str = Field(..., description="Agent ID")
    agent_type: Literal["system", "assistant", "tool", "external"] = Field(..., description="Agent类型")
    authority_scope: List[str] = Field(default_factory=list, description="请求的权限范围")
    responsibility_scope: List[str] = Field(default_factory=list, description="请求的责任域")
    delegation_allowed: bool = Field(default=False, description="是否允许责任委托")
    registered_by: str = Field(..., description="注册该Agent的实体ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Agent元数据")
    
    class Config:
        use_enum_values = True  # 序列化时使用枚举值而非名称


__all__ = []
