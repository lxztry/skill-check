---
name: skill-check
description: Skill规范检查工具。扫描并验证skill是否符合开发规范，输出诊断报告及修复建议。使用本工具检查skill是否符合Agent Skills规范，验证命名规则和内容质量。支持自动修复、并发扫描、渐进式披露检查。触发场景：检查skill、验证规范、扫描skill目录、诊断报告、skill质量评估。
compatibility:
  - Python 3.8+
  - PyYAML
---

# Skill Check

Skill规范检查与诊断工具。提供全面的skill合规性检查、问题诊断和自动修复。

## 检查项目

### 1. 目录结构检查
- `SKILL.md` 是否存在
- 资源目录命名规范：`scripts/`、`references/`、`assets/`
- 不允许的文件：`README.md`、`CHANGELOG.md` 等辅助文档
- 非标准目录警告

### 2. Frontmatter检查 (agentskills.io规范)
- **必选字段**: `name`、`description`
- **可选字段**: `license`、`compatibility`、`metadata`、`allowed-tools`
- **禁止额外字段**
- name匹配目录名检查

### 3. 命名规范检查 (agentskills.io规范)
- `name`: 小写字母、数字、连字符（hyphen-case）
- 禁止：开头/结尾连字符、连续连字符
- 最大长度：64字符
- 目录名与name一致性检查

### 4. 描述质量检查 (agentskills.io规范)
- 最大长度：1024字符
- 最小长度：20字符
- 禁止：HTML标签 `<` `>`
- 应包含：功能描述 + 触发场景
- 建议包含触发词（when/use/if/need/ask/want/handle/work with）

### 5. 内容质量检查 (agentskills.io规范)
- SKILL.md 正文不超过500行
- 内容token数建议不超过5000
- 无冗余的辅助文档
- 使用渐进式披露设计
- 建议添加章节结构

### 6. 资源完整性检查
- 脚本文件应有shebang
- 引用路径正确
- 大文件警告
- references文件命名规范

### 7. 渐进式披露检查 (agentskills.io规范)
- 检查是否引用references/目录
- 检查是否引用scripts/目录
- 建议将详细信息移至references/

## 使用方法

### 单个Skill检查
```bash
python scripts/skill_check.py <skill-path>
```

### 批量扫描
```bash
python scripts/skill_check.py <skills-directory> --scan
```

### 并发扫描 (大量skill时推荐)
```bash
python scripts/skill_check.py <skills-directory> --scan --concurrent
```

### 生成诊断报告
```bash
python scripts/diagnose.py <skill-path> --format text
python scripts/diagnose.py <skill-path> --format markdown --output report.md
python scripts/diagnose.py <skill-path> --format json --output report.json
```

### 检查并自动修复
```bash
python scripts/skill_check.py <skill-path> --fix
```

### 输出选项
```bash
python scripts/skill_check.py <skill-path> --json          # JSON输出
python scripts/skill_check.py <skill-path> --quiet        # 安静模式
python scripts/skill_check.py <skill-path> --verbose      # 详细模式(含等级)
python scripts/skill_check.py <skill-path> -o result.txt   # 输出到文件
```

## 命令行选项

| 选项 | 说明 |
|------|------|
| `path` | Skill目录路径或包含多个skill的目录 |
| `--scan`, `-s` | 扫描目录下所有skill |
| `--fix`, `-f` | 自动修复可修复的问题 |
| `--json`, `-j` | 输出JSON格式 |
| `--quiet`, `-q` | 仅输出摘要 |
| `--verbose`, `-v` | 输出详细信息(含等级) |
| `--concurrent`, `-c` | 并发扫描(多skill时) |
| `--workers`, `-w` | 并发工作线程数(默认4) |
| `--output`, `-o` | 输出到文件 |

## 输出示例

```
══════════════════════════════════════════════════
SKILL CHECK REPORT
══════════════════════════════════════════════════
Skill: example-skill
Path:  ./example-skill
Status: ❌ FAILED
──────────────────────────────────────────────────
ISSUES:
  ❌ [ERROR] Frontmatter Missing 'description' field
  ⚠️  [WARN]  Frontmatter Description too long (1050 > 1024 chars)
  ℹ️  [INFO]  Structure Empty directory: references/

FIX SUGGESTIONS:
  1. Add 'description' field to frontmatter
  2. Truncate description to 1024 characters
  3. Remove empty references/ directory

Score: 65/100
Grade: C
══════════════════════════════════════════════════
```

## 评分标准

| 分数 | 等级 | 说明 |
|------|------|------|
| 90-100 | A | 优秀，符合所有规范 |
| 70-89 | B | 良好，有少量警告 |
| 50-69 | C | 一般，存在错误需修复 |
| 0-49 | F | 不合格，需要重大修复 |

## 返回码

- `0`: 检查通过
- `1`: 检查失败（有错误）
- `2`: 严重错误（无法解析）

## 依赖

- Python 3.8+
- PyYAML