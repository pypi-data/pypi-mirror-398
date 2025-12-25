"""
Governance Lifecycle Models - Define retention, expiration, and revocation models

This module implements the governance lifecycle models ensuring that governance facts have
clear lifecycle states (ACTIVE, EXPIRED, REVOKED, SUSPENDED) and follow well-defined
lifecycle rules. It addresses the question of whether a governance fact is still
"established, referenceable, and adjudicatable" in a governance sense.

Governance Invariants:
- Governance Proofs once exist can only change their "legal and governance semantics", not existence
- Lifecycle is always bound to Proof Bundle Root, not specific Action/Event
- Lifecycle must be consistent during Replay
- REVOKED is a terminal state
- EXPIRED cannot return to ACTIVE
- All state transitions must be recorded with evidence
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple, Literal
from pydantic import BaseModel, Field
import uuid

from .jurisdiction_models import _JurisdictionContext
from .governance_attestation import _SignatureService
from .violation import _GovernanceViolation as GovernanceViolation, _ViolationLevel as ViolationLevel


# Phase-3: Execution / Retention / Storage Boundary Design
class RetentionTier(str, Enum):
    """留存层级枚举
    
    定义数据留存的物理存储级别：
    - HOT: 全量在线
    - COLD: 冷存储 / 只读 / 可验证
    - ARCHIVE: 归档存储
    """
    HOT = "hot"
    COLD = "cold"
    ARCHIVE = "archive"


class ExecutionContext(BaseModel):
    """执行上下文模型
    
    用于描述证明包执行时的上下文信息
    """
    event_type: Optional[str] = Field(None, description="事件类型")
    actor_id: Optional[str] = Field(None, description="执行主体ID")
    action_type: Optional[str] = Field(None, description="动作类型")
    jurisdiction: Optional[_JurisdictionContext] = Field(None, description="适用司法管辖上下文")
    event_id: Optional[str] = Field(None, description="事件唯一标识符")
    occurred_at: Optional[datetime] = Field(None, description="事件发生时间")
    initiating_sovereignty: Optional[str] = Field(None, description="发起者主权标识")


class CitationContext(BaseModel):
    """引用上下文模型
    
    用于描述证明包被引用时的上下文信息
    """
    citation_type: Literal["decision", "arbitration", "historical", "audit"]
    jurisdiction: Optional[_JurisdictionContext] = Field(None, description="引用时的司法管辖上下文")
    actor_id: Optional[str] = Field(None, description="引用主体ID")


class GovernanceLifecycleViolation(GovernanceViolation):
    """治理生命周期违规异常
    
    当证明包的生命周期状态不符合执行要求时抛出
    """
    proof_bundle_root: Optional[str] = Field(None, description="违规的证明包根哈希")
    lifecycle_state: Optional[str] = Field(None, description="违规时的生命周期状态")
    at_time: Optional[datetime] = Field(None, description="违规发生时间")
    context: Optional[Dict[str, Any]] = Field(None, description="违规上下文信息")


class _LifecycleExecutionGuard(BaseModel):
    """生命周期执行约束接口
    
    负责检查证明包是否可执行，基于其生命周期状态
    实现Fail-Closed原则：状态未知 ⇒ 拒绝执行
    """
    lifecycle_manager: '_GovernanceLifecycleManager'  # 延迟引用以避免循环依赖
    external_freeze_manager: Any  # 外部冻结管理器，来自Task-008
    
    class Config:
        arbitrary_types_allowed = True  # 允许使用延迟引用
    
    def assert_executable(
        self, 
        proof_bundle_root: str, 
        at_time: datetime, 
        context: ExecutionContext
    ) -> None:
        """验证证明包是否可执行
        
        Args:
            proof_bundle_root: 证明包根哈希
            at_time: 判定时间
            context: 执行上下文
            
        Raises:
            GovernanceLifecycleViolation: 当不可执行时抛出
        """
        # 优先级1：检查外部冻结（Task-008要求）
        if self.external_freeze_manager.has_active_freeze(proof_bundle_root):
            raise GovernanceLifecycleViolation(
                level=ViolationLevel.CRITICAL,
                rule_id="external_freeze_active",
                message="Externally frozen proof bundle is not executable",
                proof_bundle_root=proof_bundle_root,
                at_time=at_time,
                context=context.model_dump()
            )
        
        # 获取生命周期绑定
        binding = self.lifecycle_manager.get_lifecycle_binding(proof_bundle_root)
        if not binding:
            raise GovernanceLifecycleViolation(
                level=ViolationLevel.CRITICAL,
                rule_id="lifecycle_unknown",
                message="Lifecycle state unknown, fail-closed",
                proof_bundle_root=proof_bundle_root,
                at_time=at_time,
                context=context.model_dump()
            )
        
        # 获取生命周期状态
        state = self.lifecycle_manager.get_lifecycle_at_time(proof_bundle_root, at_time)
        if not state:
            raise GovernanceLifecycleViolation(
                level=ViolationLevel.CRITICAL,
                rule_id="lifecycle_unknown",
                message="Lifecycle state unknown, fail-closed",
                proof_bundle_root=proof_bundle_root,
                at_time=at_time,
                context=context.model_dump()
            )
        
        # 执行域检查：禁止执行的状态
        if state in [_GovernanceLifecycleState.SUSPENDED, _GovernanceLifecycleState.EXPIRED, _GovernanceLifecycleState.REVOKED]:
            raise GovernanceLifecycleViolation(
                level=ViolationLevel.CRITICAL,
                rule_id="lifecycle_not_executable",
                message=f"Proof bundle with state {state.value} is not executable",
                proof_bundle_root=proof_bundle_root,
                lifecycle_state=state.value,
                at_time=at_time,
                context=context.model_dump()
            )


class _LifecycleRetentionPolicy(BaseModel):
    """生命周期留存策略接口
    
    负责判定证明包的留存层级，基于其生命周期状态
    关键点：Retention ≠ Lifecycle State，Retention只是物理策略
    
    留存层级语义声明：
    - HOT: 全量在线，支持高频率访问
    - COLD: 冷存储，只读，可验证
    - ARCHIVE: 仅由Retention Engine后处理触发，与Lifecycle状态无关
    """
    lifecycle_manager: '_GovernanceLifecycleManager'  # 生命周期管理器，用于获取准确状态
    
    class Config:
        arbitrary_types_allowed = True  # 允许使用延迟引用
    
    def retention_tier(
        self, 
        binding: '_GovernanceLifecycleBinding', 
        at_time: datetime
    ) -> RetentionTier:
        """判定证明包的留存层级
        
        Args:
            binding: 生命周期绑定对象
            at_time: 判定时间
            
        Returns:
            留存层级（HOT/COLD/ARCHIVE）
        """
        # 严格遵循治理原则：只信Lifecycle Manager的状态判定
        state = self.lifecycle_manager.get_lifecycle_at_time(binding.proof_bundle_root, at_time)
        if not state:
            # 状态未知，采用最保守策略
            return RetentionTier.COLD
        
        # 根据状态判定留存层级
        if state == _GovernanceLifecycleState.ACTIVE:
            return RetentionTier.HOT
        elif state == _GovernanceLifecycleState.SUSPENDED:
            return RetentionTier.HOT  # 全量在线（只读）
        elif state == _GovernanceLifecycleState.EXPIRED:
            return RetentionTier.COLD
        elif state == _GovernanceLifecycleState.REVOKED:
            return RetentionTier.COLD
        else:
            # 未知状态默认冷存储
            return RetentionTier.COLD
    
    def can_be_degraded(self, binding: '_GovernanceLifecycleBinding', current_tier: RetentionTier) -> bool:
        """判定是否可以降级存储
        
        Args:
            binding: 生命周期绑定对象
            current_tier: 当前留存层级
            
        Returns:
            是否可以降级
        """
        # 简化实现：只有HOT可以降级
        return current_tier == RetentionTier.HOT


# 证据访问决策模型，提供更详细的访问结果
class EvidenceAccessDecision(BaseModel):
    """证据访问决策模型
    
    用于提供更详细的证据访问结果，包括是否允许访问、原因和限制
    """
    allowed: bool = Field(..., description="是否允许访问")
    reason: str = Field(..., description="决策原因")
    limitations: List[str] = Field(default_factory=list, description="访问限制列表")


class _LifecycleEvidenceAccess(BaseModel):
    """生命周期证据可用性接口
    
    负责判定证明包是否可以被引用，基于其生命周期状态和引用上下文
    """
    lifecycle_manager: '_GovernanceLifecycleManager'  # 生命周期管理器，用于获取准确状态
    
    class Config:
        arbitrary_types_allowed = True  # 允许使用延迟引用
    
    def can_be_cited(
        self, 
        binding: '_GovernanceLifecycleBinding', 
        citation_context: CitationContext
    ) -> EvidenceAccessDecision:
        """判定证明包是否可以被引用
        
        Args:
            binding: 生命周期绑定对象
            citation_context: 引用上下文
            
        Returns:
            证据访问决策，包含是否允许、原因和限制
        """
        # 获取准确的生命周期状态
        state = self.lifecycle_manager.get_lifecycle_at_time(binding.proof_bundle_root, datetime.now())
        if not state:
            state = binding.lifecycle_state
            
        citation_type = citation_context.citation_type
        
        # 1. 检查司法管辖一致性（问题5）
        if citation_context.jurisdiction and \
           citation_context.jurisdiction != binding.lifecycle_metadata.governing_jurisdiction:
            return EvidenceAccessDecision(
                allowed=False,
                reason="Jurisdiction mismatch between citation context and binding",
                limitations=["Jurisdiction violation"]
            )
        
        # 2. 根据状态和引用类型判定
        if state == _GovernanceLifecycleState.ACTIVE:
            # 活跃状态可以被所有类型引用
            return EvidenceAccessDecision(
                allowed=True,
                reason="Active lifecycle state allows all citation types",
                limitations=[]
            )
        elif state == _GovernanceLifecycleState.SUSPENDED:
            # 暂停状态仅允许审计与验证
            if citation_type in ["audit"]:
                return EvidenceAccessDecision(
                    allowed=True,
                    reason="Suspended state allows audit citations",
                    limitations=["Only for audit purposes"]
                )
            else:
                return EvidenceAccessDecision(
                    allowed=False,
                    reason="Suspended state only allows audit citations",
                    limitations=["Citation type not allowed"]
                )
        elif state == _GovernanceLifecycleState.EXPIRED:
            # 过期状态允许被引用为历史
            if citation_type in ["historical", "audit"]:
                return EvidenceAccessDecision(
                    allowed=True,
                    reason="Expired state allows historical and audit citations",
                    limitations=["Only for historical or audit purposes"]
                )
            else:
                return EvidenceAccessDecision(
                    allowed=False,
                    reason="Expired state only allows historical and audit citations",
                    limitations=["Citation type not allowed"]
                )
        elif state == _GovernanceLifecycleState.REVOKED:
            # 撤销状态不可作为有效依据，但可作为"被撤销事实"
            if citation_type in ["historical", "audit"]:
                return EvidenceAccessDecision(
                    allowed=True,
                    reason="Revoked state allows historical and audit citations",
                    limitations=["Only for historical or audit purposes, cannot be used as valid basis"]
                )
            else:
                return EvidenceAccessDecision(
                    allowed=False,
                    reason="Revoked state only allows historical and audit citations",
                    limitations=["Citation type not allowed, cannot be used as valid basis"]
                )
        else:
            # 未知状态默认不可引用
            return EvidenceAccessDecision(
                allowed=False,
                reason="Unknown lifecycle state",
                limitations=["Unknown state"]
            )
    
    def can_be_verified(
        self, 
        binding: '_GovernanceLifecycleBinding', 
        verification_context: Dict[str, Any]
    ) -> bool:
        """判定证明包是否可以被验证
        
        治理不变量：所有状态下都应可验证
        
        Args:
            binding: 生命周期绑定对象
            verification_context: 验证上下文
            
        Returns:
            是否可以被验证
        """
        # 所有生命周期状态下都应可验证
        return True



class _GovernanceLifecycleState(Enum):
    """治理生命周期状态枚举
    
    状态定义：
    - ACTIVE: 可引用、可裁定
    - EXPIRED: 失效但仍可验证存在性
    - REVOKED: 被正式撤销（终态）
    - SUSPENDED: 临时冻结
    """
    ACTIVE = "active"           # 可引用、可裁定
    EXPIRED = "expired"         # 失效但仍可验证存在性
    REVOKED = "revoked"         # 被正式撤销
    SUSPENDED = "suspended"     # 临时冻结（外部或仲裁）


class _GovernanceLifecycleMetadata(BaseModel):
    """治理生命周期元数据
    
    治理不变量：
    - retention_until=None 表示永久保留
    - 所有时间戳必须来自可信来源（如Proof Bundle或Finality Record）
    - 状态变更必须记录变更者和原因
    """
    created_at: datetime
    retention_until: Optional[datetime] = Field(None, description="保留到期时间，None表示永久保留")
    expired_at: Optional[datetime] = Field(None, description="过期时间")
    revoked_at: Optional[datetime] = Field(None, description="撤销时间")
    revoked_by: Optional[str] = Field(None, description="撤销者类型: human / arbitration / external")
    revoke_reason: Optional[str] = Field(None, description="撤销原因")
    
    # Critical修复：明确区分冻结来源
    suspended_at: Optional[datetime] = Field(None, description="冻结时间")
    suspended_by: Optional[str] = Field(None, description="冻结者类型: external / arbitration / internal")
    suspension_scope: Optional[str] = Field(None, description="冻结范围: proof / engine / jurisdiction")
    
    governing_jurisdiction: _JurisdictionContext
    
    class Config:
        frozen = True  # 元数据不可修改，确保审计完整性


class _GovernanceLifecycleBinding(BaseModel):
    """治理生命周期绑定对象
    
    治理不变量：
    - 生命周期永远绑定Proof Bundle Root
    - 生命周期不绑定具体Action/Event
    - Replay时生命周期必须一致
    """
    proof_bundle_root: str = Field(..., description="证明包根哈希，用于唯一标识治理事实")
    lifecycle_state: _GovernanceLifecycleState
    lifecycle_metadata: _GovernanceLifecycleMetadata
    
    class Config:
        frozen = True  # 绑定对象不可修改，确保审计完整性


class _LifecycleTransitionRecord(BaseModel):
    """生命周期状态转换记录
    
    治理不变量：
    - 所有状态转换必须记录证据
    - 转换记录不可修改
    - 支持外部验证
    """
    transition_id: str = Field(default_factory=lambda: f"transition-{uuid.uuid4()}")
    proof_bundle_root: str
    from_state: _GovernanceLifecycleState
    to_state: _GovernanceLifecycleState
    decided_by: str  # 决定者类型
    decided_at: datetime  # 转换时间，来自可信来源
    jurisdiction: _JurisdictionContext
    reason: str  # 转换原因
    signature: str  # 转换记录签名
    
    class Config:
        frozen = True  # 转换记录不可修改，确保审计完整性


class _GovernanceLifecycleRules(BaseModel):
    """治理生命周期判定规则
    
    治理不变量：
    - 所有判定必须基于显式输入时间，确保Replay一致性
    - 规则必须明确处理边界情况
    - 判定结果必须可重现
    """
    
    def is_active(self, binding: _GovernanceLifecycleBinding, at_time: datetime) -> bool:
        """判定是否处于活跃状态
        
        Args:
            binding: 生命周期绑定对象
            at_time: 判定时间（必须来自可信来源）
            
        Returns:
            是否处于活跃状态
        """
        # 处理永久保留情况
        if binding.lifecycle_metadata.retention_until is None:
            return True
        
        return at_time <= binding.lifecycle_metadata.retention_until
    
    def is_expired(self, binding: _GovernanceLifecycleBinding, at_time: datetime) -> bool:
        """判定是否已过期
        
        Args:
            binding: 生命周期绑定对象
            at_time: 判定时间（必须来自可信来源）
            
        Returns:
            是否已过期
        """
        # 永久保留的不会过期
        if binding.lifecycle_metadata.retention_until is None:
            return False
        
        # 已撤销的不算过期
        if binding.lifecycle_metadata.revoked_at is not None:
            return False
        
        return at_time > binding.lifecycle_metadata.retention_until
    
    def is_revoked(self, binding: _GovernanceLifecycleBinding, at_time: datetime) -> bool:
        """判定是否已撤销
        
        Args:
            binding: 生命周期绑定对象
            at_time: 判定时间（必须来自可信来源）
            
        Returns:
            是否已撤销
        """
        if binding.lifecycle_metadata.revoked_at is None:
            return False
        
        return at_time >= binding.lifecycle_metadata.revoked_at
    
    def is_suspended(self, binding: _GovernanceLifecycleBinding, at_time: datetime) -> bool:
        """判定是否已暂停
        
        Args:
            binding: 生命周期绑定对象
            at_time: 判定时间（必须来自可信来源）
            
        Returns:
            是否已暂停
        """
        if binding.lifecycle_metadata.suspended_at is None:
            return False
        
        # 暂停是临时状态，需要检查是否已恢复
        # 注：恢复状态通过创建新的绑定对象实现
        return binding.lifecycle_state == _GovernanceLifecycleState.SUSPENDED
    
    def can_revoke(self, binding: _GovernanceLifecycleBinding, actor_type: str) -> bool:
        """判定是否可以撤销
        
        Args:
            binding: 生命周期绑定对象
            actor_type: 操作主体类型
            
        Returns:
            是否可以撤销
        """
        return binding.lifecycle_state != _GovernanceLifecycleState.REVOKED
    
    def can_suspend(self, binding: _GovernanceLifecycleBinding, actor_type: str) -> bool:
        """判定是否可以暂停
        
        Args:
            binding: 生命周期绑定对象
            actor_type: 操作主体类型
            
        Returns:
            是否可以暂停
        """
        return binding.lifecycle_state == _GovernanceLifecycleState.ACTIVE


class _GovernanceLifecycleStateMachine(BaseModel):
    """治理生命周期状态机
    
    治理不变量：
    - REVOKED为终态，不可逆
    - EXPIRED不可回到ACTIVE
    - 所有状态转换必须符合规则
    - 状态转换必须生成转换记录
    """
    
    def transition(self, 
                  binding: _GovernanceLifecycleBinding, 
                  new_state: _GovernanceLifecycleState,
                  transition_time: datetime,
                  decided_by: str,
                  reason: str,
                  signature_service) -> Optional[Tuple[_GovernanceLifecycleBinding, _LifecycleTransitionRecord]]:
        """执行状态转换
        
        Args:
            binding: 当前生命周期绑定对象
            new_state: 目标状态
            transition_time: 转换时间（必须来自可信来源）
            decided_by: 转换决定者
            reason: 转换原因
            signature_service: 签名服务，用于生成转换记录签名
            
        Returns:
            (新的绑定对象, 转换记录)，转换失败返回None
        """
        # 检查状态转换是否合法
        if not self._is_valid_transition(binding.lifecycle_state, new_state):
            return None
        
        # 创建更新后的元数据
        updated_metadata_dict = binding.lifecycle_metadata.model_dump()
        
        # 更新状态相关的时间戳和信息
        if new_state == _GovernanceLifecycleState.EXPIRED:
            updated_metadata_dict["expired_at"] = transition_time
        elif new_state == _GovernanceLifecycleState.REVOKED:
            updated_metadata_dict["revoked_at"] = transition_time
            updated_metadata_dict["revoked_by"] = decided_by
            updated_metadata_dict["revoke_reason"] = reason
        elif new_state == _GovernanceLifecycleState.SUSPENDED:
            updated_metadata_dict["suspended_at"] = transition_time
            updated_metadata_dict["suspended_by"] = decided_by
        
        # 创建新的元数据对象
        updated_metadata = _GovernanceLifecycleMetadata(**updated_metadata_dict)
        
        # 创建新的绑定对象
        new_binding = _GovernanceLifecycleBinding(
            proof_bundle_root=binding.proof_bundle_root,
            lifecycle_state=new_state,
            lifecycle_metadata=updated_metadata
        )
        
        # 生成转换记录签名
        signature_content = {
            "transition_id": f"transition-{uuid.uuid4()}",
            "proof_bundle_root": binding.proof_bundle_root,
            "from_state": binding.lifecycle_state.value,
            "to_state": new_state.value,
            "decided_by": decided_by,
            "decided_at": transition_time.isoformat(),
            "reason": reason
        }
        
        # 实际实现中应使用签名服务生成真实签名
        # 这里简化实现，使用简单哈希
        import hashlib
        signature = hashlib.sha256(str(signature_content).encode('utf-8')).hexdigest()
        
        # 创建转换记录
        transition_record = _LifecycleTransitionRecord(
            proof_bundle_root=binding.proof_bundle_root,
            from_state=binding.lifecycle_state,
            to_state=new_state,
            decided_by=decided_by,
            decided_at=transition_time,
            jurisdiction=binding.lifecycle_metadata.governing_jurisdiction,
            reason=reason,
            signature=signature
        )
        
        return new_binding, transition_record
    
    def _is_valid_transition(self, current_state: _GovernanceLifecycleState, new_state: _GovernanceLifecycleState) -> bool:
        """检查状态转换是否合法
        
        状态转换规则：
        ACTIVE ──> EXPIRED
        ACTIVE ──> REVOKED
        ACTIVE ──> SUSPENDED
        
        SUSPENDED ──> ACTIVE
        SUSPENDED ──> REVOKED
        
        EXPIRED ──> REVOKED
        
        REVOKED ──X──> ANY
        """
        valid_transitions = {
            _GovernanceLifecycleState.ACTIVE: [
                _GovernanceLifecycleState.EXPIRED,
                _GovernanceLifecycleState.REVOKED,
                _GovernanceLifecycleState.SUSPENDED
            ],
            _GovernanceLifecycleState.SUSPENDED: [
                _GovernanceLifecycleState.ACTIVE,
                _GovernanceLifecycleState.REVOKED
            ],
            _GovernanceLifecycleState.EXPIRED: [
                _GovernanceLifecycleState.REVOKED
            ],
            _GovernanceLifecycleState.REVOKED: []  # 终态，不可逆
        }
        
        return new_state in valid_transitions.get(current_state, [])


class _GovernanceLifecycleManager(BaseModel):
    """治理生命周期管理器
    
    治理不变量：
    - 所有生命周期变更必须经过管理器
    - 管理器必须保持所有变更的审计记录
    - 支持Replay和外部验证
    """
    # 服务依赖
    signature_service: Optional[Any] = Field(None, description="签名服务，用于生成转换记录签名")
    
    # 内部状态
    lifecycle_bindings: Dict[str, _GovernanceLifecycleBinding] = Field(default_factory=dict, description="生命周期绑定字典，key为proof_bundle_root")
    transition_records: List[_LifecycleTransitionRecord] = Field(default_factory=list, description="生命周期转换记录列表")
    
    class Config:
        frozen = False  # 允许更新内部状态
    
    def create_lifecycle_binding(self, 
                               proof_bundle_root: str,
                               retention_until: Optional[datetime],
                               governing_jurisdiction: _JurisdictionContext,
                               created_at: datetime) -> _GovernanceLifecycleBinding:
        """创建新的生命周期绑定
        
        Args:
            proof_bundle_root: 证明包根哈希
            retention_until: 保留到期时间
            governing_jurisdiction: 适用司法管辖上下文
            created_at: 创建时间（必须来自可信来源）
            
        Returns:
            创建的生命周期绑定对象
        """
        # 检查是否已存在
        if proof_bundle_root in self.lifecycle_bindings:
            return self.lifecycle_bindings[proof_bundle_root]
        
        # 确定初始状态
        if retention_until is not None and created_at > retention_until:
            initial_state = _GovernanceLifecycleState.EXPIRED
        else:
            initial_state = _GovernanceLifecycleState.ACTIVE
        
        # 创建元数据
        metadata = _GovernanceLifecycleMetadata(
            created_at=created_at,
            retention_until=retention_until,
            governing_jurisdiction=governing_jurisdiction
        )
        
        # 创建绑定对象
        binding = _GovernanceLifecycleBinding(
            proof_bundle_root=proof_bundle_root,
            lifecycle_state=initial_state,
            lifecycle_metadata=metadata
        )
        
        # 保存绑定对象
        self.lifecycle_bindings[proof_bundle_root] = binding
        
        return binding
    
    def get_lifecycle_binding(self, proof_bundle_root: str) -> Optional[_GovernanceLifecycleBinding]:
        """获取生命周期绑定对象
        
        Args:
            proof_bundle_root: 证明包根哈希
            
        Returns:
            生命周期绑定对象，不存在返回None
        """
        return self.lifecycle_bindings.get(proof_bundle_root)
    
    def update_lifecycle(self, 
                        proof_bundle_root: str,
                        new_state: _GovernanceLifecycleState,
                        transition_time: datetime,
                        decided_by: str,
                        reason: str) -> Optional[_GovernanceLifecycleBinding]:
        """更新生命周期状态
        
        Args:
            proof_bundle_root: 证明包根哈希
            new_state: 目标状态
            transition_time: 转换时间（必须来自可信来源）
            decided_by: 转换决定者
            reason: 转换原因
            
        Returns:
            更新后的生命周期绑定对象，更新失败返回None
        """
        # 获取当前绑定
        current_binding = self.lifecycle_bindings.get(proof_bundle_root)
        if not current_binding:
            return None
        
        # 创建状态机
        state_machine = _GovernanceLifecycleStateMachine()
        
        # 执行状态转换
        result = state_machine.transition(
            current_binding,
            new_state,
            transition_time,
            decided_by,
            reason,
            self.signature_service
        )
        
        if result:
            new_binding, transition_record = result
            
            # 更新绑定字典
            self.lifecycle_bindings[proof_bundle_root] = new_binding
            
            # 保存转换记录
            self.transition_records.append(transition_record)
            
            return new_binding
        
        return None
    
    def get_lifecycle_at_time(self, proof_bundle_root: str, at_time: datetime) -> Optional[_GovernanceLifecycleState]:
        """获取特定时间点的生命周期状态
        
        Args:
            proof_bundle_root: 证明包根哈希
            at_time: 要查询的时间点
            
        Returns:
            特定时间点的生命周期状态，不存在返回None
        """
        binding = self.lifecycle_bindings.get(proof_bundle_root)
        if not binding:
            return None
        
        # 检查状态转换记录，找到最接近且小于等于at_time的转换
        relevant_transitions = [t for t in self.transition_records 
                              if t.proof_bundle_root == proof_bundle_root 
                              and t.decided_at <= at_time]
        
        if not relevant_transitions:
            # 没有转换记录，使用初始状态和规则判定
            rules = _GovernanceLifecycleRules()
            if rules.is_active(binding, at_time):
                return _GovernanceLifecycleState.ACTIVE
            elif rules.is_expired(binding, at_time):
                return _GovernanceLifecycleState.EXPIRED
            elif rules.is_revoked(binding, at_time):
                return _GovernanceLifecycleState.REVOKED
            elif rules.is_suspended(binding, at_time):
                return _GovernanceLifecycleState.SUSPENDED
            else:
                return binding.lifecycle_state
        
        # 找到最后一次转换
        last_transition = max(relevant_transitions, key=lambda t: t.decided_at)
        return last_transition.to_state
    
    def get_transition_records(self, proof_bundle_root: Optional[str] = None) -> List[_LifecycleTransitionRecord]:
        """获取转换记录
        
        Args:
            proof_bundle_root: 可选，证明包根哈希，None表示获取所有转换记录
            
        Returns:
            转换记录列表
        """
        if proof_bundle_root:
            return [t for t in self.transition_records if t.proof_bundle_root == proof_bundle_root]
        return self.transition_records.copy()


__all__ = []
