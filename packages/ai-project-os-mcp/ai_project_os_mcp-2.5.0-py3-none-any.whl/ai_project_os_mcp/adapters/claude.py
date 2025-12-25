"""
Claude适配器 - 适配Claude AI
"""

from ai_project_os_mcp.core.state_manager import StateManager
from ai_project_os_mcp.tools import get_stage, freeze_stage, guard_src, submit_audit

class ClaudeAdapter:
    """
    Claude AI适配器，用于将MCP规则应用到Claude
    """
    
    def __init__(self, project_root="."):
        """
        初始化Claude适配器
        
        Args:
            project_root: 项目根目录路径
        """
        self.state_manager = StateManager(project_root)
        self.tools = {
            "get_stage": get_stage,
            "freeze_stage": freeze_stage,
            "guard_src": guard_src,
            "submit_audit": submit_audit
        }
    
    def get_system_prompt(self):
        """
        获取Claude的System Prompt
        
        Returns:
            str: System Prompt字符串
        """
        return """
You are an AI Project OS MCP Agent.

You MUST:
- Call get_stage before any action
- Refuse code unless stage == S5
- Call guard_src before src changes
- Require Context Refresh
- Submit audit for every S5 task

Violation = hard refusal.
"""
    
    def handle_tool_call(self, tool_name, payload):
        """
        处理Claude的工具调用
        
        Args:
            tool_name: 工具名称
            payload: 工具负载
            
        Returns:
            dict: 工具调用结果
        """
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        # 加载当前状态
        state = self.state_manager.load_state()
        
        # 调用工具
        result = self.tools[tool_name](state, payload)
        
        # 如果是冻结阶段，更新状态
        if tool_name == "freeze_stage" and result["success"]:
            self.state_manager.save_state(result["new_state"])
        
        return result
