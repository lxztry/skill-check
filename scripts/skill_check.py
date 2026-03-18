#!/usr/bin/env python3
"""
Skill Check - 检查Skill是否符合规范
"""

import sys
import re
import yaml
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

ALLOWED_FRONTMATTER_PROPS = {'name', 'description', 'license', 'allowed-tools', 'metadata'}
FORBIDDEN_FILES = {'README.md', 'CHANGELOG.md', 'INSTALLATION_GUIDE.md', 'QUICK_REFERENCE.md', 'TODO.md', 'NOTES.md'}
ALLOWED_DIRS = {'scripts', 'references', 'assets'}

@dataclass
class Issue:
    level: str
    category: str
    message: str
    file: str = ""
    line: int = 0
    fix: str = ""

@dataclass
class CheckResult:
    skill_name: str
    skill_path: str
    passed: bool
    score: int
    issues: List[Issue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def add_issue(self, level: str, category: str, message: str, file: str = "", line: int = 0, fix: str = ""):
        self.issues.append(Issue(level, category, message, file, line, fix))
        if fix and fix not in self.suggestions:
            self.suggestions.append(fix)

def check_file_structure(skill_path: Path) -> CheckResult:
    result = CheckResult(
        skill_name=skill_path.name,
        skill_path=str(skill_path),
        passed=True,
        score=100
    )

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        result.passed = False
        result.add_issue("ERROR", "Structure", "SKILL.md not found", fix="Create SKILL.md file")
        return result

    for item in skill_path.iterdir():
        if item.is_file():
            if item.name in FORBIDDEN_FILES:
                result.add_issue(
                    "ERROR", "Structure",
                    f"Forbidden file: {item.name}",
                    file=str(item),
                    fix=f"Remove {item.name} - skills should not contain auxiliary documentation"
                )
        elif item.is_dir():
            if item.name not in ALLOWED_DIRS:
                result.add_issue(
                    "WARN", "Structure",
                    f"Non-standard directory: {item.name}",
                    fix=f"Use only: {', '.join(sorted(ALLOWED_DIRS))}"
                )
            elif not any(item.iterdir()):
                result.add_issue(
                    "INFO", "Structure",
                    f"Empty directory: {item.name}/",
                    fix=f"Remove empty {item.name}/ directory"
                )

    return result

def check_frontmatter(skill_md: Path, result: CheckResult):
    content = skill_md.read_text(encoding='utf-8')

    if not content.startswith('---'):
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", "No YAML frontmatter found", file="SKILL.md", fix="Add YAML frontmatter starting with '---'")
        return None

    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", "Invalid frontmatter format", file="SKILL.md", fix="Ensure frontmatter is valid YAML between '---' delimiters")
        return None

    try:
        frontmatter = yaml.safe_load(match.group(1))
        if not isinstance(frontmatter, dict):
            result.passed = False
            result.add_issue("ERROR", "Frontmatter", "Frontmatter must be a YAML dictionary", file="SKILL.md", fix="Start frontmatter with key-value pairs")
            return None
    except yaml.YAMLError as e:
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", f"Invalid YAML: {e}", file="SKILL.md", fix="Fix YAML syntax errors")
        return None

    unexpected_keys = set(frontmatter.keys()) - ALLOWED_FRONTMATTER_PROPS
    if unexpected_keys:
        result.add_issue(
            "ERROR", "Frontmatter",
            f"Unexpected keys: {', '.join(sorted(unexpected_keys))}",
            file="SKILL.md",
            fix=f"Allowed keys: {', '.join(sorted(ALLOWED_FRONTMATTER_PROPS))}"
        )

    if 'name' not in frontmatter:
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", "Missing 'name' field", file="SKILL.md", fix="Add 'name' field to frontmatter")
    elif not isinstance(frontmatter['name'], str):
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", f"Name must be string, got {type(frontmatter['name']).__name__}", file="SKILL.md", fix="Change name to a string value")
    else:
        name = frontmatter['name'].strip()
        if not name:
            result.passed = False
            result.add_issue("ERROR", "Frontmatter", "Name cannot be empty", file="SKILL.md", fix="Provide a non-empty name")
        elif not re.match(r'^[a-z0-9-]+$', name):
            result.passed = False
            result.add_issue("ERROR", "Naming", f"Name '{name}' should be hyphen-case (lowercase, digits, hyphens only)", file="SKILL.md", fix="Use lowercase letters, digits, and hyphens only")
        elif name.startswith('-') or name.endswith('-') or '--' in name:
            result.passed = False
            result.add_issue("ERROR", "Naming", f"Invalid name format: '{name}'", file="SKILL.md", fix="Name cannot start/end with hyphen or contain consecutive hyphens")
        elif len(name) > 64:
            result.passed = False
            result.add_issue("ERROR", "Naming", f"Name too long ({len(name)} > 64 chars)", file="SKILL.md", fix="Shorten name to 64 characters or less")
        result.skill_name = name

    if 'description' not in frontmatter:
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", "Missing 'description' field", file="SKILL.md", fix="Add 'description' field to frontmatter")
    elif not isinstance(frontmatter['description'], str):
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", f"Description must be string", file="SKILL.md", fix="Change description to a string value")
    else:
        desc = frontmatter['description']
        if '<' in desc or '>' in desc:
            result.add_issue("WARN", "Frontmatter", "Description contains angle brackets", file="SKILL.md", fix="Remove '<' and '>' from description")
        if len(desc) > 1024:
            result.add_issue("WARN", "Frontmatter", f"Description too long ({len(desc)} > 1024 chars)", file="SKILL.md", fix="Truncate description to 1024 characters or less")
        if len(desc) < 20:
            result.add_issue("WARN", "Frontmatter", "Description too short", file="SKILL.md", fix="Expand description to at least 20 characters")

    return frontmatter

def check_content_quality(skill_md: Path, result: CheckResult):
    content = skill_md.read_text(encoding='utf-8')
    lines = content.split('\n')

    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith('---') and i > 0:
            body_start = i + 2
            break

    body_lines = len(lines) - body_start
    if body_lines > 500:
        result.add_issue("WARN", "Content", f"SKILL.md body too long ({body_lines} lines)", file="SKILL.md", fix="Split content into reference files, keep SKILL.md under 500 lines")

    empty_lines = sum(1 for line in lines if not line.strip())
    if empty_lines > len(lines) * 0.3:
        result.add_issue("INFO", "Content", f"Many empty lines ({empty_lines}/{len(lines)})", file="SKILL.md", fix="Remove unnecessary empty lines")

def check_resources(skill_path: Path, result: CheckResult):
    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        for script in scripts_dir.iterdir():
            if script.is_file() and script.suffix in ['.py', '.sh', '.js']:
                content = script.read_text(encoding='utf-8')
                if '#!' not in content[:100] and script.suffix == '.sh':
                    result.add_issue("INFO", "Resources", f"Script {script.name} may need shebang", file=str(script))

    references_dir = skill_path / "references"
    if references_dir.exists():
        for ref in references_dir.iterdir():
            if ref.is_file() and ref.suffix == '.md':
                content = ref.read_text(encoding='utf-8')
                if len(content.split('\n')) > 200:
                    result.add_issue("INFO", "Resources", f"Large reference file: {ref.name}", file=str(ref))

def calculate_score(result: CheckResult) -> int:
    errors = sum(1 for i in result.issues if i.level == "ERROR")
    warnings = sum(1 for i in result.issues if i.level == "WARN")
    infos = sum(1 for i in result.issues if i.level == "INFO")

    score = 100 - (errors * 20) - (warnings * 5) - (infos * 1)
    return max(0, min(100, score))

def check_skill(skill_path: Path, auto_fix: bool = False) -> CheckResult:
    skill_path = Path(skill_path)

    if not skill_path.exists():
        result = CheckResult("", str(skill_path), False, 0)
        result.add_issue("ERROR", "Structure", f"Path not found: {skill_path}")
        return result

    if not skill_path.is_dir():
        result = CheckResult("", str(skill_path), False, 0)
        result.add_issue("ERROR", "Structure", f"Not a directory: {skill_path}")
        return result

    result = check_file_structure(skill_path)

    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        check_frontmatter(skill_md, result)
        check_content_quality(skill_md, result)
        check_resources(skill_path, result)

    result.score = calculate_score(result)

    if errors := [i for i in result.issues if i.level == "ERROR"]:
        result.passed = False

    return result

def scan_directory(dir_path: Path) -> List[CheckResult]:
    results = []
    for item in dir_path.iterdir():
        if item.is_dir() and (item / "SKILL.md").exists():
            results.append(check_skill(item))
    return results

def format_report(result: CheckResult) -> str:
    status = "✅ PASSED" if result.passed else "❌ FAILED"
    lines = [
        "",
        "═" * 50,
        "SKILL CHECK REPORT",
        "═" * 50,
        f"Skill: {result.skill_name}",
        f"Path:  {result.skill_path}",
        f"Status: {status}",
        "─" * 50,
    ]

    if result.issues:
        lines.append("ISSUES:")
        for issue in result.issues:
            icon = {"ERROR": "❌", "WARN": "⚠️", "INFO": "ℹ️"}.get(issue.level, "•")
            loc = f" [{issue.file}:{issue.line}]" if issue.file else ""
            lines.append(f"  {icon} [{issue.level}] {issue.category}{loc}")
            lines.append(f"     {issue.message}")
        lines.append("")

    if result.suggestions:
        lines.append("FIX SUGGESTIONS:")
        for i, fix in enumerate(result.suggestions, 1):
            lines.append(f"  {i}. {fix}")
        lines.append("")

    lines.append(f"Score: {result.score}/100")
    lines.append("═" * 50)

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Skill规范检查工具")
    parser.add_argument("path", help="Skill目录路径或包含多个skill的目录")
    parser.add_argument("--scan", action="store_true", help="扫描目录下所有skill")
    parser.add_argument("--fix", action="store_true", help="自动修复可修复的问题")
    parser.add_argument("--json", action="store_true", help="输出JSON格式")
    parser.add_argument("--quiet", action="store_true", help="仅输出摘要")

    args = parser.parse_args()

    path = Path(args.path)
    results = []

    if args.scan and path.is_dir():
        results = scan_directory(path)
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
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        for result in results:
            report = format_report(result)
            if args.quiet:
                icon = "✅" if result.passed else "❌"
                print(f"{icon} {result.skill_name}: {result.score}/100")
            else:
                print(report)

    has_errors = any(not r.passed for r in results)
    sys.exit(1 if has_errors else 0)

if __name__ == "__main__":
    main()
