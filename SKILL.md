---
name: skill-check
description: Skill规范检查工具。扫描并验证skill是否符合开发规范，输出诊断报告及修复建议。触发场景：检查skill、验证规范、扫描skill目录、诊断报告、skill质量评估。
---

# Skill Check

Skill规范检查与诊断工具。提供全面的skill合规性检查、问题诊断和修复建议。

## 检查项目

### 1. 目录结构检查
- `SKILL.md` 是否存在
- 资源目录命名规范：`scripts/`、`references/`、`assets/`
- 不允许的文件：`README.md`、`CHANGELOG.md` 等辅助文档

### 2. Frontmatter检查
- 必须字段：`name`、`description`
- 可选字段：`license`、`allowed-tools`、`metadata`
- 禁止额外字段

### 3. 命名规范检查
- `name`：小写字母、数字、连字符（hyphen-case）
- 禁止：开头/结尾连字符、连续连字符
- 最大长度：64字符

### 4. 描述质量检查
- 最大长度：1024字符
- 禁止：HTML标签 `<` `>`
- 应包含：功能描述 + 触发场景

### 5. 内容质量检查
- SKILL.md 正文不超过500行
- 无冗余的辅助文档
- 使用渐进式披露设计

### 6. 资源完整性检查
- 脚本文件应可执行
- 引用路径正确
- 无悬空引用

## 使用方法

### 单个Skill检查
```bash
python scripts/skill_check.py <skill-path>
```

### 批量扫描
```bash
python scripts/skill_check.py <skills-directory> --scan
```

### 生成诊断报告
```bash
python scripts/diagnose.py <skill-path> --report
```

### 检查并自动修复
```bash
python scripts/skill_check.py <skill-path> --fix
```

## 输出示例

```
SKILL CHECK REPORT
═══════════════════════════════════════
Skill: example-skill
Status: ❌ FAILED
───────────────────────────────────────
ISSUES:
  [ERROR] SKILL.md: Missing 'description' field
  [WARN]  SKILL.md: Description too long (1050 > 1024 chars)
  [INFO]  references/: Empty directory

FIXES:
  1. Add description field to frontmatter
  2. Truncate description to 1024 chars
  3. Remove empty directories

Score: 65/100
═══════════════════════════════════════
```

## 返回码

- `0`: 检查通过
- `1`: 检查失败（有错误）
- `2`: 严重错误（无法解析）
