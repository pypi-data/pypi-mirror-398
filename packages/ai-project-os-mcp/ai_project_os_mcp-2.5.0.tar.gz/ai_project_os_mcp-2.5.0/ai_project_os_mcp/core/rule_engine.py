"""
规则引擎 - 5S + S5 稳定性规则
"""

# Module-level hard rejection - Only allow internal imports
import sys
import inspect

# 更严格的内部导入检查函数
def _is_internal_import():
    stack = inspect.stack()
    for frame_info in stack[1:]:  # 跳过当前帧
        filename = frame_info.filename
        if filename:
            # 处理 Windows 路径
            normalized_filename = filename.replace('\\', '/')
            # 检查是否是核心模块内部导入
            if 'ai_project_os_mcp/core' in normalized_filename:
                return True
    return False

# 仅允许 GovernanceEngine 导入核心模块
if not _is_internal_import():
    raise RuntimeError(
        "Direct access to core modules is forbidden. "
        "Use GovernanceEngine as the single entry point."
    )

VALID_STAGES = ["S1", "S2", "S3", "S4", "S5"]

class _RuleEngine:
    """
    规则引擎，负责执行AI Project OS的所有工程规则
    """
    
    def __init__(self, caller):
        """
        初始化规则引擎
        
        Args:
            caller: 调用者，必须是 GovernanceEngine 实例
        """
        if caller.__class__.__name__ != "GovernanceEngine":
            raise RuntimeError("Unauthorized access to RuleEngine")
        self.caller = caller
        
        self.rules = {
            "R1": "AI MUST query current stage before any action",
            "R2": "AI MUST NOT generate code unless stage == S5",
            "R3": "AI MUST abort on architecture violation",
            "R4": "AI MUST submit audit for every S5 task",
            "R5": "AI MUST respect src guard and lock status"
        }
    
    def validate_stage_transition(self, current_stage, target_stage):
        """
        验证阶段转换是否合法
        
        Args:
            current_stage: 当前阶段
            target_stage: 目标阶段
            
        Returns:
            tuple: (is_valid, reason)
        """
        if target_stage not in VALID_STAGES:
            return False, f"Invalid stage: {target_stage}"
        
        current_idx = VALID_STAGES.index(current_stage)
        target_idx = VALID_STAGES.index(target_stage)
        
        # 禁止回滚
        if target_idx < current_idx:
            return False, "Cannot rollback stage"
        
        # 禁止跳级
        if target_idx > current_idx + 1:
            return False, "Cannot skip stages"
        
        return True, "Valid stage transition"
    
    def can_generate_code(self, state):
        """
        检查是否可以生成代码
        
        Args:
            state: 当前项目状态
            
        Returns:
            tuple: (can_generate, reason)
        """
        if state["stage"] != "S5":
            return False, "Code generation only allowed in S5"
        
        if state.get("locked", False):
            return False, "S5 is locked"
        
        return True, "Code generation allowed"
    
    def can_modify_src(self, state):
        """
        检查是否可以修改src目录
        
        Args:
            state: 当前项目状态
            
        Returns:
            tuple: (can_modify, reason)
        """
        return self.can_generate_code(state)
    
    def is_architecture_violation(self, action, architecture_constraints=None):
        """
        检查是否违反架构约束
        
        Args:
            action: 要执行的动作 (dict, 包含 'file_path', 'content' 等)
            architecture_constraints: 架构约束 (可选)
            
        Returns:
            tuple: (is_violation, reason)
        """
        # 默认架构约束
        if architecture_constraints is None:
            architecture_constraints = {
                "allowed_dirs": ["ai_project_os_mcp", "docs", "examples", "tests", "scripts"],
                "dependency_rules": {
                    "core": ["tools", "adapters"], # core 不能导入 tools 或 adapters
                    "tools": ["adapters"]          # tools 不能导入 adapters
                }
            }
            
        file_path = action.get("file_path", "")
        
        # 1. 检查文件位置是否合法
        if file_path:
            # 标准化路径分隔符
            file_path = file_path.replace("\\", "/")
            parts = file_path.split("/")
            
            # 如果是根目录文件，允许
            if len(parts) == 1:
                pass
            # 检查顶层目录
            elif parts[0] not in architecture_constraints["allowed_dirs"]:
                # 允许隐藏文件/目录 (以.开头)
                if not parts[0].startswith("."):
                    return True, f"Directory '{parts[0]}' is not allowed by architecture"
        
        # 2. 检查依赖关系 (如果提供了内容)
        content = action.get("content", "")
        if content and file_path:
            import re
            
            # 简单的 import 检查
            # from ai_project_os_mcp.tools import ...
            # import ai_project_os_mcp.tools
            
            current_module = parts[1] if len(parts) > 1 else ""
            
            if current_module in architecture_constraints["dependency_rules"]:
                forbidden_modules = architecture_constraints["dependency_rules"][current_module]
                
                for forbidden in forbidden_modules:
                    pattern = f"(from|import)\\s+ai_project_os_mcp\\.{forbidden}"
                    if re.search(pattern, content):
                        return True, f"Module '{current_module}' cannot import '{forbidden}'"
        
        return False, "No architecture violation"
    
    def requires_audit(self, stage):
        """
        检查当前阶段是否需要审计
        
        Args:
            stage: 当前阶段
            
        Returns:
            bool: 是否需要审计
        """
        return stage == "S5"
    
    def validate_context_refresh(self, code_content):
        """
        验证代码是否包含Context Refresh
        
        Args:
            code_content: 代码内容
            
        Returns:
            tuple: (is_valid, reason)
        """
        if "[Context Refresh]" in code_content:
            return True, "Context Refresh found"
        else:
            return False, "Missing [Context Refresh]"
    
    def validate_pseudo_tdd(self, code_content):
        """
        验证代码是否包含Pseudo-TDD断言
        
        Args:
            code_content: 代码内容
            
        Returns:
            tuple: (is_valid, reason)
        """
        # 检查是否包含断言相关的注释或代码
        tdd_markers = ["# 正确性断言", "# 什么是对的", "# 预期结果", "assert ", "test_", "def test_"]
        
        found = False
        for marker in tdd_markers:
            if marker in code_content:
                found = True
                break
        
        if found:
            return True, "Pseudo-TDD assertion found"
        else:
            return False, "Missing Pseudo-TDD assertion"


__all__ = []
