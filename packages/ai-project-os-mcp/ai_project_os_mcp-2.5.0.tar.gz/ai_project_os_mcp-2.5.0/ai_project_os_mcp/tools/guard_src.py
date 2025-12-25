"""
guard_src工具 - 验证是否允许修改src目录
"""

from ai_project_os_mcp.core.rule_engine import RuleEngine
from ai_project_os_mcp.config import config

rule_engine = RuleEngine()

def guard_src(state, payload):
    """
    验证是否允许修改src目录
    
    Args:
        state: 当前项目状态
        payload: 工具负载，包含intent字段和file_path字段
        
    Returns:
        dict: 验证结果
    """
    intent = payload.get("intent", "write")
    file_path = payload.get("file_path", "")
    
    # 如果是只读意图，总是允许
    if intent == "read":
        return {"allowed": True, "reason": "Read access allowed"}
    
    # 检查是否可以修改src目录
    can_modify, reason = rule_engine.can_modify_src(state)
    
    # 细粒度路径保护
    if can_modify and file_path:
        # 即使在S5，某些核心目录也可能被保护
        # 这里可以从config读取受保护路径
        protected_paths = ["ai_project_os_mcp/core", "ai_project_os_mcp/server.py"]
        
        for protected in protected_paths:
            if file_path.replace("\\", "/").startswith(protected):
                # 除非明确解锁，否则保护
                if not state.get("unlocked_core", False):
                    return {
                        "allowed": False, 
                        "reason": f"Path '{protected}' is protected even in S5. Request 'unlocked_core' state to modify.",
                        "stage": state["stage"]
                    }
    
    return {
        "allowed": can_modify,
        "reason": reason,
        "stage": state["stage"],
        "locked": state.get("locked", False)
    }
