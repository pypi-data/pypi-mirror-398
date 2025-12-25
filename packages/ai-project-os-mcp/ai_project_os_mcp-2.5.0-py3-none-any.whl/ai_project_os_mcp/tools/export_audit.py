"""
export_audit工具 - 导出审计记录

该模块负责：
1. 将 Markdown 审计日志导出为 JSON 格式
2. 支持导出为 PDF 格式（实验性）
"""

import os
import re
import json
from datetime import datetime

class ExportAudit:
    """
    审计记录导出类
    """
    
    @staticmethod
    def parse_audit_file(audit_file_path: str) -> list:
        """
        解析 Markdown 审计文件
        
        Args:
            audit_file_path: 审计文件路径
            
        Returns:
            list: 解析后的审计记录列表
        """
        if not os.path.exists(audit_file_path):
            raise FileNotFoundError(f"Audit file not found: {audit_file_path}")
        
        with open(audit_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 分割审计记录
        # 每条记录以 "## Sub-task: " 开头
        record_separator = r"\n## Sub-task: "
        records = re.split(record_separator, content)
        
        parsed_records = []
        
        # 第一条记录是文件标题，跳过
        for record in records[1:]:
            # 重新添加分隔符
            full_record = f"## Sub-task: {record}"
            parsed_record = ExportAudit._parse_single_record(full_record)
            if parsed_record:
                parsed_records.append(parsed_record)
        
        return parsed_records
    
    @staticmethod
    def _parse_single_record(record_content: str) -> dict:
        """
        解析单个审计记录
        
        Args:
            record_content: 单个审计记录内容
            
        Returns:
            dict: 解析后的审计记录
        """
        parsed = {}
        
        # 提取子任务 ID
        subtask_match = re.search(r"## Sub-task: (.*?)", record_content)
        if subtask_match:
            parsed["sub_task_id"] = subtask_match.group(1).strip()
        
        # 提取其他字段
        fields = [
            "Context Refresh",
            "Layer",
            "Files Changed",
            "Correctness Assertion",
            "Architecture Compliance",
            "Reviewer",
            "Commit Hash",
            "Approval",
            "Status",
            "Record Hash"
        ]
        
        for field in fields:
            if field == "Files Changed":
                # 特殊处理 Files Changed 字段（多行）
                pattern = rf"- {field}:\n((?:  - .*?\n)*)"
                match = re.search(pattern, record_content, re.DOTALL)
                if match:
                    files_changed = match.group(1).strip()
                    if files_changed:
                        parsed[field.lower().replace(" ", "_")] = [
                            f.strip() for f in files_changed.split("\n") if f.strip()
                        ]
                    else:
                        parsed[field.lower().replace(" ", "_")] = []
            elif field == "Approval":
                # 特殊处理 Approval 字段（结构化）
                pattern = rf"- {field}:\n((?:  - .*?\n)*)"
                match = re.search(pattern, record_content, re.DOTALL)
                if match:
                    approval_content = match.group(1).strip()
                    approval = {}
                    if approval_content:
                        approval_lines = approval_content.split("\n")
                        for line in approval_lines:
                            line = line.strip()
                            if line.startswith("- "):
                                line = line[2:]
                            if ": " in line:
                                key, value = line.split(": ", 1)
                                approval[key.lower().replace(" ", "_")] = value.strip()
                    parsed[field.lower().replace(" ", "_")] = approval
            else:
                # 普通字段
                pattern = rf"- {field}: (.*?)\n"
                match = re.search(pattern, record_content)
                if match:
                    parsed[field.lower().replace(" ", "_")] = match.group(1).strip()
        
        return parsed
    
    @staticmethod
    def export_to_json(audit_file_path: str, output_path: str = None) -> dict:
        """
        将审计记录导出为 JSON 格式
        
        Args:
            audit_file_path: 审计文件路径
            output_path: 输出文件路径，若为 None 则返回 JSON 数据
            
        Returns:
            dict: 导出的 JSON 数据
        """
        # 解析审计文件
        records = ExportAudit.parse_audit_file(audit_file_path)
        
        # 构建导出数据
        export_data = {
            "schema_version": "1.0",
            "export_timestamp": datetime.now().isoformat(),
            "records_count": len(records),
            "records": records
        }
        
        # 写入文件（如果提供了输出路径）
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return export_data
    
    @staticmethod
    def export_to_pdf(audit_file_path: str, output_path: str) -> bool:
        """
        将审计记录导出为 PDF 格式（实验性）
        
        Args:
            audit_file_path: 审计文件路径
            output_path: 输出文件路径
            
        Returns:
            bool: 导出成功返回 True，否则返回 False
        """
        try:
            # PDF 导出功能暂时未实现
            # 预留接口，未来可以使用 reportlab 或其他库实现
            print("PDF export is currently experimental and not implemented.")
            return False
        except Exception as e:
            print(f"PDF export failed: {str(e)}")
            return False

def export_audit(state, payload):
    """
    导出审计记录工具的入口函数
    
    Args:
        state: 当前项目状态
        payload: 工具负载，包含导出配置
        
    Returns:
        dict: 导出结果
    """
    # 验证必填字段
    required_fields = ["export_format"]
    for field in required_fields:
        if field not in payload:
            return {"status": "FAILED", "reason": f"Missing required field: {field}"}
    
    export_format = payload["export_format"]
    audit_file = payload.get("audit_file", "docs/S5_audit.md")
    output_path = payload.get("output_path")
    
    # 构建完整路径
    from ai_project_os_mcp.config import config
    project_root = config.project_root
    audit_file_path = os.path.join(project_root, audit_file)
    
    if not os.path.exists(audit_file_path):
        return {"status": "FAILED", "reason": f"Audit file not found: {audit_file_path}"}
    
    try:
        if export_format == "json":
            # 导出为 JSON
            export_data = ExportAudit.export_to_json(audit_file_path, output_path)
            return {
                "status": "PASSED",
                "message": f"Audit records exported to JSON successfully",
                "exported_records": len(export_data["records"]),
                "export_format": export_format,
                "output_path": output_path
            }
        elif export_format == "pdf":
            # 导出为 PDF
            success = ExportAudit.export_to_pdf(audit_file_path, output_path)
            if success:
                return {
                    "status": "PASSED",
                    "message": f"Audit records exported to PDF successfully",
                    "export_format": export_format,
                    "output_path": output_path
                }
            else:
                return {
                    "status": "FAILED",
                    "reason": "PDF export failed (experimental feature)",
                    "export_format": export_format
                }
        else:
            return {
                "status": "FAILED",
                "reason": f"Unsupported export format: {export_format}",
                "supported_formats": ["json", "pdf"]
            }
    except Exception as e:
        return {
            "status": "FAILED",
            "reason": f"Export failed: {str(e)}",
            "export_format": export_format
        }
