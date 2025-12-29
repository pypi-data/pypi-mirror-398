"""
数据模型定义
"""

from dataclasses import dataclass, field
from typing import Literal
from enum import Enum


class Region(str, Enum):
    """文档区域类型"""
    BODY = "body"           # 正文（含表格）
    HEADER = "header"       # 页眉
    FOOTER = "footer"       # 页脚
    FOOTNOTE = "footnote"   # 脚注
    ENDNOTE = "endnote"     # 尾注
    COMMENT = "comment"     # 批注
    TEXTBOX = "textbox"     # 文本框/形状


class RiskTag(str, Enum):
    """风险标签"""
    SAFE = "safe"                       # 低风险，可安全转换
    MONEY_LIKE = "money_like"           # 疑似金额（如 $100$）
    NUMBER_ONLY = "number_only"         # 纯数字内容
    DELIMITER_AMBIGUOUS = "delimiter_ambiguous"  # 分隔符歧义
    MULTILINE = "multiline"             # 跨行公式
    COMPLEX_ENV = "complex_env"         # 复杂环境（cases/matrix 等）
    WORD_NOISE = "word_noise"           # 含 Word 噪声字符
    TOO_LONG = "too_long"               # 过长片段
    UNPAIRED = "unpaired"               # 不成对分隔符


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"       # 低风险，建议转换
    MEDIUM = "medium" # 中风险，建议检查后转换
    HIGH = "high"     # 高风险，建议跳过或手动处理


# 文档类型预设
ProfileType = Literal["balanced", "strict", "paper", "engineering", "contract", "finance"]

# 报告详细程度
ReportDetailType = Literal["summary", "detailed"]

# 选择策略
SelectionType = Literal["all", "safe_only"]


# 正文区域集合（快速模式）
BODY_REGIONS = {Region.BODY}

# 所有区域集合（兜底模式）
ALL_REGIONS = {
    Region.BODY, 
    Region.HEADER, 
    Region.FOOTER, 
    Region.FOOTNOTE, 
    Region.ENDNOTE, 
    Region.COMMENT, 
    Region.TEXTBOX
}


@dataclass
class LatexMatch:
    """单个 LaTeX 片段的定位信息"""
    
    latex_code: str
    """原始 LaTeX 代码（不含分隔符）"""
    
    full_match: str
    """完整匹配（含 $ 或 $$）"""
    
    start_pos: int
    """在 Range 中的起始位置"""
    
    end_pos: int
    """在 Range 中的结束位置"""
    
    region: Region
    """所属区域"""
    
    is_display: bool
    """是否为显示公式（$$...$$）"""
    
    paragraph_index: int = -1
    """段落索引（用于定位，-1 表示未知）"""
    
    context: str = ""
    """上下文摘要（前后各 20 字符）"""
    
    region_index: int = -1
    """区域内索引（如第几个页眉、第几个脚注等）"""
    
    match_id: int = -1
    """全局唯一标识符（用于 include_ids/exclude_ids）"""
    
    risk_tags: list = field(default_factory=list)
    """风险标签列表"""
    
    risk_level: str = "low"
    """风险等级：low/medium/high"""
    
    risk_reasons: list = field(default_factory=list)
    """风险原因说明"""
    
    suggested_action: str = "convert"
    """建议动作：convert/skip/review"""
    
    def __repr__(self) -> str:
        display_type = "display" if self.is_display else "inline"
        code_preview = self.latex_code[:30] + "..." if len(self.latex_code) > 30 else self.latex_code
        return f"LatexMatch({display_type}, {self.region.value}, '{code_preview}')"
    
    def is_safe(self) -> bool:
        """判断是否为安全片段（低风险）"""
        return self.risk_level == "low" or RiskLevel.LOW.value == self.risk_level


class SkipReason(str, Enum):
    """跳过原因"""
    MONEY_PATTERN = "money_pattern"         # 金额模式
    USER_EXCLUDED = "user_excluded"         # 用户手动排除
    RULE_EXCLUDED = "rule_excluded"         # 规则排除
    RISK_FILTERED = "risk_filtered"         # 风险过滤（safe_only 模式）
    UNPAIRED_DELIMITER = "unpaired_delimiter"  # 分隔符不成对


class FailureCategory(str, Enum):
    """失败分类"""
    SCAN_FAILED = "scan_failed"             # 识别失败
    CONVERT_FAILED = "convert_failed"       # 转换失败
    BUILDUP_FAILED = "buildup_failed"       # BuildUp 失败
    RANGE_MISMATCH = "range_mismatch"       # Range 位置偏移
    WORD_ERROR = "word_error"               # Word COM 错误
    UNKNOWN = "unknown"                     # 未知错误


@dataclass
class ConversionResult:
    """单个片段的转换结果"""
    
    match: LatexMatch
    """对应的匹配信息"""
    
    success: bool
    """是否转换成功"""
    
    skipped: bool = False
    """是否被跳过（如金额模式）"""
    
    skip_reason: str | None = None
    """跳过原因"""
    
    error_message: str | None = None
    """失败时的错误信息"""
    
    failure_category: str | None = None
    """失败分类"""
    
    retry_attempted: bool = False
    """是否尝试过重试"""
    
    sanitized_latex: str | None = None
    """清洗后的 LaTeX 代码（用于调试）"""


@dataclass
class ConversionReport:
    """整体转换报告"""
    
    total_found: int = 0
    """发现的 LaTeX 片段总数"""
    
    total_success: int = 0
    """成功转换数量"""
    
    total_failed: int = 0
    """转换失败数量"""
    
    total_skipped: int = 0
    """跳过数量（如金额模式）"""
    
    results: list[ConversionResult] = field(default_factory=list)
    """详细结果列表"""
    
    body_remaining: int = 0
    """正文区域遗留数量"""
    
    other_remaining: int = 0
    """非正文区域遗留数量"""
    
    backup_path: str | None = None
    """备份文件路径"""
    
    duration_seconds: float = 0.0
    """耗时（秒）"""
    
    mode: Literal["quick", "full", "scan"] = "quick"
    """运行模式"""
    
    document_path: str = ""
    """文档路径"""
    
    @property
    def has_remaining(self) -> bool:
        """是否有遗留片段"""
        return self.body_remaining > 0 or self.other_remaining > 0
    
    @property
    def needs_fallback(self) -> bool:
        """是否需要兜底模式"""
        return self.other_remaining > 0 and self.mode == "quick"
    
    def get_failed_results(self) -> list[ConversionResult]:
        """获取失败的结果列表"""
        return [r for r in self.results if not r.success and not r.skipped]
    
    def get_summary(self) -> str:
        """生成摘要文本"""
        lines = [
            f"📊 转换报告",
            f"   文档: {self.document_path}",
            f"   模式: {self.mode}",
            f"   耗时: {self.duration_seconds:.2f} 秒",
            f"",
            f"📈 统计",
            f"   发现: {self.total_found}",
            f"   成功: {self.total_success}",
            f"   失败: {self.total_failed}",
            f"   跳过: {self.total_skipped}",
        ]
        
        if self.backup_path:
            lines.append(f"")
            lines.append(f"💾 备份: {self.backup_path}")
        
        if self.needs_fallback:
            lines.append(f"")
            lines.append(f"⚠️ 非正文区域仍有 {self.other_remaining} 个 LaTeX 片段")
            lines.append(f"   提示: 可使用 mode='full' 进行兜底转换")
        
        if self.total_failed > 0:
            lines.append(f"")
            lines.append(f"❌ 失败清单:")
            for r in self.get_failed_results()[:5]:  # 只显示前5个
                ctx = r.match.context[:40] + "..." if len(r.match.context) > 40 else r.match.context
                lines.append(f"   - [{r.match.region.value}] {ctx}")
                lines.append(f"     错误: {r.error_message}")
            if self.total_failed > 5:
                lines.append(f"   ... 还有 {self.total_failed - 5} 个失败项")
        
        return "\n".join(lines)



