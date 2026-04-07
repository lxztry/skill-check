#!/usr/bin/env python3
"""
Skill Scaffold - Create new skills from templates
"""

import os
import sys
import argparse
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Add parent directory to path
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))


TEMPLATES_DIR = script_dir / "templates"

TEMPLATE_MAP = {
    "basic": "basic",
    "api-integration": "api-integration",
    "web-automation": "web-automation",
    "file-processing": "file-processing",
}

VALID_NAME_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$|^[a-z0-9]$')


def validate_name(name: str) -> tuple[bool, Optional[str]]:
    """Validate skill name according to naming conventions"""
    if not name:
        return False, "Name cannot be empty"
    
    if len(name) > 64:
        return False, f"Name too long: {len(name)} chars (max 64)"
    
    if not VALID_NAME_PATTERN.match(name):
        if '-' in name and '--' not in name:
            return True, None  # hyphen-case is valid
        return False, "Name must be lowercase letters, numbers, and hyphens only (hyphen-case)"
    
    if name.startswith('-') or name.endswith('-'):
        return False, "Name cannot start or end with hyphen"
    
    return True, None


def list_templates() -> List[str]:
    """List available templates"""
    templates = []
    if TEMPLATES_DIR.exists():
        for item in TEMPLATES_DIR.iterdir():
            if item.is_dir():
                templates.append(item.name)
    return templates


def copy_template_dir(src: Path, dst: Path, skill_name: str) -> List[str]:
    """Copy template directory, replacing placeholders"""
    copied_files = []
    
    for item in src.rglob('*'):
        if item.is_file():
            rel_path = item.relative_to(src)
            dest_path = dst / rel_path
            
            # Create parent directories
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read and substitute placeholders
            content = item.read_text(encoding='utf-8')
            content = content.replace('{{SKILL_NAME}}', skill_name)
            content = content.replace('{{DATE}}', datetime.now().strftime('%Y-%m-%d'))
            
            # Write file
            dest_path.write_text(content, encoding='utf-8')
            copied_files.append(str(rel_path))
    
    return copied_files


def create_skill(skill_name: str, template: str, output_dir: Path, force: bool = False) -> bool:
    """Create a new skill from template"""
    # Validate name
    valid, error = validate_name(skill_name)
    if not valid:
        print(f"❌ Invalid skill name: {error}")
        return False
    
    # Check template exists
    template_path = TEMPLATES_DIR / template
    if not template_path.exists():
        print(f"❌ Template not found: {template}")
        print(f"   Available templates: {', '.join(list_templates())}")
        return False
    
    # Check output directory
    skill_dir = output_dir / skill_name
    if skill_dir.exists() and not force:
        print(f"❌ Skill already exists: {skill_dir}")
        print(f"   Use --force to overwrite")
        return False
    
    # Create skill directory
    skill_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy template files
    copied_files = copy_template_dir(template_path, skill_dir, skill_name)
    
    print(f"✅ Created skill: {skill_name}")
    print(f"   Template: {template}")
    print(f"   Location: {skill_dir}")
    print(f"\n📁 Files created:")
    for f in sorted(copied_files):
        print(f"   - {f}")
    
    print(f"\n📝 Next steps:")
    print(f"   1. cd {skill_dir}")
    print(f"   2. Edit SKILL.md with your skill description")
    print(f"   3. Customize scripts/ and references/ as needed")
    print(f"   4. Run: python {script_dir}/scripts/skill_check.py {skill_dir}")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Create new skills from templates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a basic skill
  python create.py my-skill

  # Create from specific template
  python create.py my-api-skill --template api-integration

  # Create in custom directory
  python create.py my-skill --output ./my-skills

  # List available templates
  python create.py --list-templates

Template types:
  basic            - Minimal skill structure
  api-integration  - For API calling skills
  web-automation   - For browser automation skills
  file-processing  - For file processing skills
"""
    )
    
    parser.add_argument('name', nargs='?', help='Skill name (hyphen-case, e.g., my-skill)')
    parser.add_argument('--template', '-t', default='basic',
                        help='Template to use (default: basic)')
    parser.add_argument('--output', '-o', type=Path, default=Path.cwd(),
                        help='Output directory (default: current directory)')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Overwrite if skill exists')
    parser.add_argument('--list-templates', '-l', action='store_true',
                        help='List available templates')
    
    args = parser.parse_args()
    
    if args.list_templates:
        templates = list_templates()
        print("📦 Available templates:")
        for t in sorted(templates):
            desc = TEMPLATE_MAP.get(t, t)
            print(f"   - {t}")
        return
    
    if not args.name:
        parser.print_help()
        return
    
    success = create_skill(args.name, args.template, args.output, args.force)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
