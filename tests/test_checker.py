#!/usr/bin/env python3
"""
Skill Check 测试用例
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))

from skill_check.checker import check_skill, scan_directory, get_config, set_config
from skill_check.config import load_config, Config

os.environ['PYTHONIOENCODING'] = 'utf-8'


def create_temp_skill(name: str, content: str = None, extra_files: dict = None) -> Path:
    """创建临时 skill 目录"""
    temp_dir = Path(tempfile.mkdtemp())
    skill_dir = temp_dir / name
    skill_dir.mkdir()
    
    default_content = """---
name: {name}
description: 这是一个测试技能。用于测试检查功能。使用本工具来验证skill是否符合规范。
---

# Test Skill

这是测试内容。

## 使用方法

1. 步骤一
2. 步骤二
""".format(name=name)
    
    (skill_dir / "SKILL.md").write_text(content or default_content, encoding='utf-8')
    
    if extra_files:
        for file_path, file_content in extra_files.items():
            full_path = skill_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(file_content, encoding='utf-8')
    
    return skill_dir


def test_valid_skill():
    """测试有效的 skill"""
    skill_dir = create_temp_skill("test-valid")
    try:
        result = check_skill(skill_dir)
        print(f"✅ test_valid_skill: Score={result.score}, Passed={result.passed}")
        assert result.passed, f"Expected passed=True, got {result.passed}"
        assert result.score >= 90, f"Expected score >= 90, got {result.score}"
    finally:
        shutil.rmtree(skill_dir.parent)


def test_missing_skill_md():
    """测试缺少 SKILL.md"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        (temp_dir / "test-no-md").mkdir()
        result = check_skill(temp_dir / "test-no-md")
        print(f"✅ test_missing_skill_md: Score={result.score}, Passed={result.passed}")
        assert not result.passed, f"Expected passed=False"
        assert any("SKILL.md not found" in i.message for i in result.issues), "Should report missing SKILL.md"
    finally:
        shutil.rmtree(temp_dir)


def test_forbidden_file():
    """测试禁止文件"""
    skill_dir = create_temp_skill("test-forbidden")
    try:
        (skill_dir / "README.md").write_text("# README", encoding='utf-8')
        result = check_skill(skill_dir)
        print(f"✅ test_forbidden_file: Score={result.score}")
        assert not result.passed, f"Expected passed=False"
        assert any("Forbidden file" in i.message for i in result.issues), "Should report forbidden file"
    finally:
        shutil.rmtree(skill_dir.parent)


def test_name_validation():
    """测试名称验证"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        invalid_dir = temp_dir / "Test-UPPER"
        invalid_dir.mkdir()
        (invalid_dir / "SKILL.md").write_text("""---
name: Test-UPPER
description: 测试
---
""", encoding='utf-8')
        
        result = check_skill(invalid_dir)
        print(f"✅ test_name_validation: Score={result.score}")
        assert not result.passed, "Should fail for uppercase name"
    finally:
        shutil.rmtree(temp_dir)


def test_description_length():
    """测试描述长度"""
    skill_dir = create_temp_skill("test-desc")
    try:
        (skill_dir / "SKILL.md").write_text("""---
name: test-desc
description: 短
---
""", encoding='utf-8')
        
        result = check_skill(skill_dir)
        print(f"✅ test_description_length: Score={result.score}")
        assert any("too short" in i.message.lower() for i in result.issues), "Should warn about short description"
    finally:
        shutil.rmtree(skill_dir.parent)


def test_auto_fix():
    """测试自动修复"""
    skill_dir = create_temp_skill("test-fix")
    try:
        (skill_dir / "README.md").write_text("# README", encoding='utf-8')
        
        result = check_skill(skill_dir, auto_fix=True)
        print(f"✅ test_auto_fix: Score={result.score}")
        
        assert not (skill_dir / "README.md").exists(), "README.md should be removed"
    finally:
        shutil.rmtree(skill_dir.parent)


def test_config_loading():
    """测试配置加载"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        config_file = temp_dir / "custom.md"
        config_file.write_text("""---
rules:
  max_body_lines: 100
---
""", encoding='utf-8')
        
        cfg = load_config(config_file)
        print(f"✅ test_config_loading: max_body_lines={cfg.rules['max_body_lines']}")
        assert cfg.rules['max_body_lines'] == 100, "Should load custom config"
    finally:
        shutil.rmtree(temp_dir)


def test_concurrent_scan():
    """测试并发扫描"""
    temp_base = Path(tempfile.mkdtemp())
    try:
        for i in range(3):
            skill_dir = temp_base / f"skill-{i}"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"""---
name: skill-{i}
description: 测试技能{i}。用于测试。
---

# Test
""", encoding='utf-8')
        
        results = scan_directory(temp_base, concurrent=True, max_workers=2)
        print(f"✅ test_concurrent_scan: Scanned {len(results)} skills")
        assert len(results) == 3, f"Should scan 3 skills, got {len(results)}"
    finally:
        shutil.rmtree(temp_base)


def test_markdown_config():
    """测试 Markdown 配置"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        config_file = temp_dir / "test.md"
        config_file.write_text("""---
allowed_frontmatter_fields:
  - name
  - description
  - custom-field
rules:
  max_name_length: 32
---
""", encoding='utf-8')
        
        cfg = load_config(config_file)
        print(f"✅ test_markdown_config: max_name_length={cfg.rules['max_name_length']}")
        assert cfg.rules['max_name_length'] == 32, "Should load markdown config"
        assert "custom-field" in cfg.allowed_frontmatter_fields, "Should have custom field"
    finally:
        shutil.rmtree(temp_dir)


def test_yaml_config():
    """测试 YAML 配置"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        config_file = temp_dir / "test.yaml"
        config_file.write_text("""rules:
  max_body_lines: 200
trigger_words:
  - custom-trigger
""", encoding='utf-8')
        
        cfg = load_config(config_file)
        print(f"✅ test_yaml_config: max_body_lines={cfg.rules['max_body_lines']}")
        assert cfg.rules['max_body_lines'] == 200, "Should load yaml config"
    finally:
        shutil.rmtree(temp_dir)


def main():
    print("=" * 50)
    print("Skill Check 测试用例")
    print("=" * 50)
    
    tests = [
        test_valid_skill,
        test_missing_skill_md,
        test_forbidden_file,
        test_name_validation,
        test_description_length,
        test_auto_fix,
        test_config_loading,
        test_concurrent_scan,
        test_markdown_config,
        test_yaml_config,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print("=" * 50)
    print(f"结果: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())