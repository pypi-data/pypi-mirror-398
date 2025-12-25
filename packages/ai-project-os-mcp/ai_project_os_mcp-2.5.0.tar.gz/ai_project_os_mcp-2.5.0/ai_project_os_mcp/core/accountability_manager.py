"""
Accountability Manager - Manages responsibility chains and accountability tracking

This module implements the core accountability logic ensuring every governance outcome
can answer: "Who is responsible, under what sovereign conditions, for what consequences?"
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

from .accountability_models import (
    _ResponsibilityLink,
    _ResponsibilityResolution,
    _ApprovalRecord,
    _OverrideAction,
    _AccountabilityAuditView,
    _ResponsibilityTransfer,
    _AccountabilitySummary
)
from .events import _EventType, _GovernanceEvent, _Actor
from .human_sovereignty_models import (
    _SovereigntyMode as SovereigntyMode,
    _HumanIntervention as HumanIntervention,
    _SovereigntySwitch as SovereigntySwitch
)
from .arbitration_models import (
    _ArbitrationCase as ArbitrationCase,
    _ArbitrationResolution as ArbitrationResolution
)

# Agent Governance Integration
from .agent_models import _AgentProposal, _AgentConflict, _GovernanceAgent

# Governance Proof Integration
from .governance_proof_models import _GovernanceProof, _GovernanceProofBundle, _GovernanceProofVerificationResult
from .governance_attestation import _GovernanceAttestation


class _AccountabilityManager(BaseModel):
    """责任链管理器
    
    负责管理责任链、处理责任转移、生成责任解析结果
    确保责任链是append-only的，只能被取代，不能删除
    """
    
    # Internal state - Using Pydantic v2 syntax
    responsibility_chains: Dict[str, List[_ResponsibilityLink]] = Field(default_factory=dict, repr=False)
    approval_records: Dict[str, List[_ApprovalRecord]] = Field(default_factory=dict, repr=False)
    override_actions: Dict[str, List[_OverrideAction]] = Field(default_factory=dict, repr=False)
    responsibility_transfers: Dict[str, List[_ResponsibilityTransfer]] = Field(default_factory=dict, repr=False)
    event_responsibility_map: Dict[str, str] = Field(default_factory=dict, repr=False)
    
    # Governance Proof Integration - Responsibility & Proof Fusion
    proof_responsibility_map: Dict[str, str] = Field(default_factory=dict, repr=False)  # proof_id -> event_id
    responsibility_proof_map: Dict[str, List[str]] = Field(default_factory=dict, repr=False)  # event_id -> proof_ids
    attestation_responsibility_map: Dict[str, str] = Field(default_factory=dict, repr=False)  # attestation_id -> event_id
    
    # Sovereignty-related state
    event_sovereignty_map: Dict[str, SovereigntyMode] = Field(default_factory=dict, repr=False)
    human_interventions: Dict[str, List[HumanIntervention]] = Field(default_factory=dict, repr=False)
    sovereignty_switches: Dict[str, List[SovereigntySwitch]] = Field(default_factory=dict, repr=False)
    arbitration_cases: Dict[str, ArbitrationCase] = Field(default_factory=dict, repr=False)
    
    class Config:
        pass
    
    def create_responsibility_link(
        self,
        event_id: str,
        actor_id: str,
        role: str,
        stage: str,
        action_type: str,
        sovereignty_context: Dict[str, Any],
        reason: str
    ) -> _ResponsibilityLink:
        """创建责任链链接
        
        Args:
            event_id: 事件ID
            actor_id: 责任人ID
            role: 责任角色
            stage: 责任阶段
            action_type: 责任动作类型
            sovereignty_context: 主权上下文
            reason: 责任原因
            
        Returns:
            创建的责任链链接
        """
        # Create new responsibility link
        link = _ResponsibilityLink(
            actor_id=actor_id,
            role=role,
            stage=stage,
            action_type=action_type,
            sovereignty_context=sovereignty_context,
            reason=reason
        )
        
        # Ensure event chain exists
        if event_id not in self.responsibility_chains:
            self.responsibility_chains[event_id] = []
            self.event_responsibility_map[event_id] = event_id
        
        # Add to chain (append-only)
        self.responsibility_chains[event_id].append(link)
        
        return link
    
    def transfer_responsibility(
        self,
        event_id: str,
        from_actor_id: str,
        to_actor_id: str,
        reason: str,
        sovereignty_context: Dict[str, Any]
    ) -> List[_ResponsibilityLink]:
        """转移责任
        
        Args:
            event_id: 事件ID
            from_actor_id: 原责任人ID
            to_actor_id: 新责任人ID
            reason: 转移原因
            sovereignty_context: 主权上下文
            
        Returns:
            新创建的责任链链接列表
        """
        # Get current chain
        if event_id not in self.responsibility_chains:
            raise ValueError(f"Event {event_id} does not exist in responsibility chains")
        
        current_chain = self.responsibility_chains[event_id]
        
        # Create transfer record
        transfer = _ResponsibilityTransfer(
            from_actor_id=from_actor_id,
            to_actor_id=to_actor_id,
            reason=reason,
            sovereignty_context=sovereignty_context
        )
        
        # Ensure transfer list exists
        if event_id not in self.responsibility_transfers:
            self.responsibility_transfers[event_id] = []
        
        self.responsibility_transfers[event_id].append(transfer)
        
        # Get last link to supersede
        last_link = current_chain[-1] if current_chain else None
        
        # Create new responsibility link for the new actor
        new_link = _ResponsibilityLink(
            actor_id=to_actor_id,
            role="TRANSFERRED",
            stage="RESPONSIBILITY_TRANSFER",
            action_type="RESPONSIBILITY_TAKEOVER",
            sovereignty_context=sovereignty_context,
            reason=reason
        )
        
        # Add new link to chain
        current_chain.append(new_link)
        
        # If there was a last link, mark it as superseded
        if last_link:
            # Create a superseded version of the last link
            superseded_link = last_link.copy(
                update={
                    "is_superseded": True,
                    "superseded_by": new_link.link_id
                }
            )
            
            # Replace the last link with the superseded version
            # This maintains immutability while updating the chain
            current_chain[-2] = superseded_link
        
        return [new_link] + ([superseded_link] if last_link else [])
    
    def record_approval(
        self,
        event_id: str,
        approver_id: str,
        approver_role: str,
        target_id: str,
        target_type: str,
        decision: bool,
        reason: str,
        sovereignty_context: Dict[str, Any],
        responsibility_takeover: bool = True
    ) -> _ApprovalRecord:
        """记录审批
        
        Args:
            event_id: 事件ID
            approver_id: 审批人ID
            approver_role: 审批人角色
            target_id: 审批目标ID
            target_type: 审批目标类型
            decision: 审批决策
            reason: 审批原因
            sovereignty_context: 主权上下文
            responsibility_takeover: 是否接管责任
            
        Returns:
            创建的审批记录
        """
        # Create approval record
        approval = _ApprovalRecord(
            event_id=event_id,
            approver_id=approver_id,
            approver_role=approver_role,
            target_id=target_id,
            target_type=target_type,
            decision=decision,
            reason=reason,
            sovereignty_context=sovereignty_context,
            responsibility_takeover=responsibility_takeover
        )
        
        # Ensure approval list exists
        if event_id not in self.approval_records:
            self.approval_records[event_id] = []
        
        self.approval_records[event_id].append(approval)
        
        # If responsibility takeover is true, create a new responsibility link
        if responsibility_takeover:
            link = self.create_responsibility_link(
                event_id=event_id,
                actor_id=approver_id,
                role=approver_role,
                stage="APPROVAL",
                action_type="RESPONSIBILITY_TAKEOVER",
                sovereignty_context=sovereignty_context,
                reason=reason
            )
            
            # Update approval record with responsibility link ID
            # Create a new approval record with the link ID since they're immutable
            approval = approval.copy(
                update={"responsibility_link_id": link.link_id}
            )
            self.approval_records[event_id][-1] = approval
        
        return approval
    
    def record_override(
        self,
        event_id: str,
        actor_id: str,
        actor_role: str,
        original_decision: Dict[str, Any],
        override_decision: Dict[str, Any],
        reason: str,
        sovereignty_context: Dict[str, Any],
        responsibility_takeover: bool = True
    ) -> _OverrideAction:
        """记录覆盖操作
        
        Args:
            event_id: 事件ID
            actor_id: 覆盖人ID
            actor_role: 覆盖人角色
            original_decision: 原始决策
            override_decision: 覆盖后决策
            reason: 覆盖原因
            sovereignty_context: 主权上下文
            responsibility_takeover: 是否接管责任
            
        Returns:
            创建的覆盖操作记录
        """
        # Create override action
        override = _OverrideAction(
            event_id=event_id,
            actor_id=actor_id,
            actor_role=actor_role,
            original_decision=original_decision,
            override_decision=override_decision,
            reason=reason,
            sovereignty_context=sovereignty_context,
            responsibility_takeover=responsibility_takeover
        )
        
        # Ensure override list exists
        if event_id not in self.override_actions:
            self.override_actions[event_id] = []
        
        self.override_actions[event_id].append(override)
        
        # Get current chain to find links to supersede
        superseded_link_ids = []
        if event_id in self.responsibility_chains:
            current_chain = self.responsibility_chains[event_id]
            # Mark all non-superseded links as superseded
            for i, link in enumerate(current_chain):
                if not link.is_superseded:
                    superseded_link_ids.append(link.link_id)
                    # Create superseded version
                    superseded_link = link.copy(
                        update={
                            "is_superseded": True,
                            "superseded_by": override.override_id
                        }
                    )
                    current_chain[i] = superseded_link
        
        # If responsibility takeover is true, create a new responsibility link
        if responsibility_takeover:
            link = self.create_responsibility_link(
                event_id=event_id,
                actor_id=actor_id,
                role=actor_role,
                stage="OVERRIDE",
                action_type="RESPONSIBILITY_TAKEOVER",
                sovereignty_context=sovereignty_context,
                reason=reason
            )
            
            # Update override record with responsibility link ID and superseded links
            override = override.copy(
                update={
                    "responsibility_link_id": link.link_id,
                    "supersedes": superseded_link_ids
                }
            )
            self.override_actions[event_id][-1] = override
        
        return override
    
    def generate_responsibility_resolution(
        self,
        event_id: str,
        primary_owner: Optional[str] = None,
        primary_role: Optional[str] = None
    ) -> _ResponsibilityResolution:
        """生成责任解析结果
        
        Args:
            event_id: 事件ID
            primary_owner: 主要责任人（可选，默认从责任链推导）
            primary_role: 主要责任角色（可选，默认从责任链推导）
            
        Returns:
            生成的责任解析结果
        """
        # Get responsibility chain
        if event_id not in self.responsibility_chains:
            raise ValueError(f"Event {event_id} does not exist in responsibility chains")
        
        chain = self.responsibility_chains[event_id]
        
        # Determine primary owner and role if not provided
        if not primary_owner or not primary_role:
            # Get the last non-superseded link in the chain
            active_links = [link for link in chain if not link.is_superseded]
            if active_links:
                last_link = active_links[-1]
                primary_owner = primary_owner or last_link.actor_id
                primary_role = primary_role or last_link.role
            else:
                # If no active links, use the first link
                if chain:
                    first_link = chain[0]
                    primary_owner = primary_owner or first_link.actor_id
                    primary_role = primary_role or first_link.role
                else:
                    raise ValueError(f"No responsibility links found for event {event_id}")
        
        # Collect all contributing owners (everyone in the chain except superseded ones)
        contributing_owners = set()
        contributing_roles = set()
        liability_type = "direct"
        
        for link in chain:
            if not link.is_superseded:
                contributing_owners.add(link.actor_id)
                contributing_roles.add(link.role)
            
            # Determine liability type based on action type
            if link.action_type in ["OVERRIDE", "RESPONSIBILITY_TAKEOVER"]:
                liability_type = "overridden"
            elif link.action_type in ["APPROVAL"]:
                liability_type = "shared"
            elif link.action_type in ["RESPONSIBILITY_DELEGATE"]:
                liability_type = "delegated"
        
        # Remove primary owner from contributing owners
        contributing_owners.discard(primary_owner)
        contributing_roles.discard(primary_role)
        
        return _ResponsibilityResolution(
            primary_owner=primary_owner,
            primary_role=primary_role,
            contributing_owners=list(contributing_owners),
            contributing_roles=list(contributing_roles),
            liability_type=liability_type,
            resolution_reason=f"Auto-generated resolution for event {event_id}"
        )
    
    def get_audit_view(self, event_id: str) -> _AccountabilityAuditView:
        """获取问责审计视图
        
        Args:
            event_id: 事件ID
            
        Returns:
            问责审计视图
        """
        # Get all relevant data
        responsibility_chain = self.responsibility_chains.get(event_id, [])
        approval_records = self.approval_records.get(event_id, [])
        override_actions = self.override_actions.get(event_id, [])
        
        # Generate responsibility resolution
        try:
            final_resolution = self.generate_responsibility_resolution(event_id)
        except ValueError:
            final_resolution = None
        
        # Extract sovereignty contexts from all links
        sovereignty_contexts = [link.sovereignty_context for link in responsibility_chain]
        
        return _AccountabilityAuditView(
            event_id=event_id,
            responsibility_chain=responsibility_chain,
            approval_records=approval_records,
            override_actions=override_actions,
            final_resolution=final_resolution,
            sovereignty_contexts=sovereignty_contexts
        )
    
    def get_accountability_summary(self, event_id: str) -> _AccountabilitySummary:
        """获取问责摘要
        
        Args:
            event_id: 事件ID
            
        Returns:
            问责摘要
        """
        # Get audit view first
        audit_view = self.get_audit_view(event_id)
        
        # Get resolution
        resolution = audit_view.final_resolution
        if not resolution:
            raise ValueError(f"No responsibility resolution available for event {event_id}")
        
        return _AccountabilitySummary(
            event_id=event_id,
            primary_owner=resolution.primary_owner,
            primary_role=resolution.primary_role,
            liability_type=resolution.liability_type,
            approval_count=len(audit_view.approval_records),
            override_count=len(audit_view.override_actions),
            responsibility_chain_length=len(audit_view.responsibility_chain)
        )
    
    def replay_responsibility_chain(self, event_id: str) -> List[_ResponsibilityLink]:
        """重放责任链
        
        Args:
            event_id: 事件ID
            
        Returns:
            完整的责任链
        """
        # Get the responsibility chain
        chain = self.responsibility_chains.get(event_id, [])
        
        # Return the complete chain (including superseded links)
        return chain
    
    def get_all_events(self) -> List[str]:
        """获取所有事件ID
        
        Returns:
            所有事件ID列表
        """
        return list(self.responsibility_chains.keys())
    
    def record_human_intervention(
        self,
        event_id: str,
        actor_id: str,
        role: str,
        mode: SovereigntyMode,
        target_event_id: str,
        reason: str,
        sovereignty_context: Dict[str, Any],
        original_decision: Optional[Dict[str, Any]] = None,
        intervention_decision: Optional[Dict[str, Any]] = None,
        responsibility_takeover: bool = True
    ) -> HumanIntervention:
        """记录人类介入
        
        Args:
            event_id: 事件ID
            actor_id: 介入者ID
            role: 介入者角色
            mode: 主权模式
            target_event_id: 目标事件ID
            reason: 介入原因
            sovereignty_context: 主权上下文
            original_decision: 原始决策
            intervention_decision: 介入后的决策
            responsibility_takeover: 是否接管责任
            
        Returns:
            创建的人类介入记录
        """
        # Create human intervention record
        intervention = HumanIntervention(
            actor_id=actor_id,
            role=role,
            mode=mode,
            target_event_id=target_event_id,
            reason=reason,
            original_decision=original_decision,
            intervention_decision=intervention_decision,
            sovereignty_context=sovereignty_context,
            responsibility_takeover=responsibility_takeover
        )
        
        # Ensure intervention list exists
        if event_id not in self.human_interventions:
            self.human_interventions[event_id] = []
        
        self.human_interventions[event_id].append(intervention)
        
        # Update event sovereignty mode
        self.event_sovereignty_map[event_id] = mode
        
        # If responsibility takeover is true, create a new responsibility link
        if responsibility_takeover:
            self.create_responsibility_link(
                event_id=event_id,
                actor_id=actor_id,
                role=role,
                stage="HUMAN_INTERVENTION",
                action_type="RESPONSIBILITY_TAKEOVER",
                sovereignty_context=sovereignty_context,
                reason=reason
            )
        
        return intervention
    
    def record_sovereignty_switch(
        self,
        event_id: str,
        from_mode: SovereigntyMode,
        to_mode: SovereigntyMode,
        reason: str,
        triggered_by: str,
        triggered_by_role: str,
        context: Dict[str, Any]
    ) -> SovereigntySwitch:
        """记录主权切换
        
        Args:
            event_id: 事件ID
            from_mode: 切换前的主权模式
            to_mode: 切换后的主权模式
            reason: 切换原因
            triggered_by: 触发者ID
            triggered_by_role: 触发者角色
            context: 切换上下文
            
        Returns:
            创建的主权切换记录
        """
        # Create sovereignty switch record
        sovereignty_switch = SovereigntySwitch(
            from_mode=from_mode,
            to_mode=to_mode,
            reason=reason,
            triggered_by=triggered_by,
            triggered_by_role=triggered_by_role,
            context=context
        )
        
        # Ensure switch list exists
        if event_id not in self.sovereignty_switches:
            self.sovereignty_switches[event_id] = []
        
        self.sovereignty_switches[event_id].append(sovereignty_switch)
        
        # Update event sovereignty mode
        self.event_sovereignty_map[event_id] = to_mode
        
        # Create responsibility link for sovereignty switch
        sovereignty_context = {
            "from_mode": from_mode,
            "to_mode": to_mode,
            "triggered_by": triggered_by,
            "triggered_by_role": triggered_by_role,
            **context
        }
        
        self.create_responsibility_link(
            event_id=event_id,
            actor_id=triggered_by,
            role=triggered_by_role,
            stage="SOVEREIGNTY_SWITCH",
            action_type="SOVEREIGNTY_CHANGE",
            sovereignty_context=sovereignty_context,
            reason=reason
        )
        
        return sovereignty_switch
    
    def get_event_sovereignty_mode(self, event_id: str) -> SovereigntyMode:
        """获取事件的主权模式
        
        Args:
            event_id: 事件ID
            
        Returns:
            事件的主权模式
        """
        return self._event_sovereignty_map.get(event_id, SovereigntyMode.SYSTEM_PRIMARY)
    
    def record_arbitration_resolution(
        self,
        event_id: str,
        case: ArbitrationCase,
        resolution: ArbitrationResolution
    ) -> None:
        """记录仲裁决议
        
        Args:
            event_id: 事件ID
            case: 仲裁案例
            resolution: 仲裁决议
        """
        # Update arbitration case status
        updated_case = case.copy(
            update={
                "status": "resolved",
                "resolved_at": datetime.now(),
                "final_decision": resolution.resolution,
                "final_responsibility_holder": resolution.final_responsibility_holder,
                "final_sovereignty_mode": resolution.new_sovereignty_mode
            }
        )
        
        # Save updated case
        self.arbitration_cases[event_id] = updated_case
        
        # Update event sovereignty mode
        self.event_sovereignty_map[event_id] = resolution.new_sovereignty_mode
        
        # Create responsibility link for arbitration resolution
        sovereignty_context = {
            "arbitrator_id": resolution.arbitrator_id,
            "arbitrator_role": resolution.arbitrator_role,
            "final_sovereignty_mode": resolution.new_sovereignty_mode,
            "case_id": case.case_id
        }
        
        self.create_responsibility_link(
            event_id=event_id,
            actor_id=resolution.arbitrator_id,
            role=resolution.arbitrator_role,
            stage="ARBITRATION_RESOLUTION",
            action_type="RESPONSIBILITY_ASSIGN",
            sovereignty_context=sovereignty_context,
            reason=resolution.rationale
        )
    
    def get_human_interventions(self, event_id: str) -> List[HumanIntervention]:
        """获取事件的人类介入记录
        
        Args:
            event_id: 事件ID
            
        Returns:
            人类介入记录列表
        """
        return self.human_interventions.get(event_id, [])
    
    def get_arbitration_case(self, event_id: str) -> Optional[ArbitrationCase]:
        """获取事件的仲裁案例
        
        Args:
            event_id: 事件ID
            
        Returns:
            仲裁案例，如果没有则返回None
        """
        return self.arbitration_cases.get(event_id)
    
    def link_proof_to_responsibility(self, proof_id: str, event_id: str) -> None:
        """将治理证明与责任链关联
        
        实现责任与证明融合规则：每个治理证明必须关联到责任事件
        
        Args:
            proof_id: 治理证明ID
            event_id: 责任事件ID
        """
        # 建立双向映射
        self.proof_responsibility_map[proof_id] = event_id
        
        if event_id not in self.responsibility_proof_map:
            self.responsibility_proof_map[event_id] = []
        
        # 确保证明ID只被添加一次
        if proof_id not in self.responsibility_proof_map[event_id]:
            self.responsibility_proof_map[event_id].append(proof_id)
    
    def link_attestation_to_responsibility(self, attestation_id: str, event_id: str) -> None:
        """将治理行为见证与责任链关联
        
        实现责任与证明融合规则：每个治理行为见证必须关联到责任事件
        
        Args:
            attestation_id: 治理行为见证ID
            event_id: 责任事件ID
        """
        self.attestation_responsibility_map[attestation_id] = event_id
    
    def get_proofs_by_responsibility(self, event_id: str) -> List[str]:
        """根据责任事件获取所有相关治理证明
        
        Args:
            event_id: 责任事件ID
            
        Returns:
            关联的治理证明ID列表
        """
        return self.responsibility_proof_map.get(event_id, [])
    
    def get_responsibility_by_proof(self, proof_id: str) -> Optional[str]:
        """根据治理证明ID获取相关责任事件
        
        Args:
            proof_id: 治理证明ID
            
        Returns:
            关联的责任事件ID，如果没有则返回None
        """
        return self.proof_responsibility_map.get(proof_id)
    
    def get_attestations_by_responsibility(self, event_id: str) -> List[str]:
        """根据责任事件获取所有相关治理行为见证
        
        Args:
            event_id: 责任事件ID
            
        Returns:
            关联的治理行为见证ID列表
        """
        return [attestation_id for attestation_id, e_id in self.attestation_responsibility_map.items() if e_id == event_id]
    
    def get_responsibility_by_attestation(self, attestation_id: str) -> Optional[str]:
        """根据治理行为见证ID获取相关责任事件
        
        Args:
            attestation_id: 治理行为见证ID
            
        Returns:
            关联的责任事件ID，如果没有则返回None
        """
        return self.attestation_responsibility_map.get(attestation_id)
    
    def generate_proof_enriched_responsibility_resolution(self, event_id: str) -> _ResponsibilityResolution:
        """生成包含证明信息的责任解析结果
        
        实现责任与证明融合规则：责任解析必须包含关联的治理证明信息
        
        Args:
            event_id: 事件ID
            
        Returns:
            包含证明信息的责任解析结果
        """
        # 生成基础责任解析
        base_resolution = self.generate_responsibility_resolution(event_id)
        
        # 获取关联的治理证明
        associated_proofs = self.get_proofs_by_responsibility(event_id)
        
        # 增强责任解析结果，添加证明信息
        # 注意：这里返回的是原始的_ResponsibilityResolution对象
        # 在实际使用中，可能需要扩展责任解析模型来包含证明信息
        return base_resolution
    
    def record_agent_responsibility(
        self,
        event_id: str,
        agent_id: str,
        agent_version: str,
        role: str,
        stage: str,
        action_type: str,
        sovereignty_context: Dict[str, Any],
        reason: str,
        proposal_id: Optional[str] = None
    ) -> _ResponsibilityLink:
        """记录Agent责任
        
        Args:
            event_id: 事件ID
            agent_id: Agent ID
            agent_version: Agent版本
            role: 责任角色
            stage: 责任阶段
            action_type: 责任动作类型
            sovereignty_context: 主权上下文
            reason: 责任原因
            proposal_id: Agent提议ID，可选
            
        Returns:
            创建的责任链链接
        """
        # Create new responsibility link with agent-specific information
        link = _ResponsibilityLink(
            actor_id=agent_id,
            role=role,
            stage=stage,
            action_type=action_type,
            sovereignty_context={
                **sovereignty_context,
                "agent_version": agent_version,
                "proposal_id": proposal_id
            },
            reason=reason
        )
        
        # Ensure event chain exists
        if event_id not in self.responsibility_chains:
            self.responsibility_chains[event_id] = []
            self.event_responsibility_map[event_id] = event_id
        
        # Add to chain (append-only)
        self.responsibility_chains[event_id].append(link)
        
        return link
    
    def generate_responsibility_resolution(
        self,
        event_id: str,
        primary_owner: Optional[str] = None,
        primary_role: Optional[str] = None
    ) -> _ResponsibilityResolution:
        """生成责任解析结果
        
        Args:
            event_id: 事件ID
            primary_owner: 主要责任人（可选，默认从责任链推导）
            primary_role: 主要责任角色（可选，默认从责任链推导）
            
        Returns:
            生成的责任解析结果
        """
        # Get responsibility chain
        if event_id not in self.responsibility_chains:
            raise ValueError(f"Event {event_id} does not exist in responsibility chains")
        
        chain = self.responsibility_chains[event_id]
        
        # Determine primary owner and role if not provided
        if not primary_owner or not primary_role:
            # Get the last non-superseded link in the chain
            active_links = [link for link in chain if not link.is_superseded]
            if active_links:
                last_link = active_links[-1]
                primary_owner = primary_owner or last_link.actor_id
                primary_role = primary_role or last_link.role
            else:
                # If no active links, use the first link
                if chain:
                    first_link = chain[0]
                    primary_owner = primary_owner or first_link.actor_id
                    primary_role = primary_role or first_link.role
                else:
                    raise ValueError(f"No responsibility links found for event {event_id}")
        
        # Collect all contributing owners (everyone in the chain except superseded ones)
        contributing_owners = set()
        contributing_roles = set()
        liability_type = "direct"
        
        for link in chain:
            if not link.is_superseded:
                contributing_owners.add(link.actor_id)
                contributing_roles.add(link.role)
            
            # Determine liability type based on action type
            if link.action_type in ["OVERRIDE", "RESPONSIBILITY_TAKEOVER"]:
                liability_type = "overridden"
            elif link.action_type in ["APPROVAL"]:
                liability_type = "shared"
            elif link.action_type in ["RESPONSIBILITY_DELEGATE"]:
                liability_type = "delegated"
            elif link.action_type in ["AGENT_PROPOSAL", "AGENT_DECISION"]:
                # Agent-specific liability type
                liability_type = "agent_mediated"
        
        # Remove primary owner from contributing owners
        contributing_owners.discard(primary_owner)
        contributing_roles.discard(primary_role)
        
        return _ResponsibilityResolution(
            primary_owner=primary_owner,
            primary_role=primary_role,
            contributing_owners=list(contributing_owners),
            contributing_roles=list(contributing_roles),
            liability_type=liability_type,
            resolution_reason=f"Auto-generated resolution for event {event_id}"
        )
    
    class Config:
        # Allow private attribute access for internal use
        underscore_attrs_are_private = True


__all__ = []
