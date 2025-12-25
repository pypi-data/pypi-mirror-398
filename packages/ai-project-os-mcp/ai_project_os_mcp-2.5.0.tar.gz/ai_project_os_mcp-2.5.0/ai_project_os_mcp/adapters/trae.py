"""
Trae适配器 - 适配Trae多Agent环境
"""

from ai_project_os_mcp.core.state_manager import StateManager
from ai_project_os_mcp.core.rule_engine import RuleEngine
from ai_project_os_mcp.tools import get_stage, freeze_stage, guard_src, submit_audit

class TraeAdapter:
    """
    Trae多Agent适配器，用于将MCP规则应用到Trae多Agent环境
    """
    
    def __init__(self, project_root="."):
        """
        初始化Trae适配器
        
        Args:
            project_root: 项目根目录路径
        """
        self.state_manager = StateManager(project_root)
        self.rule_engine = RuleEngine()
        self.tools = {
            "get_stage": get_stage,
            "freeze_stage": freeze_stage,
            "guard_src": guard_src,
            "submit_audit": submit_audit
        }
    
    def get_agent_configs(self):
        """
        获取Trae多Agent的配置
        
        Returns:
            dict: 多Agent配置
        """
        return {
            "agents": {
                "Planner": {
                    "role": "S1-S4 Planning Agent",
                    "capabilities": ["get_stage", "freeze_stage"],
                    "constraints": ["No code generation", "Must freeze stage before proceeding"]
                },
                "Executor": {
                    "role": "S5 Execution Agent",
                    "capabilities": ["get_stage", "guard_src", "submit_audit"],
                    "constraints": ["Code only in S5", "Must call guard_src before writing", "Must submit audit for each task"]
                },
                "Auditor": {
                    "role": "Audit Validation Agent",
                    "capabilities": ["get_stage"],
                    "constraints": ["Read-only access", "Must validate all S5 tasks"]
                }
            },
            "workflow": {
                "S1": "Planner",
                "S2": "Planner",
                "S3": "Planner",
                "S4": "Planner",
                "S5": "Executor -> Auditor"
            }
        }
    
    def validate_agent_action(self, agent_role, action_type):
        """
        验证Agent的行为是否符合MCP规则
        
        Args:
            agent_role: Agent角色
            action_type: 行为类型
            
        Returns:
            tuple: (is_valid, reason)
        """
        state = self.state_manager.load_state()
        current_stage = state["stage"]
        
        # Planner只能在S1-S4阶段活动，不能生成代码
        if agent_role == "Planner":
            if current_stage == "S5":
                return False, "Planner cannot operate in S5 stage"
            if action_type == "generate_code":
                return False, "Planner cannot generate code"
        
        # Executor只能在S5阶段活动，必须调用guard_src
        elif agent_role == "Executor":
            if current_stage != "S5":
                return False, "Executor can only operate in S5 stage"
            if action_type == "write_src" and not state.get("guard_called", False):
                return False, "Executor must call guard_src before writing to src"
        
        # Auditor只能进行只读操作
        elif agent_role == "Auditor":
            if action_type in ["write_file", "generate_code", "modify_state"]:
                return False, "Auditor can only perform read-only operations"
        
        return True, "Agent action allowed"
    
    def handle_tool_call(self, agent_role, tool_name, payload):
        """
        处理Trae Agent的工具调用
        
        Args:
            agent_role: Agent角色
            tool_name: 工具名称
            payload: 工具负载
            
        Returns:
            dict: 工具调用结果
        """
        # 验证Agent行为
        is_valid, reason = self.validate_agent_action(agent_role, tool_name)
        if not is_valid:
            return {"success": False, "error": reason}
        
        if tool_name not in self.tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        # 加载当前状态
        state = self.state_manager.load_state()
        
        # 调用工具
        result = self.tools[tool_name](state, payload)
        
        # 如果是冻结阶段，更新状态
        if tool_name == "freeze_stage" and result["success"]:
            self.state_manager.save_state(result["new_state"])
        
        return result
