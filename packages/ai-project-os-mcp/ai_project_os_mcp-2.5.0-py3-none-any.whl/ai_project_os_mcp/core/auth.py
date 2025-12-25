"""
Auth - 认证与授权模块

该模块负责：
1. 基于 Token 的 Agent 鉴权机制
2. Agent 权限管理
"""

import hashlib
import time
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

class _AuthManager:
    """
    认证管理类，负责 Token 生成、验证和权限管理
    """
    
    def __init__(self, caller):
        """
        初始化认证管理器
        
        Args:
            caller: 调用者，必须是 GovernanceEngine 实例
        """
        if caller.__class__.__name__ != "GovernanceEngine":
            raise RuntimeError("Unauthorized access to AuthManager")
        self.caller = caller
        
        # 存储 Agent 信息
        self.agents = {
            "planner": {
                "name": "Planner Agent",
                "role": "planner",
                "permissions": ["read_state", "write_state", "run_tests", "analyze_dependencies"],
                "secret": secrets.token_hex(32)
            },
            "coder": {
                "name": "Coder Agent",
                "role": "coder",
                "permissions": ["write_code", "run_tests", "submit_audit"],
                "secret": secrets.token_hex(32)
            },
            "reviewer": {
                "name": "Reviewer Agent",
                "role": "reviewer",
                "permissions": ["read_code", "verify_audit", "run_tests"],
                "secret": secrets.token_hex(32)
            }
        }
        
        # 存储 Token 信息
        self.tokens = {}
        
        # Token 有效期（小时）
        self.token_expiry_hours = 24
    
    def generate_token(self, agent_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        为指定 Agent 生成 Token
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (Token, 错误信息)
        """
        if agent_id not in self.agents:
            return None, f"Unknown agent: {agent_id}"
        
        # 生成 Token
        # 格式: agent_id:timestamp:signature
        timestamp = int(time.time())
        secret = self.agents[agent_id]["secret"]
        
        # 生成签名
        message = f"{agent_id}:{timestamp}"
        signature = hashlib.sha256(f"{message}:{secret}".encode("utf-8")).hexdigest()
        
        token = f"{agent_id}:{timestamp}:{signature}"
        
        # 存储 Token 信息
        self.tokens[token] = {
            "agent_id": agent_id,
            "timestamp": timestamp,
            "expiry": timestamp + (self.token_expiry_hours * 3600),
            "last_used": timestamp
        }
        
        return token, None
    
    def verify_token(self, token: str) -> Tuple[Optional[Dict], Optional[str]]:
        """
        验证 Token 有效性
        
        Args:
            token: 要验证的 Token
            
        Returns:
            Tuple[Optional[Dict], Optional[str]]: (Agent 信息, 错误信息)
        """
        if token not in self.tokens:
            return None, "Invalid token"
        
        token_info = self.tokens[token]
        agent_id = token_info["agent_id"]
        
        # 检查 Token 是否过期
        if time.time() > token_info["expiry"]:
            del self.tokens[token]
            return None, "Token expired"
        
        # 验证 Token 签名
        agent_secret = self.agents[agent_id]["secret"]
        try:
            parts = token.split(":")
            if len(parts) != 3:
                del self.tokens[token]
                return None, "Invalid token format"
            
            token_agent_id, token_timestamp, token_signature = parts
            message = f"{token_agent_id}:{token_timestamp}"
            expected_signature = hashlib.sha256(f"{message}:{agent_secret}".encode("utf-8")).hexdigest()
            
            if token_signature != expected_signature:
                del self.tokens[token]
                return None, "Invalid token signature"
        except Exception:
            del self.tokens[token]
            return None, "Invalid token format"
        
        # 更新 Token 最后使用时间
        self.tokens[token]["last_used"] = int(time.time())
        
        # 返回 Agent 信息
        agent_info = self.agents[agent_id].copy()
        # 不返回密钥
        agent_info.pop("secret")
        agent_info["token"] = token
        agent_info["expiry"] = token_info["expiry"]
        
        return agent_info, None
    
    def revoke_token(self, token: str) -> bool:
        """
        撤销 Token
        
        Args:
            token: 要撤销的 Token
            
        Returns:
            bool: 撤销成功返回 True，否则返回 False
        """
        if token in self.tokens:
            del self.tokens[token]
            return True
        return False
    
    def check_permission(self, agent_id: str, action: str) -> bool:
        """
        检查 Agent 是否有执行特定操作的权限
        
        Args:
            agent_id: Agent ID
            action: 要执行的操作
            
        Returns:
            bool: 有权限返回 True，否则返回 False
        """
        if agent_id not in self.agents:
            return False
        
        agent = self.agents[agent_id]
        return action in agent.get("permissions", [])
    
    def get_agent_permissions(self, agent_id: str) -> Optional[list]:
        """
        获取 Agent 的权限列表
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Optional[list]: 权限列表，若 Agent 不存在则返回 None
        """
        if agent_id not in self.agents:
            return None
        
        return self.agents[agent_id].get("permissions", [])
    
    def list_agents(self) -> Dict:
        """
        列出所有注册的 Agent
        
        Returns:
            Dict: Agent 列表
        """
        agents_list = {}
        for agent_id, agent_info in self.agents.items():
            # 不返回密钥
            safe_info = agent_info.copy()
            safe_info.pop("secret")
            agents_list[agent_id] = safe_info
        
        return agents_list
    
    def cleanup_expired_tokens(self) -> int:
        """
        清理过期 Token
        
        Returns:
            int: 清理的 Token 数量
        """
        current_time = int(time.time())
        expired_tokens = []
        
        for token, token_info in self.tokens.items():
            if current_time > token_info["expiry"]:
                expired_tokens.append(token)
        
        # 删除过期 Token
        for token in expired_tokens:
            del self.tokens[token]
        
        return len(expired_tokens)


__all__ = []
