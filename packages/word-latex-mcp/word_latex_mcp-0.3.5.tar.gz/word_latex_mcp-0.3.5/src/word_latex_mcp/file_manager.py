"""
Word 文件管理模块

提供文件打开、状态检测、占用检查等功能
"""

import os
import re
from typing import Optional, Any, Tuple


class FileManager:
    """Word 文件管理器"""
    
    # 支持的文件格式
    SUPPORTED_FORMATS = {'.docx', '.doc'}
    
    def __init__(self, word_app: Any):
        """
        初始化文件管理器
        
        Args:
            word_app: Word.Application COM 对象
        """
        self._app = word_app
    
    def normalize_path(self, file_path: str) -> str:
        """
        标准化文件路径
        
        - 展开环境变量
        - 转换为绝对路径
        - 统一使用反斜杠（Windows）
        - 统一大小写（Windows 不区分大小写）
        
        Args:
            file_path: 原始文件路径
            
        Returns:
            str: 标准化后的路径
        """
        # 展开环境变量
        path = os.path.expandvars(file_path)
        
        # 展开用户目录 ~
        path = os.path.expanduser(path)
        
        # 转换为绝对路径
        path = os.path.abspath(path)
        
        # 统一使用反斜杠（Windows 风格）
        path = path.replace('/', '\\')
        
        return path
    
    def check_file_exists(self, file_path: str) -> Tuple[bool, str]:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径（应已标准化）
            
        Returns:
            tuple[bool, str]: (是否存在, 错误信息)
        """
        if os.path.exists(file_path):
            return True, ""
        else:
            return False, f"文件不存在: {file_path}"
    
    def check_file_format(self, file_path: str) -> Tuple[bool, str]:
        """
        检查文件格式是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            tuple[bool, str]: (是否支持, 错误信息)
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext in self.SUPPORTED_FORMATS:
            return True, ""
        else:
            return False, f"不支持的文件格式 '{ext}'，仅支持 .docx/.doc 文件"
    
    def check_file_locked(self, file_path: str) -> Tuple[bool, str]:
        """
        检查文件是否被其他进程锁定
        
        通过尝试以独占写模式打开文件来检测
        
        Args:
            file_path: 文件路径
            
        Returns:
            tuple[bool, str]: (是否被锁定, 锁定信息)
        """
        try:
            # 尝试以独占写模式打开
            fd = os.open(file_path, os.O_RDWR | os.O_EXCL)
            os.close(fd)
            return False, ""
        except PermissionError:
            return True, "文件被其他程序占用，请关闭后重试"
        except OSError as e:
            # errno 13: Permission denied
            # errno 32: Sharing violation (Windows)
            if e.errno in (13, 32):
                return True, "文件正在被其他程序使用，请关闭后重试"
            # 其他错误不认为是锁定
            return False, ""
        except Exception:
            return False, ""
    
    def find_open_document(self, file_path: str) -> Optional[Any]:
        """
        在 Word 已打开的文档中查找指定文件
        
        Args:
            file_path: 文件路径（应已标准化）
            
        Returns:
            Document COM 对象或 None
        """
        normalized_target = self.normalize_path(file_path).lower()
        
        try:
            for doc in self._app.Documents:
                try:
                    doc_path = self.normalize_path(doc.FullName).lower()
                    if doc_path == normalized_target:
                        return doc
                except Exception:
                    continue
        except Exception:
            pass
        
        return None
    
    def activate_document(self, doc: Any) -> bool:
        """
        激活文档窗口（使其成为活动文档）
        
        Args:
            doc: Document COM 对象
            
        Returns:
            bool: 是否激活成功
        """
        try:
            doc.Activate()
            return True
        except Exception:
            return False
    
    def open_document(self, file_path: str) -> Tuple[Optional[Any], str]:
        """
        打开 Word 文档
        
        完整流程：
        1. 标准化路径
        2. 检查文件存在
        3. 检查格式支持
        4. 检查是否已打开（复用）
        5. 检查是否被锁定
        6. 打开文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            tuple[Document, str]: (文档对象, 错误信息)
                - 成功时：(doc, "")
                - 失败时：(None, 错误信息)
        """
        # 1. 标准化路径
        normalized_path = self.normalize_path(file_path)
        
        # 2. 检查文件存在
        exists, err = self.check_file_exists(normalized_path)
        if not exists:
            return None, err
        
        # 3. 检查格式支持
        supported, err = self.check_file_format(normalized_path)
        if not supported:
            return None, err
        
        # 4. 检查是否已在 Word 中打开
        existing_doc = self.find_open_document(normalized_path)
        if existing_doc is not None:
            # 激活并复用
            self.activate_document(existing_doc)
            return existing_doc, ""
        
        # 5. 检查是否被其他程序锁定
        locked, err = self.check_file_locked(normalized_path)
        if locked:
            return None, err
        
        # 6. 打开文件
        try:
            doc = self._app.Documents.Open(normalized_path)
            return doc, ""
        except Exception as e:
            error_msg = str(e)
            # 解析常见错误
            if "cannot open" in error_msg.lower() or "无法打开" in error_msg:
                return None, f"无法打开文件，可能文件已损坏或格式不兼容: {normalized_path}"
            elif "permission" in error_msg.lower() or "权限" in error_msg:
                return None, f"没有权限打开此文件: {normalized_path}"
            else:
                return None, f"打开文件失败: {error_msg}"
