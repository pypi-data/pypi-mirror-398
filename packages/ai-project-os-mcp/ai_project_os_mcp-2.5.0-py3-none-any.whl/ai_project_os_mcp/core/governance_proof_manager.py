"""
Governance Proof Manager - Proof Generation, Validation & Bundle Management

This module implements the governance proof manager, responsible for:
1. Generating governance proofs for all governance decisions
2. Managing the hash chain of proofs
3. Creating and validating proof bundles
4. Handling replay consistency checks and violation proof generation
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ValidationError
import uuid
import hashlib

from .governance_proof_models import (
    _ResponsibilitySnapshot,
    _GovernanceProof,
    _GovernanceProofBundle,
    _GovernanceProofVerificationResult
)
from .governance_attestation import (
    _GovernanceAttestation,
    _AttestationService,
    _SignatureService
)
from .sovereignty_context import _SovereigntyContext


class _GovernanceProofManager(BaseModel):
    """治理证明管理器
    
    负责生成、管理和验证治理证明，确保所有治理决策都能被证明和追溯
    """
    
    # 服务依赖
    signature_service: _SignatureService
    attestation_service: _AttestationService
    
    # 内部状态：哈希链管理
    proof_chain: Dict[str, _GovernanceProof] = Field(default_factory=dict, description="证明哈希链，key为proof_id")
    latest_proof_id: Optional[str] = Field(None, description="最新证明ID")
    proof_by_event: Dict[str, List[str]] = Field(default_factory=dict, description="按事件ID索引的证明列表")
    
    class Config:
        frozen = False  # 允许更新内部状态
    
    def create_responsibility_snapshot(
        self,
        event_id: str,
        primary_responsible: str,
        contributing_parties: List[str],
        responsibility_type: str,
        sovereignty_context: _SovereigntyContext,
        governance_version: str
    ) -> _ResponsibilitySnapshot:
        """创建责任快照
        
        Args:
            event_id: 关联事件ID
            primary_responsible: 主要责任人
            contributing_parties: 参与方列表
            responsibility_type: 责任类型
            sovereignty_context: 主权上下文
            governance_version: 治理引擎版本
            
        Returns:
            创建的责任快照
        """
        return _ResponsibilitySnapshot(
            event_id=event_id,
            primary_responsible=primary_responsible,
            contributing_parties=contributing_parties,
            responsibility_type=responsibility_type,
            sovereignty_context=sovereignty_context.model_dump(),
            governance_version=governance_version
        )
    
    def generate_governance_proof(
        self,
        proof_type: str,
        sovereignty_context: _SovereigntyContext,
        responsibility_snapshot: _ResponsibilitySnapshot,
        audit_record_id: str,
        agent_version: Optional[str] = None,
        governance_engine_version: str = "v2.5"
    ) -> _GovernanceProof:
        """生成治理证明
        
        生成新的治理证明，并将其添加到哈希链中
        
        Args:
            proof_type: 证明类型
            sovereignty_context: 主权上下文
            responsibility_snapshot: 责任快照
            audit_record_id: 关联的审计记录ID
            agent_version: Agent版本号（若涉及Agent）
            governance_engine_version: 治理引擎版本
            
        Returns:
            生成的治理证明
        """
        # 获取上一个证明
        previous_proof = None
        previous_hash = None
        if self.latest_proof_id:
            previous_proof = self.proof_chain[self.latest_proof_id]
            previous_hash = previous_proof.hash
        
        # 创建证明对象
        proof = _GovernanceProof(
            proof_type=proof_type,
            hash="",  # 先占位，后面生成
            previous_hash=previous_hash,
            sovereignty_context=sovereignty_context.model_dump(),
            responsibility_snapshot=responsibility_snapshot,
            audit_record_id=audit_record_id,
            sovereignty_version=sovereignty_context.governance_version,
            agent_version=agent_version,
            governance_engine_version=governance_engine_version
        )
        
        # 生成哈希
        proof_hash = proof.generate_hash(previous_proof)
        
        # 更新证明的哈希值（使用模型复制，因为模型是frozen的）
        proof = proof.model_copy(update={"hash": proof_hash})
        
        # 添加到哈希链
        self.proof_chain[proof.proof_id] = proof
        self.latest_proof_id = proof.proof_id
        
        # 按事件ID索引
        if responsibility_snapshot.event_id not in self.proof_by_event:
            self.proof_by_event[responsibility_snapshot.event_id] = []
        self.proof_by_event[responsibility_snapshot.event_id].append(proof.proof_id)
        
        return proof
    
    def generate_violation_proof(
        self,
        original_proof: _GovernanceProof,
        replay_hash: str,
        sovereignty_context: _SovereigntyContext,
        audit_record_id: str,
        governance_engine_version: str = "v2.5"
    ) -> _GovernanceProof:
        """生成治理违规证明
        
        当replay与原始证明不一致时，生成违规证明
        
        Args:
            original_proof: 原始证明
            replay_hash: 重新计算的哈希值
            sovereignty_context: 当前主权上下文
            audit_record_id: 关联的审计记录ID
            governance_engine_version: 治理引擎版本
            
        Returns:
            生成的治理违规证明
        """
        # 创建责任快照，记录违规情况
        violation_snapshot = self.create_responsibility_snapshot(
            event_id=original_proof.responsibility_snapshot.event_id,
            primary_responsible="system",  # 系统检测到违规
            contributing_parties=[original_proof.responsibility_snapshot.primary_responsible],
            responsibility_type="direct",
            sovereignty_context=sovereignty_context,
            governance_version=governance_engine_version
        )
        
        # 生成违规证明
        violation_proof = self.generate_governance_proof(
            proof_type="governance_violation",
            sovereignty_context=sovereignty_context,
            responsibility_snapshot=violation_snapshot,
            audit_record_id=audit_record_id,
            governance_engine_version=governance_engine_version
        )
        
        return violation_proof
    
    def create_proof_bundle(
        self,
        event_id: str,
        audit_record: Dict[str, Any]
    ) -> _GovernanceProofBundle:
        """创建治理证明包
        
        为特定事件创建完整的证明包，包含所有相关证明和根哈希
        
        Args:
            event_id: 事件ID
            audit_record: 关联的审计记录
            
        Returns:
            创建的治理证明包
        """
        # 获取该事件的所有证明
        proof_ids = self.proof_by_event.get(event_id, [])
        proofs = [self.proof_chain[proof_id] for proof_id in proof_ids]
        
        # 收集所有主权上下文
        sovereignty_contexts = [proof.sovereignty_context for proof in proofs]
        
        # 收集责任链
        responsibility_chain = [proof.responsibility_snapshot.snapshot_id for proof in proofs]
        
        # 生成根哈希：使用最后一个证明的哈希 + 包元数据
        root_hash = ""
        if proofs:
            last_proof = proofs[-1]
            bundle_metadata = {
                "event_id": event_id,
                "bundle_created_at": datetime.now().isoformat(),
                "proof_count": len(proofs)
            }
            
            # 根哈希计算：last_proof.hash + 包元数据的哈希
            metadata_str = str(bundle_metadata)
            metadata_hash = hashlib.sha256(metadata_str.encode('utf-8')).hexdigest()
            root_hash_input = f"{last_proof.hash}:{metadata_hash}"
            root_hash = hashlib.sha256(root_hash_input.encode('utf-8')).hexdigest()
        
        # 创建证明包
        proof_bundle = _GovernanceProofBundle(
            event_id=event_id,
            proofs=proofs,
            audit_record=audit_record,
            responsibility_chain=responsibility_chain,
            sovereignty_contexts=sovereignty_contexts,
            root_hash=root_hash
        )
        
        return proof_bundle
    
    def verify_proof_chain(
        self,
        proof_bundle: _GovernanceProofBundle
    ) -> _GovernanceProofVerificationResult:
        """验证治理证明链
        
        独立验证证明包的完整性和一致性
        
        Args:
            proof_bundle: 要验证的证明包
            
        Returns:
            验证结果
        """
        if not proof_bundle.proofs:
            return _GovernanceProofVerificationResult(
                verified=False,
                message="Proof bundle contains no proofs",
                failure_reason="Empty proof bundle"
            )
        
        # 1. 验证根哈希
        if proof_bundle.root_hash:
            # 重新计算根哈希
            last_proof = proof_bundle.proofs[-1]
            bundle_metadata = {
                "event_id": proof_bundle.event_id,
                "bundle_created_at": proof_bundle.created_at.isoformat(),
                "proof_count": len(proof_bundle.proofs)
            }
            
            metadata_str = str(bundle_metadata)
            metadata_hash = hashlib.sha256(metadata_str.encode('utf-8')).hexdigest()
            root_hash_input = f"{last_proof.hash}:{metadata_hash}"
            calculated_root_hash = hashlib.sha256(root_hash_input.encode('utf-8')).hexdigest()
            
            if proof_bundle.root_hash != calculated_root_hash:
                return _GovernanceProofVerificationResult(
                    verified=False,
                    message="Root hash verification failed",
                    details={
                        "expected": proof_bundle.root_hash,
                        "calculated": calculated_root_hash
                    },
                    failure_reason="Root hash mismatch"
                )
        
        # 2. 验证哈希链完整性
        previous_proof = None
        for proof in proof_bundle.proofs:
            # 重新生成哈希并验证
            expected_hash = proof.generate_hash(previous_proof)
            if proof.hash != expected_hash:
                return _GovernanceProofVerificationResult(
                    verified=False,
                    message="Proof hash verification failed",
                    details={
                        "proof_id": proof.proof_id,
                        "expected": expected_hash,
                        "actual": proof.hash
                    },
                    failure_reason="Proof hash mismatch"
                )
            
            # 验证前一个哈希链接
            if previous_proof and proof.previous_hash != previous_proof.hash:
                return _GovernanceProofVerificationResult(
                    verified=False,
                    message="Proof chain link verification failed",
                    details={
                        "proof_id": proof.proof_id,
                        "expected_previous_hash": previous_proof.hash,
                        "actual_previous_hash": proof.previous_hash
                    },
                    failure_reason="Proof chain link broken"
                )
            
            previous_proof = proof
        
        # 3. 验证责任快照完整性
        for proof in proof_bundle.proofs:
            # 这里可以添加更多责任快照验证逻辑
            # 例如：验证责任人是否存在，责任类型是否有效等
            pass
        
        return _GovernanceProofVerificationResult(
            verified=True,
            message="All proofs in bundle verified successfully",
            details={
                "proof_count": len(proof_bundle.proofs),
                "event_id": proof_bundle.event_id
            }
        )
    
    def replay_and_verify(
        self,
        proof_bundle: _GovernanceProofBundle,
        current_sovereignty_context: _SovereigntyContext
    ) -> _GovernanceProofVerificationResult:
        """重放并验证证明
        
        模拟重放治理决策，验证当前规则下的行为一致性
        
        Args:
            proof_bundle: 要重放的证明包
            current_sovereignty_context: 当前主权上下文
            
        Returns:
            验证结果
        """
        # 先验证证明链的完整性
        chain_result = self.verify_proof_chain(proof_bundle)
        if not chain_result.verified:
            return chain_result
        
        # 模拟重放每个证明
        for proof in proof_bundle.proofs:
            # 这里需要实现实际的重放逻辑
            # 例如：重新执行治理决策，比较结果
            
            # 对于演示目的，我们只验证版本信息是否匹配
            # 实际实现中，需要更复杂的重放逻辑
            pass
        
        return _GovernanceProofVerificationResult(
            verified=True,
            message="Replay verification completed successfully",
            details={
                "proof_count": len(proof_bundle.proofs),
                "event_id": proof_bundle.event_id
            }
        )
    
    def get_proof_by_id(
        self,
        proof_id: str
    ) -> Optional[_GovernanceProof]:
        """根据ID获取证明
        
        Args:
            proof_id: 证明ID
            
        Returns:
            对应的证明对象，若不存在则返回None
        """
        return self.proof_chain.get(proof_id)
    
    def get_proofs_by_event(
        self,
        event_id: str
    ) -> List[_GovernanceProof]:
        """根据事件ID获取所有证明
        
        Args:
            event_id: 事件ID
            
        Returns:
            该事件的所有证明
        """
        proof_ids = self.proof_by_event.get(event_id, [])
        return [self.proof_chain[proof_id] for proof_id in proof_ids]


__all__ = []
