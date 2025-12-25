"""
Jurisdiction Models - Implement jurisdiction and contract domain binding

This module implements the jurisdiction and contract domain binding ensuring that governance facts
are bound to specific legal/contract jurisdictions, and jurisdiction inconsistencies generate violations.

Governance Rules:
- Each Proof Bundle must be bound to a Jurisdiction
- Replay with inconsistent Jurisdiction → violation proof
- Jurisdiction must be specified at proof generation time
- Jurisdiction changes must be explicitly recorded
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class _JurisdictionContext(BaseModel):
    """司法管辖上下文
    
    定义司法/合同适用域，包括法律体系、适用法律、争议解决机制和升级路径
    """
    jurisdiction_id: str = Field(default_factory=lambda: f"jurisdiction-{uuid.uuid4()}", description="司法管辖上下文唯一标识")
    legal_system: Literal["common_law", "civil_law", "religious_law", "hybrid"] = Field(..., description="法律体系类型")
    governing_law: str = Field(..., description="适用法律")
    dispute_resolution: Literal["court", "arbitration", "mediation", "negotiation"] = Field(default="court", description="争议解决机制")
    arbitration_institution: Optional[str] = Field(None, description="仲裁机构")
    escalation_path: List[str] = Field(default_factory=lambda: ["negotiation", "mediation", "arbitration", "court"], description="争议升级路径")
    effective_from: datetime = Field(default_factory=datetime.now, description="生效时间")
    effective_until: Optional[datetime] = Field(None, description="失效时间")
    applicable_scopes: List[Literal["governance", "execution", "audit", "all"]] = Field(default_factory=lambda: ["all"], description="适用范围")
    version: str = Field(default_factory=lambda: f"v1-{uuid.uuid4()}", description="版本号")
    
    class Config:
        frozen = True  # 司法管辖上下文不可修改，确保审计完整性
        use_enum_values = True  # 序列化时使用枚举值


class _JurisdictionBinding(BaseModel):
    """司法管辖绑定记录
    
    记录治理证明与司法管辖上下文的绑定关系
    """
    binding_id: str = Field(default_factory=lambda: f"binding-{uuid.uuid4()}", description="绑定记录唯一标识")
    proof_id: str = Field(..., description="关联的治理证明ID")
    jurisdiction_id: str = Field(..., description="关联的司法管辖上下文ID")
    jurisdiction_context: Dict[str, Any] = Field(..., description="司法管辖上下文内容")
    bound_at: datetime = Field(default_factory=datetime.now, description="绑定时间")
    signature: str = Field(..., description="绑定签名，用于验证绑定真实性")
    
    class Config:
        frozen = True  # 绑定记录不可修改，确保审计完整性


class _JurisdictionInconsistency(BaseModel):
    """司法管辖不一致记录
    
    记录司法管辖上下文不一致的情况
    """
    inconsistency_id: str = Field(default_factory=lambda: f"inconsistency-{uuid.uuid4()}", description="不一致记录唯一标识")
    event_id: str = Field(..., description="关联事件ID")
    expected_jurisdiction: str = Field(..., description="预期的司法管辖ID")
    actual_jurisdiction: str = Field(..., description="实际的司法管辖ID")
    expected_context: Dict[str, Any] = Field(..., description="预期的司法管辖上下文")
    actual_context: Dict[str, Any] = Field(..., description="实际的司法管辖上下文")
    detected_at: datetime = Field(default_factory=datetime.now, description="检测时间")
    detected_by: str = Field(..., description="检测者ID")
    violation_proof_id: Optional[str] = Field(None, description="关联的违规证明ID")
    
    class Config:
        frozen = True  # 不一致记录不可修改，确保审计完整性


class _JurisdictionManager(BaseModel):
    """司法管辖管理器
    
    负责管理司法管辖上下文，处理司法管辖绑定和解绑，检测司法管辖不一致
    """
    # 内部状态
    jurisdictions: Dict[str, _JurisdictionContext] = Field(default_factory=dict, description="已注册的司法管辖上下文字典")
    jurisdiction_bindings: Dict[str, _JurisdictionBinding] = Field(default_factory=dict, description="司法管辖绑定记录字典")
    jurisdiction_inconsistencies: List[_JurisdictionInconsistency] = Field(default_factory=list, description="司法管辖不一致记录列表")
    default_jurisdiction_id: Optional[str] = Field(None, description="默认司法管辖ID")
    
    class Config:
        frozen = False  # 允许更新内部状态
    
    def register_jurisdiction(self, jurisdiction: _JurisdictionContext) -> _JurisdictionContext:
        """注册司法管辖上下文
        
        Args:
            jurisdiction: 司法管辖上下文
            
        Returns:
            注册后的司法管辖上下文
        """
        # 验证司法管辖唯一性
        if jurisdiction.jurisdiction_id in self.jurisdictions:
            raise ValueError(f"Jurisdiction {jurisdiction.jurisdiction_id} already registered")
        
        # 注册司法管辖
        self.jurisdictions[jurisdiction.jurisdiction_id] = jurisdiction
        
        # 如果是第一个司法管辖，设置为默认
        if not self.default_jurisdiction_id:
            self.default_jurisdiction_id = jurisdiction.jurisdiction_id
        
        return jurisdiction
    
    def set_default_jurisdiction(self, jurisdiction_id: str) -> bool:
        """设置默认司法管辖
        
        Args:
            jurisdiction_id: 司法管辖ID
            
        Returns:
            是否设置成功
        """
        if jurisdiction_id not in self.jurisdictions:
            return False
        
        self.default_jurisdiction_id = jurisdiction_id
        return True
    
    def get_jurisdiction(self, jurisdiction_id: Optional[str] = None) -> Optional[_JurisdictionContext]:
        """获取司法管辖上下文
        
        Args:
            jurisdiction_id: 司法管辖ID，None表示获取默认司法管辖
            
        Returns:
            司法管辖上下文，若不存在则返回None
        """
        if not jurisdiction_id:
            jurisdiction_id = self.default_jurisdiction_id
            if not jurisdiction_id:
                return None
        
        return self.jurisdictions.get(jurisdiction_id)
    
    def bind_proof_to_jurisdiction(self, proof_id: str, jurisdiction_id: str, signature: str) -> _JurisdictionBinding:
        """将治理证明绑定到司法管辖上下文
        
        Args:
            proof_id: 治理证明ID
            jurisdiction_id: 司法管辖ID
            signature: 绑定签名，用于验证绑定真实性
            
        Returns:
            创建的绑定记录
        """
        # 验证司法管辖存在
        if jurisdiction_id not in self.jurisdictions:
            raise ValueError(f"Jurisdiction {jurisdiction_id} not registered")
        
        jurisdiction = self.jurisdictions[jurisdiction_id]
        
        # 创建绑定记录
        binding = _JurisdictionBinding(
            proof_id=proof_id,
            jurisdiction_id=jurisdiction_id,
            jurisdiction_context=jurisdiction.model_dump(),
            signature=signature
        )
        
        # 保存绑定记录
        self.jurisdiction_bindings[binding.binding_id] = binding
        
        return binding
    
    def get_proof_jurisdiction(self, proof_id: str) -> Optional[_JurisdictionContext]:
        """获取治理证明绑定的司法管辖上下文
        
        Args:
            proof_id: 治理证明ID
            
        Returns:
            绑定的司法管辖上下文，若不存在则返回None
        """
        # 查找绑定记录
        bindings = [b for b in self.jurisdiction_bindings.values() if b.proof_id == proof_id]
        if not bindings:
            return None
        
        # 返回最新的绑定
        latest_binding = max(bindings, key=lambda b: b.bound_at)
        return self.jurisdictions.get(latest_binding.jurisdiction_id)
    
    def detect_jurisdiction_inconsistency(
        self, 
        event_id: str, 
        expected_jurisdiction: str, 
        actual_jurisdiction: str, 
        detected_by: str
    ) -> Optional[_JurisdictionInconsistency]:
        """检测司法管辖不一致
        
        Args:
            event_id: 关联事件ID
            expected_jurisdiction: 预期的司法管辖ID
            actual_jurisdiction: 实际的司法管辖ID
            detected_by: 检测者ID
            
        Returns:
            不一致记录，若一致则返回None
        """
        # 检查是否一致
        if expected_jurisdiction == actual_jurisdiction:
            return None
        
        # 获取司法管辖上下文
        expected_context = self.jurisdictions.get(expected_jurisdiction)
        actual_context = self.jurisdictions.get(actual_jurisdiction)
        
        # 创建不一致记录
        inconsistency = _JurisdictionInconsistency(
            event_id=event_id,
            expected_jurisdiction=expected_jurisdiction,
            actual_jurisdiction=actual_jurisdiction,
            expected_context=expected_context.model_dump() if expected_context else {},
            actual_context=actual_context.model_dump() if actual_context else {},
            detected_by=detected_by
        )
        
        # 保存不一致记录
        self.jurisdiction_inconsistencies.append(inconsistency)
        
        return inconsistency
    
    def get_jurisdictions(self) -> List[_JurisdictionContext]:
        """获取所有已注册的司法管辖上下文
        
        Returns:
            司法管辖上下文列表
        """
        return list(self.jurisdictions.values())
    
    def get_jurisdictions_by_legal_system(self, legal_system: str) -> List[_JurisdictionContext]:
        """根据法律体系获取司法管辖上下文
        
        Args:
            legal_system: 法律体系类型
            
        Returns:
            司法管辖上下文列表
        """
        return [j for j in self.jurisdictions.values() if j.legal_system == legal_system]
    
    def get_jurisdiction_bindings_by_proof(self, proof_id: str) -> List[_JurisdictionBinding]:
        """根据治理证明ID获取绑定记录
        
        Args:
            proof_id: 治理证明ID
            
        Returns:
            绑定记录列表
        """
        return [b for b in self.jurisdiction_bindings.values() if b.proof_id == proof_id]


__all__ = []
