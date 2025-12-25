"""
Governance Lifecycle Phase-3 - Execution / Retention / Storage Boundary Design

This module implements the Phase-3 components for Task-010, focusing on:
1. Lifecycle Execution Guard (Execution Domain)
2. Lifecycle Retention Policy (Retention / Cleanup Domain)
3. Lifecycle Evidence Access (Storage & Evidence Domain)

Governance Invariants:
- Lifecycle never affects Proof existence
- Execution domain checks happen at Governance Engine Single Gate
- Fail-Closed: Unknown state ⇒ Reject execution
- External Freeze has priority over Lifecycle
- Lifecycle does not modify any Hash / Anchor / Finality
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal, Any
from pydantic import BaseModel, Field

from .governance_lifecycle_models import (
    _GovernanceLifecycleBinding,
    _GovernanceLifecycleState
)
from .jurisdiction_models import _JurisdictionContext
from .violation import _GovernanceViolation as GovernanceViolation, _ViolationLevel as ViolationLevel, _ViolationStatus as ViolationStatus


class RetentionTier(str, Enum):
    """留存层级枚举
    
    治理语义：
    - HOT: 全量在线
    - COLD: 冷存储 / 只读 / 可验证
    - ARCHIVE: 归档存储（仅由Retention Engine后处理触发，与Lifecycle无关）
    """
    HOT = "hot"
    COLD = "cold"
    ARCHIVE = "archive"


class ExecutionContext(BaseModel):
    """执行上下文（最小标准化）
    
    治理原则：
    - 包含审计所需的最小信息
    - 不可修改，确保审计完整性
    """
    event_id: str = Field(..., description="事件ID")
    event_type: str = Field(..., description="事件类型")
    occurred_at: datetime = Field(..., description="事件发生时间")
    initiating_sovereignty: str = Field(..., description="发起主权")
    
    class Config:
        frozen = True  # 执行上下文不可修改


class EvidenceAccessDecision(BaseModel):
    """证据访问决策（替代简单bool返回值）
    
    治理原则：
    - 提供详细的决策理由
    - 明确访问限制
    - 支持仲裁和审计需求
    """
    allowed: bool = Field(..., description="是否允许访问")
    reason: str = Field(..., description="决策理由")
    limitations: List[str] = Field(default_factory=list, description="访问限制")
    
    class Config:
        frozen = True  # 决策结果不可修改


class CitationContext(BaseModel):
    """引用上下文
    
    治理原则：
    - 包含引用所需的完整上下文
    - 支持司法管辖一致性检查
    """
    citation_type: Literal["decision", "arbitration", "historical", "audit"] = Field(..., description="引用类型")
    jurisdiction: Optional[_JurisdictionContext] = Field(None, description="引用方司法管辖")
    citation_purpose: str = Field(..., description="引用目的")
    
    class Config:
        frozen = True  # 引用上下文不可修改


class GovernanceLifecycleViolation(Exception):
    """治理生命周期违规异常
    
    治理原则：
    - 包含完整证据
    - 明确违规规则ID
    - 支持审计和仲裁需求
    """
    def __init__(self, level, rule_id, message, proof_bundle_root, at_time, lifecycle_state=None, event_id="", actor_id=""):
        self.level = level
        self.rule_id = rule_id
        self.message = message
        self.proof_bundle_root = proof_bundle_root
        self.at_time = at_time
        self.lifecycle_state = lifecycle_state
        self.event_id = event_id
        self.actor_id = actor_id
        super().__init__(self.message)
    
    def model_dump(self):
        """将异常转换为字典，用于序列化"""
        return {
            "level": self.level.value if hasattr(self.level, "value") else self.level,
            "rule_id": self.rule_id,
            "message": self.message,
            "proof_bundle_root": self.proof_bundle_root,
            "at_time": self.at_time.isoformat(),
            "lifecycle_state": self.lifecycle_state,
            "event_id": self.event_id,
            "actor_id": self.actor_id
        }


class _LifecycleExecutionGuard(BaseModel):
    """生命周期执行约束接口（执行域）
    
    治理原则：
    - 只做判定 + fail-closed
    - 不直接操作生命周期对象
    - 外部冻结优先于生命周期
    - 仅关注是否能"执行动作 / 驱动系统"
    """
    # 服务依赖（必须由GovernanceEngine注入）
    lifecycle_manager: Any = Field(..., description="生命周期管理器")
    external_freeze_manager: Any = Field(..., description="外部冻结管理器")
    
    def assert_executable(
        self, 
        proof_bundle_root: str, 
        at_time: datetime, 
        context: ExecutionContext
    ) -> None:
        """验证证明包是否可执行
        
        优先级顺序：
        1. External Freeze (Task-008)
        2. Lifecycle State
        3. Action Permission
        
        Args:
            proof_bundle_root: 证明包根哈希
            at_time: 判定时间（必须来自事件时间线，确保Replay一致性）
            context: 执行上下文
            
        Raises:
            GovernanceLifecycleViolation: 当不可执行时抛出，包含完整证据
        """
        # 1. 外部冻结检查（Task-008：外部冻结优先于生命周期）
        if self.external_freeze_manager.has_active_freeze(proof_bundle_root):
            raise GovernanceLifecycleViolation(
                level=ViolationLevel.CRITICAL,
                rule_id="external_freeze_active",
                message="Externally frozen proof bundle is not executable",
                proof_bundle_root=proof_bundle_root,
                at_time=at_time
            )
        
        # 2. 获取生命周期绑定
        binding = self.lifecycle_manager.get_lifecycle_binding(proof_bundle_root)
        if not binding:
            raise GovernanceLifecycleViolation(
                level=ViolationLevel.CRITICAL,
                rule_id="lifecycle_unknown",
                message="Lifecycle state unknown, fail-closed",
                proof_bundle_root=proof_bundle_root,
                at_time=at_time
            )
        
        # 3. 获取生命周期状态（使用Lifecycle Manager确保一致性）
        state = self.lifecycle_manager.get_lifecycle_at_time(proof_bundle_root, at_time)
        
        # 4. 执行域检查（仅关注是否能执行动作/驱动系统）
        if state in [
            _GovernanceLifecycleState.SUSPENDED, 
            _GovernanceLifecycleState.EXPIRED, 
            _GovernanceLifecycleState.REVOKED
        ]:
            raise GovernanceLifecycleViolation(
                level=ViolationLevel.CRITICAL,
                rule_id="lifecycle_not_executable",
                message=f"Proof bundle with state {state.value} is not executable",
                proof_bundle_root=proof_bundle_root,
                lifecycle_state=state.value,
                at_time=at_time
            )


class _LifecycleRetentionPolicy(BaseModel):
    """生命周期留存策略接口（留存与清理域）
    
    治理原则：
    - Retention ≠ Lifecycle State
    - Retention is just physical policy, not governance semantics
    - No deletion, only accessibility and availability control
    """
    # 服务依赖（必须由GovernanceEngine注入）
    lifecycle_manager: Any = Field(..., description="生命周期管理器")
    
    def retention_tier(
        self, 
        binding: _GovernanceLifecycleBinding, 
        at_time: datetime
    ) -> RetentionTier:
        """判定留存层级
        
        Args:
            binding: 生命周期绑定
            at_time: 判定时间
            
        Returns:
            留存层级
            
        治理原则：
        - 不自己计算状态，只依赖Lifecycle Manager
        - 确保与Execution Domain判定一致
        - 清理 ≠ 删除
        """
        # 使用Lifecycle Manager获取状态，确保一致性
        state = self.lifecycle_manager.get_lifecycle_at_time(
            binding.proof_bundle_root, 
            at_time
        )
        
        # 根据状态判定留存层级
        if state == _GovernanceLifecycleState.ACTIVE:
            return RetentionTier.HOT
        elif state == _GovernanceLifecycleState.SUSPENDED:
            return RetentionTier.HOT  # 全量在线（只读）
        elif state in [
            _GovernanceLifecycleState.EXPIRED, 
            _GovernanceLifecycleState.REVOKED
        ]:
            return RetentionTier.COLD
        else:
            # 未知状态默认冷存储
            return RetentionTier.COLD


class _LifecycleEvidenceAccess(BaseModel):
    """生命周期证据可用性接口（存储与证据域）
    
    治理原则：
    - Lifecycle does not modify any Hash / Anchor / Finality
    - All state changes generate new governance evidence
    - Cold storage data must still be verifiable
    """
    
    def can_be_cited(
        self, 
        binding: _GovernanceLifecycleBinding, 
        citation_context: CitationContext
    ) -> EvidenceAccessDecision:
        """判定证据是否可被引用
        
        Args:
            binding: 生命周期绑定
            citation_context: 引用上下文
            
        Returns:
            证据访问决策，包含详细信息
            
        治理原则：
        - 司法管辖一致性检查
        - 根据状态和引用类型判定
        - EXPIRED: 可历史引用
        - REVOKED: 不可作为有效依据，但可作为"被撤销事实"
        """
        state = binding.lifecycle_state
        citation_type = citation_context.citation_type
        
        # 1. 司法管辖一致性检查
        if citation_context.jurisdiction and \
           citation_context.jurisdiction != binding.lifecycle_metadata.governing_jurisdiction:
            return EvidenceAccessDecision(
                allowed=False,
                reason="Jurisdiction mismatch between citation context and binding",
                limitations=["Cross-jurisdiction citation not allowed"]
            )
        
        # 2. 根据状态和引用类型判定
        if state == _GovernanceLifecycleState.ACTIVE:
            return EvidenceAccessDecision(
                allowed=True,
                reason=f"Proof bundle with state {state.value} is fully accessible"
            )
        elif state == _GovernanceLifecycleState.SUSPENDED:
            # 仅允许审计与验证
            if citation_type == "audit":
                return EvidenceAccessDecision(
                    allowed=True,
                    reason=f"Proof bundle with state {state.value} is only accessible for audit",
                    limitations=["Only for audit purposes"]
                )
            return EvidenceAccessDecision(
                allowed=False,
                reason=f"Proof bundle with state {state.value} is only accessible for audit",
                limitations=["Only for audit purposes"]
            )
        elif state == _GovernanceLifecycleState.EXPIRED:
            # 允许被引用为历史
            if citation_type in ["historical", "audit"]:
                return EvidenceAccessDecision(
                    allowed=True,
                    reason=f"Proof bundle with state {state.value} is accessible for historical reference",
                    limitations=["Only as historical evidence"]
                )
            return EvidenceAccessDecision(
                allowed=False,
                reason=f"Proof bundle with state {state.value} is only accessible for historical reference",
                limitations=["Only for historical or audit purposes"]
            )
        elif state == _GovernanceLifecycleState.REVOKED:
            # 不可作为有效依据，但可作为"被撤销事实"
            if citation_type in ["historical", "audit"]:
                return EvidenceAccessDecision(
                    allowed=True,
                    reason=f"Proof bundle with state {state.value} is accessible as revoked evidence",
                    limitations=["Only as revoked evidence, not valid basis"]
                )
            return EvidenceAccessDecision(
                allowed=False,
                reason=f"Proof bundle with state {state.value} is only accessible as revoked evidence",
                limitations=["Only for historical or audit purposes"]
            )
        else:
            return EvidenceAccessDecision(
                allowed=False,
                reason=f"Unknown lifecycle state {state.value}",
                limitations=["Access denied"]
            )


__all__ = []
