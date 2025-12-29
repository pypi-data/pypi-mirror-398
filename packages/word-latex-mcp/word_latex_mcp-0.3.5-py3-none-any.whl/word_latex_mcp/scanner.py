"""
LaTeX 片段识别与定位模块
"""

import re
from typing import Iterator, Optional
from .models import LatexMatch, Region, BODY_REGIONS, ALL_REGIONS


class LatexPreProcessor:
    """Word 文本预处理器"""
    
    # Word 特殊字符映射
    CHAR_REPLACEMENTS = {
        '\r': '\n',         # 回车 -> 换行
        '\x0b': '\n',       # 垂直制表符（软回车）-> 换行
        '\x0c': '',         # 分页符 -> 移除
        '\x07': '',         # 表格单元格结束标记 -> 移除
        '\xa0': ' ',        # 不间断空格 -> 普通空格
        '\u2028': '\n',     # 行分隔符 -> 换行
        '\u2029': '\n',     # 段落分隔符 -> 换行
        '\u200b': '',       # 零宽空格 -> 移除
        '\u200c': '',       # 零宽非连接符 -> 移除
        '\u200d': '',       # 零宽连接符 -> 移除
        '\ufeff': '',       # BOM -> 移除
        # 智能引号
        '"': '"',           # 左双引号
        '"': '"',           # 右双引号
        ''': "'",           # 左单引号
        ''': "'",           # 右单引号
        '–': '-',           # En dash
        '—': '-',           # Em dash
        '…': '...',         # 省略号
    }
    
    @classmethod
    def preprocess(cls, text: str) -> str:
        """
        预处理 Word 文本，标准化特殊字符
        
        Args:
            text: 原始文本
            
        Returns:
            str: 标准化后的文本
        """
        result = text
        for old, new in cls.CHAR_REPLACEMENTS.items():
            result = result.replace(old, new)
        return result
    
    @classmethod
    def get_original_positions(cls, original: str, processed: str) -> dict[int, int]:
        """
        计算处理后位置到原始位置的映射
        
        这是为了在预处理后仍能定位到原文档中的正确位置
        """
        # 简单实现：假设字符一一对应（对于我们的替换规则基本成立）
        # 如果需要更精确的映射，可以扩展此方法
        return {}


class LatexScanner:
    """LaTeX 公式扫描器"""
    
    # 预编译正则表达式 - 升级版
    # 策略：同时匹配转义字符和LaTeX模式
    # 1. escaped: 匹配 \\. (消耗掉转义符和被转义的字符，如 \$ 或 \\)
    # 2. display: 匹配 $$...$$
    # 3. inline: 匹配 $...$
    
    LATEX_PATTERN_MULTILINE = re.compile(
        r'(?P<escaped>\\.)|'
        r'(?P<display>\$\$(?P<d_content>.*?)\$\$)|'
        r'(?P<inline>\$(?P<i_content>.*?)\$)',
        re.DOTALL
    )
    
    # 单行模式（不允许行内公式跨行）
    LATEX_PATTERN_SINGLELINE = re.compile(
        r'(?P<escaped>\\.)|'
        r'(?P<display>\$\$(?P<d_content>.*?)\$\$)|'
        r'(?P<inline>\$(?P<i_content>[^\n\r\x0b]*?)\$)',
        re.DOTALL
    )
    
    # 金额模式：$后面紧跟数字（可能有小数点和逗号）
    MONEY_PATTERN = re.compile(r'^[\d,]+\.?\d*$')
    
    def __init__(
        self, 
        skip_money_patterns: bool = True,
        policy_manager: Optional["PolicyManager"] = None
    ):
        """
        初始化扫描器
        
        Args:
            skip_money_patterns: 是否跳过疑似金额的模式如 $100$
            policy_manager: 策略管理器（可选）
        """
        self.skip_money_patterns = skip_money_patterns
        self.policy_manager = policy_manager
        
        # 根据配置选择正则
        if policy_manager and not policy_manager.config.allow_multiline_inline:
            self.latex_pattern = self.LATEX_PATTERN_SINGLELINE
        else:
            self.latex_pattern = self.LATEX_PATTERN_MULTILINE
    
    def _is_money_pattern(self, latex_code: str) -> bool:
        """判断是否为金额模式"""
        if not self.skip_money_patterns:
            return False
        return bool(self.MONEY_PATTERN.match(latex_code.strip()))
    
    def _extract_context(self, text: str, start: int, end: int, context_len: int = 20) -> str:
        """提取上下文摘要"""
        ctx_start = max(0, start - context_len)
        ctx_end = min(len(text), end + context_len)
        
        prefix = "..." if ctx_start > 0 else ""
        suffix = "..." if ctx_end < len(text) else ""
        
        return prefix + text[ctx_start:ctx_end] + suffix
    
    def _check_length_limits(self, latex_code: str, is_display: bool) -> bool:
        """检查是否超过长度限制"""
        if not self.policy_manager:
            return True  # 无配置时不限制
        
        config = self.policy_manager.config
        max_len = config.max_display_length if is_display else config.max_inline_length
        return len(latex_code) <= max_len
    
    def _check_line_count(self, latex_code: str) -> bool:
        """检查跨行数是否在限制内"""
        if not self.policy_manager:
            return True
        
        config = self.policy_manager.config
        line_count = latex_code.count('\n') + latex_code.count('\r') + latex_code.count('\x0b') + 1
        return line_count <= config.max_line_count
    
    def scan_text(
        self, 
        text: str, 
        region: Region,
        base_offset: int = 0,
        paragraph_index: int = -1,
        region_index: int = -1,
        preprocess: bool = True
    ) -> Iterator[LatexMatch]:
        """
        扫描文本中的 LaTeX 片段
        
        Args:
            text: 要扫描的文本
            region: 所属区域
            base_offset: 基础偏移量（用于计算在文档中的绝对位置）
            paragraph_index: 段落索引
            region_index: 区域内索引
            preprocess: 是否预处理文本
            
        Yields:
            LatexMatch: 匹配的 LaTeX 片段信息
        """
        # 预处理文本（标准化 Word 特殊字符）
        # 注意：我们在原始文本上匹配，但可能需要在预处理后的文本上识别
        # 为了保持位置准确性，我们使用原始文本匹配
        working_text = text
        
        for match in self.latex_pattern.finditer(working_text):
            # 如果匹配的是转义字符，跳过
            if match.group('escaped'):
                continue
            
            # 判断是 $$ 还是 $
            if match.group('display'):
                # $$...$$ 显示公式
                latex_code = match.group('d_content')
                is_display = True
            elif match.group('inline'):
                # $...$ 行内公式
                latex_code = match.group('i_content')
                is_display = False
            else:
                continue
            
            # 跳过金额模式
            if self._is_money_pattern(latex_code):
                continue
            
            # 检查长度限制
            if not self._check_length_limits(latex_code, is_display):
                continue
            
            # 检查跨行数限制
            if not self._check_line_count(latex_code):
                continue
            
            full_match = match.group(0)
            start_pos = base_offset + match.start()
            end_pos = base_offset + match.end()
            context = self._extract_context(working_text, match.start(), match.end())
            
            yield LatexMatch(
                latex_code=latex_code,
                full_match=full_match,
                start_pos=start_pos,
                end_pos=end_pos,
                region=region,
                is_display=is_display,
                paragraph_index=paragraph_index,
                context=context,
                region_index=region_index,
            )
    
    def scan_word_range(self, word_range, region: Region, region_index: int = -1) -> list[LatexMatch]:
        """
        扫描 Word Range 对象
        
        Args:
            word_range: Word Range COM 对象
            region: 所属区域
            region_index: 区域内索引
            
        Returns:
            list[LatexMatch]: 匹配列表
        """
        try:
            text = word_range.Text
            base_offset = word_range.Start
            matches = list(self.scan_text(text, region, base_offset, region_index=region_index))
            return matches
        except Exception:
            # COM 对象访问失败时返回空列表
            return []
    
    def scan_paragraphs(self, doc, region: Region = Region.BODY) -> list[LatexMatch]:
        """
        扫描文档正文段落
        
        Args:
            doc: Word Document COM 对象
            region: 区域类型
            
        Returns:
            list[LatexMatch]: 匹配列表
        """
        matches = []
        try:
            for i, para in enumerate(doc.Paragraphs):
                para_matches = list(self.scan_text(
                    para.Range.Text,
                    region,
                    base_offset=para.Range.Start,
                    paragraph_index=i
                ))
                matches.extend(para_matches)
        except Exception:
            pass
        return matches
    
    def scan_tables(self, doc, region: Region = Region.BODY) -> list[LatexMatch]:
        """
        扫描文档表格
        
        Args:
            doc: Word Document COM 对象
            region: 区域类型
            
        Returns:
            list[LatexMatch]: 匹配列表
        """
        matches = []
        try:
            for table_idx, table in enumerate(doc.Tables):
                for row in table.Rows:
                    for cell in row.Cells:
                        cell_matches = self.scan_word_range(
                            cell.Range, 
                            region, 
                            region_index=table_idx
                        )
                        matches.extend(cell_matches)
        except Exception:
            pass
        return matches
    
    def scan_headers_footers(self, doc) -> list[LatexMatch]:
        """
        扫描页眉页脚
        
        Args:
            doc: Word Document COM 对象
            
        Returns:
            list[LatexMatch]: 匹配列表
        """
        matches = []
        try:
            for sec_idx, section in enumerate(doc.Sections):
                # 页眉
                for header in section.Headers:
                    header_matches = self.scan_word_range(
                        header.Range,
                        Region.HEADER,
                        region_index=sec_idx
                    )
                    matches.extend(header_matches)
                
                # 页脚
                for footer in section.Footers:
                    footer_matches = self.scan_word_range(
                        footer.Range,
                        Region.FOOTER,
                        region_index=sec_idx
                    )
                    matches.extend(footer_matches)
        except Exception:
            pass
        return matches
    
    def scan_footnotes(self, doc) -> list[LatexMatch]:
        """
        扫描脚注
        
        Args:
            doc: Word Document COM 对象
            
        Returns:
            list[LatexMatch]: 匹配列表
        """
        matches = []
        try:
            for i, footnote in enumerate(doc.Footnotes):
                fn_matches = self.scan_word_range(
                    footnote.Range,
                    Region.FOOTNOTE,
                    region_index=i
                )
                matches.extend(fn_matches)
        except Exception:
            pass
        return matches
    
    def scan_endnotes(self, doc) -> list[LatexMatch]:
        """
        扫描尾注
        
        Args:
            doc: Word Document COM 对象
            
        Returns:
            list[LatexMatch]: 匹配列表
        """
        matches = []
        try:
            for i, endnote in enumerate(doc.Endnotes):
                en_matches = self.scan_word_range(
                    endnote.Range,
                    Region.ENDNOTE,
                    region_index=i
                )
                matches.extend(en_matches)
        except Exception:
            pass
        return matches
    
    def scan_comments(self, doc) -> list[LatexMatch]:
        """
        扫描批注
        
        Args:
            doc: Word Document COM 对象
            
        Returns:
            list[LatexMatch]: 匹配列表
        """
        matches = []
        try:
            for i, comment in enumerate(doc.Comments):
                comment_matches = self.scan_word_range(
                    comment.Range,
                    Region.COMMENT,
                    region_index=i
                )
                matches.extend(comment_matches)
        except Exception:
            pass
        return matches
    
    def scan_textboxes(self, doc) -> list[LatexMatch]:
        """
        扫描文本框和形状
        
        Args:
            doc: Word Document COM 对象
            
        Returns:
            list[LatexMatch]: 匹配列表
        """
        matches = []
        try:
            # 浮动形状
            for i, shape in enumerate(doc.Shapes):
                if shape.TextFrame.HasText:
                    tb_matches = self.scan_word_range(
                        shape.TextFrame.TextRange,
                        Region.TEXTBOX,
                        region_index=i
                    )
                    matches.extend(tb_matches)
        except Exception:
            pass
        
        try:
            # 内联形状
            for i, shape in enumerate(doc.InlineShapes):
                if hasattr(shape, 'TextFrame') and shape.TextFrame.HasText:
                    tb_matches = self.scan_word_range(
                        shape.TextFrame.TextRange,
                        Region.TEXTBOX,
                        region_index=i
                    )
                    matches.extend(tb_matches)
        except Exception:
            pass
        
        return matches
    
    def scan_body(self, doc) -> list[LatexMatch]:
        """
        扫描正文区域（段落 + 表格）
        
        Args:
            doc: Word Document COM 对象
            
        Returns:
            list[LatexMatch]: 匹配列表
        """
        matches = []
        matches.extend(self.scan_paragraphs(doc))
        # matches.extend(self.scan_tables(doc))  # Paragraphs 已经包含表格内容，避免重复扫描
        return matches
    
    def scan_other_regions(self, doc) -> list[LatexMatch]:
        """
        扫描非正文区域
        
        Args:
            doc: Word Document COM 对象
            
        Returns:
            list[LatexMatch]: 匹配列表
        """
        matches = []
        matches.extend(self.scan_headers_footers(doc))
        matches.extend(self.scan_footnotes(doc))
        matches.extend(self.scan_endnotes(doc))
        matches.extend(self.scan_comments(doc))
        matches.extend(self.scan_textboxes(doc))
        return matches
    
    def scan_all(self, doc) -> list[LatexMatch]:
        """
        扫描全部区域
        
        Args:
            doc: Word Document COM 对象
            
        Returns:
            list[LatexMatch]: 匹配列表
        """
        matches = []
        matches.extend(self.scan_body(doc))
        matches.extend(self.scan_other_regions(doc))
        return matches
    
    def scan_regions(self, doc, regions: set[Region]) -> list[LatexMatch]:
        """
        扫描指定区域
        
        Args:
            doc: Word Document COM 对象
            regions: 要扫描的区域集合
            
        Returns:
            list[LatexMatch]: 匹配列表
        """
        matches = []
        
        if Region.BODY in regions:
            matches.extend(self.scan_body(doc))
        if Region.HEADER in regions or Region.FOOTER in regions:
            matches.extend(self.scan_headers_footers(doc))
        if Region.FOOTNOTE in regions:
            matches.extend(self.scan_footnotes(doc))
        if Region.ENDNOTE in regions:
            matches.extend(self.scan_endnotes(doc))
        if Region.COMMENT in regions:
            matches.extend(self.scan_comments(doc))
        if Region.TEXTBOX in regions:
            matches.extend(self.scan_textboxes(doc))
        
        return matches



