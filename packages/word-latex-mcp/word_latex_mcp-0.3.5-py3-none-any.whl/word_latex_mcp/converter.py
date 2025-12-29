"""
LaTeX 转换核心模块
"""

import re
import win32com.client
from typing import Literal, Optional
from .models import LatexMatch, ConversionResult, Region, FailureCategory


class LatexSanitizer:
    """LaTeX 清洗器"""
    
    # Word 特殊字符替换映射
    CHAR_REPLACEMENTS = {
        # 智能引号 -> 普通引号（使用 Unicode 码点）
        '\u201c': '"',  # 左双引号 "
        '\u201d': '"',  # 右双引号 "
        '\u2018': "'",  # 左单引号 '
        '\u2019': "'",  # 右单引号 '
        # 特殊空格
        '\xa0': ' ',        # 不间断空格
        '\u2009': ' ',      # 细空格
        '\u200a': ' ',      # 发空格
        # 特殊破折号
        '–': '-',           # En dash
        '—': '-',           # Em dash
        # 不可见字符
        '\u200b': '',       # 零宽空格
        '\u200c': '',       # 零宽非连接符
        '\u200d': '',       # 零宽连接符
        '\ufeff': '',       # BOM
        # Word 特殊标记
        '\x07': '',         # 表格单元格结束
        '\x0c': '',         # 分页符
    }
    
    # 换行符标准化
    NEWLINE_CHARS = ['\r\n', '\r', '\x0b']
    
    @classmethod
    def sanitize(cls, latex_code: str) -> str:
        """
        清洗 LaTeX 代码
        
        Args:
            latex_code: 原始 LaTeX 代码
            
        Returns:
            str: 清洗后的代码
        """
        result = latex_code
        
        # 1. 替换特殊字符
        for old, new in cls.CHAR_REPLACEMENTS.items():
            result = result.replace(old, new)
        
        # 2. 标准化换行符
        for char in cls.NEWLINE_CHARS:
            result = result.replace(char, '\n')
        
        # 3. 清理多余空白（但保留必要的空格）
        result = re.sub(r' +', ' ', result)  # 多个空格合并
        result = re.sub(r'\n\s*\n', '\n', result)  # 多个空行合并
        
        # 4. 去除首尾空白
        result = result.strip()
        
        return result


class LatexNormalizer:
    """LaTeX 归一化器 - 将标准 LaTeX 转换为 Word 更友好的形式"""
    
    # Word 对部分 LaTeX 命令支持不稳定：用 Unicode/纯文本进行兜底
    # 目标：避免出现 `\theta`/`\pi`/`\approx` 等以原样文本残留在公式对象中
    SYMBOL_MAP = {
        # 常见希腊字母（小写）
        "alpha": "α",
        "beta": "β",
        "gamma": "γ",
        "delta": "δ",
        "epsilon": "ε",
        "varepsilon": "ϵ",
        "theta": "θ",
        "phi": "φ",
        "varphi": "ϕ",
        "pi": "π",
        "rho": "ρ",
        "sigma": "σ",
        "mu": "μ",
        "nu": "ν",
        "lambda": "λ",
        "kappa": "κ",
        "omega": "ω",
        # 🆕 v3 新增希腊字母
        "zeta": "ζ",
        "eta": "η",
        "iota": "ι",
        "xi": "ξ",
        "tau": "τ",
        "upsilon": "υ",
        "chi": "χ",
        "psi": "ψ",
        # 常见希腊字母（大写）
        "Gamma": "Γ",
        "Delta": "Δ",
        "Theta": "Θ",
        "Lambda": "Λ",
        "Xi": "Ξ",
        "Pi": "Π",
        "Sigma": "Σ",
        "Phi": "Φ",
        "Psi": "Ψ",
        "Omega": "Ω",
        # 常见算符/关系符
        "approx": "≈",
        "neq": "≠",
        "leq": "≤",
        "geq": "≥",
        # NOTE: \to / \infty 在 Word 里更稳的做法是保留 LaTeX 命令，
        # 否则可能触发 lim(...) 后出现空槽位或显示异常
        # "to": "→",
        # "infty": "∞",
        "cdot": "·",
        "times": "×",
        "pm": "±",
        # 部分函数：去掉反斜杠更稳
        "sin": "sin",
        "cos": "cos",
        "tan": "tan",
        "cot": "cot",
        "log": "log",
        "ln": "ln",
        # 🆕 v3 新增函数名
        "max": "max",
        "min": "min",
        "sup": "sup",
        "inf": "inf",
        "arg": "arg",
        "dim": "dim",
        "ker": "ker",
        "gcd": "gcd",
        "Pr": "Pr",
        # 其他
        "det": "det",
        # 🆕 LaTeX 空格命令 -> 普通空格（Word 方程编辑器不支持 Unicode 特殊空格）
        # \quad = 1em ≈ 4 个普通空格, \qquad = 2em ≈ 8 个普通空格
        "quad": "    ",         # 4x 普通空格 (模拟 1em)
        "qquad": "        ",    # 8x 普通空格 (模拟 2em)
        # 细微空格命令 -> 普通空格（Word 方程编辑器兼容）
        # ",": " ",             # \, 暂不处理（单字符命令需要特殊正则）
        # ";": " ",             # \; 暂不处理
        # ":": " ",             # \: 暂不处理
        # "!": "",              # \! 暂不处理
    }
    
    TEXT_CMD_PATTERN = re.compile(r"\\text\{([^}]*)\}")
    LATEX_CMD_PATTERN = re.compile(r"\\([A-Za-z]+)(?=[^A-Za-z]|$)")
    FUNC_NEEDS_SPACE_PATTERN = re.compile(r"\b(sin|cos|tan|cot|log|ln)(?=[A-Za-zα-ωΑ-Ω])")
    MATRIX_ENV_PATTERN = re.compile(
        r"\\begin\{(pmatrix|bmatrix|matrix|vmatrix)\}([\s\S]*?)\\end\{\1\}",
        re.IGNORECASE,
    )
    LIM_ATTACH_PATTERN = re.compile(r"(\\lim_\{[^}]*\})\s+(?=\\)")
    
    # 归一化规则：(模式, 替换函数或字符串)
    NORMALIZATION_RULES = [
        # cases 环境 -> 等价的 Word 友好写法
        # \begin{cases} ... \end{cases} 通常可以保持原样，Word 支持
        # 但如果失败，可以尝试转换为矩阵形式
        
        # 移除 \displaystyle（Word 自动处理）
        (re.compile(r'\\displaystyle\s*'), ''),
        
        # \text{} -> 在某些情况下可能需要处理
        # Word 的 OMML 通常支持 \text
        
        # \limits 有时会导致问题（保留，因为 Word 可能需要它）
        # (re.compile(r'\\limits\b'), ''),  # 已移至降级规则
        
        # \nonumber 和 \notag（Word 不需要这些）
        (re.compile(r'\\(nonumber|notag)\b'), ''),
        
        # \label{...}（移除标签）
        (re.compile(r'\\label\{[^}]*\}'), ''),
        
        # \tag{...}（移除标签）
        (re.compile(r'\\tag\{[^}]*\}'), ''),
    ]
    
    # 降级规则（失败后尝试）
    FALLBACK_RULES = [
        # 移除 \left 和 \right（有时会导致问题）
        (re.compile(r'\\left\s*'), ''),
        (re.compile(r'\\right\s*'), ''),
        
        # \limits 有时会导致问题（后面可能跟 _ 或 ^ 或空格）
        (re.compile(r'\\limits(?=[\s_^{]|$)'), ''),
        
        # \boldsymbol -> \mathbf
        (re.compile(r'\\boldsymbol\b'), r'\\mathbf'),
        
        # \bm -> \mathbf
        (re.compile(r'\\bm\b'), r'\\mathbf'),
    ]
    
    @classmethod
    def normalize(cls, latex_code: str) -> str:
        """
        归一化 LaTeX 代码
        
        Args:
            latex_code: 原始 LaTeX 代码
            
        Returns:
            str: 归一化后的代码
        """
        from .handlers.matrix_handler import MatrixHandler
        from .handlers.cases_handler import CasesHandler
        
        result = latex_code
        
        # 0) 优先处理复杂环境（矩阵、cases）
        # 使用专项处理器转换为 OMML 友好格式
        result = MatrixHandler.process(result)
        result = CasesHandler.process(result)
        
        # 1) 清理 \text{...}：Word 对 \text 支持不稳定，先降级为纯文本
        result = cls.TEXT_CMD_PATTERN.sub(r"\1", result)
        
        # 2) 兼容性兜底：将部分 LaTeX 命令替换为 Unicode/纯文本
        def _cmd_repl(m: re.Match) -> str:
            cmd = m.group(1)
            mapped = cls.SYMBOL_MAP.get(cmd)
            return mapped if mapped is not None else m.group(0)
        
        result = cls.LATEX_CMD_PATTERN.sub(_cmd_repl, result)
        
        # 3) 函数与紧跟的字母/希腊字母之间补空格，避免粘连导致解析失败（如 cosθ）
        result = cls.FUNC_NEEDS_SPACE_PATTERN.sub(r"\1 ", result)
        
        # 4) 修复 Word 对 lim 的"空槽位"问题：
        # 现象：\lim_{...} \frac{...}{...} 会被解析成 lim(...) 且参数为空，随后出现一个空框。
        # 处理：去掉 lim_{...} 后到下一个命令之间的空白，让 Word 将后续表达式作为 lim 的参数。
        result = cls.LIM_ATTACH_PATTERN.sub(r"\1", result)
        
        for pattern, replacement in cls.NORMALIZATION_RULES:
            result = pattern.sub(replacement, result)
        
        return result
    
    @classmethod
    def apply_fallback(cls, latex_code: str) -> str:
        """
        应用降级规则
        
        Args:
            latex_code: LaTeX 代码
            
        Returns:
            str: 降级处理后的代码
        """
        result = latex_code
        
        for pattern, replacement in cls.FALLBACK_RULES:
            result = pattern.sub(replacement, result)
        
        return result


class LatexConverter:
    """LaTeX 到 Word 公式转换器"""
    
    def __init__(self, policy_manager: Optional["PolicyManager"] = None):
        """初始化转换器"""
        self._app = None
        self._original_screen_updating = True
        self.policy_manager = policy_manager
        
        # 从 policy 获取配置
        if policy_manager:
            self.enable_normalization = policy_manager.config.enable_normalization
            self.enable_retry = policy_manager.config.enable_retry
            self.max_retry_count = policy_manager.config.max_retry_count
        else:
            self.enable_normalization = True
            self.enable_retry = True
            self.max_retry_count = 2
    
    def connect(self) -> bool:
        """
        连接到 Word 应用程序
        
        Returns:
            bool: 是否连接成功
        """
        try:
            self._app = win32com.client.Dispatch("Word.Application")
            return True
        except Exception:
            return False
    
    @property
    def app(self):
        """获取 Word 应用程序对象"""
        if self._app is None:
            self.connect()
        return self._app
    
    @property
    def active_document(self):
        """获取当前活动文档"""
        return self.app.ActiveDocument
    
    def _optimize_start(self):
        """开始优化：关闭屏幕刷新等"""
        try:
            self._original_screen_updating = self.app.ScreenUpdating
            self.app.ScreenUpdating = False
        except Exception:
            pass
    
    def _optimize_end(self):
        """结束优化：恢复设置"""
        try:
            self.app.ScreenUpdating = self._original_screen_updating
        except Exception:
            pass
    
    def check_document_status(self, doc) -> tuple[bool, str]:
        """
        检查文档状态
        
        Args:
            doc: Word Document COM 对象
            
        Returns:
            tuple[bool, str]: (是否可以处理, 状态描述)
        """
        try:
            # 检查只读
            if doc.ReadOnly:
                return False, "文档为只读模式，请解除只读后重试"
            
            # 检查保护状态
            # wdNoProtection = -1
            if doc.ProtectionType != -1:
                return False, "文档受保护，请取消保护后重试"
            
            # 检查兼容模式
            # Word 2007+ 的 CompatibilityMode 应该 >= 12
            if hasattr(doc, 'CompatibilityMode') and doc.CompatibilityMode < 12:
                return False, "文档处于兼容模式，建议另存为 .docx 格式"
            
            return True, "文档状态正常"
            
        except Exception as e:
            return False, f"检查文档状态时出错: {str(e)}"
    
    def handle_track_changes(
        self, 
        doc, 
        action: Literal["pause", "keep", "skip"]
    ) -> tuple[bool, bool]:
        """
        处理修订模式
        
        Args:
            doc: Word Document COM 对象
            action: 处理策略
                - pause: 临时关闭修订，转换后恢复
                - keep: 保留修订模式
                - skip: 检测到修订模式则跳过
                
        Returns:
            tuple[bool, bool]: (是否继续处理, 原修订状态)
        """
        try:
            original_track_changes = doc.TrackRevisions
            
            if not original_track_changes:
                return True, False
            
            if action == "skip":
                return False, True
            elif action == "pause":
                doc.TrackRevisions = False
                return True, True
            else:  # keep
                return True, True
                
        except Exception:
            return True, False
    
    def restore_track_changes(self, doc, original_state: bool):
        """恢复修订模式状态"""
        try:
            doc.TrackRevisions = original_state
        except Exception:
            pass
    
    def convert_single_match(self, doc, match: LatexMatch) -> ConversionResult:
        """
        转换单个 LaTeX 片段（带清洗、归一化和智能重试）
        
        Args:
            doc: Word Document COM 对象
            match: LaTeX 匹配信息
            
        Returns:
            ConversionResult: 转换结果
        """
        # 1. 清洗 LaTeX 代码
        sanitized_code = LatexSanitizer.sanitize(match.latex_code)
        
        # 2. 归一化（如果启用）
        if self.enable_normalization:
            normalized_code = LatexNormalizer.normalize(sanitized_code)
        else:
            normalized_code = sanitized_code
        
        # 3. 尝试转换
        result = self._try_convert(doc, match, normalized_code)
        
        # 4. 如果失败且启用重试，尝试降级策略
        if not result.success and self.enable_retry:
            retry_count = 0
            current_code = normalized_code
            
            while retry_count < self.max_retry_count and not result.success:
                retry_count += 1
                
                # 应用降级规则
                fallback_code = LatexNormalizer.apply_fallback(current_code)
                
                # 如果降级后代码没有变化，停止重试
                if fallback_code == current_code:
                    break
                
                current_code = fallback_code
                result = self._try_convert(doc, match, current_code)
                result.retry_attempted = True
        
        # 记录清洗后的代码（用于调试）
        result.sanitized_latex = normalized_code
        
        return result
    
    def _try_convert(self, doc, match: LatexMatch, latex_code: str) -> ConversionResult:
        """
        尝试转换单个 LaTeX 片段
        
        Args:
            doc: Word Document COM 对象
            match: LaTeX 匹配信息
            latex_code: 处理后的 LaTeX 代码
            
        Returns:
            ConversionResult: 转换结果
        """
        try:
            # 1. 定位 Range
            rng = doc.Range(match.start_pos, match.end_pos)
            
            # 验证 Range 内容是否匹配
            current_text = rng.Text
            if current_text != match.full_match:
                # Range 位置可能已经偏移
                return ConversionResult(
                    match=match,
                    success=False,
                    error_message=f"Range 内容不匹配，可能位置已偏移。期望: {match.full_match[:30]}..., 实际: {current_text[:30]}...",
                    failure_category=FailureCategory.RANGE_MISMATCH.value
                )
            
            # 2. 替换为处理后的 LaTeX（去掉 $ 分隔符）
            rng.Text = latex_code
            
            # 3. 重新定位 Range（因为 Text 赋值后 Range 可能变化）
            new_end = match.start_pos + len(latex_code)
            rng = doc.Range(match.start_pos, new_end)
            
            # 4. 转换为 OMath
            try:
                doc.OMaths.Add(rng)
            except Exception as e:
                # 恢复原文本
                self._restore_original(doc, match)
                return ConversionResult(
                    match=match,
                    success=False,
                    error_message=f"OMaths.Add 失败: {str(e)}",
                    failure_category=FailureCategory.CONVERT_FAILED.value
                )
            
            # 5. 获取刚添加的 OMath 并 BuildUp
            try:
                rng = doc.Range(match.start_pos, match.start_pos + 1)
                if rng.OMaths.Count > 0:
                    omath = rng.OMaths(1)
                    omath.BuildUp()
            except Exception as e:
                # BuildUp 失败，但 OMath 可能已创建
                # 不恢复，返回警告
                return ConversionResult(
                    match=match,
                    success=True,  # OMath 已创建，只是 BuildUp 可能不完整
                    error_message=f"BuildUp 警告: {str(e)}",
                    failure_category=FailureCategory.BUILDUP_FAILED.value
                )
            
            return ConversionResult(match=match, success=True)
            
        except Exception as e:
            # 失败时尝试恢复原文本
            self._restore_original(doc, match, latex_code)
            
            # 分类错误
            error_msg = str(e)
            if "COM" in error_msg or "pywintypes" in error_msg:
                failure_cat = FailureCategory.WORD_ERROR.value
            else:
                failure_cat = FailureCategory.UNKNOWN.value
            
            return ConversionResult(
                match=match,
                success=False,
                error_message=error_msg,
                failure_category=failure_cat
            )
    
    def _restore_original(self, doc, match: LatexMatch, current_code: str = None):
        """恢复原始文本"""
        try:
            if current_code:
                end_pos = match.start_pos + len(current_code)
            else:
                end_pos = match.end_pos
            rng = doc.Range(match.start_pos, end_pos)
            rng.Text = match.full_match
        except Exception:
            pass
    
    def convert_matches(
        self, 
        doc, 
        matches: list[LatexMatch],
        skip_money: bool = True
    ) -> list[ConversionResult]:
        """
        批量转换 LaTeX 片段
        
        注意：从后向前处理，避免 Range 位移问题
        
        Args:
            doc: Word Document COM 对象
            matches: LaTeX 匹配列表
            skip_money: 是否跳过金额模式
            
        Returns:
            list[ConversionResult]: 转换结果列表
        """
        results = []
        
        # 从后向前排序
        sorted_matches = sorted(matches, key=lambda m: m.start_pos, reverse=True)
        
        self._optimize_start()
        
        try:
            for match in sorted_matches:
                result = self.convert_single_match(doc, match)
                results.append(result)
        finally:
            self._optimize_end()
        
        return results
    
    def convert_body(self, doc, scanner) -> list[ConversionResult]:
        """
        转换正文区域
        
        Args:
            doc: Word Document COM 对象
            scanner: LatexScanner 实例
            
        Returns:
            list[ConversionResult]: 转换结果列表
        """
        matches = scanner.scan_body(doc)
        return self.convert_matches(doc, matches)
    
    def convert_all(self, doc, scanner) -> list[ConversionResult]:
        """
        转换全部区域
        
        Args:
            doc: Word Document COM 对象
            scanner: LatexScanner 实例
            
        Returns:
            list[ConversionResult]: 转换结果列表
        """
        matches = scanner.scan_all(doc)
        return self.convert_matches(doc, matches)
    
    def convert_remaining(
        self, 
        doc, 
        scanner, 
        previous_results: list[ConversionResult]
    ) -> list[ConversionResult]:
        """
        转换遗留片段（增量模式）
        
        Args:
            doc: Word Document COM 对象
            scanner: LatexScanner 实例
            previous_results: 之前的转换结果
            
        Returns:
            list[ConversionResult]: 新的转换结果列表
        """
        # 获取之前成功转换的位置
        converted_positions = {
            (r.match.start_pos, r.match.end_pos) 
            for r in previous_results 
            if r.success
        }
        
        # 扫描全部区域
        all_matches = scanner.scan_all(doc)
        
        # 过滤掉已转换的
        remaining_matches = [
            m for m in all_matches 
            if (m.start_pos, m.end_pos) not in converted_positions
        ]
        
        return self.convert_matches(doc, remaining_matches)

