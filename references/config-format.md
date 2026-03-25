# Skill Check 配置示例 (Markdown 格式)

```yaml
---
allowed_frontmatter_fields:
  - name
  - description
  - license
  - compatibility
  - metadata
  - allowed-tools
  - author
  - version
forbidden_files:
  - README.md
  - CHANGELOG.md
  - TODO.md
allowed_dirs:
  - scripts
  - references
  - assets
  - tests
ignored_dirs:
  - .git
  - __pycache__
  - node_modules
rules:
  max_name_length: 64
  max_description_length: 2048
  min_description_length: 10
  max_body_lines: 1000
  max_body_tokens: 10000
  max_reference_lines: 500
trigger_words:
  - when
  - use
  - if
  - need
  - 使用
  - 用于
---
```

## 配置文件格式

支持两种格式：

### 1. YAML 格式 (`.yaml` / `.yml`)

```yaml
rules:
  max_name_length: 64
  max_description_length: 1024
```

### 2. Markdown 格式 (`.md`)

使用 YAML frontmatter 包裹配置：

```markdown
---
rules:
  max_name_length: 64
  max_description_length: 1024
---
```

## 配置项说明

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `allowed_frontmatter_fields` | list | 允许的 frontmatter 字段 |
| `forbidden_files` | list | 禁止的文件名 |
| `allowed_dirs` | list | 允许的目录名 |
| `ignored_dirs` | list | 忽略的目录（不报警告） |
| `rules.max_name_length` | int | name 最大字符数 |
| `rules.min_description_length` | int | description 最小字符数 |
| `rules.max_description_length` | int | description 最大字符数 |
| `rules.max_body_lines` | int | SKILL.md 正文最大行数 |
| `rules.max_body_tokens` | int | SKILL.md 正文最大 token 数 |
| `rules.max_reference_lines` | int | 参考文件最大行数 |
| `rules.large_file_threshold_mb` | int | 大文件阈值(MB) |
| `trigger_words` | list | 触发词列表（用于检查 description） |