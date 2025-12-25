"""
Governance Acceptance Tests - v2.5 核心功能验收测试

测试场景：
1. S3 写代码 → FREEZE
2. 无 Actor → REJECT
3. CRITICAL → global score 扣 30
4. 冻结后 CODE_GENERATION → BLOCKED
"""

import pytest
from ai_project_os_mcp.core import GovernanceEngine
from ai_project_os_mcp.core.events import GovernanceEvent, EventType, Actor
from ai_project_os_mcp.core.violation import ViolationLevel


class TestGovernanceAcceptance:
    """治理验收测试类"""
    
    def setup_method(self):
        """设置测试环境"""
        self.governance_engine = GovernanceEngine(".")
    
    def test_s3_code_generation_triggers_freeze(self):
        """测试场景1：S3 写代码 → FREEZE"""
        # 创建 Actor
        actor = Actor(
            id="test_actor",
            role="coder",
            role_type="AI",
            source="trae",
            name="Test AI Coder"
        )
        
        # 创建 CODE_GENERATION 事件，stage 为 S3
        event = GovernanceEvent(
            event_type=EventType.CODE_GENERATION,
            actor=actor,
            payload={
                "stage": "S3",
                "code": "print('test code')"
            }
        )
        
        # 处理事件
        result = self.governance_engine.handle_event(event)
        
        # 验证结果
        assert result["status"] == "FAILED", "S3 写代码应该失败"
        
        # 验证至少有一个 CRITICAL 违规
        critical_violations = [v for v in result["violations"] if v["level"] == ViolationLevel.CRITICAL]
        assert len(critical_violations) > 0, "S3 写代码应该产生 CRITICAL 违规"
        
        # 验证状态被冻结
        state = self.governance_engine.get_state()
        assert state["is_frozen"] == True, "S3 写代码应该导致项目冻结"
    
    def test_anonymous_event_rejected(self):
        """测试场景2：无 Actor → REJECT"""
        # 创建 CODE_GENERATION 事件，不设置 actor（会在 handle_event 中被拒绝）
        # 这里我们需要直接测试 handle_event 方法对无 actor 的处理
        # 注意：GovernanceEvent 模型要求 actor 是必填字段，所以我们需要测试模型验证
        
        # 创建 Actor
        actor = None  # 无 actor
        
        # 尝试创建事件（应该失败，因为 actor 是必填字段）
        # 但我们需要测试 handle_event 方法的处理
        
        # 创建带有 actor 的事件，然后手动将其设为 None
        event = GovernanceEvent(
            event_type=EventType.CODE_GENERATION,
            actor=Actor(id="temp", role="coder", role_type="AI", source="trae", name="Test"),
            payload={"stage": "S3"}
        )
        
        # 这里我们需要修改事件的 actor 属性，使其为 None
        # 注意：这是为了测试 handle_event 方法的验证逻辑
        event.actor = None
        
        # 处理事件
        result = self.governance_engine.handle_event(event)
        
        # 验证结果
        assert result["status"] == "FAILED", "无 Actor 的事件应该失败"
        
        # 验证有 anonymous_event 违规
        anonymous_violations = [v for v in result["violations"] if v["rule_id"] == "anonymous_event"]
        assert len(anonymous_violations) > 0, "无 Actor 的事件应该产生 anonymous_event 违规"
    
    def test_critical_violation_causes_global_score_decay(self):
        """测试场景3：CRITICAL → global score 扣 30"""
        # 获取初始状态
        initial_state = self.governance_engine.get_state()
        initial_global_score = initial_state["score"]["global"]
        
        # 创建 Actor
        actor = Actor(
            id="test_actor",
            role="coder",
            role_type="AI",
            source="trae",
            name="Test AI Coder"
        )
        
        # 创建 CODE_GENERATION 事件，stage 为 S3（会产生 CRITICAL 违规）
        event = GovernanceEvent(
            event_type=EventType.CODE_GENERATION,
            actor=actor,
            payload={
                "stage": "S3",
                "code": "print('test code')"
            }
        )
        
        # 处理事件
        result = self.governance_engine.handle_event(event)
        
        # 获取处理后的状态
        new_state = self.governance_engine.get_state()
        new_global_score = new_state["score"]["global"]
        
        # 计算分数变化
        global_score_change = new_global_score - initial_global_score
        stage_score_change = new_state["score"]["stage"] - initial_state["score"]["stage"]
        
        # 验证 global score 减少了 30（CRITICAL 违规的扣分）
        assert global_score_change == -30, f"CRITICAL 违规应该导致 global score 扣 30，实际变化为 {global_score_change}"

        # 验证 stage score 也减少了（根据配置）
        assert stage_score_change <= 0, "CRITICAL 违规应该导致 stage score 不增加"
        assert global_score_change < 0, "CRITICAL 违规应该导致 global score 减少"
    
    def test_code_generation_blocked_when_frozen(self):
        """测试场景4：冻结后 CODE_GENERATION → BLOCKED"""
        # 1. 首先冻结项目
        actor = Actor(
            id="test_actor",
            role="system",
            role_type="SYSTEM",
            source="api",
            name="Test System"
        )
        
        # 创建 FREEZE_REQUEST 事件
        freeze_event = GovernanceEvent(
            event_type=EventType.FREEZE_REQUEST,
            actor=actor,
            payload={
                "target_stage": "S5",
                "current_stage": "S4"
            }
        )
        
        # 处理冻结事件
        freeze_result = self.governance_engine.handle_event(freeze_event)
        
        # 验证项目被冻结
        frozen_state = self.governance_engine.get_state()
        assert frozen_state["is_frozen"] == True, "项目应该被成功冻结"
        
        # 2. 然后尝试在冻结状态下创建 CODE_GENERATION 事件
        code_event = GovernanceEvent(
            event_type=EventType.CODE_GENERATION,
            actor=actor,
            payload={
                "stage": "S5",
                "code": "print('test code in frozen state')"
            }
        )
        
        # 处理代码生成事件
        code_result = self.governance_engine.handle_event(code_event)
        
        # 验证结果：应该失败，因为项目处于冻结状态
        assert code_result["status"] == "FAILED", "冻结状态下的 CODE_GENERATION 事件应该失败"
        
        # 验证有 frozen_project 违规
        frozen_violations = [v for v in code_result["violations"] if v["rule_id"] == "frozen_project"]
        assert len(frozen_violations) > 0, "冻结状态下的 CODE_GENERATION 事件应该产生 frozen_project 违规"
    
    def test_unfreeze_event_allowed_when_frozen(self):
        """测试：冻结状态下允许 UNFREEZE 事件"""
        # 1. 首先冻结项目
        actor = Actor(
            id="test_actor",
            role="system",
            role_type="SYSTEM",
            source="api",
            name="Test System"
        )
        
        # 创建 FREEZE_REQUEST 事件
        freeze_event = GovernanceEvent(
            event_type=EventType.FREEZE_REQUEST,
            actor=actor,
            payload={
                "target_stage": "S5",
                "current_stage": "S4"
            }
        )
        
        # 处理冻结事件
        freeze_result = self.governance_engine.handle_event(freeze_event)
        
        # 验证项目被冻结
        frozen_state = self.governance_engine.get_state()
        assert frozen_state["is_frozen"] == True, "项目应该被成功冻结"
        
        # 2. 然后尝试在冻结状态下创建 UNFREEZE 事件
        unfreeze_event = GovernanceEvent(
            event_type=EventType.UNFREEZE,
            actor=actor,
            payload={}
        )
        
        # 处理解冻事件
        unfreeze_result = self.governance_engine.handle_event(unfreeze_event)
        
        # 验证结果：应该成功
        assert unfreeze_result["status"] == "PASSED", "冻结状态下的 UNFREEZE 事件应该成功"
        
        # 验证项目被解冻
        unfrozen_state = self.governance_engine.get_state()
        assert unfrozen_state["is_frozen"] == False, "项目应该被成功解冻"
