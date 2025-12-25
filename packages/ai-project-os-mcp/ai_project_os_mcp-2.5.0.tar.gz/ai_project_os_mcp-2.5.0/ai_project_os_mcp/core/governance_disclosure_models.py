"""
Governance Disclosure Models - Define governance disclosure and proof export models

This module implements the governance disclosure models ensuring that governance facts
can be disclosed to external entities in a secure, verifiable, and non-repudiable manner.

Principles:
- Disclosure is one-way and irreversible
- Disclosure itself must generate a governance proof
- Disclosure must be auditable and tamper-proof
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
import uuid


class _GovernanceDisclosure(BaseModel):
    """治理披露记录
    
    记录治理事实向外部实体的披露过程
    披露是单向不可撤销的，披露行为本身生成治理证明
    """
    disclosure_id: str = Field(default_factory=lambda: f"disclosure-{uuid.uuid4()}", description="披露记录唯一标识")
    proof_bundle_root: str = Field(..., description="披露的证明包根哈希")
    disclosed_to: str = Field(..., description="披露对象（外部权威ID）")
    disclosed_to_type: Literal["regulator", "court", "counterparty"] = Field(..., description="披露对象类型")
    disclosure_scope: List[str] = Field(default_factory=lambda: ["proof", "attestation", "audit"], description="披露范围")
    jurisdiction: str = Field(..., description="司法/合同适用域")
    timestamp: datetime = Field(default_factory=datetime.now, description="披露时间")
    reason: Optional[str] = Field(None, description="披露原因")
    signature: str = Field(..., description="披露签名，用于验证披露真实性")
    proof_id: Optional[str] = Field(None, description="关联的治理证明ID")
    
    class Config:
        frozen = True  # 披露记录不可修改，确保审计完整性
        use_enum_values = True  # 序列化时使用枚举值


class _DisclosureReceipt(BaseModel):
    """披露收据
    
    记录外部实体接收治理披露的确认
    """
    receipt_id: str = Field(default_factory=lambda: f"receipt-{uuid.uuid4()}", description="收据唯一标识")
    disclosure_id: str = Field(..., description="关联的披露记录ID")
    receiver_id: str = Field(..., description="接收者ID")
    receiver_signature: str = Field(..., description="接收者签名，用于确认接收")
    received_at: datetime = Field(default_factory=datetime.now, description="接收时间")
    jurisdiction: str = Field(..., description="司法/合同适用域")
    comment: Optional[str] = Field(None, description="接收者注释")
    
    class Config:
        frozen = True  # 披露收据不可修改，确保审计完整性


class _ProofExport(BaseModel):
    """证明导出记录
    
    记录治理证明的导出过程
    """
    export_id: str = Field(default_factory=lambda: f"export-{uuid.uuid4()}", description="导出记录唯一标识")
    proof_bundle_id: str = Field(..., description="关联的证明包ID")
    proof_bundle_root: str = Field(..., description="证明包根哈希")
    export_format: Literal["json", "binary"] = Field(default="json", description="导出格式")
    export_scope: List[str] = Field(default_factory=lambda: ["proof", "attestation", "audit"], description="导出范围")
    exported_by: str = Field(..., description="导出执行者ID")
    exported_at: datetime = Field(default_factory=datetime.now, description="导出时间")
    jurisdiction: str = Field(..., description="司法/合同适用域")
    signature: str = Field(..., description="导出签名，用于验证导出真实性")
    
    class Config:
        frozen = True  # 证明导出记录不可修改，确保审计完整性


class _ProofBundleExport(BaseModel):
    """证明包导出
    
    实际导出的证明包内容
    """
    bundle_id: str = Field(..., description="证明包ID")
    root_hash: str = Field(..., description="证明包根哈希")
    proof_count: int = Field(..., description="证明包中包含的证明数量")
    attestation_count: int = Field(..., description="证明包中包含的行为见证数量")
    timestamp: datetime = Field(default_factory=datetime.now, description="导出时间")
    export_id: str = Field(..., description="关联的导出记录ID")
    jurisdiction: str = Field(..., description="司法/合同适用域")
    governance_version: str = Field(..., description="治理引擎版本")
    content: dict = Field(..., description="证明包内容")
    signature: str = Field(..., description="证明包签名，用于验证证明包完整性")
    
    class Config:
        frozen = True  # 证明包导出不可修改，确保审计完整性


class _DisclosureStatus(str, Enum):
    """披露状态枚举
    
    定义治理披露的不同状态
    """
    PENDING = "pending"  # 披露待处理
    COMPLETED = "completed"  # 披露完成
    REJECTED = "rejected"  # 披露被拒绝
    EXPIRED = "expired"  # 披露过期


class _DisclosureLog(BaseModel):
    """披露日志
    
    记录治理披露的完整生命周期
    """
    log_id: str = Field(default_factory=lambda: f"log-{uuid.uuid4()}", description="日志唯一标识")
    disclosure_id: str = Field(..., description="关联的披露记录ID")
    status: _DisclosureStatus = Field(..., description="当前状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="日志时间")
    actor_id: str = Field(..., description="执行动作的参与者ID")
    actor_type: Literal["system", "human", "external"] = Field(..., description="参与者类型")
    action: str = Field(..., description="执行的动作")
    details: dict = Field(default_factory=dict, description="动作详细信息")
    
    class Config:
        frozen = True  # 披露日志不可修改，确保审计完整性


__all__ = []
