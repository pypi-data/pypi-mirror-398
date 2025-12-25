"""
External Authority Models - Define external governance authority entities

This module implements the external authority models ensuring that external entities
can interact with the system's governance layer in a secure and controlled manner.

Governance Rules:
- ExternalAuthority is never a Sovereign
- ExternalAuthority only has freeze/verify/adjudicate powers
- ExternalAuthority interactions must be auditable and non-repudiable
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
import uuid


class _ExternalAuthority(BaseModel):
    """外部权威实体
    
    定义外部权威实体，包括监管机构、仲裁机构和法律/SLA 对手方
    外部权威仅拥有冻结/验证/裁定权，永远不是主权主体
    """
    authority_id: str = Field(default_factory=lambda: f"authority-{uuid.uuid4()}", description="外部权威唯一标识")
    authority_type: Literal["regulator", "court", "counterparty"] = Field(..., description="外部权威类型")
    jurisdiction: str = Field(..., description="司法/合同适用域")
    public_key: str = Field(..., description="外部权威公钥，用于身份验证和签名验证")
    freeze_power: bool = Field(default=True, description="是否拥有冻结系统权限")
    verification_scope: List[str] = Field(default_factory=lambda: ["proof", "attestation", "audit"], description="可验证的治理内容范围")
    registered_at: datetime = Field(default_factory=datetime.now, description="注册时间")
    last_active: Optional[datetime] = Field(None, description="最后活跃时间")
    is_active: bool = Field(default=True, description="是否活跃")
    description: Optional[str] = Field(None, description="外部权威描述")
    contact_info: Optional[str] = Field(None, description="联系信息")
    
    class Config:
        frozen = True  # 外部权威信息不可修改，确保审计完整性
        use_enum_values = True  # 序列化时使用枚举值


class _ExternalAuthorityRegistry(BaseModel):
    """外部权威注册表
    
    管理所有已注册的外部权威实体
    确保外部权威注册表是append-only的，任何变更都会创建新的版本
    """
    registry_id: str = Field(default_factory=lambda: f"registry-{uuid.uuid4()}", description="注册表ID")
    authorities: List[_ExternalAuthority] = Field(default_factory=list, description="已注册的外部权威列表")
    version: str = Field(default_factory=lambda: f"v1-{uuid.uuid4()}", description="注册表版本")
    created_at: datetime = Field(default_factory=datetime.now, description="注册表创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="注册表更新时间")
    
    class Config:
        frozen = True  # 注册表不可修改，确保审计完整性


class _ExternalAuthorityVerificationResult(BaseModel):
    """外部权威验证结果
    
    记录外部权威身份验证结果
    """
    verified: bool = Field(..., description="验证是否通过")
    authority_id: Optional[str] = Field(None, description="验证的外部权威ID")
    reason: Optional[str] = Field(None, description="验证结果原因")
    verified_by: str = Field(..., description="验证执行者")
    verified_at: datetime = Field(default_factory=datetime.now, description="验证时间")
    
    class Config:
        frozen = True  # 验证结果不可修改，确保审计完整性


class _ExternalAuthorityAction(BaseModel):
    """外部权威动作
    
    记录外部权威执行的动作
    """
    action_id: str = Field(default_factory=lambda: f"action-{uuid.uuid4()}", description="动作ID")
    authority_id: str = Field(..., description="执行动作的外部权威ID")
    action_type: Literal["freeze", "unfreeze", "verify", "adjudicate"] = Field(..., description="动作类型")
    target_id: Optional[str] = Field(None, description="动作目标ID")
    target_type: Optional[str] = Field(None, description="动作目标类型")
    parameters: Optional[dict] = Field(default_factory=dict, description="动作参数")
    signature: str = Field(..., description="动作签名，用于验证动作真实性")
    timestamp: datetime = Field(default_factory=datetime.now, description="动作执行时间")
    
    class Config:
        frozen = True  # 外部权威动作不可修改，确保审计完整性


__all__ = []
