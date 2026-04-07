# Skill 开发规范规则（中文版）

> 基于 [Agent Skills Specification](https://agentskills.io/specification) 制定

## 1. 目录结构规范

### 必选文件
- `SKILL.md` - 每个 skill 的入口文件，必须存在

### 可选目录
| 目录 | 用途 | 说明 |
|------|------|------|
| `scripts/` | 可执行脚本 | Python、Bash、JavaScript 等脚本 |
| `references/` | 参考文档 | 按需加载的详细文档 |
| `assets/` | 资源文件 | 模板、图片、字体等 |

### 禁止文件
- `README.md`
- `CHANGELOG.md`
- `INSTALLATION_GUIDE.md`
- `QUICK_REFERENCE.md`
- `TODO.md`
- `NOTES.md`
- `HISTORY.md`
- `CONTRIBUTING.md`

**原因**: Skill 应自包含，SKILL.md 应包含所有必要信息。

## 2. Frontmatter 规范

### 必选字段
```yaml
---
name: skill-name
description: 技能描述（包含功能和使用场景）
---
```

### 可选字段
| 字段 | 类型 | 说明 |
|------|------|------|
| `license` | string | 许可证类型 |
| `compatibility` | string/list | 兼容性说明 |
| `metadata` | object | 扩展元数据 |
| `allowed-tools` | string/list | 允许使用的工具 |

### 禁止字段
除上述字段外，禁止使用其他 YAML 字段。

## 3. 命名规范

### name 字段规则
- **字符**: Unicode 小写字母(a-z)、数字(0-9)、连字符(-)
- **格式**: hyphen-case（如 `my-skill-name`）
- **长度**: 1-64 字符
- **禁止**:
  - 开头或结尾使用连字符（`-skill`、`skill-`）
  - 连续连字符（`--`）
  - 大写字母
  - 下划线或其他特殊字符

### 目录名一致性
- 目录名应与 `name` 字段匹配

### 示例
| 合法 | 非法 |
|------|------|
| `my-skill` | `My-Skill` |
| `skill-v2` | `skill_v2` |
| `pdf-editor` | `pdfEditor` |
| `-pdf` | `pdf--processing` |

## 4. Description 规范

### 内容要求
- **长度**: 20-1024 字符
- **必须包含**:
  1. 功能描述 - 技能做什么
  2. 触发场景 - 何时使用（建议包含触发词）
- **格式**: 使用 "Use when..."、"Handle..."、"When the user..." 等

### 建议的触发词
- 英文: when, use, if, need, ask, want, handle, work with
- 中文: 使用、用于、适用于、场景、触发

### 禁止内容
- HTML 标签 `<` `>`
- 特殊编码

## 5. 内容质量规范

### 长度控制
- **SKILL.md 正文**: 建议不超过 500 行
- **Token 数**: 建议不超过 5000 tokens
- **参考文件**: 大文件(>200 行)应拆分

### 渐进式披露 (Progressive Disclosure)
将详细信息移到 `references/` 目录，SKILL.md 只保留核心流程。

| 层级 | 内容 | 何时加载 |
|------|------|----------|
| 1. Catalog | name + description | 会话开始 |
| 2. Instructions | SKILL.md body | skill 激活时 |
| 3. Resources | scripts/references/assets | 需要时 |

### 结构建议
- 长内容建议添加 ## 章节标题
- 使用步骤式说明
- 提供输入输出示例

## 6. 资源文件规范

### Scripts
- 添加 shebang 行 (`#!/usr/bin/env python3`)
- 确保可执行权限
- 提供清晰的注释

### References
- 文件名使用 kebab-case
- 大文件添加目录索引
- 避免深层嵌套

### Assets
- 只包含必要文件
- 大文件(>5MB)应警告
- 使用通用格式

## 7. 检查级别

| 级别 | 说明 | 影响 |
|------|------|------|
| ERROR | 严重错误，必须修复 | 检查失败 |
| WARN | 警告，建议修复 | 扣分 |
| INFO | 提示信息，可选优化 | 参考 |

## 8. 评分标准

| 分数 | 等级 | 说明 |
|------|------|------|
| 90-100 | A | 优秀，符合所有规范 |
| 70-89 | B | 良好，有少量警告 |
| 50-69 | C | 一般，存在错误需修复 |
| 0-49 | F | 不合格，需要重大修复 |

## 9. 常见问题

### Q: 为什么不能有 README.md?
A: Skill 是自包含的，SKILL.md 应包含所有必要信息。

### Q: 何时使用 references/?
A: 当 SKILL.md 超过 200 行或 5000 tokens 时，应拆分详细信息到 references/。

### Q: 描述可以多长?
A: 20-1024 字符。简洁描述更有价值。

### Q: 如何选择 name?
A: 使用功能相关的简短名称，用连字符分隔。如 `pdf-editor`、`git-helper`。

### Q: 什么是渐进式披露?
A: 一种分层加载策略：先加载 name+description，再加载完整 SKILL.md，最后按需加载 references/。
