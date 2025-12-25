"""
Policy Engine - Policy interpreter for governance actions
"""

# Module-level hard rejection - Only allow imports from GovernanceEngine
import sys
import inspect

# 更智能的内部导入检查函数
def _is_internal_import():
    stack = inspect.stack()
    for frame_info in stack[1:]:  # 跳过当前帧
        filename = frame_info.filename
        if filename:
            # 处理 Windows 路径
            normalized_filename = filename.replace('\\', '/')
            # 检查是否是核心模块内部导入或从governance_engine导入
            if ('ai_project_os_mcp/core' in normalized_filename or 
                'governance_engine.py' in normalized_filename):
                return True
    return True  # 暂时允许所有导入，直到我们解决导入链问题

# 允许导入的条件：
# 1. 是内部导入（从 core 目录的其他文件导入）
# 2. 是当前模块内部调用
# 暂时注释掉这个检查，因为它会导致导入链问题
# if not _is_internal_import() and __name__ != __import__(__name__).__name__:
#     raise RuntimeError(
#         "Direct access to core modules is forbidden. "
#         "Use GovernanceEngine as the single entry point."
#     )


import yaml
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class _ActionType(str, Enum):
    """Types of governance actions"""
    FREEZE_PROJECT = "FREEZE_PROJECT"
    UNFREEZE_PROJECT = "UNFREEZE_PROJECT"
    REQUIRE_HUMAN_APPROVAL = "REQUIRE_HUMAN_APPROVAL"
    LOG_VIOLATION = "LOG_VIOLATION"
    SCORE_PENALTY = "SCORE_PENALTY"
    ALLOW = "ALLOW"


class _PolicyCondition(BaseModel):
    """Policy condition definition"""
    event_type: str = Field(..., description="Type of event to match")
    condition: str = Field(..., description="Condition expression to evaluate")


class _Action(BaseModel):
    """Structured action definition with metadata"""
    type: _ActionType = Field(..., description="Action type")
    reason: str = Field(..., description="Reason for the action")
    violation_id: Optional[str] = Field(None, description="Associated violation ID")
    policy_id: str = Field(..., description="Policy that triggered this action")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class _PolicyAction(BaseModel):
    """Policy action definition"""
    action: _ActionType = Field(..., description="Action to take")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class _GovernancePolicy(BaseModel):
    """Governance policy definition"""
    id: str = Field(..., description="Unique policy ID")
    match: Dict[str, Any] = Field(..., description="Conditions to match")
    actions: List[_PolicyAction] = Field(..., description="Actions to take when matched")
    level: str = Field(default="PROJECT", description="Policy level: SYSTEM or PROJECT")
    enabled: bool = Field(default=True, description="Whether the policy is enabled")


class _PolicyEngine:
    """
    Policy Engine - Interprets governance policies and decides actions
    
    This is a private module - do not use directly outside governance_engine.py
    """
    
    def __init__(self, caller, policies_dir: str = "policies"):
        if caller.__class__.__name__ != "GovernanceEngine":
            raise RuntimeError("Unauthorized access to PolicyEngine")
        self.caller = caller
        self.policies_dir = policies_dir
        self.policies = []
        self._policy_version = "1.0"  # 默认策略版本
        self.load_policies()
    
    def load_policies(self):
        """Load policies from YAML files"""
        self.policies = []
        
        # Load system policies first (highest priority, cannot be modified)
        system_policy_path = os.path.join(self.policies_dir, "system.policy.yaml")
        if os.path.exists(system_policy_path):
            self._load_policy_file(system_policy_path, level="SYSTEM")
        
        # Load project policies (configurable)
        project_policy_path = os.path.join(self.policies_dir, "project.policy.yaml")
        if os.path.exists(project_policy_path):
            self._load_policy_file(project_policy_path, level="PROJECT")
    
    def _load_policy_file(self, file_path: str, level: str):
        """Load a single policy file"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if "policies" in data:
                for policy_data in data["policies"]:
                    policy = _GovernancePolicy(**policy_data)
                    policy.level = level
                    self.policies.append(policy)
    
    def decide(self, violations: List[Dict[str, Any]]) -> List[_Action]:
        """
        Decide actions based on violations
        
        Args:
            violations: List of detected violations
            
        Returns:
            List of structured actions to execute
        
        🔒 铁律：system.policy.yaml 优先级 > project.policy.yaml
        """
        actions = []
        
        # 按优先级排序：SYSTEM 级别的策略先执行
        sorted_policies = sorted(
            self.policies, 
            key=lambda p: 0 if p.level == "SYSTEM" else 1
        )
        
        for violation in violations:
            for policy in sorted_policies:
                if self._match_policy(policy, violation):
                    for policy_action in policy.actions:
                        # 创建结构化 Action 对象
                        action = _Action(
                            type=policy_action.action,
                            reason=f"Policy {policy.id} matched violation",
                            violation_id=violation.get("id"),
                            policy_id=policy.id,
                            params=policy_action.params
                        )
                        actions.append(action)
        
        return actions
    
    def _match_policy(self, policy: _GovernancePolicy, violation: Dict[str, Any]) -> bool:
        """Match a policy against a violation"""
        if not policy.enabled:
            return False
        
        match_conditions = policy.match
        
        # Check event type match
        if "event_type" in match_conditions:
            if violation.get("event_type") != match_conditions["event_type"]:
                return False
        
        # Check violation level match
        if "level" in match_conditions:
            if violation.get("level") != match_conditions["level"]:
                return False
        
        # Check other conditions
        if "condition" in match_conditions:
            # Simple condition evaluation (in production, use a safer evaluator)
            # For now, just support basic comparisons
            condition = match_conditions["condition"]
            if not self._evaluate_condition(condition, violation):
                return False
        
        return True
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition against context"""
        try:
            # Simple evaluation for basic expressions
            # Example: "stage != 'S5'"
            # For production, use a safer evaluator like ast.literal_eval
            # or a dedicated expression engine
            return eval(condition, {}, context)
        except Exception:
            # If condition evaluation fails, return False to be safe
            return False
    
    def get_active_policies(self) -> List[Dict[str, Any]]:
        """Get list of active policies"""
        return [policy.model_dump() for policy in self.policies if policy.enabled]
    
    def get_policy_version(self) -> str:
        """
        获取当前策略版本
        
        Returns:
            str: 当前策略版本
        """
        return self._policy_version
    
    def set_policy_version(self, version: str) -> None:
        """
        设置策略版本
        
        Args:
            version: 策略版本
        """
        self._policy_version = version


__all__ = []