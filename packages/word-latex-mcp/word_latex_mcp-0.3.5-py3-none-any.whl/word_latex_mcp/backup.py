"""
备份管理模块
"""

import os
from datetime import datetime


class BackupManager:
    """文档备份管理器"""
    
    @staticmethod
    def generate_backup_path(original_path: str) -> str:
        """
        生成备份文件路径
        
        Args:
            original_path: 原文件路径
            
        Returns:
            str: 备份文件路径
        """
        dir_path = os.path.dirname(original_path)
        filename = os.path.basename(original_path)
        name, ext = os.path.splitext(filename)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{name}_backup_{timestamp}{ext}"
        
        return os.path.join(dir_path, backup_name)
    
    @staticmethod
    def generate_copy_path(original_path: str) -> str:
        """
        生成工作副本路径
        
        Args:
            original_path: 原文件路径
            
        Returns:
            str: 工作副本路径
        """
        dir_path = os.path.dirname(original_path)
        filename = os.path.basename(original_path)
        name, ext = os.path.splitext(filename)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        copy_name = f"{name}_converted_{timestamp}{ext}"
        
        return os.path.join(dir_path, copy_name)
    
    def create_backup(self, doc) -> str | None:
        """
        创建文档备份
        
        Args:
            doc: Word Document COM 对象
            
        Returns:
            str | None: 备份文件路径，失败返回 None
        """
        try:
            original_path = doc.FullName
            backup_path = self.generate_backup_path(original_path)
            
            # 使用 SaveAs2 保存副本
            doc.SaveAs2(backup_path)
            
            # 重新打开原文件（因为 SaveAs 会切换到新文件）
            doc.SaveAs2(original_path)
            
            return backup_path
            
        except Exception:
            return None
    
    def create_working_copy(self, doc, app) -> tuple:
        """
        创建工作副本并在副本上操作
        
        Args:
            doc: Word Document COM 对象
            app: Word Application COM 对象
            
        Returns:
            tuple: (新文档对象, 副本路径) 或 (None, None)
        """
        try:
            original_path = doc.FullName
            copy_path = self.generate_copy_path(original_path)
            
            # 保存副本
            doc.SaveAs2(copy_path)
            
            # 关闭当前文档
            doc.Close(SaveChanges=False)
            
            # 重新打开原文件（保持不变）
            app.Documents.Open(original_path)
            
            # 打开副本进行操作
            new_doc = app.Documents.Open(copy_path)
            
            return new_doc, copy_path
            
        except Exception:
            return None, None
    
    def save_document(self, doc) -> bool:
        """
        保存文档
        
        Args:
            doc: Word Document COM 对象
            
        Returns:
            bool: 是否保存成功
        """
        try:
            doc.Save()
            return True
        except Exception:
            return False





