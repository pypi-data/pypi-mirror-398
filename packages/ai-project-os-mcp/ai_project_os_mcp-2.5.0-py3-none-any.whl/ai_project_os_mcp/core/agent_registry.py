"""
Agent Registry - Manage agent registration, identity, permissions, and responsibility scopes

This module implements the core agent registry ensuring that:
- Agent registry is append-only
- Any change creates a new agent version
- Historical events bind to agent version, not agent_id alone
- Agents can only act within authorized responsibility scopes

Governance Rules:
- No Agent may directly communicate decisions to another Agent
- All inter-agent influence MUST be mediated by GovernanceEngine
- Agent registry is append-only
- Any change creates a new agent version
- Historical events bind to agent version, not agent_id alone
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

from .agent_models import (
    _GovernanceAgent,
    _AgentVersion,
    _AgentRegistration
)


class _AgentRegistry(BaseModel):
    """Agent注册中心
    
    负责Agent的注册、身份验证、权限管理和责任域管理
    确保Agent Registry是append-only的，任何变更都会创建新的Agent版本
    
    治理规则：
    - Agent Registry是append-only的
    - 任何变更都会创建新的Agent版本
    - 历史事件绑定到Agent版本，而不仅仅是Agent ID
    - Agents can only act within authorized responsibility scopes
    """
    
    # Internal state - Using Pydantic v2 syntax
    agents: Dict[str, Dict[str, _GovernanceAgent]] = Field(default_factory=dict, repr=False)
    agent_versions: Dict[str, List[_AgentVersion]] = Field(default_factory=dict, repr=False)
    current_versions: Dict[str, str] = Field(default_factory=dict, repr=False)
    
    class Config:
        pass
    
    def register_agent(self, registration: _AgentRegistration) -> _GovernanceAgent:
        """注册新Agent
        
        Args:
            registration: Agent注册请求
            
        Returns:
            创建的Agent实例
        """
        # Check if agent already exists
        if registration.agent_id in self.agents:
            # Agent already exists, create a new version
            current_version = self.current_versions[registration.agent_id]
            current_agent = self.agents[registration.agent_id][current_version]
            
            # Create new version
            # Extract major version from current_version (format: v1-uuid)
            major_version = int(current_version.split('-')[0][1:])
            new_version = f"v{major_version + 1}-{uuid.uuid4()}"
            
            # Create new agent instance
            new_agent = _GovernanceAgent(
                agent_id=registration.agent_id,
                agent_type=registration.agent_type,
                authority_scope=registration.authority_scope,
                responsibility_scope=registration.responsibility_scope,
                delegation_allowed=registration.delegation_allowed,
                registered_by=registration.registered_by,
                version=new_version,
                created_at=datetime.now(),
                is_active=True
            )
        else:
            # New agent, create first version
            new_version = f"v1-{uuid.uuid4()}"
            
            # Create new agent instance
            new_agent = _GovernanceAgent(
                agent_id=registration.agent_id,
                agent_type=registration.agent_type,
                authority_scope=registration.authority_scope,
                responsibility_scope=registration.responsibility_scope,
                delegation_allowed=registration.delegation_allowed,
                registered_by=registration.registered_by,
                version=new_version,
                created_at=datetime.now(),
                is_active=True
            )
            
            # Initialize agent records
            self.agents[registration.agent_id] = {}
            self.agent_versions[registration.agent_id] = []
        
        # Add agent to registry
        self.agents[registration.agent_id][new_version] = new_agent
        
        # Create and add version record
        version_record = _AgentVersion(
            agent_id=registration.agent_id,
            version=new_version,
            parent_version=self.current_versions.get(registration.agent_id),
            created_at=datetime.now(),
            created_by=registration.registered_by,
            change_log={
                "action": "REGISTER" if registration.agent_id not in self.current_versions else "UPDATE",
                "agent_type": registration.agent_type,
                "authority_scope": registration.authority_scope,
                "responsibility_scope": registration.responsibility_scope,
                "delegation_allowed": registration.delegation_allowed,
                "metadata": registration.metadata
            }
        )
        
        self.agent_versions[registration.agent_id].append(version_record)
        
        # Update current version
        self.current_versions[registration.agent_id] = new_version
        
        return new_agent
    
    def get_agent(self, agent_id: str, version: Optional[str] = None) -> Optional[_GovernanceAgent]:
        """获取Agent实例
        
        Args:
            agent_id: Agent ID
            version: Agent版本，可选，默认获取当前版本
            
        Returns:
            Agent实例，如果不存在则返回None
        """
        if agent_id not in self.agents:
            return None
        
        if version is None:
            # Get current version
            version = self.current_versions.get(agent_id)
            if version is None:
                return None
        
        return self.agents[agent_id].get(version)
    
    def get_current_agent(self, agent_id: str) -> Optional[_GovernanceAgent]:
        """获取当前版本的Agent实例
        
        Args:
            agent_id: Agent ID
            
        Returns:
            当前版本的Agent实例，如果不存在则返回None
        """
        return self.get_agent(agent_id)
    
    def get_agent_versions(self, agent_id: str) -> List[_AgentVersion]:
        """获取Agent的所有版本记录
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent的所有版本记录列表
        """
        return self.agent_versions.get(agent_id, [])
    
    def update_agent(self, agent_id: str, updates: Dict[str, Any], updated_by: str) -> _GovernanceAgent:
        """更新Agent信息
        
        Args:
            agent_id: Agent ID
            updates: 更新内容
            updated_by: 更新人ID
            
        Returns:
            更新后的Agent实例
        """
        # Get current agent
        current_agent = self.get_current_agent(agent_id)
        if current_agent is None:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Create registration request with updates
        registration = _AgentRegistration(
            agent_id=agent_id,
            agent_type=updates.get("agent_type", current_agent.agent_type),
            authority_scope=updates.get("authority_scope", current_agent.authority_scope),
            responsibility_scope=updates.get("responsibility_scope", current_agent.responsibility_scope),
            delegation_allowed=updates.get("delegation_allowed", current_agent.delegation_allowed),
            registered_by=updated_by,
            metadata=updates.get("metadata", {})
        )
        
        # Register as new version
        return self.register_agent(registration)
    
    def deactivate_agent(self, agent_id: str, deactivated_by: str) -> _GovernanceAgent:
        """停用Agent
        
        Args:
            agent_id: Agent ID
            deactivated_by: 停用操作的执行实体ID
            
        Returns:
            停用后的Agent实例
        """
        # Get current agent
        current_agent = self.get_current_agent(agent_id)
        if current_agent is None:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Create registration request with is_active=False
        registration = _AgentRegistration(
            agent_id=agent_id,
            agent_type=current_agent.agent_type,
            authority_scope=current_agent.authority_scope,
            responsibility_scope=current_agent.responsibility_scope,
            delegation_allowed=current_agent.delegation_allowed,
            registered_by=deactivated_by,
            metadata={}
        )
        
        # Register new version with is_active=False
        new_agent = self.register_agent(registration)
        
        # Create new agent instance with is_active=False
        deactivated_agent = new_agent.copy(update={"is_active": False})
        
        # Update registry with deactivated agent
        self.agents[agent_id][new_agent.version] = deactivated_agent
        
        return deactivated_agent
    
    def is_agent_authorized(self, agent_id: str, action: str, scope: str) -> bool:
        """检查Agent是否被授权执行特定动作
        
        Args:
            agent_id: Agent ID
            action: 要执行的动作
            scope: 动作涉及的范围
            
        Returns:
            如果Agent被授权则返回True，否则返回False
        """
        # Get current agent
        agent = self.get_current_agent(agent_id)
        if agent is None:
            return False
        
        # Check if agent is active
        if not agent.is_active:
            return False
        
        # Check if action is in authority scope
        if action not in agent.authority_scope:
            return False
        
        # Check if scope is in responsibility scope
        if scope not in agent.responsibility_scope:
            return False
        
        return True
    
    def validate_agent_action(self, agent_id: str, action: str, scope: str) -> bool:
        """验证Agent动作是否合法
        
        Args:
            agent_id: Agent ID
            action: 要执行的动作
            scope: 动作涉及的范围
            
        Returns:
            如果动作合法则返回True，否则返回False
        """
        return self.is_agent_authorized(agent_id, action, scope)
    
    def get_all_agents(self) -> List[_GovernanceAgent]:
        """获取所有Agent的当前版本
        
        Returns:
            所有Agent的当前版本列表
        """
        return [self.get_current_agent(agent_id) for agent_id in self.current_versions.keys() if self.get_current_agent(agent_id) is not None]
    
    def get_active_agents(self) -> List[_GovernanceAgent]:
        """获取所有活跃的Agent
        
        Returns:
            所有活跃的Agent列表
        """
        return [agent for agent in self.get_all_agents() if agent.is_active]
    
    class Config:
        pass


__all__ = []
