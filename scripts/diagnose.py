#!/usr/bin/env python3
"""
Skill Diagnose - 生成详细诊断报告和修复建议
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict

script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))

from skill_check.checker import check_skill


@dataclass
class DiagnosticReport:
    skill_name: str
    skill_path: str
    timestamp: str
    summary: dict
    details: Dict[str, List] = field(default_factory=dict)
    fixes: List[dict] = field(default_factory=list)


def generate_diagnosis_report(skill_path: Path) -> DiagnosticReport:
    skill_path = Path(skill_path)
    result = check_skill(skill_path)

    report = DiagnosticReport(
        skill_name=result.skill_name,
        skill_path=str(skill_path),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        summary={
            "passed": result.passed,
            "score": result.score,
            "total_issues": len(result.issues),
            "errors": sum(1 for i in result.issues if i.level == "ERROR"),
            "warnings": sum(1 for i in result.issues if i.level == "WARN"),
            "info": sum(1 for i in result.issues if i.level == "INFO")
        },
        details={
            "structure": [],
            "frontmatter": [],
            "naming": [],
            "content": [],
            "resources": [],
            "progressive": []
        },
        fixes=[]
    )

    for issue in result.issues:
        category = issue.category.lower()
        if "structure" in category:
            report.details["structure"].append({
                "level": issue.level,
                "message": issue.message,
                "file": issue.file,
                "line": issue.line
            })
        elif "frontmatter" in category or "metadata" in category:
            report.details["frontmatter"].append({
                "level": issue.level,
                "message": issue.message,
                "file": issue.file,
                "line": issue.line
            })
        elif "naming" in category:
            report.details["naming"].append({
                "level": issue.level,
                "message": issue.message,
                "file": issue.file,
                "line": issue.line
            })
        elif "content" in category or "body" in category:
            report.details["content"].append({
                "level": issue.level,
                "message": issue.message,
                "file": issue.file,
                "line": issue.line
            })
        elif "resources" in category or "script" in category or "reference" in category:
            report.details["resources"].append({
                "level": issue.level,
                "message": issue.message,
                "file": issue.file,
                "line": issue.line
            })
        else:
            report.details["progressive"].append({
                "level": issue.level,
                "message": issue.message,
                "file": issue.file,
                "line": issue.line
            })

    for suggestion in result.suggestions:
        report.fixes.append({"suggestion": suggestion})

    return report


def format_text_report(report: DiagnosticReport) -> str:
    score_bar = "█" * (report.summary["score"] // 10) + "░" * (10 - report.summary["score"] // 10)

    lines = [
        "",
        "╔══════════════════════════════════════════════════════╗",
        "║            SKILL DIAGNOSTIC REPORT                     ║",
        "╚══════════════════════════════════════════════════════╝",
        "",
        f"  Skill Name : {report.skill_name}",
        f"  Path       : {report.skill_path}",
        f"  Checked At : {report.timestamp}",
        "",
        "┌────────────────────────────────────────────────────────┐",
        "│  SUMMARY                                               │",
        "├────────────────────────────────────────────────────────┤",
        f"│  Status    : {'✅ PASSED' if report.summary['passed'] else '❌ FAILED':<46}│",
        f"│  Score     : [{score_bar}] {report.summary['score']:>3}/100{' '*35}│",
        f"│  Errors    : {report.summary['errors']:<5}  Warnings: {report.summary['warnings']:<5}  Info: {report.summary['info']:<5}     │",
        "└────────────────────────────────────────────────────────┘",
        "",
    ]

    categories = {
        "structure": "📁 Structure (目录结构)",
        "frontmatter": "📝 Frontmatter (元数据)",
        "naming": "🏷️  Naming (命名规范)",
        "content": "📄 Content (内容质量)",
        "resources": "📦 Resources (资源文件)",
        "progressive": "📚 Progressive Disclosure (渐进式披露)"
    }

    for cat, title in categories.items():
        issues = report.details.get(cat, [])
        if issues:
            lines.append(f"\n{title}")
            lines.append("─" * 50)
            for issue in issues:
                icon = {"ERROR": "❌", "WARN": "⚠️", "INFO": "ℹ️"}.get(issue["level"], "•")
                loc = f" → {issue['file']}" if issue['file'] else ""
                lines.append(f"  {icon} {issue['level']:<7} {issue['message']}{loc}")

    if report.fixes:
        lines.append("\n" + "─" * 50)
        lines.append("🔧 FIX RECOMMENDATIONS (修复建议)")
        lines.append("─" * 50)
        for i, fix in enumerate(report.fixes, 1):
            lines.append(f"  {i}. {fix['suggestion']}")

    lines.append("")
    lines.append("═" * 54)
    lines.append("")

    return "\n".join(lines)


def format_markdown_report(report: DiagnosticReport) -> str:
    status_icon = "✅" if report.summary["passed"] else "❌"

    lines = [
        f"# Skill Diagnostic Report: {report.skill_name}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|---------|-------|",
        f"| Status | {status_icon} {'PASSED' if report.summary['passed'] else 'FAILED'} |",
        f"| Score | {report.summary['score']}/100 |",
        f"| Errors | {report.summary['errors']} |",
        f"| Warnings | {report.summary['warnings']} |",
        f"| Info | {report.summary['info']} |",
        "",
        f"- **Path**: `{report.skill_path}`",
        f"- **Checked**: {report.timestamp}",
        "",
        "## Issues",
        ""
    ]

    for cat, issues in report.details.items():
        if issues:
            lines.append(f"### {cat.title()}")
            lines.append("")
            for issue in issues:
                icon = {"ERROR": "❌", "WARN": "⚠️", "INFO": "ℹ️"}.get(issue["level"], "•")
                lines.append(f"- {icon} **{issue['level']}**: {issue['message']}")
            lines.append("")

    if report.fixes:
        lines.append("## Fix Recommendations")
        lines.append("")
        for i, fix in enumerate(report.fixes, 1):
            lines.append(f"{i}. {fix['suggestion']}")
        lines.append("")

    return "\n".join(lines)


def format_json_report(report: DiagnosticReport) -> str:
    import json
    return json.dumps({
        "skill_name": report.skill_name,
        "skill_path": report.skill_path,
        "timestamp": report.timestamp,
        "summary": report.summary,
        "details": report.details,
        "fixes": report.fixes
    }, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Skill诊断报告生成器")
    parser.add_argument("path", help="Skill目录路径")
    parser.add_argument("--format", choices=["text", "markdown", "json"], default="text", help="输出格式")
    parser.add_argument("--output", "-o", help="输出到文件")

    args = parser.parse_args()

    skill_path = Path(args.path)
    if not skill_path.exists() or not skill_path.is_dir():
        print(f"❌ Error: Invalid skill path: {skill_path}")
        sys.exit(1)

    report = generate_diagnosis_report(skill_path)

    if args.format == "text":
        output = format_text_report(report)
    elif args.format == "markdown":
        output = format_markdown_report(report)
    else:
        output = format_json_report(report)

    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"✅ Report saved to: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()