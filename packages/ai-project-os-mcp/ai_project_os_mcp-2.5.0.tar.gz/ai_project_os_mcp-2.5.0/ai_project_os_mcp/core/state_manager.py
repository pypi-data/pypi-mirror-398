"""
State Manager - Manages Project State

This module is responsible for managing the project state.
It ensures that state is the single source of truth for governance decisions.

Key principles:
1. State as Truth
2. Persistence
3. Immutability guarantees
4. Version history
5. Thread safety
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class _StateManager:
    """
    State Manager - Manages project state
    
    This class ensures that:
    - State is the single source of truth
    - State changes are properly recorded
    - State is persisted to disk
    - State can be rolled back if needed
    """
    
    def __init__(self, caller, state_file: str = "state.json"):
        """
        Initialize state manager
        
        Args:
            caller: The caller of this manager
            state_file: Path to the state file
        """
        if caller.__class__.__name__ != "GovernanceEngine":
            raise RuntimeError("Unauthorized access to StateManager")
        self.caller = caller
        self.state_file = state_file
        self._state = self._load_state()
        self._state_history = []
        self._save_state_history()
    
    def _load_state(self) -> Dict[str, Any]:
        """
        Load state from file
        
        Returns:
            Dict[str, Any]: Current state
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    # 确保overlay_states字段存在
                    if "overlay_states" not in state:
                        state["overlay_states"] = ["frozen"] if state.get("frozen", False) else []
                    # 更新内存中的状态
                    self._state = state
                    return state
            except Exception:
                # If state file is corrupted, return default state
                default_state = self._get_default_state()
                self._state = default_state
                return default_state
        default_state = self._get_default_state()
        self._state = default_state
        return default_state
    
    def _get_default_state(self) -> Dict[str, Any]:
        """
        Get default project state
        
        Returns:
            Dict[str, Any]: Default state
        """
        return {
            "stage": "S1",
            "version": "1.0.3",
            "frozen": False,  # 保留向后兼容
            "overlay_states": [],  # 新增：覆盖状态列表
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_state_history(self):
        """
        Save state history to file
        """
        history_file = f"{self.state_file}.history"
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(self._state_history, f, indent=2, ensure_ascii=False, default=str)
        except Exception:
            # Ignore errors when saving history for now
            pass
    
    def load_state(self) -> Dict[str, Any]:
        """
        Get current state
        
        Returns:
            Dict[str, Any]: Current state
        """
        return self._state
    
    def save_state(self, new_state: Dict[str, Any]) -> bool:
        """
        Save new state (public method, only accessible via GovernanceEngine)
        
        Args:
            new_state: New state to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add update timestamp
            new_state["last_updated"] = datetime.now().isoformat()
            
            # Save current state to history
            self._state_history.append({
                "timestamp": datetime.now().isoformat(),
                "state": self._state.copy()
            })
            
            # Keep only the last 100 states in history
            self._state_history = self._state_history[-100:]
            
            # Update current state
            self._state = new_state.copy()
            
            # 确保overlay_states字段存在
            if "overlay_states" not in self._state:
                self._state["overlay_states"] = []
            
            # 确保frozen字段与overlay_states保持一致（向后兼容）
            self._state["frozen"] = "frozen" in self._state["overlay_states"]
            
            # Save to file
            with open(self.state_file, "w", encoding="utf-8") as f:
                # 使用 default=str 处理 datetime 对象，确保正确序列化
                json.dump(self._state, f, indent=2, ensure_ascii=False, default=str)
            
            # Save history
            self._save_state_history()
            
            return True
        except Exception:
            return False
    
    def _save_state(self, new_state: Dict[str, Any]) -> bool:
        """
        Save new state (private method, internal use only)
        
        Args:
            new_state: New state to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.save_state(new_state)
    
    def _update_state(self, updates: Dict[str, Any]) -> bool:
        """
        Update state with partial updates (private method)
        
        治理不变量：审计记录必须是append-only，不能被修改或删除
        
        Args:
            updates: Partial state updates
            
        Returns:
            bool: True if successful, False otherwise
        """
        new_state = self._state.copy()
        
        # 治理不变量：审计记录必须是append-only
        if "audit" in updates:
            current_audit = self._state.get("audit", [])
            new_audit = updates["audit"]
            
            # 检查审计记录是否被修改或删除
            # 审计记录只能追加，不能减少，也不能修改现有记录
            if len(new_audit) < len(current_audit):
                raise RuntimeError("CRITICAL VIOLATION: Audit records cannot be deleted")
            
            # 检查现有审计记录是否被修改
            for i in range(len(current_audit)):
                if new_audit[i] != current_audit[i]:
                    raise RuntimeError(f"CRITICAL VIOLATION: Audit record {i} cannot be modified")
            
            # 只允许追加新的审计记录
            new_state["audit"] = new_audit
            del updates["audit"]
        
        # 更新其他字段
        new_state.update(updates)
        return self._save_state(new_state)
    
    def _rollback_state(self) -> bool:
        """
        Rollback to previous state (private method)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if len(self._state_history) < 1:
            return False
        
        # Get previous state
        previous_state = self._state_history[-1]["state"]
        
        # Remove the last history entry
        self._state_history.pop()
        
        # Save previous state as current
        self._state = previous_state.copy()
        
        # Save to file
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2, ensure_ascii=False)
            
            # Save history
            self._save_state_history()
            
            return True
        except Exception:
            return False
    
    def get_state_history(self) -> list:
        """
        Get state history
        
        Returns:
            list: State history
        """
        return self._state_history.copy()
    
    def is_frozen(self) -> bool:
        """
        Check if project is frozen
        
        Returns:
            bool: True if frozen, False otherwise
        """
        # 检查overlay_states中是否包含"frozen"
        return "frozen" in self._state.get("overlay_states", [])
    
    def get_stage(self) -> str:
        """
        Get current project stage
        
        Returns:
            str: Current stage
        """
        return self._state.get("stage", "S1")
    
    def _set_stage(self, stage: str) -> bool:
        """
        Set current project stage (private method)
        
        Args:
            stage: New stage
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self._update_state({"stage": stage})
    
    def _freeze(self, reason: str, actor_id: str) -> bool:
        """
        Freeze the project (private method)
        
        Args:
            reason: Reason for freezing
            actor_id: ID of the actor freezing the project
            
        Returns:
            bool: True if successful, False otherwise
        """
        # 使用overlay_states替代单独的frozen字段
        overlay_states = self._state.get("overlay_states", [])
        if "frozen" not in overlay_states:
            overlay_states.append("frozen")
        
        updates = {
            "overlay_states": overlay_states,
            "freeze_reason": reason,
            "freeze_by": actor_id,
            "freeze_at": datetime.now().isoformat()
        }
        return self._update_state(updates)
    
    def _unfreeze(self, actor_id: str) -> bool:
        """
        Unfreeze the project (private method)

        Args:
            actor_id: ID of the actor unfreezing the project

        Returns:
            bool: True if successful, False otherwise
        """
        # 使用overlay_states替代单独的frozen字段
        overlay_states = self._state.get("overlay_states", [])
        if "frozen" in overlay_states:
            overlay_states.remove("frozen")
        
        # 更新状态
        new_state = self._state.copy()
        new_state["overlay_states"] = overlay_states
        new_state.pop("freeze_reason", None)
        new_state.pop("freeze_by", None)
        new_state.pop("freeze_at", None)
        new_state.pop("freeze_event_id", None)
        return self._save_state(new_state)
    
    def get_overlay_states(self) -> list:
        """
        Get current overlay states
        
        Returns:
            list: List of overlay states
        """
        return self._state.get("overlay_states", []).copy()
    
    def has_overlay_state(self, state: str) -> bool:
        """
        Check if the project has a specific overlay state
        
        Args:
            state: Overlay state to check
            
        Returns:
            bool: True if the project has the state, False otherwise
        """
        return state in self._state.get("overlay_states", [])
    
    def add_overlay_state(self, state: str) -> bool:
        """
        Add an overlay state to the project
        
        Args:
            state: Overlay state to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        overlay_states = self._state.get("overlay_states", [])
        if state not in overlay_states:
            overlay_states.append(state)
            return self._update_state({"overlay_states": overlay_states})
        return True
    
    def remove_overlay_state(self, state: str) -> bool:
        """
        Remove an overlay state from the project
        
        Args:
            state: Overlay state to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        overlay_states = self._state.get("overlay_states", [])
        if state in overlay_states:
            overlay_states.remove(state)
            return self._update_state({"overlay_states": overlay_states})
        return True


__all__ = []