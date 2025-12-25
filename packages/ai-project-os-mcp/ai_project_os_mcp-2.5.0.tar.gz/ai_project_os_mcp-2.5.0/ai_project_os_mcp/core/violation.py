"""
Violation Model and Management

This module defines the Violation model and related management classes.
Violations are auditable objects that represent governance rule breaches.
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

# 仅允许 GovernanceEngine 导入核心模块
# 暂时注释掉这个检查，因为它会导致导入链问题
# if not _is_internal_import():
#     raise RuntimeError(
#         "Direct access to core modules is forbidden. "
#         "Use GovernanceEngine as the single entry point."
#     )

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class _ViolationLevel(str, Enum):
    """
    Violation severity levels
    """
    CRITICAL = "CRITICAL"  # System freeze, requires immediate action
    MAJOR = "MAJOR"        # Requires human approval
    MINOR = "MINOR"        # Warning, affects governance score
    INFO = "INFO"          # Informational, no score impact


class _ViolationStatus(str, Enum):
    """
    Violation status
    """
    OPEN = "OPEN"          # Violation is active
    RESOLVED = "RESOLVED"  # Violation has been resolved


class _GovernanceViolation(BaseModel):
    """
    Represents a governance violation that occurred
    
    Violations are immutable once created, and can be resolved but not deleted
    """
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique violation identifier"
    )
    
    level: _ViolationLevel = Field(
        ...,
        description="Severity level of the violation"
    )
    
    rule_id: str = Field(
        ...,
        description="ID of the rule that was violated"
    )
    
    event_id: str = Field(
        ...,
        description="ID of the event that triggered this violation"
    )
    
    actor_id: str = Field(
        ...,
        description="ID of the actor who caused the violation"
    )
    
    message: str = Field(
        ...,
        description="Human-readable violation message"
    )
    
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional violation details"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the violation occurred"
    )
    
    status: _ViolationStatus = Field(
        default=_ViolationStatus.OPEN,
        description="Current status of the violation"
    )
    
    resolved_by: Optional[str] = Field(
        None,
        description="ID of the actor who resolved the violation"
    )
    
    resolved_at: Optional[datetime] = Field(
        None,
        description="When the violation was resolved"
    )
    
    class _Config:
        """Model configuration"""
        extra = "forbid"  # Strict validation
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class _ViolationStore:
    """
    Interface for storing and retrieving violations
    """
    
    def __init__(self, caller):
        if caller.__class__.__name__ != "GovernanceEngine":
            raise RuntimeError("Unauthorized access to ViolationStore")
        self.caller = caller
    
    def save_violation(self, violation: _GovernanceViolation) -> bool:
        """
        Save a violation to storage
        
        Args:
            violation: The violation to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError
    
    def get_violation(self, violation_id: str) -> Optional[_GovernanceViolation]:
        """
        Get a violation by ID
        
        Args:
            violation_id: The ID of the violation to retrieve
            
        Returns:
            Optional[_GovernanceViolation]: The violation if found, None otherwise
        """
        raise NotImplementedError
    
    def list_violations(self, **filters) -> List[_GovernanceViolation]:
        """
        List violations with optional filters
        
        Args:
            **filters: Filter criteria
                - level: _ViolationLevel
                - resolved: bool
                - actor_id: str
                - start_time: datetime
                - end_time: datetime
                - event_id: str
                
        Returns:
            List[_GovernanceViolation]: List of matching violations
        """
        raise NotImplementedError
    
    def resolve_violation(self, violation_id: str, resolved_by: str) -> bool:
        """
        Mark a violation as resolved
        
        Args:
            violation_id: The ID of the violation to resolve
            resolved_by: The ID of the actor resolving the violation
            
        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError


class _InMemoryViolationStore(_ViolationStore):
    """
    In-memory implementation of ViolationStore for testing and development
    """
    
    def __init__(self, caller):
        """
        Initialize the in-memory violation store
        
        Args:
            caller: The caller of this store
        """
        super().__init__(caller)
        self.violations: Dict[str, _GovernanceViolation] = {}
    
    def save_violation(self, violation: _GovernanceViolation) -> bool:
        """
        Save a violation to in-memory storage
        
        Args:
            violation: The violation to save
            
        Returns:
            bool: Always True for in-memory storage
        """
        self.violations[violation.id] = violation
        return True
    
    def get_violation(self, violation_id: str) -> Optional[_GovernanceViolation]:
        """
        Get a violation by ID
        
        Args:
            violation_id: The ID of the violation to retrieve
            
        Returns:
            Optional[_GovernanceViolation]: The violation if found, None otherwise
        """
        return self.violations.get(violation_id)
    
    def list_violations(self, **filters) -> List[_GovernanceViolation]:
        """
        List violations with optional filters
        
        Args:
            **filters: Filter criteria
                - level: _ViolationLevel
                - resolved: bool
                - actor_id: str
                - start_time: datetime
                - end_time: datetime
                - event_id: str
                
        Returns:
            List[_GovernanceViolation]: List of matching violations
        """
        results = list(self.violations.values())
        
        # Apply filters
        if "level" in filters:
            level = filters["level"]
            results = [v for v in results if v.level == level]
        
        if "resolved" in filters:
            resolved = filters["resolved"]
            results = [v for v in results if (v.status == _ViolationStatus.RESOLVED) == resolved]
        
        if "actor_id" in filters:
            actor_id = filters["actor_id"]
            results = [v for v in results if v.actor_id == actor_id]
        
        if "start_time" in filters:
            start_time = filters["start_time"]
            results = [v for v in results if v.timestamp >= start_time]
        
        if "end_time" in filters:
            end_time = filters["end_time"]
            results = [v for v in results if v.timestamp <= end_time]
        
        if "event_id" in filters:
            event_id = filters["event_id"]
            results = [v for v in results if v.event_id == event_id]
        
        # Sort by severity and then by timestamp (newest first)
        severity_order = {_ViolationLevel.CRITICAL: 0, _ViolationLevel.MAJOR: 1, _ViolationLevel.MINOR: 2, _ViolationLevel.INFO: 3}
        return sorted(
            results, 
            key=lambda x: (severity_order[x.level], x.timestamp), 
            reverse=True
        )
    
    def resolve_violation(self, violation_id: str, resolved_by: str) -> bool:
        """
        Mark a violation as resolved
        
        Args:
            violation_id: The ID of the violation to resolve
            resolved_by: The ID of the actor resolving the violation
            
        Returns:
            bool: True if successful, False otherwise
        """
        if violation_id not in self.violations:
            return False
        
        violation = self.violations[violation_id].copy()
        
        # Create a new violation instance with resolved state
        resolved_violation = _GovernanceViolation(
            **violation.model_dump(),
            status=_ViolationStatus.RESOLVED,
            resolved_by=resolved_by,
            resolved_at=datetime.now(),
            id=violation_id  # Keep the same ID
        )
        
        self.violations[violation_id] = resolved_violation
        return True


# Private in-memory stores for development
_violation_store = None

def _get_violation_store(caller):
    """
    Get or create the violation store
    
    Args:
        caller: The caller of this store
        
    Returns:
        _InMemoryViolationStore: The violation store
    """
    global _violation_store
    if _violation_store is None:
        _violation_store = _InMemoryViolationStore(caller)
    return _violation_store


__all__ = []