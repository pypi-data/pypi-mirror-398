"""
矩阵环境处理器

将 LaTeX 矩阵环境转换为 Word OMML 友好的格式
"""

import re
from typing import Dict, List, Tuple


class MatrixHandler:
    """矩阵环境处理器"""
    
    # 支持的矩阵类型及其括号映射
    # (左括号, 右括号)
    MATRIX_TYPES: Dict[str, Tuple[str, str]] = {
        'matrix':      ('', ''),           # 无括号
        'pmatrix':     ('(', ')'),         # 圆括号
        'bmatrix':     ('[', ']'),         # 方括号
        'Bmatrix':     ('\\{', '\\}'),     # 大括号
        'vmatrix':     ('|', '|'),         # 单竖线（行列式）
        'Vmatrix':     ('\\|', '\\|'),     # 双竖线（范数）
        'smallmatrix': ('', ''),           # 行内小矩阵
    }
    
    # 矩阵环境正则表达式（LaTeX 语法）
    MATRIX_PATTERN = re.compile(
        r'\\begin\{(' + '|'.join(MATRIX_TYPES.keys()) + r')\}'
        r'([\s\S]*?)'
        r'\\end\{\1\}',
        re.IGNORECASE
    )
    
    # UnicodeMath 矩阵语法：\matrix(...) 使用圆括号
    # 例如：\matrix(a & b @ c & d)
    UNICODEMATH_MATRIX_PATTERN = re.compile(
        r'\\matrix\(([^)]*)\)',
        re.IGNORECASE
    )
    
    # 非标准行分隔符模式（单反斜杠后跟空白）
    NONSTANDARD_ROW_SEP = re.compile(r'(?<!\\)\\(?=\s+[^\\])')
    
    @classmethod
    def detect_matrix(cls, latex_code: str) -> List[dict]:
        """
        检测 LaTeX 代码中的矩阵环境
        
        Args:
            latex_code: LaTeX 代码
            
        Returns:
            list[dict]: 检测到的矩阵信息列表
        """
        matrices = []
        for match in cls.MATRIX_PATTERN.finditer(latex_code):
            matrices.append({
                'type': match.group(1),
                'content': match.group(2),
                'start': match.start(),
                'end': match.end(),
                'full_match': match.group(0)
            })
        return matrices
    
    @classmethod
    def detect_unicodemath_matrix(cls, latex_code: str) -> List[dict]:
        """
        检测 UnicodeMath 语法的矩阵：\\matrix(...)
        
        Args:
            latex_code: LaTeX 代码
            
        Returns:
            list[dict]: 检测到的矩阵信息列表
        """
        matrices = []
        for match in cls.UNICODEMATH_MATRIX_PATTERN.finditer(latex_code):
            matrices.append({
                'type': 'unicodemath_matrix',
                'content': match.group(1),
                'start': match.start(),
                'end': match.end(),
                'full_match': match.group(0)
            })
        return matrices
    
    @classmethod
    def convert_unicodemath_to_omml(cls, content: str) -> str:
        """
        将 UnicodeMath 矩阵语法转换为 Word OMML 友好的格式
        
        \\matrix(a & b @ c & d) → \\left(\\matrix{a & b @ c & d}\\right)
        
        Args:
            content: 矩阵内部内容（已经是 @ 分隔行，& 分隔列）
            
        Returns:
            str: OMML 友好的格式（带圆括号包裹）
        """
        # UnicodeMath 语法已经使用 @ 作为行分隔符，& 作为列分隔符
        # 添加圆括号包裹，使矩阵显示更符合数学惯例
        return f"\\left(\\matrix{{{content}}}\\right)"
    
    @classmethod
    def normalize_row_separator(cls, content: str) -> str:
        """
        标准化行分隔符
        
        将各种变体统一为标准 \\\\：
        - '\\ ' （单反斜杠后空格）→ '\\\\ '
        - 确保 \\\\ 后有空格
        
        Args:
            content: 矩阵内部内容
            
        Returns:
            str: 标准化后的内容
        """
        result = content
        
        # 处理单反斜杠后跟空白的情况（非标准写法）
        # 例如：a & b \ c & d → a & b \\ c & d
        result = re.sub(r'(?<!\\)\\(?=\s+(?!\\))', r'\\\\', result)
        
        # 确保 \\\\ 后有空格，避免与后续字符粘连
        result = re.sub(r'\\\\(?!\s)', r'\\\\ ', result)
        
        return result
    
    @classmethod
    def convert_to_omml_friendly(cls, matrix_type: str, content: str) -> str:
        """
        将矩阵转换为 Word OMML 友好的格式
        
        策略：
        Word 对 \\begin{pmatrix} 的原生支持不稳定，
        但对 \\left( \\matrix{...} \\right) 支持较好。
        
        转换规则：
        \\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}
        →
        \\left( \\matrix{a & b @ c & d} \\right)
        
        注意：Word UnicodeMath 使用 @ 作为行分隔符，& 作为列分隔符
        
        Args:
            matrix_type: 矩阵类型（pmatrix, bmatrix 等）
            content: 矩阵内部内容
            
        Returns:
            str: OMML 友好的格式
        """
        # 标准化行分隔符
        normalized_content = cls.normalize_row_separator(content)
        
        # 清理首尾空白
        normalized_content = normalized_content.strip()
        
        # 🔧 关键：将LaTeX换行符 \\ 转换为 Word UnicodeMath 的 @ 行分隔符
        normalized_content = re.sub(r'\\\\', '@', normalized_content)
        
        # 获取括号
        left_bracket, right_bracket = cls.MATRIX_TYPES.get(matrix_type, ('', ''))
        
        # 构建 OMML 友好格式
        if left_bracket and right_bracket:
            # 使用 \left \right 包裹
            return f"\\left{left_bracket}\\matrix{{{normalized_content}}}\\right{right_bracket}"
        else:
            # 无括号矩阵
            return f"\\matrix{{{normalized_content}}}"
    
    @classmethod
    def process(cls, latex_code: str) -> str:
        """
        处理 LaTeX 代码中的所有矩阵环境
        
        支持两种语法：
        1. LaTeX 语法：\\begin{pmatrix}...\\end{pmatrix}
        2. UnicodeMath 语法：\\matrix(...)
        
        Args:
            latex_code: 原始 LaTeX 代码
            
        Returns:
            str: 处理后的代码
        """
        result = latex_code
        
        # 1. 处理 LaTeX 语法矩阵（从后向前替换，避免位置偏移）
        matrices = cls.detect_matrix(latex_code)
        for matrix_info in reversed(matrices):
            matrix_type = matrix_info['type']
            content = matrix_info['content']
            full_match = matrix_info['full_match']
            
            # 转换为 OMML 友好格式
            omml_format = cls.convert_to_omml_friendly(matrix_type, content)
            
            # 替换
            result = result.replace(full_match, omml_format, 1)
        
        # 2. 处理 UnicodeMath 语法矩阵：\matrix(...)
        um_matrices = cls.detect_unicodemath_matrix(result)
        for matrix_info in reversed(um_matrices):
            content = matrix_info['content']
            full_match = matrix_info['full_match']
            
            # 转换为 OMML 友好格式
            omml_format = cls.convert_unicodemath_to_omml(content)
            
            # 替换
            result = result.replace(full_match, omml_format, 1)
        
        return result
