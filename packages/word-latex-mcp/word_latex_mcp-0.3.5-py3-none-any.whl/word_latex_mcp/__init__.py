"""
Word LaTeX MCP - 将 Word 文档中的 LaTeX 公式批量转换为原生数学公式

Usage:
    uvx word-latex-mcp
    
    或在 Cursor MCP 配置中添加：
    {
        "mcpServers": {
            "word-latex": {
                "command": "uvx",
                "args": ["word-latex-mcp"]
            }
        }
    }
"""

__version__ = "0.3.2"
__author__ = "Word LaTeX MCP"

from .models import LatexMatch, ConversionResult, ConversionReport
from .scanner import LatexScanner
from .converter import LatexConverter
from .backup import BackupManager
from .reporter import ReportGenerator

__all__ = [
    "__version__",
    "LatexMatch",
    "ConversionResult", 
    "ConversionReport",
    "LatexScanner",
    "LatexConverter",
    "BackupManager",
    "ReportGenerator",
]





