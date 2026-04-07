---
name: skill-check
description: >
  Skill 工程化平台 - 全生命周期质量管理工具。提供规范检查、创建向导、依赖分析、性能分析、版本迁移等完整工具链。
  Use when checking skills, validating specifications, scanning skill directories,
  creating new skills from templates, analyzing dependencies, profiling performance,
  or migrating between spec versions. 触发: skill 规范检查、创建新 skill、分析依赖关系、性能优化、版本迁移。
compatibility:
  - Python 3.8+
  - PyYAML
---

# Skill Check - Skill 工程化平台

> 完整的 Skill 工程化质量管理体系

## 🧭 平台概览

Skill Check 不再只是"质检员"，而是覆盖 Skill **创建 → 开发 → 检查 → 测试 → 发布** 全生命周期的工程化平台。

| 阶段 | 工具 | 说明 |
|------|------|------|
| 创建 | `create.py` | 从模板快速创建 Skill |
| 开发 | 实时检查 | 边写边检，提前发现问题 |
| 检查 | `skill_check.py` | 规范合规性检查 |
| 测试 | `test_runner.py` | 功能正确性验证 |
| 分析 | `deps.py` | 依赖关系图谱 |
| 优化 | `profile.py` | 性能与复杂度分析 |
| 迁移 | `migrate.py` | 版本升级迁移 |
| 发布 | ClawHub | 发布到市场 |

---

## 🚀 快速开始

### 创建新 Skill

```bash
# 基本模板
python scripts/create.py my-skill

# API集成模板
python scripts/create.py my-api-skill --template api-integration

# 查看所有模板
python scripts/create.py --list-templates
```

### 检查现有 Skill

```bash
# 单个检查
python scripts/skill_check.py ./my-skill

# 批量扫描
python scripts/skill_check.py ./skills --scan --concurrent
```

---

## 📦 创建向导 (create.py)

从模板快速创建符合规范的 Skill。

### 可用模板

| 模板 | 适用场景 |
|------|----------|
| `basic` | 最小化 Skill 结构 |
| `api-integration` | API 调用类 Skill |
| `web-automation` | 浏览器自动化类 |
| `file-processing` | 文件处理类 |

### 使用示例

```bash
# 创建基本 Skill
python scripts/create.py pdf-extractor

# 创建 API 集成 Skill
python scripts/create.py github-api --template api-integration

# 在指定目录创建
python scripts/create.py my-skill --output ~/my-skills

# 覆盖已存在的 Skill
python scripts/create.py my-skill --force
```

### 模板包含

- ✅ `SKILL.md` 骨架
- ✅ `scripts/` 示例代码
- ✅ `references/` 目录
- ✅ 规范化的目录结构

---

## 🔍 规范检查 (skill_check.py)

### 检查项目

| 检查项 | 说明 | 级别 |
|--------|------|------|
| 目录结构 | SKILL.md 存在、目录规范 | ERROR |
| Frontmatter | 必选字段、禁止字段 | ERROR |
| 命名规范 | hyphen-case、长度限制 | ERROR |
| 描述质量 | 长度、触发词、禁止 HTML | WARN |
| 内容质量 | 行数限制、token 预算 | WARN |
| 资源完整性 | shebang、引用路径 | WARN |
| 渐进式披露 | references/ 使用建议 | INFO |

### 使用示例

```bash
# 基本检查
python scripts/skill_check.py ./my-skill

# 详细输出
python scripts/skill_check.py ./my-skill --verbose

# 自动修复
python scripts/skill_check.py ./my-skill --fix

# JSON 输出
python scripts/skill_check.py ./my-skill --json

# 批量扫描
python scripts/skill_check.py ./skills --scan --concurrent
```

### 输出示例

```
══════════════════════════════════════════════════
SKILL CHECK REPORT
══════════════════════════════════════════════════
Skill: example-skill
Status: ❌ FAILED
──────────────────────────────────────────────────
ISSUES:
  ❌ [ERROR] Frontmatter Missing 'description' field
  ⚠️  [WARN]  Description too long (1050 > 1024 chars)
Score: 65/100 | Grade: C
══════════════════════════════════════════════════
```

---

## 🔗 依赖分析 (deps.py)

分析 Skill 之间的依赖关系，检测循环依赖和孤岛 Skill。

### 使用示例

```bash
# 分析依赖
python scripts/deps.py ./skills

# JSON 输出
python scripts/deps.py ./skills --json

# 生成 Graphviz DOT
python scripts/deps.py ./skills --dot > deps.dot
```

### 输出内容

- 📊 统计信息：Skill 数量、引用数量
- 🔗 依赖关系列表
- ⚠️ 循环依赖检测
- 📌 孤岛 Skill（无任何依赖）

---

## 📊 性能分析 (profile.py)

分析 Skill 的复杂度和性能指标。

### 使用示例

```bash
# 分析单个 Skill
python scripts/profile.py ./my-skill

# 批量分析
python scripts/profile.py ./skills --scan

# JSON 输出
python scripts/profile.py ./my-skill --json -o profile.json
```

### 分析指标

| 指标 | 说明 |
|------|------|
| 复杂度评分 | 0-100 分，越高越好 |
| 复杂度等级 | A/B/C/D |
| 预估加载时间 | 基于 token 数量的估算 |
| 文件统计 | 总文件数、行数、大小 |
| SKILL.md 分析 | 行数、字符数、token 估算 |

### 优化建议

- SKILL.md 过大（>5000 tokens）→ 移至 references/
- 单个引用文件过大（>200 行）→ 拆分
- 缺少渐进式结构 → 添加 references/
- 大资源文件（>5MB）→ 压缩或外部托管

---

## 🔄 版本迁移 (migrate.py)

在规范版本之间迁移 Skill。

### 支持的迁移路径

| 源版本 | 目标版本 | 说明 |
|--------|----------|------|
| v1 | v2 | 添加 compatibility、检查 name 格式 |

### 使用示例

```bash
# 预览迁移（dry-run）
python scripts/migrate.py ./my-skill --from v1 --to v2

# 应用迁移
python scripts/migrate.py ./my-skill --from v1 --to v2 --apply

# 批量迁移
python scripts/migrate.py ./skills --from v1 --to v2 --scan --apply
```

### v1 → v2 迁移规则

1. 添加默认 `compatibility: ['Python 3.8+']`
2. 修复 name 格式（lowercase、hyphen-case）
3. 移除 forbidden 字段
4. 验证 description 长度
5. 清理 HTML 标签

---

## 📁 项目结构

```
skill-check/
├── scripts/
│   ├── skill_check.py    # 规范检查
│   ├── create.py          # 创建向导
│   ├── deps.py            # 依赖分析
│   ├── profile.py         # 性能分析
│   ├── migrate.py         # 版本迁移
│   └── diagnose.py        # 诊断报告
├── skill_check/
│   ├── checker.py        # 检查核心
│   └── config.py          # 配置管理
├── templates/             # Skill 模板
│   ├── basic/
│   ├── api-integration/
│   ├── web-automation/
│   └── file-processing/
├── references/           # 规范文档
│   ├── rules.md
│   └── rules_zh.md       # 中文规则
└── tests/               # 测试套件
```

---

## 🎓 成熟度等级

| 等级 | 名称 | 要求 |
|------|------|------|
| L1 | 基础合规 | 目录结构 + frontmatter 正确 |
| L2 | 命名规范 | name + description 符合标准 |
| L3 | 内容质量 | 无冗余、触发词完整 |
| L4 | 渐进式设计 | 正确使用 references/ |
| L5 | 工程化 | 有测试、有文档、有版本管理 |

---

## 配置

### .skill-check.md

在项目根目录创建 `.skill-check.md` 来自定义规则：

```yaml
allowed_frontmatter_fields:
  - name
  - description
  - license
  - compatibility
  - metadata
  - allowed-tools

forbidden_files:
  - README.md
  - CHANGELOG.md

rules:
  max_name_length: 64
  max_description_length: 1024
  max_body_tokens: 5000
```

---

## 依赖

- Python 3.8+
- PyYAML

---

*Skill Check - 让 Skill 工程化成为可能*
