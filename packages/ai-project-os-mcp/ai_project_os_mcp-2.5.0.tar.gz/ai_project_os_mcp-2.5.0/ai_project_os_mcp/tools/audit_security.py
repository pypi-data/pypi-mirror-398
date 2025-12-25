"""
Audit Security - 审计记录防篡改功能

该模块负责：
1. 对审计记录计算 SHA256 签名
2. 验证审计记录的完整性
"""

import hashlib
import os
from datetime import datetime

class AuditSecurity:
    """
    审计记录安全管理类
    """
    
    @staticmethod
    def generate_record_hash(record_content: str) -> str:
        """
        对审计记录内容生成 SHA256 哈希值
        
        Args:
            record_content: 审计记录内容
            
        Returns:
            str: SHA256 哈希值（40 个字符）
        """
        # 使用 SHA256 算法生成哈希值
        sha256_hash = hashlib.sha256()
        sha256_hash.update(record_content.encode('utf-8'))
        return sha256_hash.hexdigest()
    
    @staticmethod
    def add_hash_to_record(record_content: str) -> str:
        """
        为审计记录添加哈希值
        
        Args:
            record_content: 审计记录内容
            
        Returns:
            str: 添加了哈希值的审计记录
        """
        # 生成哈希值
        record_hash = AuditSecurity.generate_record_hash(record_content)
        
        # 在记录末尾添加哈希值
        record_with_hash = f"{record_content.rstrip()}\n- Record Hash: {record_hash}\n"
        
        return record_with_hash
    
    @staticmethod
    def verify_record_integrity(record_content: str) -> bool:
        """
        验证审计记录的完整性
        
        Args:
            record_content: 包含哈希值的审计记录
            
        Returns:
            bool: 验证通过返回 True，否则返回 False
        """
        try:
            # 分离记录内容和哈希值
            lines = record_content.strip().split('\n')
            
            # 找到哈希值所在行
            hash_line = None
            record_lines = []
            
            for line in lines:
                if line.startswith('- Record Hash: '):
                    hash_line = line
                else:
                    record_lines.append(line)
            
            if not hash_line:
                # 没有哈希值，无法验证
                return False
            
            # 提取哈希值
            expected_hash = hash_line.split(': ')[1].strip()
            
            # 重新生成记录内容（不包含哈希值行）
            original_content = '\n'.join(record_lines)
            
            # 计算实际哈希值
            actual_hash = AuditSecurity.generate_record_hash(original_content)
            
            # 比较哈希值
            return actual_hash == expected_hash
        except Exception:
            return False
    
    @staticmethod
    def process_audit_file(audit_file_path: str) -> bool:
        """
        处理审计文件，为所有记录添加哈希值
        
        Args:
            audit_file_path: 审计文件路径
            
        Returns:
            bool: 处理成功返回 True，否则返回 False
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(audit_file_path):
                return False
            
            # 读取文件内容
            with open(audit_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 分割记录（每条记录以 ## Sub-task: 开头）
            records = content.split('\n## Sub-task: ')
            
            # 处理每个记录
            processed_records = []
            
            # 保留标题行（第一条记录可能包含文件标题）
            if records:
                processed_records.append(records[0])
                
                # 处理其余记录
                for record in records[1:]:
                    # 重新添加分隔符
                    full_record = f'\n## Sub-task: {record}'
                    # 添加哈希值
                    processed_record = AuditSecurity.add_hash_to_record(full_record)
                    processed_records.append(processed_record)
            
            # 合并处理后的记录
            processed_content = ''.join(processed_records)
            
            # 写回文件
            with open(audit_file_path, "w", encoding="utf-8") as f:
                f.write(processed_content)
            
            return True
        except Exception as e:
            print(f"Error processing audit file: {str(e)}")
            return False
    
    @staticmethod
    def verify_audit_file_integrity(audit_file_path: str) -> dict:
        """
        验证整个审计文件的完整性
        
        Args:
            audit_file_path: 审计文件路径
            
        Returns:
            dict: 验证结果，包含验证状态和详细信息
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(audit_file_path):
                return {
                    "status": "FAILED",
                    "reason": f"Audit file not found: {audit_file_path}",
                    "verified_records": 0,
                    "failed_records": 0
                }
            
            # 读取文件内容
            with open(audit_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 分割记录（每条记录以 ## Sub-task: 开头）
            records = content.split('\n## Sub-task: ')
            
            verified_records = 0
            failed_records = 0
            
            # 处理每个记录
            if len(records) > 1:
                # 跳过文件标题（第一条记录）
                for record in records[1:]:
                    # 重新添加分隔符
                    full_record = f'\n## Sub-task: {record}'
                    # 验证完整性
                    if AuditSecurity.verify_record_integrity(full_record):
                        verified_records += 1
                    else:
                        failed_records += 1
            
            # 构建结果
            if failed_records > 0:
                return {
                    "status": "FAILED",
                    "reason": f"{failed_records} out of {verified_records + failed_records} records failed verification",
                    "verified_records": verified_records,
                    "failed_records": failed_records
                }
            else:
                return {
                    "status": "PASSED",
                    "reason": f"All {verified_records} records passed verification",
                    "verified_records": verified_records,
                    "failed_records": failed_records
                }
        except Exception as e:
            return {
                "status": "FAILED",
                "reason": f"Error verifying audit file: {str(e)}",
                "verified_records": 0,
                "failed_records": 0
            }
