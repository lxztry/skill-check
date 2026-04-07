#!/usr/bin/env python3
"""
Skill Migrator - Migrate skills between specification versions
"""

import os
import sys
import re
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add parent directory to path
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))


@dataclass
class MigrationRule:
    """A single migration rule"""
    description: str
    transform: str  # 'add', 'remove', 'rename', 'modify'
    field: str
    old_value: any = None
    new_value: any = None


# Migration paths
MIGRATIONS: Dict[str, Dict[str, List[MigrationRule]]] = {
    ('v1', 'v2'): [
        MigrationRule(
            description="Add compatibility field if missing",
            transform='add',
            field='compatibility',
            new_value=['Python 3.8+']
        ),
        MigrationRule(
            description="Ensure metadata is lowercase",
            transform='modify',
            field='name',
            old_value=None,
            new_value=None
        ),
    ],
}


class SkillMigrator:
    """Migrate skills between versions"""
    
    FRONTMATTER_PATTERN = re.compile(r'^---\n(.*?)\n---', re.DOTALL)
    YAML_BLOCK_PATTERN = re.compile(r'```yaml\n(.*?)\n```', re.DOTALL)
    
    def __init__(self, skill_path: Path, dry_run: bool = True):
        self.skill_path = Path(skill_path)
        self.dry_run = dry_run
        self.skill_md = self.skill_path / 'SKILL.md'
        self.changes: List[str] = []
        self.errors: List[str] = []
    
    def load_frontmatter(self) -> Optional[Dict]:
        """Parse frontmatter from SKILL.md"""
        if not self.skill_md.exists():
            self.errors.append(f"SKILL.md not found in {self.skill_path}")
            return None
        
        content = self.skill_md.read_text(encoding='utf-8')
        match = self.FRONTMATTER_PATTERN.search(content)
        
        if not match:
            self.errors.append("No frontmatter found")
            return {}
        
        import yaml
        try:
            data = yaml.safe_load(match.group(1))
            return data if data else {}
        except yaml.YAMLError as e:
            self.errors.append(f"YAML parse error: {e}")
            return None
    
    def save_frontmatter(self, data: Dict, content: str) -> str:
        """Update frontmatter in content"""
        import yaml
        
        new_frontmatter = yaml.dump(data, allow_unicode=True, sort_keys=False)
        new_frontmatter = new_frontmatter.rstrip() + '\n'
        
        def replace(match):
            return f"---\n{new_frontmatter}---"
        
        return self.FRONTMATTER_PATTERN.sub(replace, content)
    
    def validate_name(self, name: str) -> Tuple[bool, Optional[str]]:
        """Validate skill name"""
        pattern = re.compile(r'^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$|^[a-z0-9]$')
        
        if not pattern.match(name):
            return False, f"Invalid name format: {name}"
        if name.startswith('-') or name.endswith('-'):
            return False, f"Name cannot start/end with hyphen: {name}"
        if '--' in name:
            return False, f"Name cannot have consecutive hyphens: {name}"
        
        return True, None
    
    def migrate_v1_to_v2(self) -> bool:
        """Migrate from v1 to v2 specification"""
        data = self.load_frontmatter()
        if data is None:
            return False
        
        original_data = dict(data)
        
        # Rule 1: Add compatibility if missing
        if 'compatibility' not in data:
            data['compatibility'] = ['Python 3.8+']
            self.changes.append("Added 'compatibility' field with default value ['Python 3.8+']")
        
        # Rule 2: Validate and fix name
        if 'name' in data:
            name = data['name']
            valid, error = self.validate_name(name)
            if not valid:
                # Try to fix common issues
                fixed = name.lower().replace('_', '-')
                if fixed != name:
                    self.changes.append(f"Renamed skill from '{name}' to '{fixed}'")
                    data['name'] = fixed
                    name = fixed
                
                # Remove leading/trailing hyphens
                fixed = name.strip('-')
                if fixed != name:
                    self.changes.append(f"Fixed name: '{name}' -> '{fixed}'")
                    data['name'] = fixed
        
        # Rule 3: Ensure description exists and is proper length
        if 'description' not in data:
            self.errors.append("Missing required 'description' field")
        elif len(data['description']) < 20:
            self.errors.append(f"Description too short: {len(data['description'])} chars")
        elif len(data['description']) > 1024:
            self.changes.append(f"Description truncated from {len(data['description'])} to 1024 chars")
            data['description'] = data['description'][:1024]
        
        # Rule 4: Remove forbidden fields
        forbidden = ['version', 'author', 'tags', 'categories']
        for field in forbidden:
            if field in data:
                self.changes.append(f"Removed forbidden field '{field}'")
                del data[field]
        
        # Rule 5: Check for common issues in description
        if 'description' in data:
            desc = data['description']
            # Remove HTML tags if present
            if '<' in desc and '>' in desc:
                clean = re.sub(r'<[^>]+>', '', desc)
                if clean != desc:
                    self.changes.append("Removed HTML tags from description")
                    data['description'] = clean
        
        # Apply changes if not dry run
        if self.changes and not self.dry_run:
            content = self.skill_md.read_text(encoding='utf-8')
            new_content = self.save_frontmatter(data, content)
            self.skill_md.write_text(new_content, encoding='utf-8')
        
        return len(self.errors) == 0
    
    def migrate(self, from_version: str, to_version: str) -> bool:
        """Run migration between versions"""
        migration_key = (from_version.lower(), to_version.lower())
        
        if migration_key not in MIGRATIONS:
            self.errors.append(f"Migration {from_version} -> {to_version} not supported")
            return False
        
        if from_version == 'v1' and to_version == 'v2':
            return self.migrate_v1_to_v2()
        
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Migrate skills between specification versions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run migration from v1 to v2
  python migrate.py ./my-skill --from v1 --to v2

  # Apply migration
  python migrate.py ./my-skill --from v1 --to v2 --apply

  # Migrate all skills in directory
  python migrate.py ./skills --from v1 --to v2 --scan --apply

  # Show detailed changes
  python migrate.py ./my-skill --from v1 --to v2 --verbose
"""
    )
    
    parser.add_argument('path', help='Path to skill or skills directory')
    parser.add_argument('--from', dest='from_version', required=True,
                        help='Source version (e.g., v1)')
    parser.add_argument('--to', dest='to_version', required=True,
                        help='Target version (e.g., v2)')
    parser.add_argument('--apply', action='store_true',
                        help='Apply changes (default is dry-run)')
    parser.add_argument('--scan', action='store_true',
                        help='Scan directory for all skills')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed output')
    
    args = parser.parse_args()
    
    skill_path = Path(args.path)
    
    def process_skill(path: Path) -> None:
        migrator = SkillMigrator(path, dry_run=not args.apply)
        success = migrator.migrate(args.from_version, args.to_version)
        
        status = "✅" if success else "❌"
        print(f"{status} {path.name}")
        
        if migrator.changes:
            for change in migrator.changes:
                prefix = "  →" if not args.verbose else "  📝"
                print(f"{prefix} {change}")
        
        if migrator.errors:
            for error in migrator.errors:
                print(f"  ⚠️  {error}")
        
        return success
    
    if args.scan:
        if not skill_path.is_dir():
            print(f"❌ Not a directory: {skill_path}")
            sys.exit(1)
        
        print(f"🔍 Scanning {skill_path} for skills...")
        results = []
        for item in skill_path.iterdir():
            if item.is_dir() and (item / 'SKILL.md').exists():
                result = process_skill(item)
                results.append((item.name, result))
                print()
        
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        passed = sum(1 for _, r in results if r)
        failed = sum(1 for _, r in results if not r)
        print(f"  Total: {len(results)}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        
        if args.apply:
            print("\n✅ Migration applied (dry-run mode disabled)")
        else:
            print("\n📝 This was a dry run. Use --apply to apply changes.")
    else:
        if not skill_path.is_dir():
            print(f"❌ Not a directory: {skill_path}")
            sys.exit(1)
        
        if not (skill_path / 'SKILL.md').exists():
            print(f"❌ No SKILL.md found in {skill_path}")
            sys.exit(1)
        
        print(f"🔄 Migrating {skill_path.name}: {args.from_version} -> {args.to_version}")
        if not args.apply:
            print("📝 Dry run mode (use --apply to apply changes)")
        print()
        
        success = process_skill(skill_path)
        
        if args.apply and success:
            print("\n✅ Migration applied successfully")
        elif not args.apply:
            print("\n📝 This was a dry run. Use --apply to apply changes.")


if __name__ == '__main__':
    main()
