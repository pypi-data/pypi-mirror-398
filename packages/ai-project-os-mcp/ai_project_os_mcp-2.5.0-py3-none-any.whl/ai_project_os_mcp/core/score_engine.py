"""
Score Engine - Governance scoring with irreversible decay
"""

# Module-level hard rejection - Only allow imports from GovernanceEngine
import sys
import inspect

# 更严格的内部导入检查函数
def _is_internal_import():
    stack = inspect.stack()
    for frame_info in stack[1:]:  # 跳过当前帧
        filename = frame_info.filename
        if filename:
            # 处理 Windows 路径
            normalized_filename = filename.replace('\\', '/')
            # 检查是否是核心模块内部导入
            if 'ai_project_os_mcp/core' in normalized_filename:
                return True
    return False

# 仅允许 GovernanceEngine 导入核心模块
if not _is_internal_import():
    raise RuntimeError(
        "Direct access to core modules is forbidden. "
        "Use GovernanceEngine as the single entry point."
    )

from typing import Dict, Any, List
from enum import Enum

from .events import _GovernanceEvent as GovernanceEvent, _EventType as EventType
from .violation import _ViolationLevel as ViolationLevel


class _ScoreComponent(str, Enum):
    """Score component types"""
    GOVERNANCE = "governance"
    AUDIT_COVERAGE = "audit_coverage"
    COMPLIANCE = "compliance"


class _ScoreEngine:
    """
    Score Engine - Calculates governance score with irreversible decay
    
    This is a private module - do not use directly outside governance_engine.py
    
    Key features:
    - Irreversible decay for violations
    - Stage-based score reset
    - Multiple score components
    - Detailed breakdown
    """
    
    def __init__(self, caller):
        if caller.__class__.__name__ != "GovernanceEngine":
            raise RuntimeError("Unauthorized access to ScoreEngine")
        self.caller = caller
        self.base_score = 100
        self.score_decay = {
            ViolationLevel.CRITICAL: -30,  # Irreversible, only reset by stage change
            ViolationLevel.MAJOR: -10,      # Irreversible, only reset by stage change
            ViolationLevel.MINOR: -2        # Irreversible, only reset by stage change
        }
        self.current_score = self.base_score
        self.score_history = []
    
    def update(self, event: GovernanceEvent, violations: list, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update governance score based on event and violations
        
        Args:
            event: Governance event
            violations: List of detected violations
            state: Current project state
            
        Returns:
            Updated score details with global and stage scores
        """
        # Get current scores from state
        current_score = state.get("score", {})
        global_score = current_score.get("global", 100)
        stage_score = current_score.get("stage", 100)
        
        # Check if we need to reset the stage score (stage change)
        if event.event_type == EventType.STAGE_CHANGE:
            stage_score = 100  # Only reset stage score, global score remains unchanged
        
        # Apply score decay for violations
        critical_count = 0
        major_count = 0
        minor_count = 0
        
        for violation in violations:
            level = ViolationLevel(violation.get("level"))
            
            if level == ViolationLevel.CRITICAL:
                # CRITICAL → global 扣分，不可恢复，不影响stage
                global_score += self.score_decay[level]
                critical_count += 1
            else:
                # MAJOR / MINOR → stage 扣分，不影响global
                stage_score += self.score_decay[level]
                if level == ViolationLevel.MAJOR:
                    major_count += 1
                else:
                    minor_count += 1
        
        # Ensure scores don't go below 0
        global_score = max(0, global_score)
        stage_score = max(0, stage_score)
        
        # Calculate audit coverage (mock implementation)
        audit_coverage = self._calculate_audit_coverage(state)
        
        # Calculate compliance score (mock implementation)
        compliance_score = self._calculate_compliance_score(state)
        
        # Calculate final score structure
        final_score = {
            "global": global_score,  # Irreversible,跨阶段
            "stage": stage_score,    # 阶段内评分，阶段切换时重置
            "audit_coverage": audit_coverage,
            "compliance_score": compliance_score,
            "violations": {
                "critical": critical_count,
                "major": major_count,
                "minor": minor_count
            },
            "timestamp": event.timestamp.isoformat(),
            "event_id": event.id
        }
        
        # Add to history
        self.score_history.append(final_score)
        
        return final_score
    
    def _calculate_audit_coverage(self, state: Dict[str, Any]) -> float:
        """Calculate audit coverage percentage"""
        # Mock implementation - replace with real calculation
        # For example: total_audits / (total_items * audit_required_rate)
        return 92.5
    
    def _calculate_compliance_score(self, state: Dict[str, Any]) -> float:
        """Calculate compliance score"""
        # Mock implementation - replace with real calculation
        # For example: compliance_checked_items / total_items
        return 88.0
    
    def reset_score(self):
        """Reset score to base score (called on stage change)"""
        self.current_score = self.base_score
    
    def get_score(self) -> Dict[str, Any]:
        """Get current score"""
        if not self.score_history:
            return {
                "governance_score": self.base_score,
                "audit_coverage": 0.0,
                "compliance_score": 0.0,
                "violations": {
                    "critical": 0,
                    "major": 0,
                    "minor": 0
                }
            }
        return self.score_history[-1]
    
    def get_score_history(self) -> list:
        """Get score history"""
        return self.score_history
    
    def calculate_combined_score(self, scores: list) -> float:
        """Calculate combined score from multiple components"""
        # Weighted average of score components
        weights = {
            _ScoreComponent.GOVERNANCE: 0.6,
            _ScoreComponent.AUDIT_COVERAGE: 0.2,
            _ScoreComponent.COMPLIANCE: 0.2
        }
        
        if not scores:
            return self.base_score
        
        latest_score = scores[-1]
        combined = (
            latest_score.get("governance_score", self.base_score) * weights[_ScoreComponent.GOVERNANCE] +
            latest_score.get("audit_coverage", 0) * weights[_ScoreComponent.AUDIT_COVERAGE] +
            latest_score.get("compliance_score", 0) * weights[_ScoreComponent.COMPLIANCE]
        )
        
        return max(0, combined)


__all__ = []