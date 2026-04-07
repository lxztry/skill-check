import * as vscode from 'vscode';
import { execSync, exec } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

export function activate(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('skillCheck');
    const pythonPath = config.get<string>('pythonPath') || 'python';
    
    // Get the extension's directory
    const extensionPath = context.extensionPath;
    const scriptPath = path.join(extensionPath, '..', '..', 'scripts', 'skill_check.py');
    
    // Fallback: try to find skill-check in common locations
    const findSkillCheckScript = (): string | null => {
        const possiblePaths = [
            scriptPath,
            path.join(extensionPath, '..', '..', '..', '..', 'skill-check', 'scripts', 'skill_check.py'),
            path.join(process.cwd(), 'scripts', 'skill_check.py'),
        ];
        
        for (const p of possiblePaths) {
            if (fs.existsSync(p)) {
                return p;
            }
        }
        return null;
    };
    
    const skillCheckScript = findSkillCheckScript();
    
    // Command: Check current skill
    const checkSkillCommand = vscode.commands.registerCommand('skill-check.checkSkill', async (uri?: vscode.Uri) => {
        const targetPath = uri?.fsPath || vscode.window.activeTextEditor?.document.uri.fsPath;
        
        if (!targetPath) {
            vscode.window.showErrorMessage('请在 Skill 目录中运行此命令');
            return;
        }
        
        // Find the skill directory (should contain SKILL.md)
        let skillDir = targetPath;
        if (fs.statSync(targetPath).isFile()) {
            skillDir = path.dirname(targetPath);
        }
        
        // Go up until we find SKILL.md or reach home
        let current = skillDir;
        while (current !== path.dirname(current)) {
            if (fs.existsSync(path.join(current, 'SKILL.md'))) {
                skillDir = current;
                break;
            }
            current = path.dirname(current);
        }
        
        await runSkillCheck(skillDir);
    });
    
    // Command: Check all skills in workspace
    const checkWorkspaceCommand = vscode.commands.registerCommand('skill-check.checkWorkspace', async () => {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        
        if (!workspaceFolders || workspaceFolders.length === 0) {
            vscode.window.showWarningMessage('没有打开的工作区');
            return;
        }
        
        const outputChannel = vscode.window.createOutputChannel('Skill Check');
        outputChannel.show();
        outputChannel.appendLine('🔍 扫描工作区中的 Skills...\n');
        
        for (const folder of workspaceFolders) {
            const skills = findSkillsInDirectory(folder.uri.fsPath);
            
            if (skills.length === 0) {
                outputChannel.appendLine(`📁 ${path.basename(folder.uri.fsPath)}: 未找到 Skills`);
            } else {
                outputChannel.appendLine(`📁 ${path.basename(folder.uri.fsPath)}: 找到 ${skills.length} 个 Skills`);
                
                for (const skill of skills) {
                    await runSkillCheck(skill, outputChannel);
                }
            }
        }
        
        outputChannel.appendLine('\n✅ 检查完成');
    });
    
    // Command: Create new skill
    const createSkillCommand = vscode.commands.registerCommand('skill-check.createSkill', async () => {
        const skillName = await vscode.window.showInputBox({
            prompt: '输入 Skill 名称（使用连字符分隔，如 my-skill）',
            validateInput: (value) => {
                if (!value) return '名称不能为空';
                if (!/^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$/.test(value)) {
                    return '名称格式错误：使用小写字母、数字和连字符';
                }
                return null;
            }
        });
        
        if (!skillName) return;
        
        // Select template
        const template = await vscode.window.showQuickPick([
            { label: 'basic', description: '最小化 Skill 结构' },
            { label: 'api-integration', description: 'API 调用类 Skill' },
            { label: 'web-automation', description: '浏览器自动化类' },
            { label: 'file-processing', description: '文件处理类' }
        ], {
            prompt: '选择 Skill 模板'
        });
        
        if (!template) return;
        
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd();
        const outputPath = path.join(workspaceFolder, skillName);
        
        if (fs.existsSync(outputPath)) {
            vscode.window.showErrorMessage(`Skill 已存在: ${outputPath}`);
            return;
        }
        
        // Run create.py
        const createScript = path.join(extensionPath, '..', '..', 'scripts', 'create.py');
        
        if (!fs.existsSync(createScript)) {
            vscode.window.showErrorMessage('create.py 脚本未找到');
            return;
        }
        
        try {
            const result = execSync(`${pythonPath} "${createScript}" "${skillName}" --template ${template.label}`, {
                cwd: workspaceFolder,
                encoding: 'utf-8'
            });
            
            vscode.window.showInformationMessage(`✅ Skill 创建成功: ${skillName}`);
            
            // Open the new skill
            const newSkillPath = path.join(outputPath, 'SKILL.md');
            if (fs.existsSync(newSkillPath)) {
                const doc = await vscode.workspace.openTextDocument(newSkillPath);
                vscode.window.showTextDocument(doc);
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`创建失败: ${error.message}`);
        }
    });
    
    async function runSkillCheck(skillPath: string, outputChannel?: vscode.OutputChannel): Promise<void> {
        if (!skillCheckScript) {
            const msg = 'skill-check 脚本未找到。请确保 skill-check 已安装或设置正确的 scriptPath';
            if (outputChannel) {
                outputChannel.appendLine(`❌ ${msg}`);
            } else {
                vscode.window.showErrorMessage(msg);
            }
            return;
        }
        
        const output = outputChannel || vscode.window.createOutputChannel('Skill Check');
        if (!outputChannel) output.show();
        
        output.appendLine(`\n📋 检查: ${path.basename(skillPath)}`);
        
        try {
            const result = execSync(`${pythonPath} "${skillCheckScript}" "${skillPath}"`, {
                encoding: 'utf-8',
                timeout: 30000
            });
            
            output.appendLine(result);
            
            // Parse result for status
            if (result.includes('FAILED') || result.includes('❌')) {
                vscode.window.showWarningMessage(`Skill "${path.basename(skillPath)}" 有问题需要修复`);
            }
        } catch (error: any) {
            output.appendLine(`❌ 检查失败: ${error.message}`);
        }
    }
    
    function findSkillsInDirectory(dir: string): string[] {
        const skills: string[] = [];
        
        try {
            const entries = fs.readdirSync(dir, { withFileTypes: true });
            
            for (const entry of entries) {
                if (entry.isDirectory()) {
                    const skillPath = path.join(dir, entry.name);
                    if (fs.existsSync(path.join(skillPath, 'SKILL.md'))) {
                        skills.push(skillPath);
                    } else {
                        // Recurse into subdirectories
                        skills.push(...findSkillsInDirectory(skillPath));
                    }
                }
            }
        } catch (error) {
            // Ignore permission errors
        }
        
        return skills;
    }
    
    context.subscriptions.push(checkSkillCommand);
    context.subscriptions.push(checkWorkspaceCommand);
    context.subscriptions.push(createSkillCommand);
}

export function deactivate() {}
