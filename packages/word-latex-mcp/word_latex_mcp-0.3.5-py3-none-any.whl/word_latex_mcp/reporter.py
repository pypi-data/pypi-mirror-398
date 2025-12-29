"""
报告生成模块
"""

from typing import Literal
from .models import (
    LatexMatch, 
    ConversionResult, 
    ConversionReport,
    Region,
    BODY_REGIONS,
    SkipReason,
    FailureCategory
)


class ReportGenerator:
    """转换报告生成器"""
    
    def __init__(self, report_detail: Literal["summary", "detailed"] = "summary"):
        self.report_detail = report_detail
    
    def count_by_region(
        self, 
        matches: list[LatexMatch]
    ) -> dict[Region, int]:
        """
        按区域统计匹配数量
        
        Args:
            matches: 匹配列表
            
        Returns:
            dict[Region, int]: 区域 -> 数量
        """
        counts = {}
        for match in matches:
            counts[match.region] = counts.get(match.region, 0) + 1
        return counts
    
    def count_remaining(
        self, 
        results: list[ConversionResult]
    ) -> tuple[int, int]:
        """
        统计遗留片段数量
        
        Args:
            results: 转换结果列表
            
        Returns:
            tuple[int, int]: (正文遗留数, 非正文遗留数)
        """
        body_remaining = 0
        other_remaining = 0
        
        for result in results:
            if not result.success and not result.skipped:
                if result.match.region in BODY_REGIONS:
                    body_remaining += 1
                else:
                    other_remaining += 1
        
        return body_remaining, other_remaining
    
    def generate_report(
        self,
        results: list[ConversionResult],
        mode: Literal["quick", "full", "scan"],
        document_path: str,
        backup_path: str | None,
        duration_seconds: float,
        scan_only_matches: list[LatexMatch] | None = None
    ) -> ConversionReport:
        """
        生成转换报告
        
        Args:
            results: 转换结果列表
            mode: 运行模式
            document_path: 文档路径
            backup_path: 备份路径
            duration_seconds: 耗时
            scan_only_matches: 扫描模式下的匹配列表（不转换）
            
        Returns:
            ConversionReport: 转换报告
        """
        if mode == "scan" and scan_only_matches is not None:
            # 扫描模式：只统计，不转换
            total_found = len(scan_only_matches)
            body_count = sum(1 for m in scan_only_matches if m.region in BODY_REGIONS)
            other_count = total_found - body_count
            
            return ConversionReport(
                total_found=total_found,
                total_success=0,
                total_failed=0,
                total_skipped=0,
                results=[],
                body_remaining=body_count,
                other_remaining=other_count,
                backup_path=backup_path,
                duration_seconds=duration_seconds,
                mode=mode,
                document_path=document_path,
            )
        
        # 转换模式
        total_found = len(results)
        total_success = sum(1 for r in results if r.success)
        total_skipped = sum(1 for r in results if r.skipped)
        total_failed = sum(1 for r in results if not r.success and not r.skipped)
        
        body_remaining, other_remaining = self.count_remaining(results)
        
        return ConversionReport(
            total_found=total_found,
            total_success=total_success,
            total_failed=total_failed,
            total_skipped=total_skipped,
            results=results,
            body_remaining=body_remaining,
            other_remaining=other_remaining,
            backup_path=backup_path,
            duration_seconds=duration_seconds,
            mode=mode,
            document_path=document_path,
        )
    
    def generate_scan_report(
        self,
        matches: list[LatexMatch],
        document_path: str,
        duration_seconds: float
    ) -> ConversionReport:
        """
        生成扫描报告（不转换）
        
        Args:
            matches: 匹配列表
            document_path: 文档路径
            duration_seconds: 耗时
            
        Returns:
            ConversionReport: 扫描报告
        """
        return self.generate_report(
            results=[],
            mode="scan",
            document_path=document_path,
            backup_path=None,
            duration_seconds=duration_seconds,
            scan_only_matches=matches
        )
    
    def merge_reports(
        self,
        quick_report: ConversionReport,
        full_report: ConversionReport
    ) -> ConversionReport:
        """
        合并快速模式和兜底模式的报告
        
        Args:
            quick_report: 快速模式报告
            full_report: 兜底模式报告
            
        Returns:
            ConversionReport: 合并后的报告
        """
        merged_results = quick_report.results + full_report.results
        
        return ConversionReport(
            total_found=quick_report.total_found + full_report.total_found,
            total_success=quick_report.total_success + full_report.total_success,
            total_failed=quick_report.total_failed + full_report.total_failed,
            total_skipped=quick_report.total_skipped + full_report.total_skipped,
            results=merged_results,
            body_remaining=full_report.body_remaining,
            other_remaining=full_report.other_remaining,
            backup_path=quick_report.backup_path,
            duration_seconds=quick_report.duration_seconds + full_report.duration_seconds,
            mode="full",
            document_path=quick_report.document_path,
        )



