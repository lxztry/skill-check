#!/usr/bin/env python3
"""
Skill Test Runner - Runtime validation for skills
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

# Add parent directory to path
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))

from skill_check.config import load_config


@dataclass
class TestResult:
    """Result of a single test"""
    name: str
    passed: bool
    message: str = ""
    details: Dict = field(default_factory=dict)


@dataclass
class TestSuiteResult:
    """Result of a test suite"""
    skill_name: str
    skill_path: str
    passed: bool
    tests: List[TestResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class SkillTestRunner:
    """Run tests against a skill"""
    
    def __init__(self, skill_path: Path):
        self.skill_path = Path(skill_path)
        self.skill_md = self.skill_path / 'SKILL.md'
        self.config = load_config()
        self.results: List[TestResult] = []
    
    def run_all_tests(self) -> TestSuiteResult:
        """Run all tests"""
        result = TestSuiteResult(
            skill_name=self.skill_path.name,
            skill_path=str(self.skill_path),
            passed=True
        )
        
        # Check if SKILL.md exists
        if not self.skill_md.exists():
            result.passed = False
            result.errors.append("SKILL.md not found")
            return result
        
        # Run all tests
        tests = [
            ("test_structure", self.test_structure),
            ("test_frontmatter", self.test_frontmatter),
            ("test_naming", self.test_naming),
            ("test_description", self.test_description),
            ("test_trigger_words", self.test_trigger_words),
            ("test_content_length", self.test_content_length),
            ("test_no_html", self.test_no_html),
            ("test_scripts_shebang", self.test_scripts_shebang),
            ("test_references_naming", self.test_references_naming),
        ]
        
        for test_name, test_func in tests:
            try:
                test_result = test_func()
                self.results.append(test_result)
                result.tests.append(test_result)
                if not test_result.passed:
                    result.passed = False
            except Exception as e:
                result.errors.append(f"{test_name}: {str(e)}")
                result.passed = False
        
        return result
    
    def test_structure(self) -> TestResult:
        """Test directory structure"""
        issues = []
        
        # Check required files
        if not (self.skill_path / 'SKILL.md').exists():
            issues.append("SKILL.md not found")
        
        # Check forbidden files
        for forbidden in self.config.forbidden_files:
            if (self.skill_path / forbidden).exists():
                issues.append(f"Forbidden file found: {forbidden}")
        
        # Check allowed directories
        for item in self.skill_path.iterdir():
            if item.is_dir():
                if item.name not in self.config.allowed_dirs and item.name not in self.config.ignored_dirs:
                    issues.append(f"Non-standard directory: {item.name}")
        
        return TestResult(
            name="structure",
            passed=len(issues) == 0,
            message="; ".join(issues) if issues else "Structure is valid"
        )
    
    def test_frontmatter(self) -> TestResult:
        """Test frontmatter fields"""
        import yaml
        
        content = self.skill_md.read_text(encoding='utf-8')
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        
        if not match:
            return TestResult(
                name="frontmatter",
                passed=False,
                message="No frontmatter found"
            )
        
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError as e:
            return TestResult(
                name="frontmatter",
                passed=False,
                message=f"YAML parse error: {e}"
            )
        
        issues = []
        
        # Check required fields
        if 'name' not in data:
            issues.append("Missing 'name' field")
        if 'description' not in data:
            issues.append("Missing 'description' field")
        
        # Check for forbidden fields
        allowed = set(self.config.allowed_frontmatter_fields)
        for key in data.keys():
            if key not in allowed:
                issues.append(f"Forbidden field: '{key}'")
        
        return TestResult(
            name="frontmatter",
            passed=len(issues) == 0,
            message="; ".join(issues) if issues else "Frontmatter is valid"
        )
    
    def test_naming(self) -> TestResult:
        """Test naming conventions"""
        import yaml
        
        content = self.skill_md.read_text(encoding='utf-8')
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        
        if not match:
            return TestResult(
                name="naming",
                passed=False,
                message="No frontmatter found"
            )
        
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return TestResult(
                name="naming",
                passed=False,
                message="Cannot parse YAML"
            )
        
        if 'name' not in data:
            return TestResult(
                name="naming",
                passed=False,
                message="Missing 'name' field"
            )
        
        name = data['name']
        issues = []
        
        # Check length
        if len(name) > self.config.rules.get('max_name_length', 64):
            issues.append(f"Name too long: {len(name)} chars")
        
        # Check format
        pattern = re.compile(r'^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$|^[a-z0-9]$')
        if not pattern.match(name):
            if '-' in name and '--' not in name:
                pass  # hyphen-case is valid
            else:
                issues.append(f"Invalid name format: '{name}'")
        
        # Check leading/trailing hyphens
        if name.startswith('-') or name.endswith('-'):
            issues.append("Name cannot start or end with hyphen")
        
        # Check directory name matches
        if name != self.skill_path.name:
            issues.append(f"Name mismatch: '{name}' != directory '{self.skill_path.name}'")
        
        return TestResult(
            name="naming",
            passed=len(issues) == 0,
            message="; ".join(issues) if issues else "Naming is valid"
        )
    
    def test_description(self) -> TestResult:
        """Test description quality"""
        import yaml
        
        content = self.skill_md.read_text(encoding='utf-8')
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        
        if not match:
            return TestResult(
                name="description",
                passed=False,
                message="No frontmatter found"
            )
        
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return TestResult(
                name="description",
                passed=False,
                message="Cannot parse YAML"
            )
        
        if 'description' not in data:
            return TestResult(
                name="description",
                passed=False,
                message="Missing 'description' field"
            )
        
        desc = data['description']
        issues = []
        
        # Check length
        min_len = self.config.rules.get('min_description_length', 20)
        max_len = self.config.rules.get('max_description_length', 1024)
        
        if len(desc) < min_len:
            issues.append(f"Description too short: {len(desc)} < {min_len}")
        if len(desc) > max_len:
            issues.append(f"Description too long: {len(desc)} > {max_len}")
        
        return TestResult(
            name="description",
            passed=len(issues) == 0,
            message="; ".join(issues) if issues else "Description is valid"
        )
    
    def test_trigger_words(self) -> TestResult:
        """Test for trigger words in description"""
        import yaml
        
        content = self.skill_md.read_text(encoding='utf-8')
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        
        if not match:
            return TestResult(
                name="trigger_words",
                passed=False,
                message="No frontmatter found"
            )
        
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return TestResult(
                name="trigger_words",
                passed=False,
                message="Cannot parse YAML"
            )
        
        if 'description' not in data:
            return TestResult(
                name="trigger_words",
                passed=False,
                message="Missing 'description' field"
            )
        
        desc = data['description'].lower()
        found_triggers = []
        
        for trigger in self.config.trigger_words:
            if trigger.lower() in desc:
                found_triggers.append(trigger)
        
        if not found_triggers:
            return TestResult(
                name="trigger_words",
                passed=False,
                message=f"No trigger words found. Expected one of: {', '.join(self.config.trigger_words[:5])}..."
            )
        
        return TestResult(
            name="trigger_words",
            passed=True,
            message=f"Found triggers: {', '.join(found_triggers)}"
        )
    
    def test_content_length(self) -> TestResult:
        """Test content length limits"""
        content = self.skill_md.read_text(encoding='utf-8')
        
        # Remove frontmatter
        match = re.match(r'^---\n.*?\n---\n(.*)', content, re.DOTALL)
        if match:
            body = match.group(1)
        else:
            body = content
        
        lines = body.split('\n')
        issues = []
        
        max_lines = self.config.rules.get('max_body_lines', 500)
        if len(lines) > max_lines:
            issues.append(f"Too many lines: {len(lines)} > {max_lines}")
        
        return TestResult(
            name="content_length",
            passed=len(issues) == 0,
            message="; ".join(issues) if issues else "Content length is valid"
        )
    
    def test_no_html(self) -> TestResult:
        """Test for HTML tags in description"""
        import yaml
        
        content = self.skill_md.read_text(encoding='utf-8')
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        
        if not match:
            return TestResult(
                name="no_html",
                passed=False,
                message="No frontmatter found"
            )
        
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return TestResult(
                name="no_html",
                passed=False,
                message="Cannot parse YAML"
            )
        
        if 'description' not in data:
            return TestResult(
                name="no_html",
                passed=False,
                message="Missing 'description' field"
            )
        
        desc = data['description']
        html_tags = re.findall(r'<[^>]+>', desc)
        
        if html_tags:
            return TestResult(
                name="no_html",
                passed=False,
                message=f"HTML tags found: {', '.join(html_tags)}"
            )
        
        return TestResult(
            name="no_html",
            passed=True,
            message="No HTML tags found"
        )
    
    def test_scripts_shebang(self) -> TestResult:
        """Test scripts have shebang"""
        scripts_dir = self.skill_path / 'scripts'
        
        if not scripts_dir.exists():
            return TestResult(
                name="scripts_shebang",
                passed=True,
                message="No scripts directory"
            )
        
        issues = []
        for script in scripts_dir.rglob('*'):
            if script.is_file() and script.suffix in ['.py', '.sh', '.js']:
                content = script.read_text(encoding='utf-8', errors='ignore')
                if not content.startswith('#!'):
                    issues.append(f"Missing shebang: {script.name}")
        
        return TestResult(
            name="scripts_shebang",
            passed=len(issues) == 0,
            message="; ".join(issues) if issues else "All scripts have shebangs"
        )
    
    def test_references_naming(self) -> TestResult:
        """Test references are properly named"""
        refs_dir = self.skill_path / 'references'
        
        if not refs_dir.exists():
            return TestResult(
                name="references_naming",
                passed=True,
                message="No references directory"
            )
        
        issues = []
        for ref in refs_dir.rglob('*'):
            if ref.is_file():
                # Check kebab-case naming
                if not re.match(r'^[a-z0-9][a-z0-9-]*\.[a-z]+$', ref.name):
                    if ref.name != 'README.md':  # Allow README in subdirs
                        issues.append(f"Non-kebab-case name: {ref.name}")
        
        return TestResult(
            name="references_naming",
            passed=len(issues) == 0,
            message="; ".join(issues) if issues else "Reference naming is valid"
        )


def print_report(result: TestSuiteResult) -> None:
    """Print test report"""
    status = "✅ PASSED" if result.passed else "❌ FAILED"
    print("=" * 60)
    print(f"TEST REPORT: {result.skill_name} - {status}")
    print("=" * 60)
    
    for test in result.tests:
        icon = "✅" if test.passed else "❌"
        print(f"{icon} {test.name}: {test.message}")
    
    if result.errors:
        print("\n⚠️  Errors:")
        for error in result.errors:
            print(f"   - {error}")
    
    passed = sum(1 for t in result.tests if t.passed)
    total = len(result.tests)
    print(f"\n📊 Score: {passed}/{total} tests passed")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Run tests against skills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a single skill
  python test_runner.py ./my-skill

  # Test all skills in directory
  python test_runner.py ./skills --scan

  # JSON output
  python test_runner.py ./my-skill --json
"""
    )
    
    parser.add_argument('path', nargs='?', default='.', help='Path to skill or skills directory')
    parser.add_argument('--scan', '-s', action='store_true', help='Scan directory for all skills')
    parser.add_argument('--json', '-j', action='store_true', help='Output JSON format')
    parser.add_argument('--output', '-o', type=Path, help='Write output to file')
    
    args = parser.parse_args()
    
    skill_path = Path(args.path)
    
    if args.scan and skill_path.is_dir():
        results = []
        for item in skill_path.iterdir():
            if item.is_dir() and (item / 'SKILL.md').exists():
                runner = SkillTestRunner(item)
                result = runner.run_all_tests()
                results.append(result)
                if not args.json:
                    print_report(result)
        
        if args.json:
            output_data = {
                'total': len(results),
                'passed': sum(1 for r in results if r.passed),
                'failed': sum(1 for r in results if not r.passed),
                'results': [
                    {
                        'skill_name': r.skill_name,
                        'passed': r.passed,
                        'tests': [{'name': t.name, 'passed': t.passed, 'message': t.message} for t in r.tests]
                    } for r in results
                ]
            }
            output = json.dumps(output_data, indent=2)
            if args.output:
                args.output.write_text(output, encoding='utf-8')
                print(f"✅ Written to {args.output}")
            else:
                print(output)
    else:
        if not (skill_path / 'SKILL.md').exists():
            print(f"❌ SKILL.md not found in {skill_path}")
            sys.exit(1)
        
        runner = SkillTestRunner(skill_path)
        result = runner.run_all_tests()
        
        if args.json:
            output_data = {
                'skill_name': result.skill_name,
                'passed': result.passed,
                'tests': [{'name': t.name, 'passed': t.passed, 'message': t.message} for t in result.tests],
                'errors': result.errors
            }
            output = json.dumps(output_data, indent=2)
            if args.output:
                args.output.write_text(output, encoding='utf-8')
                print(f"✅ Written to {args.output}")
            else:
                print(output)
        else:
            print_report(result)


if __name__ == '__main__':
    main()
