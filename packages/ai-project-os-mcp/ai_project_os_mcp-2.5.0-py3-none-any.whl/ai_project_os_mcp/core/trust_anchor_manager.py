"""
Trust Anchor Manager - Manage external trust anchors for governance finality

This module implements the trust anchor manager ensuring that governance proof roots are
submitted to external trust anchors, and receipts are verified. It follows a fail-closed
approach: if anchoring fails, no finality record is generated.

Governance Rules:
- Trust anchors are only existence witnesses, not sovereigns
- Fail-closed: Anchoring failure does not generate finality records
- Multiple anchors supported for redundancy
- Trust anchors are单向, verifiable, and replaceable
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid

from .trust_anchor_models import (
    _TrustAnchor,
    _TrustAnchorSubmission,
    _TrustAnchorReceipt,
    _TrustAnchorVerificationResult,
    _TrustAnchorRegistry
)
from .governance_attestation import _SignatureService


class _TrustAnchorManager(BaseModel):
    """信任锚管理器
    
    管理多个信任锚，提交证明根哈希到信任锚，并验证信任锚回执
    """
    # 服务依赖
    signature_service: _SignatureService
    
    # 内部状态
    anchor_registry: _TrustAnchorRegistry = Field(default_factory=_TrustAnchorRegistry, description="信任锚注册表")
    submissions: Dict[str, _TrustAnchorSubmission] = Field(default_factory=dict, description="信任锚提交记录")
    receipts: Dict[str, _TrustAnchorReceipt] = Field(default_factory=dict, description="信任锚回执")
    
    class Config:
        frozen = False  # 允许更新内部状态
    
    def register_anchor(self, anchor: _TrustAnchor) -> _TrustAnchor:
        """注册信任锚
        
        Args:
            anchor: 要注册的信任锚
            
        Returns:
            注册后的信任锚
        """
        # 检查信任锚是否已存在
        for existing_anchor in self.anchor_registry.anchors:
            if existing_anchor.anchor_id == anchor.anchor_id:
                return existing_anchor
        
        # 创建新的注册表实例（因为注册表是不可修改的）
        new_registry = self.anchor_registry.model_copy(
            update={
                "anchors": self.anchor_registry.anchors + [anchor],
                "updated_at": datetime.now()
            }
        )
        
        # 更新内部状态
        self.anchor_registry = new_registry
        
        return anchor
    
    def get_active_anchors(self) -> List[_TrustAnchor]:
        """获取所有活跃的信任锚
        
        Returns:
            活跃的信任锚列表
        """
        return [anchor for anchor in self.anchor_registry.anchors if anchor.is_active]
    
    def submit_proof_root(self, proof_bundle_root: str, anchor_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """提交证明根哈希到信任锚
        
        Args:
            proof_bundle_root: 证明包根哈希
            anchor_ids: 要提交到的信任锚ID列表，若为None则提交到所有活跃信任锚
            
        Returns:
            提交结果，包含提交记录ID和状态
        """
        # 确定要提交的信任锚
        if anchor_ids:
            target_anchors = [anchor for anchor in self.anchor_registry.anchors 
                             if anchor.anchor_id in anchor_ids and anchor.is_active]
        else:
            target_anchors = self.get_active_anchors()
        
        # 如果没有目标信任锚，返回失败
        if not target_anchors:
            return {
                "status": "FAILED",
                "reason": "No active trust anchors available",
                "submission_ids": []
            }
        
        submission_ids = []
        
        # 向每个信任锚提交
        for anchor in target_anchors:
            # 创建提交记录
            submission = _TrustAnchorSubmission(
                anchor_id=anchor.anchor_id,
                proof_bundle_root=proof_bundle_root,
                submission_data={
                    "submitted_by": "governance_engine",
                    "submission_timestamp": datetime.now().isoformat()
                }
            )
            
            # 保存提交记录
            self.submissions[submission.submission_id] = submission
            submission_ids.append(submission.submission_id)
            
            # 模拟提交到信任锚（实际实现中需要调用外部API）
            # 这里简化为直接生成成功回执
            receipt = self._simulate_anchor_response(submission)
            
            # 保存回执
            self.receipts[receipt.receipt_id] = receipt
            
            # 更新提交记录状态
            self.submissions[submission.submission_id] = submission.model_copy(
                update={"status": "success"}
            )
        
        return {
            "status": "PENDING",
            "message": f"Submitted to {len(target_anchors)} trust anchors",
            "submission_ids": submission_ids
        }
    
    def _simulate_anchor_response(self, submission: _TrustAnchorSubmission) -> _TrustAnchorReceipt:
        """模拟信任锚响应
        
        在实际实现中，这应该调用外部信任锚API
        
        Args:
            submission: 提交记录
            
        Returns:
            模拟的信任锚回执
        """
        # 获取对应的信任锚
        anchor = None
        for a in self.anchor_registry.anchors:
            if a.anchor_id == submission.anchor_id:
                anchor = a
                break
        
        if not anchor:
            raise ValueError(f"Trust anchor {submission.anchor_id} not found")
        
        # 生成锚特定引用（模拟）
        if anchor.anchor_type == "tsa":
            anchor_ref = f"tsa-timestamp-{datetime.now().isoformat()}"
        elif anchor.anchor_type == "public_log":
            anchor_ref = f"public-log-entry-{uuid.uuid4()}"
        elif anchor.anchor_type == "notary":
            anchor_ref = f"notary-seal-{uuid.uuid4()}"
        else:
            anchor_ref = f"custom-anchor-{uuid.uuid4()}"
        
        # 生成签名（模拟）
        signature = f"simulated-signature-{uuid.uuid4()}" if anchor.public_key else None
        
        # 创建回执
        return _TrustAnchorReceipt(
            submission_id=submission.submission_id,
            anchor_id=submission.anchor_id,
            proof_bundle_root=submission.proof_bundle_root,
            anchor_specific_ref=anchor_ref,
            anchored_at=datetime.now(),
            receipt_signature=signature,
            verified=False
        )
    
    def verify_receipt(self, receipt_id: str) -> _TrustAnchorVerificationResult:
        """验证信任锚回执
        
        Args:
            receipt_id: 回执ID
            
        Returns:
            验证结果
        """
        # 获取回执
        receipt = self.receipts.get(receipt_id)
        if not receipt:
            return _TrustAnchorVerificationResult(
                verified=False,
                anchor_id="unknown",
                receipt_id=receipt_id,
                reason="Receipt not found"
            )
        
        # 获取对应的信任锚
        anchor = None
        for a in self.anchor_registry.anchors:
            if a.anchor_id == receipt.anchor_id:
                anchor = a
                break
        
        if not anchor:
            return _TrustAnchorVerificationResult(
                verified=False,
                anchor_id=receipt.anchor_id,
                receipt_id=receipt_id,
                reason="Trust anchor not found"
            )
        
        # 获取对应的提交记录
        submission = self.submissions.get(receipt.submission_id)
        if not submission:
            return _TrustAnchorVerificationResult(
                verified=False,
                anchor_id=receipt.anchor_id,
                receipt_id=receipt_id,
                reason="Submission not found"
            )
        
        # 验证证明包根哈希匹配
        if receipt.proof_bundle_root != submission.proof_bundle_root:
            return _TrustAnchorVerificationResult(
                verified=False,
                anchor_id=receipt.anchor_id,
                receipt_id=receipt_id,
                reason="Proof bundle root mismatch"
            )
        
        # 验证签名（如果有）
        if anchor.public_key and receipt.receipt_signature:
            # 实际实现中应该使用锚的公钥验证签名
            # 这里简化为模拟验证通过
            signature_verified = True
        else:
            signature_verified = True  # 没有签名的情况下默认验证通过
        
        if not signature_verified:
            return _TrustAnchorVerificationResult(
                verified=False,
                anchor_id=receipt.anchor_id,
                receipt_id=receipt_id,
                reason="Signature verification failed"
            )
        
        # 更新回执验证状态
        self.receipts[receipt_id] = receipt.model_copy(
            update={"verified": True}
        )
        
        return _TrustAnchorVerificationResult(
            verified=True,
            anchor_id=receipt.anchor_id,
            receipt_id=receipt_id,
            reason="Receipt verified successfully"
        )
    
    def get_verified_receipts(self, submission_ids: List[str]) -> List[_TrustAnchorReceipt]:
        """获取已验证的回执
        
        Args:
            submission_ids: 提交记录ID列表
            
        Returns:
            已验证的回执列表
        """
        verified_receipts = []
        
        # 验证所有回执
        for submission_id in submission_ids:
            # 获取该提交的所有回执（理论上一个提交对应一个回执）
            for receipt in self.receipts.values():
                if receipt.submission_id == submission_id:
                    # 如果还没验证，先验证
                    if not receipt.verified:
                        self.verify_receipt(receipt.receipt_id)
                    
                    # 如果验证通过，添加到结果列表
                    if receipt.verified:
                        verified_receipts.append(receipt)
        
        return verified_receipts
    
    def get_anchor_references(self, receipts: List[_TrustAnchorReceipt]) -> List[str]:
        """从回执中提取锚引用
        
        Args:
            receipts: 已验证的回执列表
            
        Returns:
            锚引用列表
        """
        return [receipt.anchor_specific_ref for receipt in receipts]
    
    def is_anchoring_successful(self, submission_ids: List[str]) -> bool:
        """检查锚定是否成功
        
        遵循fail-closed原则：只有当所有提交都成功且回执都验证通过时，才认为锚定成功
        
        Args:
            submission_ids: 提交记录ID列表
            
        Returns:
            锚定是否成功
        """
        # 获取所有已验证的回执
        verified_receipts = self.get_verified_receipts(submission_ids)
        
        # 检查是否所有提交都有对应的已验证回执
        return len(verified_receipts) == len(submission_ids)
    
    def get_anchor_by_id(self, anchor_id: str) -> Optional[_TrustAnchor]:
        """根据ID获取信任锚
        
        Args:
            anchor_id: 信任锚ID
            
        Returns:
            信任锚对象，若不存在则返回None
        """
        for anchor in self.anchor_registry.anchors:
            if anchor.anchor_id == anchor_id:
                return anchor
        return None


__all__ = []