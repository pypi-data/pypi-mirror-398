"""
分段函数 cases 环境处理器

将 LaTeX cases 环境转换为 Word OMML 友好的格式
"""

import re
from typing import Dict, List, Tuple


class CasesHandler:
    """分段函数 cases 环境处理器"""
    
    # 支持的 cases 变体及其括号方向
    # 'left' = 左大括号, 'right' = 右大括号
    CASES_TYPES: Dict[str, str] = {
        'cases':   'left',    # 标准左大括号
        'dcases':  'left',    # 显示模式左大括号
        'rcases':  'right',   # 右大括号
        'cases*':  'left',    # 文本模式
    }
    
    # cases 环境正则表达式
    CASES_PATTERN = re.compile(
        r'\\begin\{(cases\*?|dcases|rcases)\}'
        r'([\s\S]*?)'
        r'\\end\{\1\}',
        re.IGNORECASE
    )
    
    # \text{} 提取正则
    TEXT_PATTERN = re.compile(r'\\text\{([^}]*)\}')
    
    @classmethod
    def detect_cases(cls, latex_code: str) -> List[dict]:
        """
        检测 LaTeX 代码中的 cases 环境
        
        Args:
            latex_code: LaTeX 代码
            
        Returns:
            list[dict]: 检测到的 cases 信息列表
        """
        cases_list = []
        for match in cls.CASES_PATTERN.finditer(latex_code):
            cases_list.append({
                'type': match.group(1),
                'content': match.group(2),
                'start': match.start(),
                'end': match.end(),
                'full_match': match.group(0)
            })
        return cases_list
    
    @classmethod
    def parse_branches(cls, content: str) -> List[Tuple[str, str]]:
        """
        解析 cases 内部的分支
        
        Args:
            content: cases 内部内容
            
        Returns:
            list[tuple[str, str]]: [(表达式, 条件), ...]
        """
        branches = []
        
        # 按 \\\\ 分割行
        rows = re.split(r'\\\\', content)
        
        for row in rows:
            row = row.strip()
            if not row:
                continue
            
            # 按 & 分割（只分割第一个）
            parts = row.split('&', 1)
            expr = parts[0].strip()
            cond = parts[1].strip() if len(parts) > 1 else ''
            
            branches.append((expr, cond))
        
        return branches
    
    @classmethod
    def normalize_row_separator(cls, content: str) -> str:
        """
        标准化行分隔符
        
        将单反斜杠换行（非标准写法）转换为双反斜杠：
        - '\\ ' （单反斜杠后空格）→ '\\\\ '
        
        Args:
            content: cases 内部内容
            
        Returns:
            str: 标准化后的内容
        """
        result = content
        
        # 处理单反斜杠后跟空白的情况（非标准写法）
        # 例如：x & if x>0 \ -x & if x<0 → x & if x>0 \\ -x & if x<0
        # 注意：要避免误伤已经是 \\ 的情况
        result = re.sub(r'(?<!\\)\\(?=\s+(?!\\))', r'\\\\', result)
        
        return result
    
    @classmethod
    def convert_to_omml_friendly(cls, cases_type: str, content: str) -> str:
        """
        将 cases 转换为 Word OMML 友好的格式
        
        策略：
        Word 对 \\begin{cases} 的原生支持不稳定，
        转换为等价的矩阵+左括号形式：
        
        \\begin{cases} x & \\text{if } x>0 \\\\ -x & \\text{if } x<0 \\end{cases}
        →
        \\left\\{ \\matrix{x & \\text{if } x>0 \\\\ -x & \\text{if } x<0} \\right.
        
        注意：右侧使用 \\right. 表示无括号
        
        Args:
            cases_type: cases 类型
            content: cases 内部内容
            
        Returns:
            str: OMML 友好的格式
        """
        # 标准化行分隔符（处理单反斜杠非标准写法）
        normalized_content = cls.normalize_row_separator(content.strip())
        
        # 🔧 关键：将LaTeX换行符 \\ 转换为 Word UnicodeMath 的 @ 行分隔符
        # Word \matrix 语法：行用@分隔，列用&分隔
        normalized_content = re.sub(r'\\\\', '@', normalized_content)
        
        # 获取括号方向
        bracket_side = cls.CASES_TYPES.get(cases_type, 'left')
        
        if bracket_side == 'left':
            # 左大括号：\left\{ ... \right.
            return f"\\left\\{{\\matrix{{{normalized_content}}}\\right."
        else:
            # 右大括号：\left. ... \right\}
            return f"\\left.\\matrix{{{normalized_content}}}\\right\\}}"
    
    @classmethod
    def process(cls, latex_code: str) -> str:
        """
        处理 LaTeX 代码中的所有 cases 环境
        
        Args:
            latex_code: 原始 LaTeX 代码
            
        Returns:
            str: 处理后的代码
        """
        result = latex_code
        
        # 从后向前替换，避免位置偏移
        cases_list = cls.detect_cases(latex_code)
        for cases_info in reversed(cases_list):
            cases_type = cases_info['type']
            content = cases_info['content']
            full_match = cases_info['full_match']
            
            # 转换为 OMML 友好格式
            omml_format = cls.convert_to_omml_friendly(cases_type, content)
            
            # 替换
            result = result.replace(full_match, omml_format, 1)
        
        return result
