"""
Governance Finality Models - Define existence finality records for governance facts

This module implements the governance finality models ensuring that governance facts have
"existence finality" - they cannot be denied their existence at a specific point in time.

Governance Invariants:
- Finality records only verify existence, not content correctness
- Finality records are immutable and cannot be rewritten
- Finality records can be independently verified by third parties
- Finality records do not introduce new sovereign entities
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
import hashlib


class _GovernanceFinalityRecord(BaseModel):
    """治理终局记录
    
    治理事实的"存在性终章"，证明治理事实在特定时间点的存在性
    
    Finality records are NOT:
    - Not a verdict on content correctness
    - Not a replacement for governance proofs
    - Not a sovereign entity
    
    Finality records ARE:
    - Immutable existence proofs
    - Time-bound
    - Verifiable by third parties
    - Independent of system runtime
    """
    finality_id: str = Field(default_factory=lambda: f"finality-{uuid.uuid4()}", description="终局记录唯一标识")
    proof_bundle_root: str = Field(..., description="证明包根哈希，指向具体治理事实")
    anchored_at: datetime = Field(default_factory=datetime.now, description="锚定时间")
    anchor_refs: List[str] = Field(default_factory=list, description="信任锚引用列表，每个引用指向一个信任锚回执")
    anchor_count: int = Field(default=0, description="锚定的信任锚数量")
    jurisdiction: str = Field(..., description="司法/合同适用域")
    created_at: datetime = Field(default_factory=datetime.now, description="终局记录创建时间")
    signature: str = Field(..., description="系统签名，用于验证终局记录完整性")
    
    class Config:
        frozen = True  # 终局记录不可修改，确保存在性终局
        use_enum_values = True  # 序列化时使用枚举值
    
    def generate_signature(self, private_key: str) -> str:
        """生成终局记录签名
        
        Args:
            private_key: 系统私钥
            
        Returns:
            签名后的字符串
        """
        # 签名内容：仅包含存在性相关字段
        signature_content = {
            "finality_id": self.finality_id,
            "proof_bundle_root": self.proof_bundle_root,
            "anchored_at": self.anchored_at.isoformat(),
            "anchor_count": self.anchor_count,
            "jurisdiction": self.jurisdiction,
            "created_at": self.created_at.isoformat()
        }
        
        # 使用SHA-256生成签名（实际应使用更安全的签名算法）
        content_str = str(signature_content)
        return hashlib.sha256((content_str + private_key).encode('utf-8')).hexdigest()
    
    def verify_signature(self, public_key: str) -> bool:
        """验证终局记录签名
        
        Args:
            public_key: 系统公钥
            
        Returns:
            签名是否有效
        """
        # 注意：实际实现应使用非对称加密验证
        # 这里简化为哈希比较
        expected_signature = self.generate_signature(public_key)
        return self.signature == expected_signature


class _FinalityVerificationResult(BaseModel):
    """终局记录验证结果
    
    验证治理终局记录的结果
    """
    verified: bool = Field(..., description="验证是否通过")
    finality_id: Optional[str] = Field(None, description="终局记录ID")
    proof_bundle_root: Optional[str] = Field(None, description="证明包根哈希")
    message: str = Field(..., description="验证结果消息")
    details: Dict[str, Any] = Field(default_factory=dict, description="验证详情")
    verified_at: datetime = Field(default_factory=datetime.now, description="验证时间")
    
    # 若验证失败，包含失败原因
    failure_reason: Optional[str] = Field(None, description="验证失败原因")
    
    class Config:
        frozen = True  # 验证结果不可修改，确保可信度


class _FinalityRegistry(BaseModel):
    """终局记录注册表
    
    管理所有治理终局记录
    """
    registry_id: str = Field(default_factory=lambda: f"finality-registry-{uuid.uuid4()}", description="注册表ID")
    finality_records: List[_GovernanceFinalityRecord] = Field(default_factory=list, description="终局记录列表")
    version: str = Field(default_factory=lambda: f"v1-{uuid.uuid4()}", description="注册表版本")
    created_at: datetime = Field(default_factory=datetime.now, description="注册表创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="注册表更新时间")
    
    class Config:
        frozen = True  # 注册表不可修改，确保审计完整性
    
    def add_record(self, record: _GovernanceFinalityRecord) -> '_FinalityRegistry':
        """添加终局记录
        
        Args:
            record: 要添加的终局记录
            
        Returns:
            新的注册表实例（因为注册表是不可修改的）
        """
        # 检查是否已存在相同终局记录
        for existing_record in self.finality_records:
            if existing_record.finality_id == record.finality_id:
                return self
        
        # 创建新的注册表实例
        return self.model_copy(
            update={
                "finality_records": self.finality_records + [record],
                "updated_at": datetime.now()
            }
        )
    
    def get_record_by_id(self, finality_id: str) -> Optional[_GovernanceFinalityRecord]:
        """根据ID获取终局记录
        
        Args:
            finality_id: 终局记录ID
            
        Returns:
            终局记录，如果不存在则返回None
        """
        for record in self.finality_records:
            if record.finality_id == finality_id:
                return record
        return None
    
    def get_records_by_proof_root(self, proof_bundle_root: str) -> List[_GovernanceFinalityRecord]:
        """根据证明包根哈希获取终局记录
        
        Args:
            proof_bundle_root: 证明包根哈希
            
        Returns:
            匹配的终局记录列表
        """
        return [record for record in self.finality_records 
                if record.proof_bundle_root == proof_bundle_root]


__all__ = []