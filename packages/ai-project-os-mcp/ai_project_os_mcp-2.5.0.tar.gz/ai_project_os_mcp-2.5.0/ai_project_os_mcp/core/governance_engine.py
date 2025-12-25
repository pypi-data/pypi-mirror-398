"""
Governance Engine - Core v2.5 implementation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import os

from .events import _GovernanceEvent as GovernanceEvent, _EventType as EventType, _EventStatus as EventStatus
from .event_store import _get_event_store as get_event_store
from .violation import _GovernanceViolation as GovernanceViolation, _ViolationLevel as ViolationLevel
from .policy_engine import _PolicyEngine as PolicyEngine, _ActionType as ActionType, _Action as Action
from .score_engine import _ScoreEngine as ScoreEngine
from .state_manager import _StateManager as StateManager
from .trigger_engine import _TriggerEngine as TriggerEngine
from .decision_models import ViolationSet
from .human_sovereignty_models import _SovereigntyMode as SovereigntyMode


class GovernanceEngine:
    """
    Governance Engine - The single entry point for all governance operations
    
    This is the core of v2.5 implementation and follows the Single Gate principle.
    All governance operations must pass through this engine.
    
    Key responsibilities:
    - Enforce policy compliance
    - Generate and track violations
    - Maintain audit trail
    - Calculate governance score
    - Update project state
    - Ensure structural non-bypassability
    """
    
    def __init__(self, project_root: str):
        """
        Initialize Governance Engine
        
        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        
        # Initialize sub-engines
        self.policy_engine = PolicyEngine(self, project_root)
        self.score_engine = ScoreEngine(self)
        self.state_manager = StateManager(self, os.path.join(project_root, "state.json"))
        self.trigger_engine = TriggerEngine(self)
        self.event_store = get_event_store(self)
        
        # Load initial state
        self.state = self.state_manager.load_state()
        
        # Ensure required state fields exist
        self._initialize_state()
        
        # Internal flag to track if we're inside handle_event call
        self._inside_handle_event = False
    
    def _initialize_state(self):
        """
        Ensure required state fields exist
        """
        if "score" not in self.state:
            self.state["score"] = {
                "global": 100,  # Irreversible,跨阶段
                "stage": 100    # 阶段内评分，阶段切换时重置
            }
        
        if "is_frozen" not in self.state:
            self.state["is_frozen"] = False
        
        if "events" not in self.state:
            self.state["events"] = []
    
    def handle_event(self, event: GovernanceEvent) -> Dict[str, Any]:
        """
        Process a governance event - the single entry point for all governance operations
        
        Args:
            event: Governance event with actor identity
            
        Returns:
            Processed event result with violations, score, and actions
        """
        try:
            # 设置内部标志，表示我们在handle_event内部
            self._inside_handle_event = True
            
            # 更新事件状态为处理中
            self.event_store.update_event_status(event.id, EventStatus.IN_PROGRESS)
            
            # 1. Validate actor identity (必改：无 Actor 的 Event 直接拒绝)
            if not event.actor:
                violation = GovernanceViolation(
                    level=ViolationLevel.CRITICAL,
                    rule_id="anonymous_event",
                    event_id=event.id,
                    actor_id="anonymous",  # 无 Actor 时使用默认值
                    message="Anonymous event is not allowed"
                )
                # 创建违规集合
                violation_set = ViolationSet(
                    evaluated=True,
                    empty=False,
                    violations=[violation.model_dump()],
                    trigger_result_id=event.id,
                    event_id=event.id
                )
                
                # 处理违规，确保生成审计记录
                current_stage = self.state.get("stage", "S0")
                current_sovereignty_mode = self.state.get("sovereignty", {}).get("mode", SovereigntyMode.SYSTEM_PRIMARY)
                result = self._handle_violation(event, violation_set, current_stage, current_sovereignty_mode)
                
                # 更新事件状态为已关闭
                self.event_store.update_event_status(event.id, EventStatus.CLOSED)
                return result
            
            # 2. Check frozen state (必改：Frozen 状态下，只接受 UNFREEZE / STATUS 事件)
            if self.state["is_frozen"]:
                if event.event_type not in [EventType.UNFREEZE, EventType.STATUS]:
                    violation = GovernanceViolation(
                        level=ViolationLevel.CRITICAL,
                        rule_id="frozen_project",
                        event_id=event.id,
                        actor_id=event.actor.id,
                        message="Project is frozen, only UNFREEZE and STATUS events are allowed"
                    )
                    # 创建违规集合
                    violation_set = ViolationSet(
                        evaluated=True,
                        empty=False,
                        violations=[violation.model_dump()],
                        trigger_result_id=event.id,
                        event_id=event.id
                    )
                    
                    # 处理违规，确保生成审计记录
                    current_stage = self.state.get("stage", "S0")
                    current_sovereignty_mode = self.state.get("sovereignty", {}).get("mode", SovereigntyMode.SYSTEM_PRIMARY)
                    result = self._handle_violation(event, violation_set, current_stage, current_sovereignty_mode)
                    
                    # 更新事件状态为已关闭
                    self.event_store.update_event_status(event.id, EventStatus.CLOSED)
                    return result
            
            # 2.1 仲裁事件专门处理
            if event.event_type in [EventType.ARBITRATION_REQUEST, EventType.ARBITRATION_RESOLUTION]:
                # 仲裁事件特殊处理：确保生成专门的仲裁审计记录
                with self._governance_transaction():
                    # 3. Save event to EventStore (必改：EventStore = 不可修改 append-only)
                    self.event_store.append(event)
                    
                    # 4. 仲裁事件默认无违规，除非有明确的仲裁理由
                    violations = []
                    if event.event_type == EventType.ARBITRATION_REQUEST:
                        # 检查仲裁请求是否包含有效的仲裁理由
                        if not event.payload.get("reason"):
                            violation = GovernanceViolation(
                                level=ViolationLevel.MINOR,
                                rule_id="arbitration_reason_missing",
                                event_id=event.id,
                                actor_id=event.actor.id,
                                message="Arbitration request missing reason"
                            )
                            violations.append(violation.model_dump())
                    
                    # 5. Decide actions using PolicyEngine (Phase A3)
                    actions = self.policy_engine.decide(violations)
                    
                    # 6. Update score using ScoreEngine (Phase B1)
                    score_update = self.score_engine.update(event, violations, self.state)
                    
                    # 7. Apply actions and update state in transaction (Phase A3)
                    self._apply_actions(actions, event)
                    self._update_state(event, violations, actions, score_update)
                    
                    # 8. Write audit record (新增：必改 - 所有事件必须有审计记录)
                    self._write_audit(event, violations, actions, score_update)
                
                # 9. Create result
                result = {
                    "event_id": event.id,
                    "status": "FAILED" if any(v["level"] in [ViolationLevel.CRITICAL, ViolationLevel.MAJOR] for v in violations) else "PASSED",
                    "violations": violations,
                    "actions": actions,
                    "score": score_update
                }
                
                # 更新事件状态为已关闭
                self.event_store.update_event_status(event.id, EventStatus.CLOSED)
                return result
            
            # 3. Save event to EventStore (必改：EventStore = 不可修改 append-only)
            self.event_store.append(event)
            
            # 4. Detect violations using TriggerEngine (Phase A2)
            violations = self.trigger_engine.detect_violations(event, self.state)
            
            # 5. Decide actions using PolicyEngine (Phase A3)
            actions = self.policy_engine.decide(violations)
            
            # 6. Update score using ScoreEngine (Phase B1)
            score_update = self.score_engine.update(event, violations, self.state)
            
            # 7. Apply actions and update state in transaction (Phase A3)
            with self._governance_transaction():
                # 检查是否有 CRITICAL 违规，如果有，直接冻结项目
                has_critical_violation = any(v["level"] == ViolationLevel.CRITICAL for v in violations)
                if has_critical_violation:
                    self.state["is_frozen"] = True
                
                self._apply_actions(actions, event)
                self._update_state(event, violations, actions, score_update)
                # 8. Write audit record (新增：必改 - 所有事件必须有审计记录)
                self._write_audit(event, violations, actions, score_update)
            
            # 9. Create result
            result = {
                "event_id": event.id,
                "status": "FAILED" if any(v["level"] in [ViolationLevel.CRITICAL, ViolationLevel.MAJOR] for v in violations) else "PASSED",
                "violations": violations,
                "actions": actions,
                "score": score_update
            }
            
            # 治理不变量：确保每个事件都有审计记录
            # 检查是否已经生成了审计记录
            audit_records = self.state.get("audit", [])
            has_audit_record = any(record["event_id"] == event.id for record in audit_records)
            
            if not has_audit_record:
                # 兜底机制：如果没有生成审计记录，创建一个
                with self._governance_transaction():
                    self._write_audit(event, violations, actions, score_update)
            
            # 更新事件状态为已关闭
            self.event_store.update_event_status(event.id, EventStatus.CLOSED)
            return result
        except Exception as e:
            # 更新事件状态为错误
            self.event_store.update_event_status(event.id, EventStatus.ERROR)
            raise
        finally:
            # 无论如何，在方法结束时重置内部标志
            self._inside_handle_event = False
    
    def _governance_transaction(self):
        """
        Governance transaction context manager to ensure atomicity
        
        Returns:
            Context manager for governance transactions
        """
        engine = self
        
        class GovernanceTransaction:
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    # Commit: save state to disk
                    engine.state_manager.save_state(engine.state)
                else:
                    # Rollback: do nothing, state remains in memory
                    pass
        
        return GovernanceTransaction()
    
    def _apply_actions(self, actions: List[Action], event: GovernanceEvent):
        """
        Apply actions to the system
        
        Args:
            actions: List of structured actions to apply
            event: Original event
        """
        # 检查是否从handle_event内部调用
        if not self._inside_handle_event:
            raise RuntimeError("_apply_actions can only be called from within handle_event")
        
        for action in actions:
            if action.type == ActionType.FREEZE_PROJECT:
                self.state["is_frozen"] = True
            elif action.type == ActionType.UNFREEZE_PROJECT:
                self.state["is_frozen"] = False
        
        # 特殊处理：如果是 FREEZE_REQUEST 事件，直接冻结项目
        if event.event_type == EventType.FREEZE_REQUEST:
            # 确保冻结状态不可逆性：如果已经冻结，不能重复冻结
            if not self.state.get("is_frozen", False):
                self.state["is_frozen"] = True
                # 使用overlay_states替代单独的frozen字段
                if "overlay_states" not in self.state:
                    self.state["overlay_states"] = []
                if "frozen" not in self.state["overlay_states"]:
                    self.state["overlay_states"].append("frozen")
        # 特殊处理：如果是 UNFREEZE 事件，需要严格控制
        elif event.event_type == EventType.UNFREEZE:
            # 解冻需要严格控制：只能在特定阶段或特定条件下进行
            # 检查actor权限：只有system或human角色可以解冻
            if event.actor.role_type not in ["SYSTEM", "HUMAN"]:
                raise RuntimeError("CRITICAL VIOLATION: Only SYSTEM or HUMAN actors can unfreeze a project")
            
            # 解冻前记录原因
            freeze_reason = event.payload.get("reason", "Unspecified reason")
            
            # 解冻操作：移除frozen状态
            self.state["is_frozen"] = False
            # 使用overlay_states替代单独的frozen字段
            if "overlay_states" in self.state and "frozen" in self.state["overlay_states"]:
                self.state["overlay_states"].remove("frozen")
            
            # 记录解冻操作
            self.state["unfreeze_reason"] = freeze_reason
            self.state["unfreeze_by"] = event.actor.id
            self.state["unfreeze_at"] = datetime.utcnow().isoformat() + "Z"
    
    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get event history from EventStore
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        events = self.event_store.list()[:limit]
        return [event.model_dump() for event in events]
    
    def _update_state(self, event: GovernanceEvent, violations: List[Dict[str, Any]], 
                     actions: List[Dict[str, Any]], score_update: Dict[str, Any]):
        """
        Update project state based on event, violations, and actions
        
        Args:
            event: Processed event
            violations: Detected violations
            actions: Applied actions
            score_update: Updated score
        """
        # 检查是否从handle_event内部调用
        if not self._inside_handle_event:
            raise RuntimeError("_update_state can only be called from within handle_event")
        
        # Update score
        self.state["score"] = score_update
        
        # Add event to state (for quick access, but EventStore is the source of truth)
        self.state["events"].append({
            "event_id": event.id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "actor_id": event.actor.id
        })
        
        # Update violation count
        violation_count = {
            "critical": len([v for v in violations if v["level"] == ViolationLevel.CRITICAL]),
            "major": len([v for v in violations if v["level"] == ViolationLevel.MAJOR]),
            "minor": len([v for v in violations if v["level"] == ViolationLevel.MINOR])
        }
        self.state["violation_count"] = violation_count
    
    def _write_audit(self, event: GovernanceEvent, violations: List[Dict[str, Any]], 
                    actions: List[Dict[str, Any]], score_update: Dict[str, Any]):
        """
        Write audit record for the event
        
        Args:
            event: Processed event
            violations: Detected violations
            actions: Applied actions
            score_update: Updated score
        
        🔒 铁律：所有事件必须有审计记录，且必须引用event_id
        """
        # 检查是否从handle_event内部调用
        if not self._inside_handle_event:
            raise RuntimeError("_write_audit can only be called from within handle_event")
        
        try:
            # Ensure audit field exists in state
            if "audit" not in self.state:
                self.state["audit"] = []
            
            # Create audit record
            audit_record = {
                "event_id": event.id,
                "event_type": event.event_type,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "actor": {
                    "id": event.actor.id,
                    "role": event.actor.role,
                    "role_type": event.actor.role_type,
                    "source": event.actor.source
                },
                "status": "FAILED" if any(v["level"] in [ViolationLevel.CRITICAL, ViolationLevel.MAJOR] for v in violations) else "PASSED",
                "violations": violations,
                "actions": actions,
                "score_change": {
                    "global": score_update["global"] - self.state["score"]["global"] if "global" in self.state["score"] else score_update["global"] - 100,
                    "stage": score_update["stage"] - self.state["score"]["stage"] if "stage" in self.state["score"] else score_update["stage"] - 100
                },
                "score": score_update
            }
            
            # Add audit record to state (for quick access, but EventStore is the source of truth)
            self.state["audit"].append(audit_record)
            
            # Save updated state
            self.state_manager.save_state(self.state)
        except Exception as e:
            # 即使在写入审计记录时发生异常，也要生成一个基本的审计记录
            try:
                error_audit_record = {
                    "event_id": event.id,
                    "event_type": event.event_type,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "actor": {
                        "id": event.actor.id,
                        "role": event.actor.role,
                        "role_type": event.actor.role_type,
                        "source": event.actor.source
                    },
                    "status": "ERROR",
                    "violations": violations,
                    "actions": actions,
                    "score": score_update,
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e)
                    }
                }
                if "audit" not in self.state:
                    self.state["audit"] = []
                self.state["audit"].append(error_audit_record)
                self.state_manager.save_state(self.state)
            except Exception as audit_save_error:
                # 如果连基本的审计记录都无法保存，至少记录到事件状态
                self.event_store.update_event_status(event.id, EventStatus.ERROR)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current project state
        
        Returns:
            Current project state
        """
        return self.state
    
    def _handle_violation(self, event: GovernanceEvent, violation_set: ViolationSet, 
                        current_stage: str, sovereignty_mode: SovereigntyMode) -> Dict[str, Any]:
        """
        Handle violations, ensuring audit records are generated
        
        Args:
            event: Governance event
            violation_set: Set of violations
            current_stage: Current governance stage
            sovereignty_mode: Current sovereignty mode
            
        Returns:
            Processed result with violations and audit record
        """
        try:
            # 3. Save event to EventStore (必改：EventStore = 不可修改 append-only)
            self.event_store.append(event)
            
            # 4. 使用违规集合中的违规
            violations = violation_set.violations
            
            # 5. Decide actions using PolicyEngine (Phase A3)
            actions = self.policy_engine.decide(violations)
            
            # 6. Update score using ScoreEngine (Phase B1)
            score_update = self.score_engine.update(event, violations, self.state)
            
            # 7. Apply actions and update state in transaction (Phase A3)
            with self._governance_transaction():
                # 检查是否有 CRITICAL 违规，如果有，直接冻结项目
                has_critical_violation = any(v["level"] == ViolationLevel.CRITICAL for v in violations)
                if has_critical_violation:
                    self.state["is_frozen"] = True
                
                self._apply_actions(actions, event)
                self._update_state(event, violations, actions, score_update)
                # 8. Write audit record (新增：必改 - 所有事件必须有审计记录)
                self._write_audit(event, violations, actions, score_update)
            
            # 9. Create result
            result = {
                "event_id": event.id,
                "status": "FAILED",
                "violations": violations,
                "actions": actions,
                "score": score_update
            }
            
            return result
        except Exception as e:
            # 更新事件状态为错误
            self.event_store.update_event_status(event.id, EventStatus.ERROR)
            raise
    
    def get_current_score(self) -> Dict[str, Any]:
        """
        Get current governance score
        
        Returns:
            Current governance score
        """
        return self.score_engine.get_score()
    
    def replay_lifecycle(self) -> Dict[str, Any]:
        """
        Replay all governance events to reconstruct project state
        
        This method implements lifecycle replay functionality, which:
        1. Gets all events from EventStore
        2. Processes them in chronological order
        3. Reconstructs the project state
        4. Validates the current state against the reconstructed state
        
        Returns:
            Dict[str, Any]: Replay result with:
                - success: bool indicating if replay was successful
                - message: str with replay result message
                - reconstructed_state: Dict[str, Any] with the reconstructed state
                - validation_result: Dict[str, Any] with validation result
        """
        try:
            # 获取所有事件，按时间顺序排序
            events = self.event_store.list()
            # 按时间顺序排序（从最早到最新）
            events_sorted = sorted(events, key=lambda x: x.timestamp)
            
            if not events_sorted:
                return {
                    "success": True,
                    "message": "No events to replay",
                    "reconstructed_state": self.state.copy(),
                    "validation_result": {
                        "match": True,
                        "differences": []
                    }
                }
            
            # 创建一个新的状态管理器，用于重建状态
            from .state_manager import _StateManager as StateManager
            replay_state_manager = StateManager(self, os.path.join(self.project_root, "state_replay.json"))
            
            # 保存当前状态，用于后续比较
            current_state = self.state.copy()
            
            # 重新构建初始状态
            replay_state = replay_state_manager.load_state()
            
            # 保存当前内部标志，然后设置为True，模拟从handle_event内部调用
            original_inside_handle_event = self._inside_handle_event
            self._inside_handle_event = True
            
            try:
                # 按顺序重新处理所有事件
                for event in events_sorted:
                    # 保存事件状态，用于恢复
                    original_status = event.status
                    
                    # 创建一个事件副本，重置状态为OPEN
                    event_copy = event.model_copy(update={"status": EventStatus.OPEN})
                    
                    # 处理事件
                    self.state = replay_state.copy()
                    
                    # 1. 检测违规
                    violations = self.trigger_engine.detect_violations(event_copy, self.state)
                    
                    # 2. 决定行动
                    actions = self.policy_engine.decide(violations)
                    
                    # 3. 更新分数
                    score_update = self.score_engine.update(event_copy, violations, self.state)
                    
                    # 4. 应用行动
                    self._apply_actions(actions, event_copy)
                    
                    # 5. 更新状态
                    self._update_state(event_copy, violations, actions, score_update)
                    
                    # 6. 更新回放状态
                    replay_state = self.state.copy()
                    
                    # 恢复事件原始状态
                    event.status = original_status
            finally:
                # 恢复内部标志
                self._inside_handle_event = original_inside_handle_event
                # 恢复原始状态
                self.state = current_state
            
            # 验证当前状态与重建状态是否一致
            validation_result = self._validate_state_consistency(current_state, replay_state)
            
            return {
                "success": validation_result["match"],
                "message": f"Replay completed with {len(events_sorted)} events processed",
                "reconstructed_state": replay_state,
                "validation_result": validation_result
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Replay failed: {str(e)}",
                "reconstructed_state": None,
                "validation_result": {
                    "match": False,
                    "differences": [{
                        "field": "error",
                        "current_value": str(e),
                        "replay_value": "None"
                    }]
                }
            }
    
    def _validate_state_consistency(self, current_state: Dict[str, Any], replay_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate consistency between current state and reconstructed state
        
        Args:
            current_state: Current project state
            replay_state: Reconstructed project state
            
        Returns:
            Dict[str, Any]: Validation result with match and differences
        """
        differences = []
        
        # 获取所有唯一的字段名
        all_fields = set(current_state.keys()).union(set(replay_state.keys()))
        
        for field in all_fields:
            current_value = current_state.get(field)
            replay_value = replay_state.get(field)
            
            # 跳过动态字段，如timestamps
            if field in ["last_updated", "created_at", "freeze_at", "unfreeze_at"]:
                continue
            
            # 比较字段值
            if current_value != replay_value:
                differences.append({
                    "field": field,
                    "current_value": current_value,
                    "replay_value": replay_value
                })
        
        return {
            "match": len(differences) == 0,
            "differences": differences
        }


__all__ = ["GovernanceEngine"]