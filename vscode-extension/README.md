# Skill Check VS Code Extension

VS Code 集成插件，让你在编辑器中直接检查和创建 Skills。

## 安装

### 方式 1: 从 VSIX 安装（推荐）

1. 编译扩展：
```bash
cd vscode-extension
npm install
npm run compile
```

2. 打包：
```bash
npm install -g @vscode/vsce
vsce package
```

3. 安装：
```bash
code --install-extension skill-check-1.0.0.vsix
```

### 方式 2: 链接开发

```bash
cd vscode-extension
npm install
code .
# 按 F5 启动调试
```

## 功能

### 命令面板

| 命令 | 说明 | 快捷键 |
|------|------|--------|
| `Skill Check: 检查当前 Skill` | 检查光标所在的 Skill | `Ctrl+Shift+S, C` |
| `Skill Check: 检查所有 Skills` | 扫描工作区检查所有 Skills | `Ctrl+Shift+S, A` |
| `Skill Check: 创建新 Skill` | 从模板创建新 Skill | `Ctrl+Shift+S, N` |

### 右键菜单

在 `skills/` 目录中的文件夹上右键，可以直接检查该 Skill。

## 配置

```json
{
  "skillCheck.pythonPath": "python",
  "skillCheck.scriptPath": "/path/to/skill-check/scripts"
}
```

## 使用示例

### 检查 Skill

1. 打开包含 SKILL.md 的目录
2. 按 `Ctrl+Shift+P` 打开命令面板
3. 输入 `Skill Check: 检查当前 Skill`
4. 查看输出面板中的检查结果

### 创建新 Skill

1. 按 `Ctrl+Shift+P`
2. 输入 `Skill Check: 创建新 Skill`
3. 输入 Skill 名称（如 `my-api-skill`）
4. 选择模板类型
5. 新 Skill 会在当前工作区创建

## 依赖

- Python 3.8+
- skill-check 库（位于父目录）

## License

MIT
