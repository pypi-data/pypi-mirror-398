"""
Event Store - The source of truth for governance events

This module defines the EventStore interface and implementations.
EventStore is the single source of truth for all governance events.
Events are append-only and cannot be modified or deleted.
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances


from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import uuid
import json
import os
from abc import ABC, abstractmethod

from .events import _GovernanceEvent as GovernanceEvent, _EventStatus as EventStatus


class _EventStore(ABC):
    """
    Event Store interface - The source of truth for governance events
    
    Events are append-only and cannot be modified or deleted.
    Any state, audit, or violation must reference an event_id.
    """
    
    def __init__(self, caller):
        if caller.__class__.__name__ != "GovernanceEngine":
            raise RuntimeError("Unauthorized access to EventStore")
        self.caller = caller
    
    @abstractmethod
    def append(self, event: GovernanceEvent) -> bool:
        """
        Append a governance event to the store
        
        Args:
            event: Governance event to append
            
        Returns:
            bool: True if successful, False otherwise
        
        🔒 铁律：事件一旦写入，不可修改、不可删除
        """
        pass
    
    @abstractmethod
    def get(self, event_id: str) -> Optional[GovernanceEvent]:
        """
        Get a governance event by ID
        
        Args:
            event_id: Event ID to retrieve
            
        Returns:
            Optional[GovernanceEvent]: The event if found, None otherwise
        """
        pass
    
    @abstractmethod
    def list(self, **filters) -> List[GovernanceEvent]:
        """
        List governance events with optional filters
        
        Args:
            **filters:
                - event_type: Event type to filter by
                - actor_id: Actor ID to filter by
                - start_time: Start time to filter by
                - end_time: End time to filter by
                - status: Event status to filter by
            
        Returns:
            List[GovernanceEvent]: List of matching events, sorted by timestamp descending
        """
        pass
    
    @abstractmethod
    def count(self, **filters) -> int:
        """
        Count governance events with optional filters
        
        Args:
            **filters: Filter criteria (same as list method)
            
        Returns:
            int: Number of matching events
        """
        pass
    
    @abstractmethod
    def update_event_status(self, event_id: str, status: EventStatus) -> bool:
        """
        Update the status of a governance event
        
        Args:
            event_id: Event ID to update
            status: New status for the event
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass


class _InMemoryEventStore(_EventStore):
    """
    In-memory implementation of EventStore for testing and development
    
    This implementation is not persistent and should only be used for testing.
    """
    
    def __init__(self, caller):
        """
        Initialize the in-memory event store
        
        Args:
            caller: The caller of this store
        """
        super().__init__(caller)
        self.events: Dict[str, GovernanceEvent] = {}
    
    def append(self, event: GovernanceEvent) -> bool:
        """
        Append a governance event to the store
        
        Args:
            event: Governance event to append
            
        Returns:
            bool: Always True for in-memory storage
        
        🔒 铁律：事件一旦写入，不可修改、不可删除
        """
        # 确保事件ID唯一性
        if event.id in self.events:
            return False
        
        # 写入事件（append-only）
        self.events[event.id] = event
        return True
    
    def get(self, event_id: str) -> Optional[GovernanceEvent]:
        """
        Get a governance event by ID
        
        Args:
            event_id: Event ID to retrieve
            
        Returns:
            Optional[GovernanceEvent]: The event if found, None otherwise
        """
        return self.events.get(event_id)
    
    def list(self, **filters) -> List[GovernanceEvent]:
        """
        List governance events with optional filters
        
        Args:
            **filters:
                - event_type: Event type to filter by
                - actor_id: Actor ID to filter by
                - start_time: Start time to filter by
                - end_time: End time to filter by
                - status: Event status to filter by
            
        Returns:
            List[GovernanceEvent]: List of matching events, sorted by timestamp descending
        """
        results = list(self.events.values())
        
        # Apply filters
        if "event_type" in filters:
            event_type = filters["event_type"]
            results = [e for e in results if e.event_type == event_type]
        
        if "actor_id" in filters:
            actor_id = filters["actor_id"]
            results = [e for e in results if e.actor.id == actor_id]
        
        if "start_time" in filters:
            start_time = filters["start_time"]
            results = [e for e in results if e.timestamp >= start_time]
        
        if "end_time" in filters:
            end_time = filters["end_time"]
            results = [e for e in results if e.timestamp <= end_time]
        
        if "status" in filters:
            status = filters["status"]
            results = [e for e in results if e.status == status]
        
        # Sort by timestamp (newest first)
        return sorted(results, key=lambda x: x.timestamp, reverse=True)
    
    def count(self, **filters) -> int:
        """
        Count governance events with optional filters
        
        Args:
            **filters: Filter criteria (same as list method)
            
        Returns:
            int: Number of matching events
        """
        return len(self.list(**filters))
    
    def update_event_status(self, event_id: str, status: EventStatus) -> bool:
        """
        Update the status of a governance event
        
        Args:
            event_id: Event ID to update
            status: New status for the event
            
        Returns:
            bool: True if successful, False otherwise
        """
        if event_id not in self.events:
            return False
        
        # 更新事件状态
        self.events[event_id] = self.events[event_id].model_copy(update={"status": status})
        return True


class _FileSystemEventStore(_EventStore):
    """
    File system implementation of EventStore for production use
    
    This implementation persists events to the file system, ensuring durability and auditability.
    """
    
    def __init__(self, caller, store_path: str = None):
        """
        Initialize the file system event store
        
        Args:
            caller: The caller of this store
            store_path: Path to store events (default: events.json in the current directory)
        """
        super().__init__(caller)
        if caller.__class__.__name__ != "GovernanceEngine":
            raise RuntimeError("Unauthorized access to FileSystemEventStore")
        
        # Get project root from caller
        self.project_root = getattr(caller, "project_root", ".")
        self.store_path = store_path or os.path.join(self.project_root, "events.json")
        self._events = self._load_events()
    
    def _load_events(self) -> Dict[str, GovernanceEvent]:
        """
        Load events from the file system
        
        Returns:
            Dict[str, GovernanceEvent]: Loaded events
        """
        events = {}
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    events_data = json.load(f)
                    for event_data in events_data:
                        # Convert timestamp string back to datetime
                        event_data["timestamp"] = datetime.fromisoformat(event_data["timestamp"])
                        # Create GovernanceEvent instance
                        event = GovernanceEvent(**event_data)
                        events[event.id] = event
            except Exception as e:
                # If events file is corrupted, return empty dict
                pass
        return events
    
    def _save_events(self):
        """
        Save events to the file system
        """
        try:
            with open(self.store_path, "w", encoding="utf-8") as f:
                # Convert events to serializable format
                events_data = [event.model_dump() for event in self._events.values()]
                json.dump(events_data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            # If save fails, log error but continue
            pass
    
    def append(self, event: GovernanceEvent) -> bool:
        """
        Append a governance event to the store
        
        Args:
            event: Governance event to append
            
        Returns:
            bool: True if successful, False otherwise
        
        🔒 铁律：事件一旦写入，不可修改、不可删除
        """
        # 确保事件ID唯一性
        if event.id in self._events:
            return False
        
        # 写入事件（append-only）
        self._events[event.id] = event
        # 保存到文件系统
        self._save_events()
        return True
    
    def get(self, event_id: str) -> Optional[GovernanceEvent]:
        """
        Get a governance event by ID
        
        Args:
            event_id: Event ID to retrieve
            
        Returns:
            Optional[GovernanceEvent]: The event if found, None otherwise
        """
        return self._events.get(event_id)
    
    def list(self, **filters) -> List[GovernanceEvent]:
        """
        List governance events with optional filters
        
        Args:
            **filters:
                - event_type: Event type to filter by
                - actor_id: Actor ID to filter by
                - start_time: Start time to filter by
                - end_time: End time to filter by
                - status: Event status to filter by
            
        Returns:
            List[GovernanceEvent]: List of matching events, sorted by timestamp descending
        """
        results = list(self._events.values())
        
        # Apply filters
        if "event_type" in filters:
            event_type = filters["event_type"]
            results = [e for e in results if e.event_type == event_type]
        
        if "actor_id" in filters:
            actor_id = filters["actor_id"]
            results = [e for e in results if e.actor.id == actor_id]
        
        if "start_time" in filters:
            start_time = filters["start_time"]
            results = [e for e in results if e.timestamp >= start_time]
        
        if "end_time" in filters:
            end_time = filters["end_time"]
            results = [e for e in results if e.timestamp <= end_time]
        
        if "status" in filters:
            status = filters["status"]
            results = [e for e in results if e.status == status]
        
        # Sort by timestamp (newest first)
        return sorted(results, key=lambda x: x.timestamp, reverse=True)
    
    def count(self, **filters) -> int:
        """
        Count governance events with optional filters
        
        Args:
            **filters: Filter criteria (same as list method)
            
        Returns:
            int: Number of matching events
        """
        return len(self.list(**filters))
    
    def update_event_status(self, event_id: str, status: EventStatus) -> bool:
        """
        Update the status of a governance event
        
        Args:
            event_id: Event ID to update
            status: New status for the event
            
        Returns:
            bool: True if successful, False otherwise
        """
        if event_id not in self._events:
            return False
        
        # 更新事件状态
        self._events[event_id] = self._events[event_id].model_copy(update={"status": status})
        # 保存到文件系统
        self._save_events()
        return True


# Global event store instance
_event_store = None

def _get_event_store(caller) -> _EventStore:
    """
    Get the global event store instance
    
    Args:
        caller: The caller of this store
        
    Returns:
        _EventStore: Global event store instance
    """
    global _event_store
    if caller.__class__.__name__ != "GovernanceEngine":
        raise RuntimeError("Unauthorized access to event store")
    if _event_store is None:
        # 使用文件系统事件存储，确保事件持久化
        _event_store = _FileSystemEventStore(caller)
    return _event_store


__all__ = []
