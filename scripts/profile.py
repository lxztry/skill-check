#!/usr/bin/env python3
"""
Skill Profiler - Analyze skill performance and complexity
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Add parent directory to path
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir))


@dataclass
class PerformanceMetrics:
    """Performance metrics for a skill"""
    skill_name: str
    skill_path: str
    
    # Size metrics
    total_files: int = 0
    total_lines: int = 0
    total_chars: int = 0
    total_size_bytes: int = 0
    
    # SKILL.md specific
    skill_md_lines: int = 0
    skill_md_chars: int = 0
    skill_md_tokens_est: int = 0  # rough estimate
    
    # Structure metrics
    has_scripts: bool = False
    has_references: bool = False
    has_assets: bool = False
    scripts_count: int = 0
    references_count: int = 0
    assets_count: int = 0
    
    # Complexity indicators
    complexity_score: float = 0.0
    complexity_grade: str = ""
    load_time_estimate_ms: float = 0.0
    
    # Issues
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class SkillProfiler:
    """Profile skill performance and complexity"""
    
    # Token estimation: ~4 chars per token for English, ~2 for Chinese
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 2 + other_chars / 4)
    
    def profile_skill(self, skill_path: Path) -> PerformanceMetrics:
        """Profile a single skill"""
        skill_path = Path(skill_path)
        
        metrics = PerformanceMetrics(
            skill_name=skill_path.name,
            skill_path=str(skill_path)
        )
        
        if not (skill_path / 'SKILL.md').exists():
            metrics.issues.append("SKILL.md not found")
            return metrics
        
        # Profile SKILL.md
        skill_md = skill_path / 'SKILL.md'
        content = skill_md.read_text(encoding='utf-8')
        
        metrics.skill_md_lines = len(content.split('\n'))
        metrics.skill_md_chars = len(content)
        metrics.skill_md_tokens_est = self.estimate_tokens(content)
        
        # Profile all files
        for file_path in skill_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Skip hidden and cache directories
            if any(p.startswith('.') for p in file_path.parts):
                continue
            
            try:
                size = file_path.stat().st_size
                file_content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                metrics.total_files += 1
                metrics.total_size_bytes += size
                metrics.total_lines += len(file_content.split('\n'))
                metrics.total_chars += len(file_content)
                
                # Count by type
                rel_path = file_path.relative_to(skill_path)
                if str(rel_path).startswith('scripts'):
                    metrics.scripts_count += 1
                elif str(rel_path).startswith('references'):
                    metrics.references_count += 1
                elif str(rel_path).startswith('assets'):
                    metrics.assets_count += 1
                    
            except Exception:
                pass
        
        metrics.has_scripts = metrics.scripts_count > 0
        metrics.has_references = metrics.references_count > 0
        metrics.has_assets = metrics.assets_count > 0
        
        # Calculate complexity
        self._calculate_complexity(metrics)
        
        return metrics
    
    def _calculate_complexity(self, m: PerformanceMetrics) -> None:
        """Calculate complexity score and grade"""
        score = 0.0
        
        # SKILL.md size factors
        if m.skill_md_tokens_est > 5000:
            score += 30
            m.issues.append(f"SKILL.md too large: ~{m.skill_md_tokens_est} tokens (recommended: <5000)")
            m.suggestions.append("Move detailed content to references/")
        elif m.skill_md_tokens_est > 3000:
            score += 15
            m.suggestions.append("Consider moving some content to references/")
        
        if m.skill_md_lines > 500:
            score += 20
            m.issues.append(f"SKILL.md too long: {m.skill_md_lines} lines (recommended: <500)")
        
        # File count factors
        if m.total_files > 20:
            score += 10
            m.suggestions.append("Consider consolidating files")
        
        # Missing structure
        if not m.has_scripts and not m.has_references:
            score += 5
            m.suggestions.append("Consider adding scripts/ or references/ for progressive disclosure")
        
        # Large single files in references
        refs_dir = Path(m.skill_path) / 'references'
        if refs_dir.exists():
            for ref_file in refs_dir.iterdir():
                if ref_file.is_file():
                    try:
                        lines = len(ref_file.read_text(encoding='utf-8', errors='ignore').split('\n'))
                        if lines > 200:
                            score += 5
                            m.suggestions.append(f"Large reference file: {ref_file.name} ({lines} lines)")
                    except Exception:
                        pass
        
        # Asset size
        assets_dir = Path(m.skill_path) / 'assets'
        if assets_dir.exists():
            for asset_file in assets_dir.rglob('*'):
                if asset_file.is_file():
                    size_mb = asset_file.stat().st_size / (1024 * 1024)
                    if size_mb > 5:
                        score += 10
                        m.issues.append(f"Large asset: {asset_file.name} ({size_mb:.1f}MB)")
        
        # Load time estimation (rough: ~1ms per 100 tokens + base 5ms)
        m.load_time_estimate_ms = 5 + (m.skill_md_tokens_est / 100)
        
        # Normalize score
        m.complexity_score = max(0, 100 - score)
        
        # Grade
        if m.complexity_score >= 90:
            m.complexity_grade = "A"
        elif m.complexity_score >= 70:
            m.complexity_grade = "B"
        elif m.complexity_score >= 50:
            m.complexity_grade = "C"
        else:
            m.complexity_grade = "D"
    
    def to_dict(self, m: PerformanceMetrics) -> Dict:
        """Convert metrics to dict"""
        return {
            'skill_name': m.skill_name,
            'skill_path': m.skill_path,
            'size': {
                'total_files': m.total_files,
                'total_lines': m.total_lines,
                'total_chars': m.total_chars,
                'total_size_bytes': m.total_size_bytes,
            },
            'skill_md': {
                'lines': m.skill_md_lines,
                'chars': m.skill_md_chars,
                'tokens_estimate': m.skill_md_tokens_est,
            },
            'structure': {
                'has_scripts': m.has_scripts,
                'has_references': m.has_references,
                'has_assets': m.has_assets,
                'scripts_count': m.scripts_count,
                'references_count': m.references_count,
                'assets_count': m.assets_count,
            },
            'performance': {
                'complexity_score': m.complexity_score,
                'complexity_grade': m.complexity_grade,
                'load_time_estimate_ms': m.load_time_estimate_ms,
            },
            'issues': m.issues,
            'suggestions': m.suggestions,
        }


def print_report(metrics: PerformanceMetrics) -> None:
    """Print human-readable report"""
    print("=" * 60)
    print(f"SKILL PROFILE: {metrics.skill_name}")
    print("=" * 60)
    
    print(f"\n📊 Complexity Grade: {metrics.complexity_grade} ({metrics.complexity_score:.0f}/100)")
    print(f"   Estimated Load Time: ~{metrics.load_time_estimate_ms:.0f}ms")
    
    print(f"\n📁 Structure:")
    print(f"   Total Files: {metrics.total_files}")
    print(f"   Total Lines: {metrics.total_lines:,}")
    print(f"   Scripts: {metrics.scripts_count} {'✓' if metrics.has_scripts else '✗'}")
    print(f"   References: {metrics.references_count} {'✓' if metrics.has_references else '✗'}")
    print(f"   Assets: {metrics.assets_count} {'✓' if metrics.has_assets else '✗'}")
    
    print(f"\n📝 SKILL.md:")
    print(f"   Lines: {metrics.skill_md_lines}")
    print(f"   Characters: {metrics.skill_md_chars:,}")
    print(f"   Estimated Tokens: ~{metrics.skill_md_tokens_est:,}")
    
    if metrics.issues:
        print(f"\n⚠️  Issues:")
        for issue in metrics.issues:
            print(f"   - {issue}")
    
    if metrics.suggestions:
        print(f"\n💡 Suggestions:")
        for suggestion in metrics.suggestions:
            print(f"   - {suggestion}")
    
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Analyze skill performance and complexity',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Profile a single skill
  python profile.py ./my-skill

  # Profile and save JSON
  python profile.py ./my-skill --json -o profile.json

  # Profile all skills in directory
  python profile.py ./skills --scan
"""
    )
    
    parser.add_argument('path', nargs='?', default='.',
                        help='Path to skill or skills directory')
    parser.add_argument('--scan', action='store_true',
                        help='Scan directory for all skills')
    parser.add_argument('--json', '-j', action='store_true',
                        help='Output JSON format')
    parser.add_argument('--output', '-o', type=Path,
                        help='Write output to file')
    
    args = parser.parse_args()
    
    profiler = SkillProfiler()
    skill_path = Path(args.path)
    
    if args.scan and skill_path.is_dir():
        results = []
        for item in skill_path.iterdir():
            if item.is_dir() and (item / 'SKILL.md').exists():
                metrics = profiler.profile_skill(item)
                results.append(metrics)
        
        if args.json:
            output_data = {
                'generated': datetime.now().isoformat(),
                'skills_dir': str(skill_path),
                'profiles': [profiler.to_dict(m) for m in results],
                'summary': {
                    'total': len(results),
                    'avg_complexity': sum(m.complexity_score for m in results) / len(results) if results else 0,
                    'grade_distribution': {
                        'A': sum(1 for m in results if m.complexity_grade == 'A'),
                        'B': sum(1 for m in results if m.complexity_grade == 'B'),
                        'C': sum(1 for m in results if m.complexity_grade == 'C'),
                        'D': sum(1 for m in results if m.complexity_grade == 'D'),
                    }
                }
            }
            output = json.dumps(output_data, indent=2)
            if args.output:
                args.output.write_text(output, encoding='utf-8')
                print(f"✅ Written to {args.output}")
            else:
                print(output)
        else:
            for metrics in sorted(results, key=lambda m: m.complexity_score):
                print_report(metrics)
    else:
        if not (skill_path / 'SKILL.md').exists():
            print(f"❌ SKILL.md not found in {skill_path}")
            sys.exit(1)
        
        metrics = profiler.profile_skill(skill_path)
        
        if args.json:
            output_data = profiler.to_dict(metrics)
            output = json.dumps(output_data, indent=2)
            if args.output:
                args.output.write_text(output, encoding='utf-8')
                print(f"✅ Written to {args.output}")
            else:
                print(output)
        else:
            print_report(metrics)


if __name__ == '__main__':
    main()
