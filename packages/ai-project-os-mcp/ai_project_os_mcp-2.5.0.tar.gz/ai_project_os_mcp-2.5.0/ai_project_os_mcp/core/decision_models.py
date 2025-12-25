#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
决策模型模块

包含治理决策流水线中所有阶段的结构化对象定义
确保每个阶段都有明确的验证和不可跳过机制
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from .human_sovereignty_models import _SovereigntyMode as SovereigntyMode, _HumanIntervention as HumanIntervention
from .arbitration_models import _ArbitrationCase as ArbitrationCase


class TriggerResult(BaseModel):
    """触发结果模型
    
    表示从事件到触发条件匹配的结果
    """
    evaluated: bool = Field(default=True, description="是否经过评估")
    triggered: bool = Field(default=False, description="是否触发成功")
    trigger_ids: List[str] = Field(default_factory=list, description="匹配的触发条件ID列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="评估时间戳")
    event_id: str = Field(..., description="关联的事件ID")


class ViolationSet(BaseModel):
    """违规集合模型
    
    表示从触发条件到违规识别的结果
    """
    evaluated: bool = Field(default=True, description="是否经过评估")
    empty: bool = Field(default=True, description="是否为空集")
    violations: List[dict] = Field(default_factory=list, description="违规列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="评估时间戳")
    trigger_result_id: str = Field(..., description="关联的触发结果ID")
    event_id: str = Field(..., description="关联的事件ID")


class PolicyDecision(BaseModel):
    """策略决策模型
    
    表示从违规到策略决策的结果
    """
    evaluated: bool = Field(default=True, description="是否经过评估")
    decisions: List[dict] = Field(default_factory=list, description="决策列表")
    policy_version: str = Field(default="default", description="使用的策略版本")
    timestamp: datetime = Field(default_factory=datetime.now, description="评估时间戳")
    violation_set_id: str = Field(..., description="关联的违规集合ID")
    event_id: str = Field(..., description="关联的事件ID")


class Action(BaseModel):
    """动作模型
    
    表示要执行的具体治理动作
    """
    action_type: str = Field(..., description="动作类型")
    parameters: dict = Field(default_factory=dict, description="动作参数")
    priority: int = Field(default=0, description="动作优先级")
    mandatory: bool = Field(default=True, description="是否为强制动作")


class ActionPlan(BaseModel):
    """动作计划模型
    
    表示从策略决策到动作计划生成的结果
    """
    generated: bool = Field(default=True, description="是否生成成功")
    actions: List[Action] = Field(default_factory=list, description="要执行的动作列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="计划生成时间戳")
    event_id: str = Field(..., description="关联的事件ID")
    policy_version: str = Field(default="default", description="生成计划使用的策略版本")
    policy_decision_id: str = Field(..., description="关联的策略决策ID")


class ExecutionResult(BaseModel):
    """执行结果模型
    
    表示从动作计划到状态变更的执行结果
    """
    executed: bool = Field(default=True, description="是否执行")
    success: bool = Field(default=False, description="是否执行成功")
    failed_actions: List[dict] = Field(default_factory=list, description="执行失败的动作列表")
    successful_actions: List[dict] = Field(default_factory=list, description="执行成功的动作列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="执行时间戳")
    action_plan_id: str = Field(..., description="关联的动作计划ID")
    event_id: str = Field(..., description="关联的事件ID")
    fail_strategy: str = Field(default="fail-closed", description="失败处理策略")


class AuditRecord(BaseModel):
    """审计记录模型
    
    表示整个决策流水线的最终审计记录
    包含完整的责任链和问责信息，以及主权和仲裁信息
    """
    recorded: bool = Field(default=True, description="是否记录成功")
    event_id: str = Field(..., description="关联的事件ID")
    trigger_result: Optional[TriggerResult] = Field(default=None, description="触发结果")
    violation_set: Optional[ViolationSet] = Field(default=None, description="违规集合")
    policy_decision: Optional[PolicyDecision] = Field(default=None, description="策略决策")
    action_plan: Optional[ActionPlan] = Field(default=None, description="动作计划")
    execution_result: Optional[ExecutionResult] = Field(default=None, description="执行结果")
    timestamp: datetime = Field(default_factory=datetime.now, description="审计记录时间戳")
    governance_version: str = Field(default="default", description="治理引擎版本")
    
    # Accountability fields
    responsibility_chain: List[str] = Field(default_factory=list, description="责任链链接ID列表")
    responsibility_resolution: Optional[Dict[str, Any]] = Field(default=None, description="责任解析结果")
    sovereignty_contexts: List[Dict[str, Any]] = Field(default_factory=list, description="所有阶段的主权上下文列表")
    approval_records: List[str] = Field(default_factory=list, description="审批记录ID列表")
    override_actions: List[str] = Field(default_factory=list, description="覆盖操作ID列表")
    accountability_summary: Optional[Dict[str, Any]] = Field(default=None, description="问责摘要")
    
    # Sovereignty and Arbitration fields
    sovereignty_mode: SovereigntyMode = Field(default=SovereigntyMode.SYSTEM_PRIMARY, description="主权模式")
    human_interventions: List[HumanIntervention] = Field(default_factory=list, description="人类介入记录列表")
    arbitration_case: Optional[ArbitrationCase] = Field(default=None, description="关联的仲裁案例")
    
    # Agent Governance fields
    agent_proposals: List[Dict[str, Any]] = Field(default_factory=list, description="Agent决策提议列表")
    agent_conflicts: List[Dict[str, Any]] = Field(default_factory=list, description="Agent决策冲突列表")
    agent_decision_result: Optional[Dict[str, Any]] = Field(default=None, description="Agent决策处理结果")
    active_agents: List[str] = Field(default_factory=list, description="参与决策的活跃Agent列表")
    agent_coordination_timestamp: Optional[datetime] = Field(default=None, description="Agent协同处理时间戳")
    replay_consistent: bool = Field(default=True, description="Agent提议重放一致性状态")
