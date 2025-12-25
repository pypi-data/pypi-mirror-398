"""
get_stage工具 - 获取当前项目阶段
"""

def get_stage(state, payload=None):
    """
    获取当前项目阶段
    
    Args:
        state: 当前项目状态
        payload: 工具负载（未使用）
        
    Returns:
        dict: 当前阶段信息
    """
    return {
        "stage": state["stage"],
        "frozen": state.get("frozen", False),
        "locked": state.get("locked", False),
        "success": True
    }
