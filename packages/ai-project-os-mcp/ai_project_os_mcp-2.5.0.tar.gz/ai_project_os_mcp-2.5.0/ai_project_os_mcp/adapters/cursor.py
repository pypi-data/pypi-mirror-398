"""
Cursor适配器 - 适配Cursor AI
"""

from ai_project_os_mcp.core.state_manager import StateManager
from ai_project_os_mcp.core.rule_engine import RuleEngine

class CursorAdapter:
    """
    Cursor AI适配器，用于将MCP规则应用到Cursor
    """
    
    def __init__(self, project_root="."):
        """
        初始化Cursor适配器
        
        Args:
            project_root: 项目根目录路径
        """
        self.state_manager = StateManager(project_root)
        self.rule_engine = RuleEngine()
    
    def can_write_code(self, file_path):
        """
        检查是否可以在指定文件中写入代码
        
        Args:
            file_path: 文件路径
            
        Returns:
            tuple: (can_write, reason)
        """
        state = self.state_manager.load_state()
        
        # 检查是否是src目录下的文件
        if file_path.startswith("src/"):
            can_write, reason = self.rule_engine.can_modify_src(state)
            if not can_write:
                return False, reason
        
        # 检查是否是S5阶段
        if state["stage"] != "S5":
            return False, "Code generation only allowed in S5"
        
        return True, "Code writing allowed"
    
    def validate_code(self, code_content):
        """
        验证生成的代码是否符合MCP规则
        
        Args:
            code_content: 生成的代码内容
            
        Returns:
            tuple: (is_valid, reason)
        """
        # 检查Context Refresh
        has_context_refresh, reason = self.rule_engine.validate_context_refresh(code_content)
        if not has_context_refresh:
            return False, reason
        
        # 检查Pseudo-TDD
        has_pseudo_tdd, reason = self.rule_engine.validate_pseudo_tdd(code_content)
        if not has_pseudo_tdd:
            return False, reason
        
        return True, "Code validation passed"
    
    def get_editor_config(self):
        """
        获取Cursor编辑器配置
        
        Returns:
            dict: 编辑器配置
        """
        return {
            "onCodeGenerate": {
                "validate": True,
                "requireContextRefresh": True,
                "requirePseudoTDD": True
            },
            "onFileWrite": {
                "validateSrcGuard": True,
                "checkStage": True
            }
        }
