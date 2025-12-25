"""
freeze_stage工具 - 冻结项目到下一个阶段
"""

from ai_project_os_mcp.core import GovernanceEngine
from ai_project_os_mcp.core.events import GovernanceEvent, EventType, Actor

def freeze_stage(state, payload):
    """
    冻结项目到下一个阶段
    
    Args:
        state: 当前项目状态
        payload: 工具负载，包含target_stage字段
        
    Returns:
        dict: 冻结结果
    """
    target_stage = payload.get("target_stage")
    
    if not target_stage:
        return {"success": False, "error": "Missing target_stage"}
    
    # 构造Actor
    actor = Actor(
        id=payload.get("actor_id", "system"),
        role=payload.get("actor_role", "system"),
        source=payload.get("actor_source", "system"),
        name=payload.get("actor_name", "System")
    )
    
    # 构造GovernanceEvent
    event = GovernanceEvent(
        event_type=EventType.FREEZE_REQUEST,
        actor=actor,
        payload={
            "target_stage": target_stage,
            "current_stage": state.get("stage")
        }
    )
    
    # 调用GovernanceEngine
    governance_engine = GovernanceEngine(".")
    result = governance_engine.handle_event(event)
    
    return {
        "success": result["status"] == "PASSED",
        "result": result
    }
