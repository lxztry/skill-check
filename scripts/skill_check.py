#!/usr/bin/env python3
"""
Skill Check CLI - Skill规范检查工具
"""

import sys
import os
import argparse
from pathlib import Path

script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))

from skill_check.checker import (
    check_skill, scan_directory, format_report, format_summary,
    ALLOWED_FRONTMATTER_PROPS, FORBIDDEN_FILES, ALLOWED_DIRS
)


def main():
    parser = argparse.ArgumentParser(
        description="Skill规范检查工具 - 验证skill是否符合开发规范",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s ./my-skill              # 检查单个skill
  %(prog)s ./skills --scan         # 扫描目录下所有skill
  %(prog)s ./my-skill --fix        # 检查并自动修复
  %(prog)s ./skills --scan -c      # 并发扫描
  %(prog)s ./my-skill -q           # 安静模式(仅摘要)
  %(prog)s ./my-skill -v           # 详细模式(含等级)
  %(prog)s ./my-skill --json       # JSON输出
        """
    )

    parser.add_argument("path", help="Skill目录路径或包含多个skill的目录")
    parser.add_argument("--scan", "-s", action="store_true", help="扫描目录下所有skill")
    parser.add_argument("--fix", "-f", action="store_true", help="自动修复可修复的问题")
    parser.add_argument("--json", "-j", action="store_true", help="输出JSON格式")
    parser.add_argument("--quiet", "-q", action="store_true", help="仅输出摘要")
    parser.add_argument("--verbose", "-v", action="store_true", help="输出详细信息(含等级)")
    parser.add_argument("--concurrent", "-c", action="store_true", help="并发扫描(多skill时)")
    parser.add_argument("--workers", "-w", type=int, default=4, help="并发工作线程数(默认4)")
    parser.add_argument("--output", "-o", help="输出到文件")
    parser.add_argument("--version", action="version", version="Skill Check v2.0.0")

    args = parser.parse_args()

    path = Path(args.path)
    results = []

    if args.scan and path.is_dir():
        results = scan_directory(path, args.concurrent, args.workers)
        if not args.quiet:
            print(format_summary(results))
    else:
        result = check_skill(path, args.fix)
        results = [result]

    if args.json:
        import json
        output = [{
            "name": r.skill_name,
            "path": r.skill_path,
            "passed": r.passed,
            "score": r.score,
            "issues": [{"level": i.level, "category": i.category, "message": i.message, "fix": i.fix} for i in r.issues]
        } for r in results]
        json_output = json.dumps(output, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(json_output, encoding='utf-8')
            print(f"✅ Results saved to: {args.output}")
        else:
            print(json_output)
    else:
        for result in results:
            if args.quiet:
                icon = "✅" if result.passed else "❌"
                print(f"{icon} {result.skill_name}: {result.score}/100")
            else:
                report = format_report(result, args.verbose)
                if args.output:
                    Path(args.output).write_text(report, encoding='utf-8')
                    print(f"✅ Report saved to: {args.output}")
                else:
                    print(report)

    has_errors = any(not r.passed for r in results)
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()