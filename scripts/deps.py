#!/usr/bin/env python3
"""
Skill Dependency Analyzer - Analyze skill dependencies and relationships
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

# Add parent directory to path
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))


@dataclass
class SkillReference:
    """A reference from one skill to another"""
    from_skill: str
    to_skill: str
    reference_type: str  # 'script', 'reference', 'asset'
    file_path: str
    line_number: int = 0


@dataclass
class DependencyGraph:
    """Complete dependency graph for skills"""
    skills: Dict[str, Dict] = field(default_factory=dict)
    references: List[SkillReference] = field(default_factory=list)
    circular_deps: List[List[str]] = field(default_factory=list)
    isolated_skills: List[str] = field(default_factory=list)
    orphaned_refs: List[SkillReference] = field(default_factory=list)


class DependencyAnalyzer:
    """Analyze skill dependencies"""
    
    # Patterns to detect skill references
    REFERENCE_PATTERNS = [
        re.compile(r'skills?[/\\]([a-z0-9-]+)', re.IGNORECASE),
        re.compile(r'from\s+[\'"](\.\./)?([a-z0-9-]+)', re.IGNORECASE),
        re.compile(r'references?[/\\]([a-z0-9-]+)', re.IGNORECASE),
        re.compile(r'scripts?[/\\]([a-z0-9-]+)', re.IGNORECASE),
        re.compile(r'assets?[/\\]([a-z0-9-]+)', re.IGNORECASE),
    ]
    
    def __init__(self, skills_dir: Path):
        self.skills_dir = Path(skills_dir)
        self.graph = DependencyGraph()
    
    def scan_skills(self) -> None:
        """Scan all skills in directory"""
        if not self.skills_dir.exists():
            return
        
        for item in self.skills_dir.iterdir():
            if item.is_dir() and (item / 'SKILL.md').exists():
                skill_name = item.name
                self.graph.skills[skill_name] = {
                    'path': str(item),
                    'has_scripts': (item / 'scripts').exists() and any((item / 'scripts').iterdir()),
                    'has_references': (item / 'references').exists() and any((item / 'references').iterdir()),
                    'has_assets': (item / 'assets').exists() and any((item / 'assets').iterdir()),
                    'file_count': sum(1 for _ in item.rglob('*') if _.is_file()),
                }
    
    def analyze_references(self) -> None:
        """Find all cross-skill references"""
        for skill_name, skill_info in self.graph.skills.items():
            skill_path = Path(skill_info['path'])
            
            # Scan all files in skill
            for file_path in skill_path.rglob('*'):
                if not file_path.is_file():
                    continue
                
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = content.split('\n')
                except Exception:
                    continue
                
                for line_num, line in enumerate(lines, 1):
                    for pattern in self.REFERENCE_PATTERNS:
                        for match in pattern.finditer(line):
                            ref_name = match.group(1).lower()
                            if ref_name in self.graph.skills and ref_name != skill_name:
                                # Determine reference type
                                file_rel = file_path.relative_to(skill_path)
                                if str(file_rel).startswith('scripts'):
                                    ref_type = 'script'
                                elif str(file_rel).startswith('references'):
                                    ref_type = 'reference'
                                elif str(file_rel).startswith('assets'):
                                    ref_type = 'asset'
                                else:
                                    ref_type = 'other'
                                
                                self.graph.references.append(SkillReference(
                                    from_skill=skill_name,
                                    to_skill=ref_name,
                                    reference_type=ref_type,
                                    file_path=str(file_rel),
                                    line_number=line_num
                                ))
    
    def find_circular_dependencies(self) -> None:
        """Detect circular dependencies using DFS"""
        visited = set()
        rec_stack = []
        cycles = []
        
        def dfs(skill: str, path: List[str]) -> None:
            visited.add(skill)
            rec_stack.append(skill)
            
            # Find outgoing references
            outgoing = [r.to_skill for r in self.graph.references if r.from_skill == skill]
            
            for next_skill in outgoing:
                if next_skill not in visited:
                    dfs(next_skill, path + [skill])
                elif next_skill in rec_stack:
                    # Found cycle
                    cycle_start = rec_stack.index(next_skill)
                    cycle = rec_stack[cycle_start:] + [next_skill]
                    cycles.append(cycle)
            
            rec_stack.pop()
        
        for skill in self.graph.skills:
            if skill not in visited:
                dfs(skill, [])
        
        self.graph.circular_deps = cycles
    
    def find_isolated_skills(self) -> None:
        """Find skills with no references (neither incoming nor outgoing)"""
        all_referenced = set()
        all_referencing = set()
        
        for ref in self.graph.references:
            all_referenced.add(ref.to_skill)
            all_referencing.add(ref.from_skill)
        
        # Isolated = not referenced by anyone and doesn't reference anyone
        self.graph.isolated_skills = [
            s for s in self.graph.skills
            if s not in all_referenced and s not in all_referencing
        ]
    
    def analyze(self) -> DependencyGraph:
        """Run full analysis"""
        self.scan_skills()
        self.analyze_references()
        self.find_circular_dependencies()
        self.find_isolated_skills()
        return self.graph
    
    def to_dict(self) -> Dict:
        """Convert graph to serializable dict"""
        return {
            'generated': datetime.now().isoformat(),
            'skills_dir': str(self.skills_dir),
            'skills': self.graph.skills,
            'references': [asdict(r) for r in self.graph.references],
            'circular_dependencies': self.graph.circular_deps,
            'isolated_skills': self.graph.isolated_skills,
            'stats': {
                'total_skills': len(self.graph.skills),
                'total_references': len(self.graph.references),
                'circular_count': len(self.graph.circular_deps),
                'isolated_count': len(self.graph.isolated_skills),
            }
        }


def print_report(graph: DependencyGraph) -> None:
    """Print human-readable report"""
    print("=" * 60)
    print("SKILL DEPENDENCY REPORT")
    print("=" * 60)
    
    print(f"\n📊 Statistics:")
    print(f"   Total Skills: {len(graph.skills)}")
    print(f"   Total References: {len(graph.references)}")
    print(f"   Circular Dependencies: {len(graph.circular_deps)}")
    print(f"   Isolated Skills: {len(graph.isolated_skills)}")
    
    if graph.circular_deps:
        print(f"\n⚠️  CIRCULAR DEPENDENCIES DETECTED:")
        for cycle in graph.circular_deps:
            print(f"   {' -> '.join(cycle)}")
    
    if graph.isolated_skills:
        print(f"\n📌 Isolated Skills (no dependencies):")
        for skill in sorted(graph.isolated_skills):
            print(f"   - {skill}")
    
    if graph.references:
        print(f"\n🔗 Dependencies (top 20):")
        shown = 0
        for ref in sorted(graph.references, key=lambda r: (r.from_skill, r.to_skill)):
            if shown >= 20:
                print(f"   ... and {len(graph.references) - 20} more")
                break
            print(f"   {ref.from_skill} -> {ref.to_skill} ({ref.reference_type})")
            shown += 1
    
    print()


def generate_dot(graph: DependencyGraph) -> str:
    """Generate DOT format for Graphviz"""
    lines = [
        "digraph skills {",
        "  rankdir=LR;",
        "  node [shape=box];",
        ""
    ]
    
    for skill in sorted(graph.skills.keys()):
        lines.append(f'  "{skill}" [label="{skill}"];')
    
    lines.append("")
    
    for ref in graph.references:
        style = "solid"
        if ref.reference_type == 'script':
            style = "dashed"
        elif ref.reference_type == 'reference':
            style = "dotted"
        lines.append(f'  "{ref.from_skill}" -> "{ref.to_skill}" [style={style}];')
    
    lines.append("}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze skill dependencies and relationships',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze skills in current directory
  python deps.py ./skills

  # Generate JSON output
  python deps.py ./skills --json

  # Generate Graphviz DOT file
  python deps.py ./skills --dot > dependencies.dot

  # Output file
  python deps.py ./skills -o dependency-report.json
"""
    )
    
    parser.add_argument('path', nargs='?', default='.',
                        help='Path to skills directory (default: current directory)')
    parser.add_argument('--json', '-j', action='store_true',
                        help='Output JSON format')
    parser.add_argument('--dot', '-d', action='store_true',
                        help='Output DOT format for Graphviz')
    parser.add_argument('--output', '-o', type=Path,
                        help='Write output to file')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress non-JSON output')
    
    args = parser.parse_args()
    
    # Find skills directory
    skills_path = Path(args.path)
    if not skills_path.exists():
        # Try to find skills directory
        if (Path.cwd() / 'skills').exists():
            skills_path = Path.cwd() / 'skills'
        elif (Path.cwd().parent / 'skills').exists():
            skills_path = Path.cwd().parent / 'skills'
        else:
            print(f"❌ Directory not found: {args.path}")
            sys.exit(1)
    
    analyzer = DependencyAnalyzer(skills_path)
    graph = analyzer.analyze()
    
    if args.json:
        output = json.dumps(analyzer.to_dict(), indent=2)
        if args.output:
            args.output.write_text(output, encoding='utf-8')
            print(f"✅ Written to {args.output}")
        else:
            print(output)
    elif args.dot:
        output = generate_dot(graph)
        if args.output:
            args.output.write_text(output, encoding='utf-8')
            print(f"✅ Written to {args.output}")
        else:
            print(output)
    else:
        if not args.quiet:
            print_report(graph)
        
        if args.output:
            output = json.dumps(analyzer.to_dict(), indent=2)
            args.output.write_text(output, encoding='utf-8')
            print(f"✅ Report written to {args.output}")


if __name__ == '__main__':
    main()
