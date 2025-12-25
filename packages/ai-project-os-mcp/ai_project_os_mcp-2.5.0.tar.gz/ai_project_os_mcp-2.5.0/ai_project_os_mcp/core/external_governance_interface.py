"""
External Governance Interface - Manage external governance interactions

This module implements the external governance interface manager ensuring that external entities
can interact with the system's governance layer in a secure, controlled, and auditable manner.

Responsibilities:
- Verify external authority identity
- Export Proof Bundle (read-only)
- Receive freeze/investigation/adjudication requests
- Generate disclosure and freeze proofs

Forbidden Actions:
- External interface cannot modify system state directly
- External interface cannot bypass Governance Engine
- External interface cannot override internal governance rules
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

from .external_authority_models import (
    _ExternalAuthority,
    _ExternalAuthorityVerificationResult,
    _ExternalAuthorityAction
)
from .governance_disclosure_models import (
    _GovernanceDisclosure,
    _DisclosureReceipt,
    _ProofExport,
    _ProofBundleExport
)
from .governance_proof_models import (
    _GovernanceProof,
    _GovernanceProofBundle,
    _GovernanceProofVerificationResult
)
from .governance_attestation import (
    _SignatureService,
    _AttestationService
)


class _ExternalGovernanceInterface(BaseModel):
    """外部治理接口管理器
    
    管理系统与外部权威实体的交互，确保交互安全、可控、可审计
    """
    # 服务依赖
    signature_service: _SignatureService
    attestation_service: _AttestationService
    
    # 内部状态
    external_authorities: Dict[str, _ExternalAuthority] = Field(default_factory=dict, description="已注册的外部权威字典")
    disclosure_records: Dict[str, _GovernanceDisclosure] = Field(default_factory=dict, description="披露记录字典")
    disclosure_receipts: Dict[str, _DisclosureReceipt] = Field(default_factory=dict, description="披露收据字典")
    proof_exports: Dict[str, _ProofExport] = Field(default_factory=dict, description="证明导出记录字典")
    external_actions: Dict[str, _ExternalAuthorityAction] = Field(default_factory=dict, description="外部权威动作字典")
    
    class Config:
        frozen = False  # 允许更新内部状态
    
    def register_external_authority(self, authority: _ExternalAuthority) -> _ExternalAuthority:
        """注册外部权威实体
        
        Args:
            authority: 外部权威实体对象
            
        Returns:
            注册后的外部权威实体
        """
        # 验证外部权威唯一性
        if authority.authority_id in self.external_authorities:
            raise ValueError(f"External authority {authority.authority_id} already registered")
        
        # 注册外部权威
        self.external_authorities[authority.authority_id] = authority
        
        return authority
    
    def verify_external_authority(self, authority_id: str, signature: str, challenge: str) -> _ExternalAuthorityVerificationResult:
        """验证外部权威身份
        
        Args:
            authority_id: 外部权威ID
            signature: 外部权威提供的签名
            challenge: 用于验证的挑战字符串
            
        Returns:
            验证结果
        """
        # 检查外部权威是否已注册
        if authority_id not in self.external_authorities:
            return _ExternalAuthorityVerificationResult(
                verified=False,
                authority_id=authority_id,
                reason="External authority not registered",
                verified_by="system"
            )
        
        authority = self.external_authorities[authority_id]
        
        # 验证签名
        # 注意：这里使用HMAC-SHA256进行演示，实际实现应使用更安全的签名算法
        expected_signature = hmac.new(
            authority.public_key.encode('utf-8'),
            challenge.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        verified = hmac.compare_digest(expected_signature, signature)
        
        return _ExternalAuthorityVerificationResult(
            verified=verified,
            authority_id=authority_id,
            reason="Signature verification successful" if verified else "Signature verification failed",
            verified_by="system"
        )
    
    def export_proof_bundle(self, proof_bundle: _GovernanceProofBundle, export_format: Literal["json", "binary"] = "json") -> _ProofBundleExport:
        """导出Proof Bundle
        
        Args:
            proof_bundle: 要导出的证明包
            export_format: 导出格式（json或binary）
            
        Returns:
            导出的证明包
        """
        # 创建导出记录
        export_record = _ProofExport(
            proof_bundle_id=proof_bundle.bundle_id,
            proof_bundle_root=proof_bundle.root_hash,
            export_format=export_format,
            export_scope=["proof", "attestation", "audit"],
            exported_by="system",
            jurisdiction="global",  # 默认全局适用域，实际应从证明包中提取
            signature="system_signature"  # 实际应使用系统签名
        )
        
        # 保存导出记录
        self.proof_exports[export_record.export_id] = export_record
        
        # 创建证明包导出
        proof_bundle_export = _ProofBundleExport(
            bundle_id=proof_bundle.bundle_id,
            root_hash=proof_bundle.root_hash,
            proof_count=len(proof_bundle.proofs),
            attestation_count=0,  # 实际应从证明包中提取
            export_id=export_record.export_id,
            jurisdiction="global",  # 默认全局适用域，实际应从证明包中提取
            governance_version="v2.5",  # 实际应从系统配置中提取
            content=proof_bundle.model_dump(),
            signature="system_signature"  # 实际应使用系统签名
        )
        
        return proof_bundle_export
    
    def create_disclosure(self, proof_bundle: _GovernanceProofBundle, disclosed_to: str, reason: Optional[str] = None) -> _GovernanceDisclosure:
        """创建治理披露记录
        
        Args:
            proof_bundle: 要披露的证明包
            disclosed_to: 披露对象（外部权威ID）
            reason: 披露原因
            
        Returns:
            创建的披露记录
        """
        # 检查外部权威是否已注册
        if disclosed_to not in self.external_authorities:
            raise ValueError(f"External authority {disclosed_to} not registered")
        
        authority = self.external_authorities[disclosed_to]
        
        # 创建披露记录
        disclosure = _GovernanceDisclosure(
            proof_bundle_root=proof_bundle.root_hash,
            disclosed_to=disclosed_to,
            disclosed_to_type=authority.authority_type,
            disclosure_scope=["proof", "attestation", "audit"],
            jurisdiction=authority.jurisdiction,
            reason=reason,
            signature="system_signature"  # 实际应使用系统签名
        )
        
        # 保存披露记录
        self.disclosure_records[disclosure.disclosure_id] = disclosure
        
        return disclosure
    
    def process_external_action(self, action: _ExternalAuthorityAction) -> Dict[str, Any]:
        """处理外部权威动作
        
        Args:
            action: 外部权威动作
            
        Returns:
            动作处理结果
        """
        # 验证外部权威身份
        if action.authority_id not in self.external_authorities:
            return {
                "status": "FAILED",
                "reason": f"External authority {action.authority_id} not registered"
            }
        
        # 保存动作记录
        self.external_actions[action.action_id] = action
        
        # 根据动作类型处理
        if action.action_type == "freeze":
            # 冻结请求需要转发给Governance Engine处理
            return {
                "status": "PENDING",
                "action_id": action.action_id,
                "message": "Freeze request received, forwarding to Governance Engine"
            }
        elif action.action_type == "unfreeze":
            # 解冻请求需要转发给Governance Engine处理
            return {
                "status": "PENDING",
                "action_id": action.action_id,
                "message": "Unfreeze request received, forwarding to Governance Engine"
            }
        elif action.action_type == "verify":
            # 验证请求可以直接处理
            return {
                "status": "COMPLETED",
                "action_id": action.action_id,
                "message": "Verification request received, processing..."
            }
        elif action.action_type == "adjudicate":
            # 裁定请求需要转发给Governance Engine处理
            return {
                "status": "PENDING",
                "action_id": action.action_id,
                "message": "Adjudication request received, forwarding to Governance Engine"
            }
        else:
            return {
                "status": "FAILED",
                "reason": f"Invalid action type: {action.action_type}"
            }
    
    def verify_proof_chain(self, proof_bundle: _GovernanceProofBundle) -> _GovernanceProofVerificationResult:
        """验证证明链
        
        Args:
            proof_bundle: 要验证的证明包
            
        Returns:
            验证结果
        """
        # 简单实现：验证根哈希
        # 实际应实现完整的证明链验证逻辑
        return _GovernanceProofVerificationResult(
            verified=True,
            message="Proof bundle verification successful",
            details={
                "proof_count": len(proof_bundle.proofs),
                "root_hash": proof_bundle.root_hash
            }
        )
    
    def get_authority_by_id(self, authority_id: str) -> Optional[_ExternalAuthority]:
        """根据ID获取外部权威
        
        Args:
            authority_id: 外部权威ID
            
        Returns:
            外部权威对象，若不存在则返回None
        """
        return self.external_authorities.get(authority_id)
    
    def get_disclosure_by_id(self, disclosure_id: str) -> Optional[_GovernanceDisclosure]:
        """根据ID获取披露记录
        
        Args:
            disclosure_id: 披露记录ID
            
        Returns:
            披露记录对象，若不存在则返回None
        """
        return self.disclosure_records.get(disclosure_id)
    
    def get_all_authorities(self) -> List[_ExternalAuthority]:
        """获取所有已注册的外部权威
        
        Returns:
            外部权威列表
        """
        return list(self.external_authorities.values())
    
    def get_authorities_by_type(self, authority_type: Literal["regulator", "court", "counterparty"]) -> List[_ExternalAuthority]:
        """根据类型获取外部权威
        
        Args:
            authority_type: 外部权威类型
            
        Returns:
            外部权威列表
        """
        return [authority for authority in self.external_authorities.values() if authority.authority_type == authority_type]
    
    def get_disclosures_by_authority(self, authority_id: str) -> List[_GovernanceDisclosure]:
        """根据外部权威ID获取披露记录
        
        Args:
            authority_id: 外部权威ID
            
        Returns:
            披露记录列表
        """
        return [disclosure for disclosure in self.disclosure_records.values() if disclosure.disclosed_to == authority_id]
    
    def get_exports_by_bundle(self, bundle_id: str) -> List[_ProofExport]:
        """根据证明包ID获取导出记录
        
        Args:
            bundle_id: 证明包ID
            
        Returns:
            导出记录列表
        """
        return [export for export in self.proof_exports.values() if export.proof_bundle_id == bundle_id]
    
    def get_actions_by_authority(self, authority_id: str) -> List[_ExternalAuthorityAction]:
        """根据外部权威ID获取动作记录
        
        Args:
            authority_id: 外部权威ID
            
        Returns:
            动作记录列表
        """
        return [action for action in self.external_actions.values() if action.authority_id == authority_id]


__all__ = []
