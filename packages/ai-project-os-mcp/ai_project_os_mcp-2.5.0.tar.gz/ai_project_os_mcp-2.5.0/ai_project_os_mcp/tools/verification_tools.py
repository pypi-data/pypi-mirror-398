"""
Verification Tools - 验证项目状态
"""

import subprocess
import os
import re
from ai_project_os_mcp.config import config

def run_tests(state, payload):
    """
    运行项目测试
    
    Args:
        state: 当前项目状态
        payload: 工具负载 (可选包含 test_path)
        
    Returns:
        dict: 测试结果
    """
    test_path = payload.get("test_path", "tests")
    
    # 简单使用 pytest
    try:
        # 确保在项目根目录运行
        cwd = config.project_root
        
        # 构建命令
        cmd = ["pytest", test_path]
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60 # 1分钟超时
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def verify_audit_integrity(state, payload):
    """
    验证审计记录中的 Git Commit Hash 是否存在于 Git 历史中
    
    Args:
        state: 当前项目状态
        payload: 工具负载 (未使用)
        
    Returns:
        dict: 验证结果
    """
    audit_file = os.path.join(config.project_root, "docs", "S5_audit.md")
    
    # 检查审计文件是否存在
    if not os.path.exists(audit_file):
        return {
            "status": "FAILED",
            "reason": f"Audit file not found: {audit_file}"
        }
    
    # 读取审计文件
    try:
        with open(audit_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {
            "status": "FAILED",
            "reason": f"Error reading audit file: {str(e)}"
        }
    
    # 提取所有 Commit Hash
    commit_hashes = []
    # 使用正则表达式匹配 Commit Hash
    hash_pattern = r"- Commit Hash: ([a-f0-9]{40})"
    matches = re.findall(hash_pattern, content)
    commit_hashes.extend(matches)
    
    if not commit_hashes:
        return {
            "status": "PASSED",
            "message": "No Commit Hashes found in audit file",
            "verified_hashes": [],
            "failed_hashes": []
        }
    
    # 验证每个 Commit Hash 是否存在于 Git 历史中
    verified_hashes = []
    failed_hashes = []
    
    for commit_hash in commit_hashes:
        try:
            result = subprocess.run(
                ["git", "cat-file", "-t", commit_hash],
                cwd=config.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                verified_hashes.append(commit_hash)
            else:
                failed_hashes.append(commit_hash)
        except Exception:
            failed_hashes.append(commit_hash)
    
    # 构建结果
    if failed_hashes:
        return {
            "status": "FAILED",
            "reason": f"{len(failed_hashes)} out of {len(commit_hashes)} Commit Hashes are invalid",
            "verified_hashes": verified_hashes,
            "failed_hashes": failed_hashes
        }
    else:
        return {
            "status": "PASSED",
            "message": f"All {len(commit_hashes)} Commit Hashes are valid",
            "verified_hashes": verified_hashes,
            "failed_hashes": failed_hashes
        }
