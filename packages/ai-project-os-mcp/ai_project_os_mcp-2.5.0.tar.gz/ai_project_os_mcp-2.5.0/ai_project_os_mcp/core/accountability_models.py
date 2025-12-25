"""
Accountability Models - Define responsibility attribution and accountability models

These models ensure that every governance outcome can answer:
"Who is responsible, under what sovereign conditions, for what consequences?"
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
import uuid


class _ResponsibilityLink(BaseModel):
    """责任链链接
    
    责任链是append-only的，只能被取代，不能删除
    每个责任链接包含完整的主权上下文
    """
    link_id: str = Field(default_factory=lambda: f"link-{uuid.uuid4()}", description="链接ID")
    actor_id: str = Field(..., description="责任人ID")
    role: str = Field(..., description="责任角色")
    stage: str = Field(..., description="责任阶段")
    action_type: str = Field(..., description="责任动作类型")
    sovereignty_context: Dict[str, Any] = Field(..., description="责任发生时的主权上下文")
    reason: str = Field(..., description="责任转移原因")
    timestamp: datetime = Field(default_factory=datetime.now, description="责任转移时间")
    is_superseded: bool = Field(default=False, description="是否被取代")
    superseded_by: Optional[str] = Field(None, description="被哪个链接取代")
    
    class Config:
        frozen = True  # 责任链接一旦创建不可修改
    
    def __str__(self):
        return f"{self.actor_id} ({self.role}) - {self.action_type} at {self.stage} - {self.timestamp}"


class _ResponsibilityResolution(BaseModel):
    """责任解析结果
    
    替代传统的"最终责任人"模型，支持多种责任类型
    """
    resolution_id: str = Field(default_factory=lambda: f"res-{uuid.uuid4()}", description="责任解析ID")
    primary_owner: str = Field(..., description="主要责任人")
    primary_role: str = Field(..., description="主要责任角色")
    contributing_owners: List[str] = Field(default_factory=list, description="贡献责任人")
    contributing_roles: List[str] = Field(default_factory=list, description="贡献责任角色")
    liability_type: Literal["direct", "shared", "delegated", "overridden"] = Field(..., description="责任类型")
    resolution_reason: str = Field(..., description="责任解析原因")
    timestamp: datetime = Field(default_factory=datetime.now, description="责任解析时间")
    
    class Config:
        frozen = True


class _ApprovalRecord(BaseModel):
    """审批记录
    
    审批是一个GovernanceEvent，不是简单的"同意"，而是"接管后果"
    """
    approval_id: str = Field(default_factory=lambda: f"approval-{uuid.uuid4()}", description="审批ID")
    event_id: str = Field(..., description="关联事件ID")
    approver_id: str = Field(..., description="审批人ID")
    approver_role: str = Field(..., description="审批人角色")
    target_id: str = Field(..., description="审批目标ID")
    target_type: str = Field(..., description="审批目标类型")
    decision: bool = Field(..., description="审批决策")
    reason: str = Field(..., description="审批原因")
    timestamp: datetime = Field(default_factory=datetime.now, description="审批时间")
    responsibility_takeover: bool = Field(default=True, description="是否接管责任")
    sovereignty_context: Dict[str, Any] = Field(..., description="审批时的主权上下文")
    responsibility_link_id: Optional[str] = Field(None, description="关联的责任链链接ID")
    
    class Config:
        frozen = True


class _OverrideAction(BaseModel):
    """覆盖动作
    
    覆盖是一个GovernanceEvent，不是简单的"覆盖"，而是"接管后果"
    """
    override_id: str = Field(default_factory=lambda: f"override-{uuid.uuid4()}", description="覆盖ID")
    event_id: str = Field(..., description="关联事件ID")
    actor_id: str = Field(..., description="覆盖人ID")
    actor_role: str = Field(..., description="覆盖人角色")
    original_decision: Dict[str, Any] = Field(..., description="原始决策")
    override_decision: Dict[str, Any] = Field(..., description="覆盖后决策")
    reason: str = Field(..., description="覆盖原因")
    timestamp: datetime = Field(default_factory=datetime.now, description="覆盖时间")
    responsibility_takeover: bool = Field(default=True, description="是否接管责任")
    sovereignty_context: Dict[str, Any] = Field(..., description="覆盖时的主权上下文")
    responsibility_link_id: Optional[str] = Field(None, description="关联的责任链链接ID")
    supersedes: List[str] = Field(default_factory=list, description="取代的责任链链接ID列表")
    
    class Config:
        frozen = True


class _AccountabilityAuditView(BaseModel):
    """问责审计视图
    
    提供完整的责任链和审计信息
    """
    event_id: str = Field(..., description="事件ID")
    responsibility_chain: List[_ResponsibilityLink] = Field(default_factory=list, description="责任链")
    approval_records: List[_ApprovalRecord] = Field(default_factory=list, description="审批记录")
    override_actions: List[_OverrideAction] = Field(default_factory=list, description="覆盖动作")
    final_resolution: Optional[_ResponsibilityResolution] = Field(None, description="最终责任解析")
    sovereignty_contexts: List[Dict[str, Any]] = Field(default_factory=list, description="主权上下文列表")
    
    class Config:
        frozen = True


class _ResponsibilityTransfer(BaseModel):
    """责任转移记录
    
    用于记录责任从一个角色转移到另一个角色
    """
    transfer_id: str = Field(default_factory=lambda: f"transfer-{uuid.uuid4()}", description="转移ID")
    from_actor_id: str = Field(..., description="原责任人ID")
    to_actor_id: str = Field(..., description="新责任人ID")
    reason: str = Field(..., description="转移原因")
    timestamp: datetime = Field(default_factory=datetime.now, description="转移时间")
    sovereignty_context: Dict[str, Any] = Field(..., description="转移时的主权上下文")
    responsibility_link_id: Optional[str] = Field(None, description="关联的责任链链接ID")
    
    class Config:
        frozen = True


class _AccountabilitySummary(BaseModel):
    """问责摘要
    
    用于快速查看责任信息
    """
    event_id: str = Field(..., description="事件ID")
    primary_owner: str = Field(..., description="主要责任人")
    primary_role: str = Field(..., description="主要责任角色")
    liability_type: Literal["direct", "shared", "delegated", "overridden"] = Field(..., description="责任类型")
    approval_count: int = Field(default=0, description="审批数量")
    override_count: int = Field(default=0, description="覆盖数量")
    responsibility_chain_length: int = Field(default=0, description="责任链长度")
    timestamp: datetime = Field(default_factory=datetime.now, description="摘要生成时间")
    
    class Config:
        frozen = True


__all__ = []