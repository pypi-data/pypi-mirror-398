"""
Architecture Linter - 基于 AST 的架构合规检查引擎

该模块负责：
1. 解析 architecture.yaml 配置
2. 对 Python 代码进行 AST 分析，提取导入关系
3. 检查导入关系是否符合架构规则
4. 生成合规报告
"""

# Single Gate Architecture: Core modules are private and can only be used by GovernanceEngine
# Private classes with underscore prefix enforce this pattern
# Constructor validation ensures only GovernanceEngine can create instances


import ast
import os
import yaml
from typing import Dict, List, Set, Tuple

class _ArchitectureLinter:
    """
    架构合规检查引擎
    """
    
    def __init__(self, caller):
        """
        初始化架构检查引擎
        
        Args:
            caller: 调用者，必须是 GovernanceEngine 实例
        """
        if caller.__class__.__name__ != "GovernanceEngine":
            raise RuntimeError("Unauthorized access to ArchitectureLinter")
        self.caller = caller
        self.architecture_config = None
        self.layer_dependencies = {}
        self.module_layers = {}
        self.violations = []
        self.scanned_modules = 0
    
    def load_config(self, config_path: str) -> bool:
        """
        加载架构配置文件
        
        Args:
            config_path: 架构配置文件路径
            
        Returns:
            bool: 加载成功返回 True，否则返回 False
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self.architecture_config = yaml.safe_load(f)
            
            # 解析层依赖关系
            for layer in self.architecture_config.get("layers", []):
                layer_name = layer["name"]
                allowed_deps = layer.get("allowed_dependencies", [])
                self.layer_dependencies[layer_name] = allowed_deps
            
            # 解析模块层映射
            for module in self.architecture_config.get("modules", []):
                module_name = module["name"]
                layers = module.get("layers", [])
                self.module_layers[module_name] = layers
            
            return True
        except Exception as e:
            self.violations.append({
                "source": "config",
                "target": "",
                "rule_violated": "config_load_failure",
                "severity": "ERROR",
                "message": f"Failed to load architecture config: {str(e)}"
            })
            return False
    
    def get_module_layer(self, module_path: str) -> str:
        """
        获取模块所属的层
        
        Args:
            module_path: 模块路径
            
        Returns:
            str: 模块所属的层，如果无法确定则返回 "unknown"
        """
        # 简单的层检测逻辑
        # 根据模块路径判断所属层
        path_parts = module_path.split(".")
        
        if len(path_parts) < 2:
            return "unknown"
        
        # 假设路径格式为: ai_project_os_mcp.layer.module
        if path_parts[0] == "ai_project_os_mcp":
            if len(path_parts) >= 2:
                layer_candidate = path_parts[1]
                # 检查是否在定义的层中
                if layer_candidate in self.layer_dependencies:
                    return layer_candidate
        
        return "unknown"
    
    def analyze_file(self, file_path: str) -> None:
        """
        分析单个 Python 文件的导入关系
        
        Args:
            file_path: Python 文件路径
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 解析文件为 AST
            tree = ast.parse(content)
            
            # 获取当前文件所属的模块
            # 假设 file_path 是绝对路径，我们需要找到相对于项目根目录的路径
            # 简单处理：找到 ai_project_os_mcp 作为根模块
            file_path_parts = file_path.split(os.sep)
            try:
                # 找到 ai_project_os_mcp 在路径中的位置
                mcp_index = file_path_parts.index("ai_project_os_mcp")
                # 构建相对路径
                relative_parts = file_path_parts[mcp_index:]
                # 将路径转换为模块名
                module_path = ".".join(relative_parts).replace(".py", "")
                # 移除可能的 __init__ 后缀
                if module_path.endswith("__init__"):
                    module_path = module_path[:-8]  # 移除 __init__ 后缀
            except ValueError:
                # 如果找不到 ai_project_os_mcp，则跳过
                return
            
            # 获取当前模块所属的层
            current_layer = self.get_module_layer(module_path)
            
            # 分析导入语句
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imported_module = name.name
                        self._check_import(current_layer, module_path, imported_module)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_module = node.module
                        self._check_import(current_layer, module_path, imported_module)
            
            self.scanned_modules += 1
        except Exception as e:
            self.violations.append({
                "source": file_path,
                "target": "",
                "rule_violated": "file_analysis_failure",
                "severity": "ERROR",
                "message": f"Failed to analyze file: {str(e)}"
            })
    
    def _check_import(self, current_layer: str, current_module: str, imported_module: str) -> None:
        """
        检查导入是否符合架构规则
        
        Args:
            current_layer: 当前模块所属的层
            current_module: 当前模块路径
            imported_module: 导入的模块路径
        """
        # 只检查 ai_project_os_mcp 内部的模块导入
        if not imported_module.startswith("ai_project_os_mcp"):
            return
        
        # 获取导入模块所属的层
        imported_layer = self.get_module_layer(imported_module)
        
        # 检查层依赖规则
        if current_layer != "unknown" and imported_layer != "unknown":
            # 获取当前层允许的依赖
            allowed_deps = self.layer_dependencies.get(current_layer, [])
            
            # 检查导入层是否在允许的依赖列表中
            if imported_layer not in allowed_deps and current_layer != imported_layer:
                self.violations.append({
                    "source": current_module,
                    "target": imported_module,
                    "rule_violated": "layer_dependency",
                    "severity": "ERROR",
                    "message": f"Layer violation: {current_layer} module {current_module} is not allowed to depend on {imported_layer} module {imported_module}"
                })
    
    def analyze_directory(self, directory_path: str) -> None:
        """
        分析目录下的所有 Python 文件
        
        Args:
            directory_path: 目录路径
        """
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    self.analyze_file(file_path)
    
    def get_report(self) -> Dict:
        """
        获取架构检查报告
        
        Returns:
            dict: 架构检查报告，包含违规信息和统计数据
        """
        # 计算允许的边
        allowed_edges = []
        for layer, allowed_deps in self.layer_dependencies.items():
            for dep in allowed_deps:
                allowed_edges.append({"source": layer, "target": dep})
        
        return {
            "schema_version": "1.0",
            "violations": self.violations,
            "allowed_edges": allowed_edges,
            "scanned_modules": self.scanned_modules,
            "timestamp": "2023-01-01T12:00:00Z"
        }
    
    def check_architecture(self, project_root: str) -> Dict:
        """
        执行完整的架构检查
        
        Args:
            project_root: 项目根目录
            
        Returns:
            dict: 架构检查报告
        """
        # 重置状态
        self.violations = []
        self.scanned_modules = 0
        
        # 加载配置
        config_path = os.path.join(project_root, "architecture.yaml")
        if not self.load_config(config_path):
            return self.get_report()
        
        # 分析项目代码
        source_dir = os.path.join(project_root, "ai_project_os_mcp")
        self.analyze_directory(source_dir)

        return self.get_report()


__all__ = []
