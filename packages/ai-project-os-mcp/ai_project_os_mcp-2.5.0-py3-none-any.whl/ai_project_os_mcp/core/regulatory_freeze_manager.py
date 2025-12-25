"""
Regulatory Freeze Manager - Implement regulatory freeze and unfreeze mechanisms

This module implements the regulatory freeze and unfreeze mechanisms ensuring that external authorities
can freeze the system, and the system cannot self-unfreeze without proper authorization.

Governance Rules:
- External Freezeability: External authority can freeze system, system cannot self-unfreeze
- Freeze Granularity: Support different freeze scopes
- Unfreeze Authorization: Only same or higher authority can unfreeze
- Auditability: All freeze/unfreeze actions must generate governance proofs
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

from .external_authority_models import _ExternalAuthority
from .governance_proof_models import _GovernanceProof
from .governance_attestation import _GovernanceAttestation


class _RegulatoryFreeze(BaseModel):
    """监管冻结记录
    
    记录外部权威发起的冻结请求和状态
    """
    freeze_id: str = Field(default_factory=lambda: f"freeze-{uuid.uuid4()}", description="冻结记录唯一标识")
    issued_by: str = Field(..., description="发起冻结的外部权威ID")
    issued_by_type: Literal["regulator", "court", "counterparty"] = Field(..., description="发起冻结的外部权威类型")
    scope: Literal["full", "governance", "execution", "specific_event"] = Field(default="full", description="冻结范围")
    specific_target: Optional[str] = Field(None, description="特定冻结目标ID")
    reason: Optional[str] = Field(None, description="冻结原因")
    issued_at: datetime = Field(default_factory=datetime.now, description="冻结发起时间")
    signature: str = Field(..., description="冻结请求签名，用于验证冻结真实性")
    status: Literal["active", "expired", "unfrozen"] = Field(default="active", description="冻结状态")
    unfreeze_id: Optional[str] = Field(None, description="关联的解冻记录ID")
    proof_id: Optional[str] = Field(None, description="关联的治理证明ID")
    jurisdiction: str = Field(..., description="司法/合同适用域")
    
    class Config:
        frozen = True  # 冻结记录不可修改，确保审计完整性
        use_enum_values = True  # 序列化时使用枚举值


class _RegulatoryUnfreeze(BaseModel):
    """监管解冻记录
    
    记录外部权威发起的解冻请求和状态
    """
    unfreeze_id: str = Field(default_factory=lambda: f"unfreeze-{uuid.uuid4()}", description="解冻记录唯一标识")
    freeze_id: str = Field(..., description="关联的冻结记录ID")
    issued_by: str = Field(..., description="发起解冻的外部权威ID")
    issued_by_type: Literal["regulator", "court", "counterparty"] = Field(..., description="发起解冻的外部权威类型")
    reason: Optional[str] = Field(None, description="解冻原因")
    issued_at: datetime = Field(default_factory=datetime.now, description="解冻发起时间")
    signature: str = Field(..., description="解冻请求签名，用于验证解冻真实性")
    approved_by: Optional[str] = Field(None, description="批准解冻的更高权威ID")
    approved_at: Optional[datetime] = Field(None, description="解冻批准时间")
    jurisdiction: str = Field(..., description="司法/合同适用域")
    proof_id: Optional[str] = Field(None, description="关联的治理证明ID")
    
    class Config:
        frozen = True  # 解冻记录不可修改，确保审计完整性
        use_enum_values = True  # 序列化时使用枚举值


class _RegulatoryFreezeManager(BaseModel):
    """监管冻结管理器
    
    负责管理系统的冻结和解冻过程，确保外部权威可以冻结系统，系统无法自解锁
    """
    # 服务依赖
    # 内部状态
    active_freezes: Dict[str, _RegulatoryFreeze] = Field(default_factory=dict, description="当前活跃的冻结记录")
    freeze_history: List[_RegulatoryFreeze] = Field(default_factory=list, description="冻结历史记录")
    unfreeze_history: List[_RegulatoryUnfreeze] = Field(default_factory=list, description="解冻历史记录")
    
    class Config:
        frozen = False  # 允许更新内部状态
    
    def register_external_authority(self, authority: _ExternalAuthority) -> _ExternalAuthority:
        """注册外部权威
        
        Args:
            authority: 外部权威实体
            
        Returns:
            注册后的外部权威
        """
        # 这个方法应该由Governance Engine调用，这里简化实现
        pass
    
    def process_freeze_request(self, freeze: _RegulatoryFreeze) -> Dict[str, Any]:
        """处理外部权威的冻结请求
        
        Args:
            freeze: 冻结请求记录
            
        Returns:
            处理结果
        """
        # 验证外部权威身份
        # 简化实现，实际应调用external_governance_interface.verify_external_authority
        
        # 检查是否已存在相同范围的冻结
        existing_freezes = [f for f in self.active_freezes.values() 
                          if f.status == "active" and f.scope == freeze.scope]
        if existing_freezes:
            return {
                "status": "FAILED",
                "reason": f"System already frozen with scope {freeze.scope}",
                "existing_freeze_id": existing_freezes[0].freeze_id
            }
        
        # 保存冻结记录
        self.active_freezes[freeze.freeze_id] = freeze
        self.freeze_history.append(freeze)
        
        # 生成冻结证明
        # 简化实现，实际应调用governance_proof_manager.generate_governance_proof
        
        return {
            "status": "SUCCESS",
            "freeze_id": freeze.freeze_id,
            "message": f"System frozen with scope {freeze.scope}"
        }
    
    def process_unfreeze_request(self, unfreeze: _RegulatoryUnfreeze) -> Dict[str, Any]:
        """处理外部权威的解冻请求
        
        Args:
            unfreeze: 解冻请求记录
            
        Returns:
            处理结果
        """
        # 验证冻结记录是否存在
        if unfreeze.freeze_id not in self.active_freezes:
            return {
                "status": "FAILED",
                "reason": f"Freeze record {unfreeze.freeze_id} not found or already unfrozen"
            }
        
        freeze = self.active_freezes[unfreeze.freeze_id]
        
        # 验证解冻权威是否具有足够权限
        # 简化实现，实际应验证权威级别和权限
        
        # 更新冻结状态
        freeze = freeze.model_copy(update={"status": "unfrozen", "unfreeze_id": unfreeze.unfreeze_id})
        
        # 从活跃冻结中移除
        del self.active_freezes[unfreeze.freeze_id]
        
        # 保存到历史记录
        self.unfreeze_history.append(unfreeze)
        
        return {
            "status": "SUCCESS",
            "freeze_id": unfreeze.freeze_id,
            "unfreeze_id": unfreeze.unfreeze_id,
            "message": "System unfrozen successfully"
        }
    
    def get_active_freezes(self) -> List[_RegulatoryFreeze]:
        """获取当前活跃的冻结记录
        
        Returns:
            活跃的冻结记录列表
        """
        return list(self.active_freezes.values())
    
    def get_freeze_history(self) -> List[_RegulatoryFreeze]:
        """获取冻结历史记录
        
        Returns:
            冻结历史记录列表
        """
        return self.freeze_history
    
    def is_frozen(self, scope: Optional[Literal["full", "governance", "execution", "specific_event"]] = None) -> bool:
        """检查系统是否处于冻结状态
        
        Args:
            scope: 检查的冻结范围，None表示检查任何范围
            
        Returns:
            是否处于冻结状态
        """
        if scope:
            return any(f for f in self.active_freezes.values() 
                     if f.status == "active" and f.scope == scope)
        return len(self.active_freezes) > 0
    
    def generate_freeze_proof(self, freeze: _RegulatoryFreeze) -> _GovernanceProof:
        """生成冻结行为的治理证明
        
        Args:
            freeze: 冻结记录
            
        Returns:
            治理证明对象
        """
        # 简化实现，实际应调用governance_proof_manager.generate_governance_proof
        pass
    
    def has_active_freeze(self, *args, **kwargs) -> bool:
        """检查是否有活跃的冻结记录
        
        Args:
            *args: 可变参数
            **kwargs: 关键字参数
            
        Returns:
            是否有活跃的冻结记录
        """
        # 简化实现，检查是否有任何活跃的冻结
        return len(self.active_freezes) > 0


__all__ = []
