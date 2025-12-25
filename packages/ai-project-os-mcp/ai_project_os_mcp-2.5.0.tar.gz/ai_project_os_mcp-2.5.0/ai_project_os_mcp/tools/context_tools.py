"""
Context Tools - 帮助Agent理解项目上下文
"""

import os
import re
from ai_project_os_mcp.config import config

def read_architecture(state, payload):
    """
    读取项目架构定义
    
    Args:
        state: 当前项目状态
        payload: 工具负载 (未使用)
        
    Returns:
        dict: 架构定义
    """
    # 这里可以从文件读取，或者返回硬编码的架构
    # 假设架构定义在 docs/architecture.md 或 config中
    
    architecture = {
        "layers": ["core", "tools", "adapters", "server"],
        "rules": config.rules,
        "allowed_dirs": ["ai_project_os_mcp", "docs", "examples", "tests", "scripts"]
    }
    
    return {
        "architecture": architecture,
        "source": "config"
    }

def analyze_dependencies(state, payload):
    """
    分析项目依赖关系，并对比配置进行检查
    
    Args:
        state: 当前项目状态
        payload: 工具负载 (未使用)
        
    Returns:
        dict: 依赖分析结果，包含违规信息
    """
    project_root = config.project_root
    
    # 获取配置中的依赖白名单和黑名单
    whitelist = config.dependency_whitelist
    blacklist = config.dependency_blacklist
    
    # 分析项目依赖
    project_deps = set()
    
    # 从 requirements.txt 读取依赖
    requirements_file = os.path.join(project_root, "requirements.txt")
    if os.path.exists(requirements_file):
        with open(requirements_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # 提取依赖名称（忽略版本号）
                    dep_name = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
                    project_deps.add(dep_name)
    
    # 从 pyproject.toml 读取依赖（如果存在）
    pyproject_file = os.path.join(project_root, "pyproject.toml")
    if os.path.exists(pyproject_file):
        import toml
        with open(pyproject_file, "r", encoding="utf-8") as f:
            pyproject_data = toml.load(f)
        
        # 读取 dependencies 和 optional-dependencies
        for section in ["dependencies", "optional-dependencies"]:
            if section in pyproject_data.get("project", {}):
                deps = pyproject_data["project"][section]
                if isinstance(deps, list):
                    for dep in deps:
                        dep_name = dep.split("==")[0].split(">=")[0].split("<=")[0].strip()
                        project_deps.add(dep_name)
                elif isinstance(deps, dict):
                    # optional-dependencies 是字典，values 是依赖列表
                    for opt_deps in deps.values():
                        for dep in opt_deps:
                            dep_name = dep.split("==")[0].split(">=")[0].split("<=")[0].strip()
                            project_deps.add(dep_name)
    
    # 检查依赖违规
    violations = []
    
    # 检查黑名单
    for dep in project_deps:
        if dep in blacklist:
            violations.append({
                "dependency": dep,
                "type": "blacklist",
                "message": f"Dependency {dep} is in blacklist"
            })
    
    # 检查白名单（如果白名单不为空）
    if whitelist:
        for dep in project_deps:
            if dep not in whitelist:
                violations.append({
                    "dependency": dep,
                    "type": "whitelist",
                    "message": f"Dependency {dep} is not in whitelist"
                })
    
    return {
        "dependencies": list(project_deps),
        "whitelist": whitelist,
        "blacklist": blacklist,
        "violations": violations
    }
