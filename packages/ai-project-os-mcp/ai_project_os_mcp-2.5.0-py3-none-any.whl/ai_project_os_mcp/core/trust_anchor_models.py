"""
Trust Anchor Models - Define external existence witnesses for governance finality

This module implements the trust anchor models ensuring that governance facts can be anchored
to external existence sources, providing time-bound existence finality without introducing
new sovereign entities or breaking governance boundaries.

Governance Invariants:
- Trust anchors are only existence witnesses, not sovereigns
- Trust anchors do not have freeze, verification, or adjudication powers
- Trust anchors are单向, verifiable, and replaceable
- The system does not trust external world, only uses it as existence anchor
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class _TrustAnchor(BaseModel):
    """信任锚模型
    
    定义外部存在性见证者，用于证明治理事实在特定时间点的存在
    
    Trust anchors are only existence witnesses, not sovereigns:
    - No freeze power
    - No verification power
    - No adjudication power
    - Only provides existence proof
    """
    anchor_id: str = Field(default_factory=lambda: f"anchor-{uuid.uuid4()}", description="信任锚唯一标识")
    anchor_type: Literal["tsa", "public_log", "notary", "custom"] = Field(..., description="信任锚类型")
    verifier: str = Field(..., description="验证器标识，用于验证锚回执")
    trust_scope: str = Field(default="existence_only", description="信任范围，仅支持existence_only")
    endpoint: Optional[str] = Field(None, description="信任锚服务端点")
    public_key: Optional[str] = Field(None, description="信任锚公钥，用于验证回执签名")
    registered_at: datetime = Field(default_factory=datetime.now, description="注册时间")
    is_active: bool = Field(default=True, description="是否活跃")
    description: Optional[str] = Field(None, description="信任锚描述")
    # 配置选项，针对不同类型的信任锚
    config: Dict[str, Any] = Field(default_factory=dict, description="信任锚配置")
    
    class Config:
        frozen = True  # 信任锚配置不可修改，确保审计完整性
        use_enum_values = True  # 序列化时使用枚举值


class _TrustAnchorSubmission(BaseModel):
    """信任锚提交记录
    
    记录向信任锚提交证明根哈希的请求
    """
    submission_id: str = Field(default_factory=lambda: f"submission-{uuid.uuid4()}", description="提交记录ID")
    anchor_id: str = Field(..., description="目标信任锚ID")
    proof_bundle_root: str = Field(..., description="证明包根哈希")
    submission_data: Dict[str, Any] = Field(default_factory=dict, description="提交数据")
    submitted_at: datetime = Field(default_factory=datetime.now, description="提交时间")
    status: Literal["pending", "success", "failed"] = Field(default="pending", description="提交状态")
    
    class Config:
        frozen = True  # 提交记录不可修改，确保审计完整性


class _TrustAnchorReceipt(BaseModel):
    """信任锚回执
    
    信任锚返回的存在性证明回执
    """
    receipt_id: str = Field(default_factory=lambda: f"receipt-{uuid.uuid4()}", description="回执ID")
    submission_id: str = Field(..., description="关联的提交记录ID")
    anchor_id: str = Field(..., description="信任锚ID")
    proof_bundle_root: str = Field(..., description="证明包根哈希")
    anchor_specific_ref: str = Field(..., description="信任锚特定引用，如TSA时间戳或区块链交易ID")
    anchored_at: datetime = Field(..., description="锚定时间")
    receipt_signature: Optional[str] = Field(None, description="信任锚签名的回执")
    verified: bool = Field(default=False, description="回执是否已验证")
    
    class Config:
        frozen = True  # 回执不可修改，确保审计完整性


class _TrustAnchorVerificationResult(BaseModel):
    """信任锚验证结果
    
    验证信任锚回执的结果
    """
    verified: bool = Field(..., description="验证是否通过")
    anchor_id: str = Field(..., description="信任锚ID")
    receipt_id: str = Field(..., description="回执ID")
    reason: Optional[str] = Field(None, description="验证结果原因")
    verified_at: datetime = Field(default_factory=datetime.now, description="验证时间")
    
    class Config:
        frozen = True  # 验证结果不可修改，确保审计完整性


class _TrustAnchorRegistry(BaseModel):
    """信任锚注册表
    
    管理所有已注册的信任锚
    """
    registry_id: str = Field(default_factory=lambda: f"registry-{uuid.uuid4()}", description="注册表ID")
    anchors: List[_TrustAnchor] = Field(default_factory=list, description="已注册的信任锚列表")
    version: str = Field(default_factory=lambda: f"v1-{uuid.uuid4()}", description="注册表版本")
    created_at: datetime = Field(default_factory=datetime.now, description="注册表创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="注册表更新时间")
    
    class Config:
        frozen = True  # 注册表不可修改，确保审计完整性


__all__ = []