#!/usr/bin/env python3
"""
Skill Check 配置管理
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


DEFAULT_CONFIG = {
    'allowed_frontmatter_fields': [
        'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'
    ],
    'forbidden_files': [
        'README.md', 'CHANGELOG.md', 'INSTALLATION_GUIDE.md', 'QUICK_REFERENCE.md',
        'TODO.md', 'NOTES.md', 'HISTORY.md', 'CONTRIBUTING.md'
    ],
    'allowed_dirs': ['scripts', 'references', 'assets'],
    'ignored_dirs': [
        '.git', '__pycache__', '.pytest_cache', '.tox', 'node_modules',
        '.venv', 'venv', 'env', 'skill_check'
    ],
    'rules': {
        'max_name_length': 64,
        'min_description_length': 20,
        'max_description_length': 1024,
        'max_body_lines': 500,
        'max_body_tokens': 5000,
        'max_reference_lines': 200,
        'large_file_threshold_mb': 5
    },
    'trigger_words': [
        'when', 'use', 'if', 'need', 'ask', 'want', 'handle', 'work with',
        '使用', '用于', '适用于', '场景', '触发'
    ]
}


@dataclass
class Config:
    allowed_frontmatter_fields: List[str] = field(default_factory=lambda: DEFAULT_CONFIG['allowed_frontmatter_fields'])
    forbidden_files: List[str] = field(default_factory=lambda: DEFAULT_CONFIG['forbidden_files'])
    allowed_dirs: List[str] = field(default_factory=lambda: DEFAULT_CONFIG['allowed_dirs'])
    ignored_dirs: List[str] = field(default_factory=lambda: DEFAULT_CONFIG['ignored_dirs'])
    rules: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG['rules'])
    trigger_words: List[str] = field(default_factory=lambda: DEFAULT_CONFIG['trigger_words'])

    @classmethod
    def from_dict(cls, data: Dict) -> 'Config':
        allowed_fields = data.get('allowed_frontmatter_fields', DEFAULT_CONFIG['allowed_frontmatter_fields'])
        forbidden = data.get('forbidden_files', DEFAULT_CONFIG['forbidden_files'])
        allowed_dirs = data.get('allowed_dirs', DEFAULT_CONFIG['allowed_dirs'])
        ignored = data.get('ignored_dirs', DEFAULT_CONFIG['ignored_dirs'])
        rules = {**DEFAULT_CONFIG['rules'], **data.get('rules', {})}
        triggers = data.get('trigger_words', DEFAULT_CONFIG['trigger_words'])
        
        return cls(
            allowed_frontmatter_fields=allowed_fields,
            forbidden_files=forbidden,
            allowed_dirs=allowed_dirs,
            ignored_dirs=ignored,
            rules=rules,
            trigger_words=triggers
        )


def load_config(config_path: Optional[Path] = None) -> Config:
    """加载配置文件"""
    search_paths = []
    
    if config_path:
        search_paths.append(Path(config_path))
    
    script_dir = Path(__file__).parent
    search_paths.append(script_dir / 'config.yaml')
    
    home_config = Path.home() / '.skill-check' / 'config.yaml'
    search_paths.append(home_config)
    
    current_dir = Path.cwd() / '.skill-check.yaml'
    search_paths.append(current_dir)
    
    for path in search_paths:
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                if data:
                    return Config.from_dict(data)
            except Exception:
                pass
    
    return Config()


def merge_config(base: Config, override: Dict) -> Config:
    """合并配置"""
    data = {
        'allowed_frontmatter_fields': override.get('allowed_frontmatter_fields', base.allowed_frontmatter_fields),
        'forbidden_files': override.get('forbidden_files', base.forbidden_files),
        'allowed_dirs': override.get('allowed_dirs', base.allowed_dirs),
        'ignored_dirs': override.get('ignored_dirs', base.ignored_dirs),
        'rules': {**base.rules, **override.get('rules', {})},
        'trigger_words': override.get('trigger_words', base.trigger_words)
    }
    return Config.from_dict(data)