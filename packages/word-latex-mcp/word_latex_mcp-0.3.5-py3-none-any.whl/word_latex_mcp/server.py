"""
MCP 服务器入口模块
"""

import time
import re
from typing import Literal, Optional
from mcp.server import FastMCP

from .file_manager import FileManager
from .models import (
    ConversionReport, Region, BODY_REGIONS, ALL_REGIONS,
    ProfileType, ReportDetailType, SelectionType, RiskLevel
)
from .scanner import LatexScanner
from .converter import LatexConverter
from .backup import BackupManager
from .reporter import ReportGenerator
from .policy import PolicyManager, get_profile_config


# 初始化 MCP 应用
mcp = FastMCP(
    "word-latex-mcp",
    dependencies=["pywin32>=306"],
    log_level="WARNING",
)


@mcp.tool()
def convert_latex(
    file_path: Optional[str] = None,
    mode: Literal["quick", "full", "scan"] = "quick",
    backup: bool = True,
    work_on_copy: bool = False,
    skip_money_patterns: bool = True,
    track_changes_action: Literal["pause", "keep", "skip"] = "pause",
    profile: Literal["balanced", "strict", "paper", "engineering", "contract", "finance"] = "balanced",
    selection: Literal["all", "safe_only"] = "all",
    report_detail: Literal["summary", "detailed"] = "summary",
    include_ids: str = "",
    exclude_ids: str = "",
    force_convert_regex: str = "",
    force_skip_regex: str = ""
) -> str:
    """
    批量将 Word 文档中的 LaTeX 公式转换为原生数学公式。
    
    Args:
        file_path: Word 文件绝对路径（可选）
            - 为空时：使用当前活动文档（兼容旧版本）
            - 非空时：自动打开指定文件，转换后保存并保持打开
        mode: 运行模式
            - quick: 仅转换正文（含表格），默认
            - full: 扩展到页眉页脚/脚注/文本框等全部区域
            - scan: 仅扫描统计，不做转换
        backup: 是否自动备份（默认 True）
        work_on_copy: 是否在副本上操作（默认 False）
        skip_money_patterns: 是否跳过疑似金额的模式如 $100$（默认 True）
        track_changes_action: 修订模式处理策略
            - pause: 临时关闭修订，转换后恢复
            - keep: 保留修订模式（会产生修订痕迹）
            - skip: 检测到修订模式则跳过并提示
        profile: 文档类型预设（影响扫描/清洗/风险策略）
            - balanced: 平衡模式（默认）
            - strict: 严格模式（少误转，可能多漏转）
            - paper: 论文模式（更激进识别，适合学术文档）
            - engineering: 工程模式（适合工程计算文档）
            - contract: 合同模式（更保守，避免金额误判）
            - finance: 财务模式（最保守，强金额/编号保护）
        selection: 选择策略
            - all: 转换全部识别到的片段（默认）
            - safe_only: 仅转换低风险片段
        report_detail: 报告详细程度
            - summary: 摘要（默认）
            - detailed: 详细（含 match_id 清单、风险标签）
        include_ids: 仅转换指定 match_id（逗号分隔，如 "3,7,12"），来自 scan 模式的详细报告
        exclude_ids: 排除指定 match_id（逗号分隔，如 "3,7,12"）
        force_convert_regex: 强制转换匹配此正则的片段（高级选项）
        force_skip_regex: 强制跳过匹配此正则的片段（高级选项）
    
    Returns:
        str: 转换报告文本
    """
    start_time = time.time()
    
    # 解析 ID 列表
    include_id_set = _parse_id_list(include_ids)
    exclude_id_set = _parse_id_list(exclude_ids)
    
    # 编译正则（如果提供）
    force_convert_pattern = re.compile(force_convert_regex) if force_convert_regex else None
    force_skip_pattern = re.compile(force_skip_regex) if force_skip_regex else None
    
    # 获取 profile 配置
    profile_config = get_profile_config(profile)
    
    # 初始化组件
    policy_manager = PolicyManager(profile_config)
    converter = LatexConverter(policy_manager=policy_manager)
    scanner = LatexScanner(
        skip_money_patterns=skip_money_patterns,
        policy_manager=policy_manager
    )
    backup_manager = BackupManager()
    reporter = ReportGenerator(report_detail=report_detail)
    
    # 连接 Word
    if not converter.connect():
        return "❌ 错误: 无法连接到 Word 应用程序，请确保 Word 已安装并正在运行"
    
    # 获取文档（支持 file_path 参数）
    doc, document_path, open_error = _get_document(converter, file_path)
    if doc is None:
        return f"❌ 错误: {open_error}"
    
    # 检查文档状态
    can_process, status_msg = converter.check_document_status(doc)
    if not can_process:
        return f"❌ {status_msg}"
    
    # 处理修订模式
    can_continue, original_track_changes = converter.handle_track_changes(
        doc, track_changes_action
    )
    if not can_continue:
        return "⚠️ 文档处于修订模式，根据配置已跳过处理。请关闭修订模式后重试，或使用 track_changes_action='pause' 临时关闭修订"
    
    backup_path = None
    working_doc = doc
    
    try:
        # 创建备份或工作副本
        if work_on_copy:
            working_doc, copy_path = backup_manager.create_working_copy(doc, converter.app)
            if working_doc is None:
                return "❌ 错误: 无法创建工作副本"
            backup_path = copy_path
            document_path = copy_path
        elif backup and mode != "scan":
            backup_path = backup_manager.create_backup(doc)
            if backup_path is None:
                return "⚠️ 警告: 无法创建备份，但将继续处理"
        
        # 根据模式执行
        if mode == "scan":
            # 扫描模式：只统计不转换
            all_matches = scanner.scan_all(working_doc)
            
            # 分配 match_id 并进行风险评估
            all_matches = policy_manager.assign_match_ids(all_matches)
            all_matches = policy_manager.evaluate_risks(all_matches)
            
            duration = time.time() - start_time
            report = reporter.generate_scan_report(
                matches=all_matches,
                document_path=document_path,
                duration_seconds=duration
            )
            
            # 生成扫描报告
            return _format_scan_report(report, all_matches, report_detail)
        
        elif mode == "quick":
            # 快速模式：只处理正文
            body_matches = scanner.scan_body(working_doc)
            
            # 分配 match_id 并进行风险评估
            body_matches = policy_manager.assign_match_ids(body_matches)
            body_matches = policy_manager.evaluate_risks(body_matches)
            
            # 应用过滤逻辑
            filtered_matches, skipped_results = _filter_matches(
                body_matches,
                selection=selection,
                include_ids=include_id_set,
                exclude_ids=exclude_id_set,
                force_convert_pattern=force_convert_pattern,
                force_skip_pattern=force_skip_pattern
            )
            
            results = converter.convert_matches(working_doc, filtered_matches)
            results.extend(skipped_results)
            
            # 全局扫尾（只统计）
            other_matches = scanner.scan_other_regions(working_doc)
            
            # 保存文档
            backup_manager.save_document(working_doc)
            
            duration = time.time() - start_time
            report = reporter.generate_report(
                results=results,
                mode=mode,
                document_path=document_path,
                backup_path=backup_path,
                duration_seconds=duration
            )
            
            # 更新非正文遗留数
            report.other_remaining = len(other_matches)
            
            return report.get_summary()
        
        else:  # full
            # 兜底模式：处理全部区域
            all_matches = scanner.scan_all(working_doc)
            
            # 分配 match_id 并进行风险评估
            all_matches = policy_manager.assign_match_ids(all_matches)
            all_matches = policy_manager.evaluate_risks(all_matches)
            
            # 应用过滤逻辑
            filtered_matches, skipped_results = _filter_matches(
                all_matches,
                selection=selection,
                include_ids=include_id_set,
                exclude_ids=exclude_id_set,
                force_convert_pattern=force_convert_pattern,
                force_skip_pattern=force_skip_pattern
            )
            
            results = converter.convert_matches(working_doc, filtered_matches)
            results.extend(skipped_results)
            
            # 保存文档
            backup_manager.save_document(working_doc)
            
            duration = time.time() - start_time
            report = reporter.generate_report(
                results=results,
                mode=mode,
                document_path=document_path,
                backup_path=backup_path,
                duration_seconds=duration
            )
            
            return report.get_summary()
    
    finally:
        # 恢复修订模式
        if original_track_changes and track_changes_action == "pause":
            converter.restore_track_changes(working_doc, True)


def _get_document(converter, file_path: Optional[str]) -> tuple:
    """
    获取要处理的文档
    
    Args:
        converter: LatexConverter 实例
        file_path: 文件路径（可选）
        
    Returns:
        tuple[Document, str, str]: (文档对象, 文档路径, 错误信息)
            - 成功时：(doc, path, "")
            - 失败时：(None, "", 错误信息)
    """
    if file_path:
        # 通过路径打开文件
        file_manager = FileManager(converter.app)
        doc, error = file_manager.open_document(file_path)
        if doc is None:
            return None, "", error
        return doc, doc.FullName, ""
    else:
        # 兼容旧版本：使用活动文档
        try:
            doc = converter.active_document
            if doc is None:
                return None, "", "没有打开的 Word 文档，请先打开目标文档或提供 file_path 参数"
            return doc, doc.FullName, ""
        except Exception as e:
            return None, "", f"无法获取活动文档: {str(e)}"


def _parse_id_list(id_string: str) -> set[int]:
    """解析逗号分隔的 ID 列表"""
    if not id_string or not id_string.strip():
        return set()
    try:
        return {int(x.strip()) for x in id_string.split(",") if x.strip()}
    except ValueError:
        return set()


def _filter_matches(
    matches: list,
    selection: str,
    include_ids: set[int],
    exclude_ids: set[int],
    force_convert_pattern,
    force_skip_pattern
) -> tuple[list, list]:
    """
    根据过滤条件筛选匹配项
    
    Returns:
        tuple[list, list]: (要转换的匹配, 被跳过的结果)
    """
    from .models import ConversionResult, SkipReason
    
    to_convert = []
    skipped_results = []
    
    for match in matches:
        # 1. 强制跳过正则
        if force_skip_pattern and force_skip_pattern.search(match.latex_code):
            skipped_results.append(ConversionResult(
                match=match,
                success=False,
                skipped=True,
                skip_reason=SkipReason.RULE_EXCLUDED.value
            ))
            continue
        
        # 2. 排除 ID
        if exclude_ids and match.match_id in exclude_ids:
            skipped_results.append(ConversionResult(
                match=match,
                success=False,
                skipped=True,
                skip_reason=SkipReason.USER_EXCLUDED.value
            ))
            continue
        
        # 3. 仅包含指定 ID（如果提供）
        if include_ids and match.match_id not in include_ids:
            # 不在包含列表中，但检查是否被强制转换正则命中
            if force_convert_pattern and force_convert_pattern.search(match.latex_code):
                to_convert.append(match)
                continue
            skipped_results.append(ConversionResult(
                match=match,
                success=False,
                skipped=True,
                skip_reason=SkipReason.USER_EXCLUDED.value
            ))
            continue
        
        # 4. safe_only 模式
        if selection == "safe_only" and not match.is_safe():
            # 检查是否被强制转换正则命中
            if force_convert_pattern and force_convert_pattern.search(match.latex_code):
                to_convert.append(match)
                continue
            skipped_results.append(ConversionResult(
                match=match,
                success=False,
                skipped=True,
                skip_reason=SkipReason.RISK_FILTERED.value
            ))
            continue
        
        # 5. 强制转换正则（已在上面处理过）
        to_convert.append(match)
    
    return to_convert, skipped_results


def _format_scan_report(report: ConversionReport, matches: list, report_detail: str = "summary") -> str:
    """格式化扫描报告"""
    lines = [
        f"📊 扫描报告",
        f"   文档: {report.document_path}",
        f"   耗时: {report.duration_seconds:.2f} 秒",
        f"",
        f"📈 统计",
        f"   发现 LaTeX 片段: {report.total_found}",
        f"   正文区域: {report.body_remaining}",
        f"   非正文区域: {report.other_remaining}",
    ]
    
    # 按区域分组统计
    region_counts = {}
    for m in matches:
        region_counts[m.region] = region_counts.get(m.region, 0) + 1
    
    if region_counts:
        lines.append(f"")
        lines.append(f"📍 区域分布:")
        region_names = {
            Region.BODY: "正文（含表格）",
            Region.HEADER: "页眉",
            Region.FOOTER: "页脚",
            Region.FOOTNOTE: "脚注",
            Region.ENDNOTE: "尾注",
            Region.COMMENT: "批注",
            Region.TEXTBOX: "文本框/形状",
        }
        for region, count in region_counts.items():
            lines.append(f"   - {region_names.get(region, region.value)}: {count}")
    
    # 按风险等级统计
    if matches:
        risk_counts = {"low": 0, "medium": 0, "high": 0}
        for m in matches:
            risk_counts[m.risk_level] = risk_counts.get(m.risk_level, 0) + 1
        
        lines.append(f"")
        lines.append(f"⚠️ 风险分布:")
        lines.append(f"   - 低风险（可安全转换）: {risk_counts['low']}")
        lines.append(f"   - 中风险（建议检查）: {risk_counts['medium']}")
        lines.append(f"   - 高风险（建议跳过）: {risk_counts['high']}")
    
    # 详细模式：显示完整清单
    if report_detail == "detailed" and matches:
        lines.append(f"")
        lines.append(f"📋 详细清单（使用 include_ids/exclude_ids 可指定转换）:")
        lines.append(f"")
        
        for m in matches:
            code_preview = m.latex_code[:50] + "..." if len(m.latex_code) > 50 else m.latex_code
            display_type = "显示" if m.is_display else "行内"
            risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(m.risk_level, "⚪")
            action_text = {"convert": "建议转换", "skip": "建议跳过", "review": "需人工确认"}.get(m.suggested_action, "")
            
            lines.append(f"   [{m.match_id:3d}] {risk_icon} [{display_type}] {code_preview}")
            if m.risk_tags:
                tags_text = ", ".join(str(t.value) if hasattr(t, 'value') else str(t) for t in m.risk_tags)
                lines.append(f"         标签: {tags_text}")
            if m.risk_reasons:
                reasons_text = "; ".join(m.risk_reasons)
                lines.append(f"         原因: {reasons_text}")
            lines.append(f"         动作: {action_text}")
            lines.append(f"")
    else:
        # 显示部分示例
        if matches:
            lines.append(f"")
            lines.append(f"📝 示例片段（前 5 个）:")
            for m in matches[:5]:
                code_preview = m.latex_code[:40] + "..." if len(m.latex_code) > 40 else m.latex_code
                display_type = "显示" if m.is_display else "行内"
                risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(m.risk_level, "⚪")
                lines.append(f"   - {risk_icon} [{m.match_id}] [{display_type}] {code_preview}")
    
    if report.total_found > 0:
        lines.append(f"")
        lines.append(f"💡 提示:")
        lines.append(f"   - 使用 mode='quick' 转换正文，或 mode='full' 转换全部区域")
        lines.append(f"   - 使用 selection='safe_only' 仅转换低风险片段")
        lines.append(f"   - 使用 include_ids='1,2,3' 指定转换特定片段")
        lines.append(f"   - 使用 exclude_ids='4,5' 排除特定片段")
        lines.append(f"   - 使用 report_detail='detailed' 查看完整清单")
    
    return "\n".join(lines)


def main():
    """MCP 服务器入口"""
    mcp.run()  # stdio by default


if __name__ == "__main__":
    main()


