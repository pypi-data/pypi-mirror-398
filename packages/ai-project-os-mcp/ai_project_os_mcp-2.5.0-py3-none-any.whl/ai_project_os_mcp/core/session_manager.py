"""
Session Manager - 会话管理模块

该模块负责：
1. 为不同 Agent 分配独立的 Session
2. 记录 Session 状态
3. 记录每个 Agent 的操作日志
4. Session 过期和清理
"""

# Note: Module-level hard rejection removed to avoid import issues
# Instead, we use private classes and caller verification to enforce Single Gate Architecture

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances


import time
import json
from typing import Dict, Optional, List
from datetime import datetime

class _SessionManager:
    """
    会话管理类，负责 Session 创建、管理和操作日志记录
    """
    
    def __init__(self, caller):
        """
        初始化会话管理器
        
        Args:
            caller: 调用者，必须是 GovernanceEngine 实例
        """
        if caller.__class__.__name__ != "GovernanceEngine":
            raise RuntimeError("Unauthorized access to SessionManager")
        self.caller = caller
        
        # 存储 Session 信息
        self.sessions = {}
        
        # 存储操作日志
        self.operation_logs = {}
        
        # Session 有效期（小时）
        self.session_expiry_hours = 24
        
        # 最大操作日志数量（每个 Session）
        self.max_logs_per_session = 1000
    
    def create_session(self, agent_info: Dict) -> str:
        """
        为指定 Agent 创建 Session
        
        Args:
            agent_info: Agent 信息，包含 agent_id、role、permissions 等
            
        Returns:
            str: Session ID
        """
        agent_id = agent_info["agent_id"]
        session_id = f"{agent_id}:{int(time.time())}:{hash(json.dumps(agent_info)) % 10000:04d}"
        
        # 创建 Session
        self.sessions[session_id] = {
            "session_id": session_id,
            "agent_id": agent_id,
            "agent_role": agent_info["role"],
            "agent_name": agent_info["name"],
            "permissions": agent_info["permissions"],
            "created_at": int(time.time()),
            "expiry": int(time.time()) + (self.session_expiry_hours * 3600),
            "last_activity": int(time.time()),
            "status": "active"
        }
        
        # 初始化操作日志
        self.operation_logs[session_id] = []
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        获取 Session 信息
        
        Args:
            session_id: Session ID
            
        Returns:
            Optional[Dict]: Session 信息，若 Session 不存在或已过期则返回 None
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # 检查 Session 是否过期
        if int(time.time()) > session["expiry"]:
            self.close_session(session_id)
            return None
        
        return session.copy()
    
    def update_session_activity(self, session_id: str) -> bool:
        """
        更新 Session 活动时间
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: 更新成功返回 True，否则返回 False
        """
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]["last_activity"] = int(time.time())
        return True
    
    def close_session(self, session_id: str) -> bool:
        """
        关闭 Session
        
        Args:
            session_id: Session ID
            
        Returns:
            bool: 关闭成功返回 True，否则返回 False
        """
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "closed"
            return True
        return False
    
    def record_operation(self, session_id: str, operation: str, details: Dict, success: bool) -> bool:
        """
        记录 Agent 操作
        
        Args:
            session_id: Session ID
            operation: 操作名称
            details: 操作详情
            success: 操作是否成功
            
        Returns:
            bool: 记录成功返回 True，否则返回 False
        """
        if session_id not in self.sessions:
            return False
        
        # 更新 Session 活动时间
        self.update_session_activity(session_id)
        
        # 构建操作日志
        log_entry = {
            "timestamp": int(time.time()),
            "datetime": datetime.now().isoformat(),
            "operation": operation,
            "details": details,
            "success": success
        }
        
        # 记录日志
        if session_id not in self.operation_logs:
            self.operation_logs[session_id] = []
        
        self.operation_logs[session_id].append(log_entry)
        
        # 限制日志数量
        if len(self.operation_logs[session_id]) > self.max_logs_per_session:
            # 保留最新的日志
            self.operation_logs[session_id] = self.operation_logs[session_id][-self.max_logs_per_session:]
        
        return True
    
    def get_operation_logs(self, session_id: str, limit: int = 100) -> List[Dict]:
        """
        获取指定 Session 的操作日志
        
        Args:
            session_id: Session ID
            limit: 日志数量限制
            
        Returns:
            List[Dict]: 操作日志列表
        """
        if session_id not in self.operation_logs:
            return []
        
        # 返回最新的日志
        return self.operation_logs[session_id][-limit:]
    
    def list_active_sessions(self) -> List[Dict]:
        """
        列出所有活跃的 Session
        
        Returns:
            List[Dict]: 活跃 Session 列表
        """
        active_sessions = []
        current_time = int(time.time())
        
        for session_id, session in self.sessions.items():
            if session["status"] == "active" and current_time <= session["expiry"]:
                active_sessions.append(session.copy())
        
        return active_sessions
    
    def cleanup_expired_sessions(self) -> int:
        """
        清理过期的 Session
        
        Returns:
            int: 清理的 Session 数量
        """
        current_time = int(time.time())
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if session["status"] != "active":
                expired_sessions.append(session_id)
            elif current_time > session["expiry"]:
                expired_sessions.append(session_id)
        
        # 清理 Session 和日志
        for session_id in expired_sessions:
            if session_id in self.sessions:
                del self.sessions[session_id]
            if session_id in self.operation_logs:
                del self.operation_logs[session_id]
        
        return len(expired_sessions)
    
    def check_session_permission(self, session_id: str, action: str) -> bool:
        """
        检查 Session 是否有执行特定操作的权限

        Args:
            session_id: Session ID
            action: 要执行的操作

        Returns:
            bool: 有权限返回 True，否则返回 False
        """
        session = self.get_session(session_id)
        if not session:
            return False

        return action in session["permissions"]


__all__ = []
