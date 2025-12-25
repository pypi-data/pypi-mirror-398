"""
Stage Manager - Manages governance stages and stage authority

This module is responsible for managing governance stages, stage transitions,
and enforcing stage authority constraints.

Governance Authority Invariants:
1. Stage Definition is immutable governance spec, not runtime config
2. Stage transition requires triple validation: current stage, event type, actor authority
3. Illegal events/actions result in GovernanceViolation and fail-closed
4. Freeze/unfreeze are overlay states, not independent actions
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from typing import Dict, List
from datetime import datetime

from .stage_models import (_GovernanceStage as GovernanceStage, 
                          _StageTransition as StageTransition, 
                          _RoleType as RoleType)
from .events import _EventType as EventType
from .policy_engine import _ActionType as ActionType


class _StageManager:
    """阶段管理器 - 负责管理阶段状态和阶段权限
    
    这个类确保：
    1. 阶段定义不可变
    2. 事件在当前阶段合法
    3. 动作在当前阶段合法
    4. 阶段跃迁符合主权规则
    5. 冻结/解冻符合阶段语义
    """
    
    def __init__(self, caller):
        """
        初始化阶段管理器
        
        Args:
            caller: 调用者，必须是GovernanceEngine实例
        
        Raises:
            RuntimeError: 如果调用者不是GovernanceEngine实例
        """
        if caller.__class__.__name__ != "GovernanceEngine":
            raise RuntimeError("Unauthorized access to StageManager")
        
        self.caller = caller
        self.stages = self._load_stages()
        self._stage_transitions = []
        
        # Validate stages after loading
        self._validate_stages()
    
    def _load_stages(self) -> Dict[str, GovernanceStage]:
        """
        加载阶段定义，只在系统初始化时执行
        
        Returns:
            Dict[str, GovernanceStage]: 阶段定义字典，键为阶段ID
        """
        # Define default stage definitions
        # These are immutable governance specs, not runtime config
        stages = {
            "S1": GovernanceStage(
                stage_id="S1",
                name="Initialization",
                allowed_events=[
                    EventType.STAGE_CHANGE,
                    EventType.STATUS,
                    EventType.POLICY_CHANGE
                ],
                allowed_actions=[
                    ActionType.LOG_VIOLATION,
                    ActionType.ALLOW
                ],
                can_freeze=True,
                can_unfreeze=False,
                next_stages=["S2"],
                prev_stages=[],
                overlay_states=[],
                allowed_transition_actors=[RoleType.SYSTEM, RoleType.HUMAN]
            ),
            "S2": GovernanceStage(
                stage_id="S2",
                name="Development",
                allowed_events=[
                    EventType.STAGE_CHANGE,
                    EventType.CODE_GENERATION,
                    EventType.TOOL_CALL,
                    EventType.STATUS
                ],
                allowed_actions=[
                    ActionType.FREEZE_PROJECT,
                    ActionType.LOG_VIOLATION,
                    ActionType.SCORE_PENALTY,
                    ActionType.ALLOW
                ],
                can_freeze=True,
                can_unfreeze=True,
                next_stages=["S3"],
                prev_stages=["S1"],
                overlay_states=["frozen"],
                allowed_transition_actors=[RoleType.SYSTEM, RoleType.HUMAN]
            ),
            "S3": GovernanceStage(
                stage_id="S3",
                name="Architecture Review",
                allowed_events=[
                    EventType.STAGE_CHANGE,
                    EventType.CODE_GENERATION,
                    EventType.ARCH_VIOLATION,
                    EventType.STATUS
                ],
                allowed_actions=[
                    ActionType.LOG_VIOLATION,
                    ActionType.SCORE_PENALTY,
                    ActionType.ALLOW
                ],
                can_freeze=True,
                can_unfreeze=True,
                next_stages=["S4"],
                prev_stages=["S2"],
                overlay_states=["frozen"],
                allowed_transition_actors=[RoleType.SYSTEM, RoleType.HUMAN]
            ),
            "S4": GovernanceStage(
                stage_id="S4",
                name="Audit",
                allowed_events=[
                    EventType.STAGE_CHANGE,
                    EventType.AUDIT_MISSING,
                    EventType.STATUS
                ],
                allowed_actions=[
                    ActionType.LOG_VIOLATION,
                    ActionType.REQUIRE_HUMAN_APPROVAL,
                    ActionType.ALLOW
                ],
                can_freeze=True,
                can_unfreeze=True,
                next_stages=["S5"],
                prev_stages=["S3"],
                overlay_states=["frozen"],
                allowed_transition_actors=[RoleType.SYSTEM, RoleType.HUMAN]
            ),
            "S5": GovernanceStage(
                stage_id="S5",
                name="Finalization",
                allowed_events=[
                    EventType.STAGE_CHANGE,
                    EventType.CODE_GENERATION,
                    EventType.STATUS
                ],
                allowed_actions=[
                    ActionType.ALLOW
                ],
                can_freeze=False,
                can_unfreeze=True,
                next_stages=[],
                prev_stages=["S4"],
                overlay_states=[],
                allowed_transition_actors=[RoleType.SYSTEM, RoleType.HUMAN]
            )
        }
        
        return stages
    
    def _validate_stages(self):
        """
        验证阶段定义的完整性和正确性
        
        Raises:
            ValueError: 如果阶段定义不完整或不正确
        """
        # 验证每个阶段
        for stage_id, stage in self.stages.items():
            # 验证阶段ID格式
            if not stage_id.startswith('S') or not stage_id[1:].isdigit():
                raise ValueError(f"Invalid stage ID: {stage_id}")
            
            # 验证阶段ID与字典键一致
            if stage_id != stage.stage_id:
                raise ValueError(f"Stage ID mismatch: {stage_id} != {stage.stage_id}")
            
            # 验证阶段定义是不可变的
            if not stage.immutable:
                raise ValueError(f"Stage {stage_id} must be immutable")
            
            # 验证下一阶段存在
            for next_stage_id in stage.next_stages:
                if next_stage_id not in self.stages:
                    raise ValueError(f"Next stage {next_stage_id} not found for stage {stage_id}")
            
            # 验证前一阶段存在
            for prev_stage_id in stage.prev_stages:
                if prev_stage_id not in self.stages:
                    raise ValueError(f"Previous stage {prev_stage_id} not found for stage {stage_id}")
    
    def is_event_allowed(self, stage: str, event_type: EventType) -> bool:
        """
        检查事件在当前阶段是否允许
        
        Args:
            stage: 当前阶段ID
            event_type: 事件类型
            
        Returns:
            bool: 如果事件允许，返回True，否则返回False
        """
        if stage not in self.stages:
            return False
        
        return event_type in self.stages[stage].allowed_events
    
    def is_action_allowed(self, stage: str, action_type: ActionType) -> bool:
        """
        检查动作在当前阶段是否允许
        
        Args:
            stage: 当前阶段ID
            action_type: 动作类型
            
        Returns:
            bool: 如果动作允许，返回True，否则返回False
        """
        if stage not in self.stages:
            return False
        
        return action_type in self.stages[stage].allowed_actions
    
    def is_stage_transition_allowed(self, from_stage: str, to_stage: str, 
                                   actor_role: RoleType) -> bool:
        """
        检查阶段跃迁是否允许（三重条件）
        
        Governance Authority Invariants:
        1. 当前 Stage 允许跃迁
        2. 目标 Stage 是允许的下一阶段
        3. 触发 Actor 具备 Stage Authority
        
        Args:
            from_stage: 当前阶段ID
            to_stage: 目标阶段ID
            actor_role: 触发者角色类型
            
        Returns:
            bool: 如果阶段跃迁允许，返回True，否则返回False
        """
        # 1. 检查当前阶段是否存在
        if from_stage not in self.stages:
            return False
        
        # 2. 检查目标阶段是否存在
        if to_stage not in self.stages:
            return False
        
        current_stage = self.stages[from_stage]
        
        # 3. 检查目标阶段是否是允许的下一阶段
        if to_stage not in current_stage.next_stages:
            return False
        
        # 4. 检查触发者角色是否具备跃迁权限
        if actor_role not in current_stage.allowed_transition_actors:
            return False
        
        return True
    
    def can_freeze(self, stage: str) -> bool:
        """
        检查在当前阶段是否可以冻结
        
        Args:
            stage: 当前阶段ID
            
        Returns:
            bool: 如果可以冻结，返回True，否则返回False
        """
        if stage not in self.stages:
            return False
        
        return self.stages[stage].can_freeze
    
    def can_unfreeze(self, stage: str) -> bool:
        """
        检查在当前阶段是否可以解冻
        
        Args:
            stage: 当前阶段ID
            
        Returns:
            bool: 如果可以解冻，返回True，否则返回False
        """
        if stage not in self.stages:
            return False
        
        return self.stages[stage].can_unfreeze
    
    def is_overlay_state_allowed(self, stage: str, overlay_state: str) -> bool:
        """
        检查在当前阶段是否允许特定的覆盖状态
        
        Args:
            stage: 当前阶段ID
            overlay_state: 覆盖状态
            
        Returns:
            bool: 如果覆盖状态允许，返回True，否则返回False
        """
        if stage not in self.stages:
            return False
        
        return overlay_state in self.stages[stage].overlay_states
    
    def record_transition(self, from_stage: str, to_stage: str, 
                         actor_id: str, actor_role: RoleType, 
                         reason: str) -> StageTransition:
        """
        记录阶段跃迁
        
        Args:
            from_stage: 源阶段ID
            to_stage: 目标阶段ID
            actor_id: 触发者ID
            actor_role: 触发者角色类型
            reason: 跃迁原因
            
        Returns:
            StageTransition: 阶段跃迁记录
        """
        transition = StageTransition(
            from_stage=from_stage,
            to_stage=to_stage,
            actor_id=actor_id,
            actor_role=actor_role,
            reason=reason
        )
        
        self._stage_transitions.append(transition)
        
        return transition
    
    def get_stage_definitions(self) -> Dict[str, GovernanceStage]:
        """
        获取所有阶段定义
        
        Returns:
            Dict[str, GovernanceStage]: 阶段定义字典
        """
        return self.stages.copy()
    
    def get_stage_transitions(self) -> List[StageTransition]:
        """
        获取所有阶段跃迁记录
        
        Returns:
            List[StageTransition]: 阶段跃迁记录列表
        """
        return self._stage_transitions.copy()
    
    def get_stage(self, stage_id: str) -> GovernanceStage:
        """
        获取特定阶段定义
        
        Args:
            stage_id: 阶段ID
            
        Returns:
            GovernanceStage: 阶段定义
            
        Raises:
            KeyError: 如果阶段不存在
        """
        return self.stages[stage_id]
    
    def get_allowed_events(self, stage_id: str) -> List[EventType]:
        """
        获取特定阶段允许的事件类型
        
        Args:
            stage_id: 阶段ID
            
        Returns:
            List[EventType]: 允许的事件类型列表
        """
        if stage_id not in self.stages:
            return []
        
        return self.stages[stage_id].allowed_events.copy()
    
    def get_allowed_actions(self, stage_id: str) -> List[ActionType]:
        """
        获取特定阶段允许的动作类型
        
        Args:
            stage_id: 阶段ID
            
        Returns:
            List[ActionType]: 允许的动作类型列表
        """
        if stage_id not in self.stages:
            return []
        
        return self.stages[stage_id].allowed_actions.copy()


__all__ = []
