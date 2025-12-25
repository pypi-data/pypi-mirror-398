"""
Dashboard Tools - 仪表盘工具

该模块负责：
1. 提供 CLI 工具展示关键指标
"""

import os
import json
import sys
from ai_project_os_mcp.config import config

class DashboardTools:
    """
    仪表盘工具类
    """
    
    @staticmethod
    def show_cli_dashboard():
        """
        在 CLI 中展示项目仪表盘
        """
        print("\n" + "=" * 60)
        print("AI Project OS v2.0 - 项目仪表盘")
        print("=" * 60)
        
        try:
            # 直接调用 get_stats 函数，避免依赖 server 模块
            from ai_project_os_mcp.tools.dashboard_tools import get_stats
            stats_result = get_stats({}, {})
            
            if stats_result["status"] != "PASSED":
                print(f"❌ 获取统计信息失败: {stats_result.get('reason', 'Unknown error')}")
                return False
            
            stats = stats_result["data"]
            
            # 展示统计信息
            print(f"\n📊 项目状态")
            print(f"   阶段: {stats.get('stage', 'unknown')}")
            print(f"   版本: {stats.get('version', 'unknown')}")
            print(f"   最后更新: {stats.get('last_updated', 'unknown')}")
            
            print(f"\n🔍 审计信息")
            print(f"   审计记录数: {stats.get('audit_count', 0)}")
            
            print(f"\n⚖️  依赖治理")
            violation_count = stats.get('dependency_violations', 0)
            if violation_count == 0:
                print(f"   依赖违规: ✅ {violation_count}")
            else:
                print(f"   依赖违规: ❌ {violation_count}")
            
            print(f"\n🛠️  工具信息")
            print(f"   已注册工具数: {stats.get('registered_tools', 0)}")
            
            print(f"\n📁 项目信息")
            print(f"   项目根目录: {stats.get('project_root', 'unknown')}")
            
            print("\n" + "=" * 60)
            print("仪表盘展示完毕")
            print("=" * 60)
            
            return True
        except Exception as e:
            print(f"❌ 展示仪表盘失败: {str(e)}")
            return False

def get_stats(state, payload):
    """
    获取项目统计信息工具
    
    Args:
        state: 当前项目状态
        payload: 工具负载 (未使用)
        
    Returns:
        dict: 统计信息结果
    """
    # 加载当前状态
    from ai_project_os_mcp.core.state_manager import StateManager
    state_manager = StateManager(config.project_root)
    current_state = state_manager.load_state()
    
    # 统计审计记录数量
    import re
    audit_count = 0
    audit_file = os.path.join(config.project_root, "docs", "S5_audit.md")
    if os.path.exists(audit_file):
        with open(audit_file, "r", encoding="utf-8") as f:
            content = f.read()
        audit_count = len(re.findall(r"## Sub-task:", content))
    
    # 分析依赖情况
    from ai_project_os_mcp.tools.context_tools import analyze_dependencies
    dependencies_result = analyze_dependencies({}, {})
    dependency_violations = len(dependencies_result.get("violations", []))
    
    # 构建统计信息
    stats = {
        "stage": current_state.get("stage", "unknown"),
        "version": current_state.get("version", "unknown"),
        "last_updated": current_state.get("last_updated", "unknown"),
        "audit_count": audit_count,
        "dependency_violations": dependency_violations,
        "project_root": config.project_root
    }
    
    return {
        "status": "PASSED",
        "data": stats
    }

def cli_dashboard(state, payload):
    """
    CLI 仪表盘工具入口
    
    Args:
        state: 当前项目状态
        payload: 工具负载 (未使用)
        
    Returns:
        dict: 执行结果
    """
    success = DashboardTools.show_cli_dashboard()
    if success:
        return {
            "status": "PASSED",
            "message": "CLI dashboard displayed successfully"
        }
    else:
        return {
            "status": "FAILED",
            "message": "Failed to display CLI dashboard"
        }
