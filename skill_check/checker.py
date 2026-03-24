#!/usr/bin/env python3
"""
Skill Check - Skill规范检查工具
"""

import sys
import re
import yaml
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

ALLOWED_FRONTMATTER_PROPS: Set[str] = {'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'}
FORBIDDEN_FILES: Set[str] = {'README.md', 'CHANGELOG.md', 'INSTALLATION_GUIDE.md', 'QUICK_REFERENCE.md', 'TODO.md', 'NOTES.md', 'HISTORY.md', 'CONTRIBUTING.md'}
ALLOWED_DIRS: Set[str] = {'scripts', 'references', 'assets'}
IGNORED_DIRS: Set[str] = {'.git', '__pycache__', '.pytest_cache', '.tox', 'node_modules', '.venv', 'venv', 'env', 'skill_check'}
SKILL_MD_NAME: str = "SKILL.md"
MAX_NAME_LENGTH: int = 64
MAX_DESCRIPTION_LENGTH: int = 1024
MIN_DESCRIPTION_LENGTH: int = 20
MAX_BODY_LINES: int = 500
MAX_BODY_TOKENS: int = 5000


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


def check_file_structure(skill_path: Path, auto_fix: bool = False) -> CheckResult:
    result = CheckResult(
        skill_name=skill_path.name,
        skill_path=str(skill_path),
        passed=True,
        score=100
    )

    skill_md = skill_path / SKILL_MD_NAME
    if not skill_md.exists():
        result.passed = False
        result.add_issue("ERROR", "Structure", f"{SKILL_MD_NAME} not found", fix=f"Create {SKILL_MD_NAME} file")
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
                if auto_fix:
                    item.unlink()
        elif item.is_dir():
            if item.name in IGNORED_DIRS:
                pass
            elif item.name not in ALLOWED_DIRS:
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
                if auto_fix:
                    item.rmdir()

    return result


def check_frontmatter(skill_md: Path, result: CheckResult, auto_fix: bool = False):
    content = skill_md.read_text(encoding='utf-8')

    if not content.startswith('---'):
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", "No YAML frontmatter found", file=SKILL_MD_NAME, fix="Add YAML frontmatter starting with '---'")
        return None

    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", "Invalid frontmatter format", file=SKILL_MD_NAME, fix="Ensure frontmatter is valid YAML between '---' delimiters")
        return None

    try:
        frontmatter = yaml.safe_load(match.group(1))
        if not isinstance(frontmatter, dict):
            result.passed = False
            result.add_issue("ERROR", "Frontmatter", "Frontmatter must be a YAML dictionary", file=SKILL_MD_NAME, fix="Start frontmatter with key-value pairs")
            return None
    except yaml.YAMLError as e:
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", f"Invalid YAML: {e}", file=SKILL_MD_NAME, fix="Fix YAML syntax errors")
        return None

    unexpected_keys = set(frontmatter.keys()) - ALLOWED_FRONTMATTER_PROPS
    if unexpected_keys:
        result.add_issue(
            "ERROR", "Frontmatter",
            f"Unexpected keys: {', '.join(sorted(unexpected_keys))}",
            file=SKILL_MD_NAME,
            fix=f"Allowed keys: {', '.join(sorted(ALLOWED_FRONTMATTER_PROPS))}"
        )

    if 'name' not in frontmatter:
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", "Missing 'name' field", file=SKILL_MD_NAME, fix="Add 'name' field to frontmatter")
    elif not isinstance(frontmatter['name'], str):
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", f"Name must be string, got {type(frontmatter['name']).__name__}", file=SKILL_MD_NAME, fix="Change name to a string value")
    else:
        name = frontmatter['name'].strip()
        if not name:
            result.passed = False
            result.add_issue("ERROR", "Frontmatter", "Name cannot be empty", file=SKILL_MD_NAME, fix="Provide a non-empty name")
        elif not re.match(r'^[a-z0-9-]+$', name):
            result.passed = False
            result.add_issue("ERROR", "Naming", f"Name '{name}' should be hyphen-case (lowercase, digits, hyphens only)", file=SKILL_MD_NAME, fix="Use lowercase letters, digits, and hyphens only")
        elif name.startswith('-') or name.endswith('-') or '--' in name:
            result.passed = False
            result.add_issue("ERROR", "Naming", f"Invalid name format: '{name}'", file=SKILL_MD_NAME, fix="Name cannot start/end with hyphen or contain consecutive hyphens")
        elif len(name) > MAX_NAME_LENGTH:
            result.passed = False
            result.add_issue("ERROR", "Naming", f"Name too long ({len(name)} > {MAX_NAME_LENGTH} chars)", file=SKILL_MD_NAME, fix=f"Shorten name to {MAX_NAME_LENGTH} characters or less")
        result.skill_name = name

        if result.skill_name != skill_md.parent.name and result.skill_name:
            result.add_issue(
                "WARN", "Naming",
                f"Name '{name}' does not match directory name '{skill_md.parent.name}'",
                file=SKILL_MD_NAME,
                fix=f"Rename directory to '{name}' or change name to '{skill_md.parent.name}'"
            )

    if 'description' not in frontmatter:
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", "Missing 'description' field", file=SKILL_MD_NAME, fix="Add 'description' field to frontmatter")
    elif not isinstance(frontmatter['description'], str):
        result.passed = False
        result.add_issue("ERROR", "Frontmatter", f"Description must be string", file=SKILL_MD_NAME, fix="Change description to a string value")
    else:
        desc = frontmatter['description']
        if '<' in desc or '>' in desc:
            result.add_issue("WARN", "Frontmatter", "Description contains angle brackets", file=SKILL_MD_NAME, fix="Remove '<' and '>' from description")
            if auto_fix:
                fixed_desc = desc.replace('<', '').replace('>', '')
                frontmatter['description'] = fixed_desc
        if len(desc) > MAX_DESCRIPTION_LENGTH:
            result.add_issue("WARN", "Frontmatter", f"Description too long ({len(desc)} > {MAX_DESCRIPTION_LENGTH} chars)", file=SKILL_MD_NAME, fix=f"Truncate description to {MAX_DESCRIPTION_LENGTH} characters or less")
            if auto_fix:
                frontmatter['description'] = desc[:MAX_DESCRIPTION_LENGTH]
        if len(desc) < MIN_DESCRIPTION_LENGTH:
            result.add_issue("WARN", "Frontmatter", "Description too short (less than 20 chars)", file=SKILL_MD_NAME, fix="Expand description to at least 20 characters")

        if not re.search(r'(when|use|if|need|ask|want|handle|work with|使用|用于|适用于|场景|触发)', desc, re.IGNORECASE):
            result.add_issue(
                "INFO", "Content",
                "Description should include trigger scenario hints",
                file=SKILL_MD_NAME,
                fix="Add trigger context like 'Use when...' or 'Handle...'"
            )

    if 'license' in frontmatter and not isinstance(frontmatter['license'], str):
        result.add_issue("WARN", "Frontmatter", "License should be a string", file=SKILL_MD_NAME, fix="Change license to a string value")

    if 'compatibility' in frontmatter:
        comp = frontmatter['compatibility']
        if isinstance(comp, str):
            pass
        elif isinstance(comp, list):
            pass
        else:
            result.add_issue("WARN", "Frontmatter", "Compatibility should be string or list", file=SKILL_MD_NAME)

    if 'allowed-tools' in frontmatter:
        tools = frontmatter['allowed-tools']
        if not isinstance(tools, (str, list)):
            result.add_issue("WARN", "Frontmatter", "allowed-tools should be string or list", file=SKILL_MD_NAME, fix="Use space-delimited string or list")

    return frontmatter


def check_content_quality(skill_md: Path, result: CheckResult, auto_fix: bool = False):
    content = skill_md.read_text(encoding='utf-8')
    lines = content.split('\n')

    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith('---') and i > 0:
            body_start = i + 2
            break

    body_lines = len(lines) - body_start
    if body_lines > MAX_BODY_LINES:
        result.add_issue("WARN", "Content", f"SKILL.md body too long ({body_lines} lines)", file=SKILL_MD_NAME, fix=f"Keep SKILL.md under {MAX_BODY_LINES} lines, move details to references/")

    empty_lines = sum(1 for line in lines if not line.strip())
    if empty_lines > len(lines) * 0.3:
        result.add_issue("INFO", "Content", f"Many empty lines ({empty_lines}/{len(lines)})", file=SKILL_MD_NAME, fix="Remove unnecessary empty lines")

    body_content = '\n'.join(lines[body_start:])
    token_estimate = len(body_content.split()) * 1.3
    if token_estimate > MAX_BODY_TOKENS:
        result.add_issue(
            "WARN", "Content",
            f"Body content ~{int(token_estimate)} tokens (recommended < {MAX_BODY_TOKENS})",
            file=SKILL_MD_NAME,
            fix="Move detailed content to references/ for progressive disclosure"
        )

    sections = ['##', '###', '####']
    has_sections = any(any(s in line for s in sections) for line in lines[body_start:])
    if body_lines > 50 and not has_sections:
        result.add_issue(
            "INFO", "Content",
            "Long content without sections, consider adding headers",
            file=SKILL_MD_NAME,
            fix="Add ## headers to organize content"
        )


def check_resources(skill_path: Path, result: CheckResult, auto_fix: bool = False):
    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        for script in scripts_dir.iterdir():
            if script.is_file():
                if script.suffix == '.sh':
                    content = script.read_text(encoding='utf-8')
                    if not content.startswith('#!'):
                        result.add_issue("INFO", "Resources", f"Script {script.name} missing shebang", file=str(script), fix="Add shebang: #!/usr/bin/env bash")
                        if auto_fix:
                            script.write_text(f"#!/usr/bin/env bash\n\n{content}", encoding='utf-8')
                elif script.suffix == '.py':
                    content = script.read_text(encoding='utf-8')
                    if not content.startswith('#!'):
                        result.add_issue("INFO", "Resources", f"Python script {script.name} may benefit from shebang", file=str(script), fix="Add shebang: #!/usr/bin/env python3")

    references_dir = skill_path / "references"
    if references_dir.exists():
        for ref in references_dir.iterdir():
            if ref.is_file() and ref.suffix == '.md':
                content = ref.read_text(encoding='utf-8')
                ref_lines = len(content.split('\n'))
                if ref_lines > 200:
                    result.add_issue("INFO", "Resources", f"Large reference file: {ref.name} ({ref_lines} lines)", file=str(ref), fix="Consider splitting large reference files")
                if ref.name == 'REFERENCE.md':
                    result.add_issue(
                        "INFO", "Resources",
                        "Use descriptive reference filenames instead of REFERENCE.md",
                        file=str(ref),
                        fix="Rename to specific name like api-guide.md"
                    )

    assets_dir = skill_path / "assets"
    if assets_dir.exists():
        large_files = []
        for f in assets_dir.rglob('*'):
            if f.is_file() and f.stat().st_size > 5 * 1024 * 1024:
                large_files.append(f"{f.name} ({f.stat().st_size // (1024*1024)}MB)")
        if large_files:
            result.add_issue("INFO", "Resources", f"Large asset files: {', '.join(large_files)}", fix="Consider compressing or using external hosting")


def check_progressive_disclosure(skill_path: Path, result: CheckResult):
    skill_md = skill_path / SKILL_MD_NAME
    if not skill_md.exists():
        return

    content = skill_md.read_text(encoding='utf-8')
    lines = content.split('\n')
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith('---') and i > 0:
            body_start = i + 2
            break
    body = '\n'.join(lines[body_start:])

    if 'references/' in body:
        result.add_issue(
            "INFO", "ProgressiveDisclosure",
            "References referenced in SKILL.md",
            file=SKILL_MD_NAME,
            fix="Good practice: Use progressive disclosure for detailed content"
        )

    if 'scripts/' in body:
        result.add_issue(
            "INFO", "ProgressiveDisclosure",
            "Scripts referenced in SKILL.md",
            file=SKILL_MD_NAME,
            fix="Good practice: Scripts are loaded on demand"
        )


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

    result = check_file_structure(skill_path, auto_fix)

    skill_md = skill_path / SKILL_MD_NAME
    if skill_md.exists():
        check_frontmatter(skill_md, result, auto_fix)
        check_content_quality(skill_md, result, auto_fix)
        check_resources(skill_path, result, auto_fix)
        check_progressive_disclosure(skill_path, result)

    result.score = calculate_score(result)

    if errors := [i for i in result.issues if i.level == "ERROR"]:
        result.passed = False

    return result


def scan_directory(dir_path: Path, concurrent: bool = False, max_workers: int = 4) -> List[CheckResult]:
    results = []
    skills = [item for item in dir_path.iterdir() if item.is_dir() and (item / "SKILL.md").exists()]

    if concurrent and len(skills) > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_skill, skill): skill for skill in skills}
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    skill = futures[future]
                    result = CheckResult(skill.name, str(skill), False, 0)
                    result.add_issue("ERROR", "Scan", f"Scan failed: {e}")
                    results.append(result)
    else:
        for skill in skills:
            results.append(check_skill(skill))

    return results


def format_report(result: CheckResult, verbose: bool = False) -> str:
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
    if verbose:
        grade = "A" if result.score >= 90 else "B" if result.score >= 70 else "C" if result.score >= 50 else "F"
        lines.append(f"Grade: {grade}")
    lines.append("═" * 50)

    return "\n".join(lines)


def format_summary(results: List[CheckResult]) -> str:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    avg_score = sum(r.score for r in results) / total if total else 0

    lines = [
        "",
        "─" * 50,
        "SCAN SUMMARY",
        "─" * 50,
        f"Total:   {total}",
        f"Passed:  {passed} ✅",
        f"Failed:  {failed} ❌",
        f"Average: {avg_score:.1f}/100",
        "─" * 50,
    ]
    return "\n".join(lines)