"""
Governance Proof Models - Define governance-level proof objects

This module implements the core governance proof models ensuring that every governance outcome
can be proven to have occurred, with non-repudiation, non-forgery, and non-rewrite guarantees.

Governance Invariants:
- Non-Repudiation: No Actor can deny their decisions or actions
- Non-Forgery: No valid proof without legitimate sovereignty context
- Non-Rewrite: Historical records can only be appended, not overwritten
- Independent Verifiability: Third parties can verify without runtime state
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
import hashlib
from .sovereignty_context import _SovereigntyContext


class _ResponsibilitySnapshot(BaseModel):
    """责任快照
    
    捕获特定时间点的责任状态，用于证明责任归属
    """
    snapshot_id: str = Field(default_factory=lambda: f"snapshot-{uuid.uuid4()}", description="快照ID")
    event_id: str = Field(..., description="关联事件ID")
    primary_responsible: str = Field(..., description="主要责任人")
    contributing_parties: List[str] = Field(default_factory=list, description="参与方列表")
    responsibility_type: Literal["direct", "shared", "delegated", "overridden"] = Field(..., description="责任类型")
    timestamp: datetime = Field(default_factory=datetime.now, description="快照时间")
    sovereignty_context: Dict[str, Any] = Field(..., description="主权上下文")
    governance_version: str = Field(..., description="治理引擎版本")
    
    class Config:
        frozen = True  # 责任快照不可修改，确保审计完整性


class _GovernanceProof(BaseModel):
    """治理证明模型
    
    治理级证明对象，作为治理系统的最终信任锚点
    Proof链接成hash chain，确保不可篡改性
    
    治理铁律：
    - Proof是append-only
    - Proof链接成hash chain
    - Proof不可被覆盖或删除
    - Proof Hash必须包含主权版本号
    """
    proof_id: str = Field(default_factory=lambda: f"proof-{uuid.uuid4()}", description="证明ID")
    proof_type: Literal[
        "event_execution",
        "decision_resolution",
        "action_execution",
        "sovereignty_transfer",
        "arbitration_result",
        "governance_violation"  # 新增：治理违规证明
    ] = Field(..., description="证明类型")
    hash: str = Field(..., description="证明哈希值")
    previous_hash: Optional[str] = Field(None, description="前一个证明的哈希值，用于构建哈希链")
    timestamp: datetime = Field(default_factory=datetime.now, description="证明生成时间")
    sovereignty_context: Dict[str, Any] = Field(..., description="主权上下文")
    responsibility_snapshot: _ResponsibilitySnapshot = Field(..., description="责任快照")
    audit_record_id: str = Field(..., description="关联的审计记录ID")
    
    # 新增：显式包含版本信息，防止同一逻辑不同规则版本生成相同Proof
    sovereignty_version: str = Field(..., description="主权版本号")
    agent_version: Optional[str] = Field(None, description="Agent版本号（若涉及Agent）")
    governance_engine_version: str = Field(default="v2.5", description="治理引擎版本")
    
    class Config:
        frozen = True  # 治理证明不可修改，确保不可篡改性

    def generate_hash(self, previous_proof: Optional['_GovernanceProof'] = None) -> str:
        """生成证明哈希值
        
        哈希计算包含：
        - 证明类型
        - 主权上下文（含版本号）
        - 责任快照
        - 审计记录ID
        - 前一个证明的哈希值
        - 显式包含主权版本号、Agent版本号和治理引擎版本
        
        Args:
            previous_proof: 前一个证明对象，用于获取前一个哈希值
            
        Returns:
            生成的哈希值
        """
        # 构建哈希输入
        hash_input = {
            "proof_type": self.proof_type,
            "sovereignty_context": self.sovereignty_context,
            "responsibility_snapshot": self.responsibility_snapshot.model_dump(),
            "audit_record_id": self.audit_record_id,
            "timestamp": self.timestamp.isoformat(),
            "sovereignty_version": self.sovereignty_version,
            "agent_version": self.agent_version,
            "governance_engine_version": self.governance_engine_version,
            "previous_hash": previous_proof.hash if previous_proof else None
        }
        
        # 生成SHA-256哈希
        hash_str = str(hash_input)
        return hashlib.sha256(hash_str.encode('utf-8')).hexdigest()


class _GovernanceProofBundle(BaseModel):
    """治理证明包
    
    用于导出和验证的证明集合，包含完整的哈希链
    """
    bundle_id: str = Field(default_factory=lambda: f"bundle-{uuid.uuid4()}", description="证明包ID")
    event_id: str = Field(..., description="关联事件ID")
    proofs: List[_GovernanceProof] = Field(default_factory=list, description="证明列表")
    audit_record: Dict[str, Any] = Field(..., description="关联的审计记录")
    responsibility_chain: List[str] = Field(default_factory=list, description="责任链链接ID列表")
    sovereignty_contexts: List[Dict[str, Any]] = Field(default_factory=list, description="所有阶段的主权上下文列表")
    created_at: datetime = Field(default_factory=datetime.now, description="证明包创建时间")
    
    # 新增：最小验证根，第三方只需验证此根哈希即可判断bundle是否被篡改
    root_hash: str = Field(..., description="证明包根哈希，用于快速验证完整性")
    
    class Config:
        frozen = True  # 证明包不可修改，确保完整性


class _GovernanceProofVerificationResult(BaseModel):
    """治理证明验证结果
    
    独立验证的结果，包含验证状态和详细信息
    """
    verified: bool = Field(..., description="验证是否通过")
    message: str = Field(..., description="验证结果消息")
    details: Dict[str, Any] = Field(default_factory=dict, description="验证详情")
    verified_at: datetime = Field(default_factory=datetime.now, description="验证时间")
    
    # 若验证失败，包含失败原因
    failure_reason: Optional[str] = Field(None, description="验证失败原因")
    
    class Config:
        frozen = True  # 验证结果不可修改，确保可信度


__all__ = []
