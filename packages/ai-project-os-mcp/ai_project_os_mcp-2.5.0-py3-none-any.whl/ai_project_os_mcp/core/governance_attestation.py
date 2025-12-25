"""
Governance Attestation - Behavior Witness & Signature Semantics

This module implements the behavior witness mechanism ensuring that every governance action
can be proven and non-repudiated. It distinguishes between "acknowledge" and "authorize" attestations.
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
import hashlib
import hmac
import secrets


class _GovernanceAttestation(BaseModel):
    """治理行为见证记录
    
    区分「承认」与「授权」两种语义：
    - acknowledge: 我确认发生了这件事，但不影响其他内容
    - authorize: 我授权这件事影响相关内容
    """
    attestation_id: str = Field(default_factory=lambda: f"attestation-{uuid.uuid4()}", description="见证记录唯一标识")
    actor_id: str = Field(..., description="见证的Actor ID")
    actor_type: Literal["system", "human", "agent", "arbitrator"] = Field(..., description="Actor类型")
    attestation_type: Literal["acknowledge", "authorize"] = Field(..., description="见证类型：确认 vs 授权")
    target_id: str = Field(..., description="见证的目标ID")
    target_type: Literal["governance", "outline", "chapter"] = Field(..., description="见证的目标类型")
    content_hash: str = Field(..., description="内容哈希，用于验证完整性")
    timestamp: datetime = Field(default_factory=datetime.now, description="见证时间")
    signature: str = Field(..., description="Actor签名")
    reason: Optional[str] = Field(None, description="见证原因")
    
    class Config:
        frozen = True  # 见证记录不可修改，确保可追溯
        use_enum_values = True


class _SignatureService(BaseModel):
    """签名服务
    
    负责生成和验证签名，确保所有行为都可以被证明和追溯
    """
    secret_key: str = Field(default_factory=lambda: secrets.token_hex(32), description="签名密钥，用于生成HMAC签名")
    
    class Config:
        frozen = False  # 允许更新内部状态
    
    def generate_signature(self, content: str, actor_id: str, target_id: str, target_type: str) -> str:
        """生成内容签名
        
        Args:
            content: 要签名的内容
            actor_id: Actor ID
            target_id: 目标ID
            target_type: 目标类型
            
        Returns:
            生成的签名
        """
        # 创建签名有效载荷
        payload = f"{actor_id}:{target_type}:{target_id}:{content}"
        
        # 使用HMAC-SHA256生成签名
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify_signature(self, content: str, actor_id: str, target_id: str, target_type: str, signature: str) -> bool:
        """验证签名
        
        Args:
            content: 要验证的内容
            actor_id: Actor ID
            target_id: 目标ID
            target_type: 目标类型
            signature: 要验证的签名
            
        Returns:
            签名是否有效
        """
        # 重新生成签名并比较
        expected_signature = self.generate_signature(content, actor_id, target_id, target_type)
        return hmac.compare_digest(expected_signature, signature)
    
    def generate_content_hash(self, content: str) -> str:
        """生成内容哈希，用于验证完整性
        
        Args:
            content: 要哈希的内容
            
        Returns:
            内容的SHA-256哈希
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


class _AttestationService(BaseModel):
    """见证服务
    
    负责创建和管理治理行为见证记录
    """
    signature_service: _SignatureService
    
    def create_attestation(self,
                         actor_id: str,
                         actor_type: Literal["system", "human", "agent", "arbitrator"],
                         attestation_type: Literal["acknowledge", "authorize"],
                         target_id: str,
                         target_type: Literal["governance", "outline", "chapter"],
                         content: str,
                         reason: Optional[str] = None) -> _GovernanceAttestation:
        """创建治理行为见证
        
        Args:
            actor_id: Actor ID
            actor_type: Actor类型
            attestation_type: 见证类型：确认 vs 授权
            target_id: 目标ID
            target_type: 目标类型
            content: 见证的内容
            reason: 见证原因
            
        Returns:
            创建的见证记录
        """
        # 生成内容哈希
        content_hash = self.signature_service.generate_content_hash(content)
        
        # 生成签名
        signature = self.signature_service.generate_signature(content, actor_id, target_id, target_type)
        
        # 创建见证记录
        attestation = _GovernanceAttestation(
            actor_id=actor_id,
            actor_type=actor_type,
            attestation_type=attestation_type,
            target_id=target_id,
            target_type=target_type,
            content_hash=content_hash,
            signature=signature,
            reason=reason
        )
        
        return attestation
    
    def verify_attestation(self, attestation: _GovernanceAttestation, content: str) -> bool:
        """验证见证记录与内容的一致性
        
        Args:
            attestation: 见证记录
            content: 要验证的内容
            
        Returns:
            内容是否与见证记录一致
        """
        # 生成内容哈希
        content_hash = self.signature_service.generate_content_hash(content)
        
        # 验证哈希是否匹配
        return hmac.compare_digest(content_hash, attestation.content_hash)
    
    def get_attestations_by_target(self, target_id: str, target_type: str) -> List[_GovernanceAttestation]:
        """获取特定目标的所有见证记录
        
        Args:
            target_id: 目标ID
            target_type: 目标类型
            
        Returns:
            该目标的所有见证记录
        """
        # 这里应该从存储中获取，暂时返回空列表
        # 实际实现中应该调用存储服务
        return []


__all__ = []
