"""
策略与配置管理模块
"""

import re
from dataclasses import dataclass, field
from typing import Literal

from .models import (
    LatexMatch, RiskTag, RiskLevel, ProfileType
)


@dataclass
class ProfileConfig:
    """文档类型预设配置"""
    
    name: str
    """配置名称"""
    
    # === 扫描策略 ===
    allow_multiline_inline: bool = True
    """是否允许行内公式跨行"""
    
    max_inline_length: int = 500
    """行内公式最大长度"""
    
    max_display_length: int = 2000
    """显示公式最大长度"""
    
    max_line_count: int = 10
    """最大跨行数"""
    
    # === 风险控制 ===
    money_pattern_strict: bool = False
    """是否使用严格金额检测（更少误判，可能漏检）"""
    
    number_threshold: float = 0.8
    """纯数字比例阈值（超过则标记为高风险）"""
    
    require_latex_command: bool = False
    """是否要求必须包含 LaTeX 命令才识别"""
    
    # === 复杂环境处理 ===
    enable_normalization: bool = True
    """是否启用 LaTeX 归一化"""
    
    enable_retry: bool = True
    """是否启用失败重试"""
    
    max_retry_count: int = 2
    """最大重试次数"""
    
    # === 清洗规则 ===
    replace_smart_quotes: bool = True
    """替换智能引号"""
    
    remove_invisible_chars: bool = True
    """移除不可见字符"""
    
    normalize_whitespace: bool = True
    """标准化空白字符"""


# 预定义的配置预设
PROFILE_CONFIGS: dict[str, ProfileConfig] = {
    "balanced": ProfileConfig(
        name="balanced",
        allow_multiline_inline=True,
        max_inline_length=500,
        money_pattern_strict=False,
        require_latex_command=False,
    ),
    "strict": ProfileConfig(
        name="strict",
        allow_multiline_inline=False,
        max_inline_length=200,
        money_pattern_strict=True,
        require_latex_command=True,
        number_threshold=0.5,
    ),
    "paper": ProfileConfig(
        name="paper",
        allow_multiline_inline=True,
        max_inline_length=1000,
        max_display_length=5000,
        money_pattern_strict=False,
        require_latex_command=False,
        max_line_count=20,
    ),
    "engineering": ProfileConfig(
        name="engineering",
        allow_multiline_inline=True,
        max_inline_length=800,
        money_pattern_strict=False,
        require_latex_command=False,
    ),
    "contract": ProfileConfig(
        name="contract",
        allow_multiline_inline=False,
        max_inline_length=200,
        money_pattern_strict=True,
        require_latex_command=True,
        number_threshold=0.3,
    ),
    "finance": ProfileConfig(
        name="finance",
        allow_multiline_inline=False,
        max_inline_length=100,
        money_pattern_strict=True,
        require_latex_command=True,
        number_threshold=0.2,
    ),
}


def get_profile_config(profile: str) -> ProfileConfig:
    """获取配置预设"""
    return PROFILE_CONFIGS.get(profile, PROFILE_CONFIGS["balanced"])


class PolicyManager:
    """策略管理器"""
    
    # LaTeX 命令模式
    LATEX_COMMAND_PATTERN = re.compile(r'\\[a-zA-Z]+')
    
    # 复杂环境
    COMPLEX_ENV_PATTERNS = [
        re.compile(r'\\begin\{(cases|matrix|pmatrix|bmatrix|vmatrix|aligned|array)\}', re.IGNORECASE),
        re.compile(r'\\(sum|prod|int|iint|iiint|oint|lim)(_|\^)', re.IGNORECASE),
        re.compile(r'\\(frac|dfrac|tfrac)\{', re.IGNORECASE),
    ]
    
    # 金额模式
    MONEY_PATTERN_LOOSE = re.compile(r'^[\d,\s]+\.?\d*$')
    MONEY_PATTERN_STRICT = re.compile(r'^[\d]{1,3}(,\d{3})*(\.\d{1,2})?$|^\d+(\.\d{1,2})?$')
    
    # 编号模式
    NUMBER_SEQUENCE_PATTERN = re.compile(r'^[\d\.\-\s]+$')
    
    # Word 噪声字符
    WORD_NOISE_CHARS = [
        '\r',           # 回车
        '\x0b',         # 垂直制表符（软回车）
        '\x0c',         # 分页符
        '\x07',         # 表格单元格结束标记
        '\xa0',         # 不间断空格
        '\u2028',       # 行分隔符
        '\u2029',       # 段落分隔符
        '\u200b',       # 零宽空格
        '\u200c',       # 零宽非连接符
        '\u200d',       # 零宽连接符
        '\ufeff',       # BOM
    ]
    
    def __init__(self, config: ProfileConfig):
        self.config = config
        self._match_id_counter = 0
    
    def assign_match_ids(self, matches: list[LatexMatch]) -> list[LatexMatch]:
        """为匹配项分配全局唯一 ID"""
        for match in matches:
            self._match_id_counter += 1
            match.match_id = self._match_id_counter
        return matches
    
    def evaluate_risks(self, matches: list[LatexMatch]) -> list[LatexMatch]:
        """评估每个匹配项的风险"""
        for match in matches:
            match.risk_tags = []
            match.risk_reasons = []
            
            # 1. 检查金额模式
            if self._is_money_pattern(match.latex_code):
                match.risk_tags.append(RiskTag.MONEY_LIKE)
                match.risk_reasons.append("内容类似金额格式")
            
            # 2. 检查纯数字
            if self._is_mostly_numbers(match.latex_code):
                match.risk_tags.append(RiskTag.NUMBER_ONLY)
                match.risk_reasons.append("内容主要为数字")
            
            # 3. 检查跨行
            if self._is_multiline(match.latex_code):
                match.risk_tags.append(RiskTag.MULTILINE)
                if not self.config.allow_multiline_inline and not match.is_display:
                    match.risk_reasons.append("行内公式跨行（当前配置不允许）")
            
            # 4. 检查复杂环境
            if self._has_complex_env(match.latex_code):
                match.risk_tags.append(RiskTag.COMPLEX_ENV)
                match.risk_reasons.append("包含复杂环境（cases/matrix 等）")
            
            # 5. 检查 Word 噪声
            if self._has_word_noise(match.latex_code):
                match.risk_tags.append(RiskTag.WORD_NOISE)
                match.risk_reasons.append("包含 Word 特殊字符")
            
            # 6. 检查长度
            if self._is_too_long(match.latex_code, match.is_display):
                match.risk_tags.append(RiskTag.TOO_LONG)
                match.risk_reasons.append("片段过长")
            
            # 7. 检查是否包含 LaTeX 命令
            has_command = bool(self.LATEX_COMMAND_PATTERN.search(match.latex_code))
            if self.config.require_latex_command and not has_command:
                match.risk_reasons.append("未检测到 LaTeX 命令")
            
            # 计算风险等级
            match.risk_level = self._calculate_risk_level(match)
            
            # 设置建议动作
            match.suggested_action = self._suggest_action(match)
            
            # 如果没有风险标签，标记为安全
            if not match.risk_tags:
                match.risk_tags.append(RiskTag.SAFE)
        
        return matches
    
    def _is_money_pattern(self, code: str) -> bool:
        """检查是否为金额模式"""
        code = code.strip()
        if self.config.money_pattern_strict:
            return bool(self.MONEY_PATTERN_STRICT.match(code))
        return bool(self.MONEY_PATTERN_LOOSE.match(code))
    
    def _is_mostly_numbers(self, code: str) -> bool:
        """检查是否主要为数字"""
        if not code:
            return False
        digit_count = sum(1 for c in code if c.isdigit())
        ratio = digit_count / len(code)
        return ratio >= self.config.number_threshold
    
    def _is_multiline(self, code: str) -> bool:
        """检查是否跨行"""
        return '\n' in code or '\r' in code or '\x0b' in code
    
    def _has_complex_env(self, code: str) -> bool:
        """检查是否包含复杂环境"""
        return any(p.search(code) for p in self.COMPLEX_ENV_PATTERNS)
    
    def _has_word_noise(self, code: str) -> bool:
        """检查是否包含 Word 噪声字符"""
        return any(c in code for c in self.WORD_NOISE_CHARS)
    
    def _is_too_long(self, code: str, is_display: bool) -> bool:
        """检查是否过长"""
        max_len = self.config.max_display_length if is_display else self.config.max_inline_length
        return len(code) > max_len
    
    def _calculate_risk_level(self, match: LatexMatch) -> str:
        """计算风险等级"""
        high_risk_tags = {RiskTag.MONEY_LIKE, RiskTag.NUMBER_ONLY, RiskTag.UNPAIRED}
        medium_risk_tags = {RiskTag.COMPLEX_ENV, RiskTag.WORD_NOISE, RiskTag.TOO_LONG, RiskTag.MULTILINE}
        
        # 高风险条件
        if any(t in high_risk_tags for t in match.risk_tags):
            return RiskLevel.HIGH.value
        
        # 中风险条件
        if any(t in medium_risk_tags for t in match.risk_tags):
            return RiskLevel.MEDIUM.value
        
        # 检查是否满足 require_latex_command
        if self.config.require_latex_command:
            if not self.LATEX_COMMAND_PATTERN.search(match.latex_code):
                return RiskLevel.HIGH.value
        
        return RiskLevel.LOW.value
    
    def _suggest_action(self, match: LatexMatch) -> str:
        """建议动作"""
        if match.risk_level == RiskLevel.HIGH.value:
            return "skip"
        elif match.risk_level == RiskLevel.MEDIUM.value:
            return "review"
        return "convert"



