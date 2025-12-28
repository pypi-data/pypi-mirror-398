# Rules 工具使用指南

## 📋 概述

DevGenius MCP 提供了两种获取项目 Rules 的方式：

1. **`get_project_rules`** - 自动写入（MCP Client 使用）
2. **`get_rules_content`** - 获取内容（AI 自行处理）✨ 推荐

---

## 🆕 新工具：`get_rules_content`

### 设计理念

- **职责分离**：后端只负责提供内容，前端 AI 决定如何使用
- **灵活性**：支持任意 IDE 的 Rules 规范
- **扩展性**：提供建议路径，但不强制使用

### 工具定义

```json
{
  "name": "get_rules_content",
  "description": "获取项目 Rules 内容（供 AI 自行处理）。返回渲染后的 Rules 内容，不涉及文件写入。AI 可以根据自己 IDE 的规范决定如何使用这些内容。",
  "inputSchema": {
    "type": "object",
    "properties": {
      "ide_type": {
        "type": "string",
        "description": "IDE 类型（可选）：cursor, windsurf, vscode, trae",
        "enum": ["cursor", "windsurf", "vscode", "trae"]
      }
    }
  }
}
```

### 返回格式

```json
{
  "success": true,
  "project_id": 1,
  "project_name": "DevGenius 项目",
  "ide_type": "cursor",
  "rules_content": "# DevGenius 项目开发规则\n\n你是 DevGenius 项目的 AI 助手...",
  "variables": {
    "project_name": "DevGenius 项目",
    "member_name": "全栈小李",
    "member_role": "fullstack"
  },
  "suggested_paths": {
    "cursor": ".cursor/rules/project-rules.mdc",
    "windsurf": ".windsurf/rules/project-rules.md",
    "vscode": ".vscode/rules/cursor-rules.md",
    "trae": ".trae/rules/project_rules.md"
  }
}
```

---

## 🎯 使用场景

### 场景 1：Cursor AI 自动写入 Rules

```
用户：请帮我同步项目 Rules

AI 思考：
1. 调用 get_rules_content 工具获取内容
2. 检测当前 IDE 是 Cursor
3. 使用 suggested_paths.cursor 路径
4. 创建 .cursor/rules/ 目录
5. 写入 project-rules.mdc 文件

AI 回复：
已成功同步项目 Rules 到 .cursor/rules/project-rules.mdc
```

### 场景 2：Windsurf AI 自定义路径

```
用户：获取项目规则并保存到 .windsurf/custom-rules.md

AI 思考：
1. 调用 get_rules_content(ide_type="windsurf")
2. 获取 rules_content
3. 按用户指定的路径写入

AI 回复：
已将项目 Rules 保存到 .windsurf/custom-rules.md
```

### 场景 3：Trae AI 显示 Rules 内容

```
用户：显示项目开发规则

AI 思考：
1. 调用 get_rules_content(ide_type="trae")
2. 直接展示 rules_content

AI 回复：
# DevGenius 项目开发规则

你是 DevGenius 项目的 AI 助手...
（显示完整内容）
```

---

## 🔧 AI 实现示例

### Cursor AI 实现

```typescript
// Cursor AI 内部逻辑（伪代码）
async function syncProjectRules() {
  // 1. 调用 MCP 工具
  const result = await mcp.callTool('get_rules_content', {
    ide_type: 'cursor'
  });
  
  if (!result.success) {
    return `项目未配置 Rules: ${result.error}`;
  }
  
  // 2. 确定文件路径
  const rulesPath = result.suggested_paths.cursor;
  const fullPath = path.join(workspaceRoot, rulesPath);
  
  // 3. 创建目录
  await fs.mkdir(path.dirname(fullPath), { recursive: true });
  
  // 4. 写入文件
  await fs.writeFile(fullPath, result.rules_content, 'utf-8');
  
  return `✅ Rules 已同步到 ${rulesPath}`;
}
```

### Windsurf AI 实现

```python
# Windsurf AI 内部逻辑（伪代码）
async def sync_project_rules():
    # 1. 调用 MCP 工具
    result = await mcp.call_tool('get_rules_content', {
        'ide_type': 'windsurf'
    })
    
    if not result['success']:
        return f"项目未配置 Rules: {result['error']}"
    
    # 2. 使用 Windsurf 的规范路径
    rules_path = result['suggested_paths']['windsurf']
    full_path = os.path.join(workspace_root, rules_path)
    
    # 3. 创建目录并写入
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(result['rules_content'])
    
    return f"✅ Rules 已同步到 {rules_path}"
```

---

## 📊 工具对比

| 特性 | `get_project_rules` | `get_rules_content` |
|------|-------------------|-------------------|
| **用途** | MCP Client 自动同步 | AI 自行处理 |
| **文件写入** | ✅ 自动写入 | ❌ 不写入 |
| **路径控制** | 固定路径 | AI 自定义 |
| **灵活性** | 低 | 高 |
| **适用场景** | 后台自动化 | AI 交互式操作 |
| **IDE 支持** | 需要预定义 | 任意 IDE |

---

## 🎨 建议路径规范

根据各 IDE 的官方规范：

```
cursor/
  .cursor/
    rules/
      project-rules.mdc    # Cursor 官方规范

windsurf/
  .windsurf/
    rules/
      project-rules.md     # Windsurf 官方规范

vscode/
  .vscode/
    rules/
      cursor-rules.md      # VSCode + Cursor 扩展

trae/
  .trae/
    rules/
      project_rules.md     # Trae 官方规范
```

---

## 🚀 最佳实践

### 1. AI 应该如何使用

```
推荐流程：
1. 用户请求同步 Rules
2. AI 调用 get_rules_content 获取内容
3. AI 检测当前 IDE 类型
4. AI 根据 suggested_paths 选择路径
5. AI 创建目录并写入文件
6. AI 向用户确认完成
```

### 2. 错误处理

```typescript
async function syncRules() {
  try {
    const result = await mcp.callTool('get_rules_content');
    
    if (!result.success) {
      // 项目未配置 Rules
      return `⚠️ ${result.error}\n\n建议：请在 DevGenius 后台配置项目 Rules`;
    }
    
    // 正常写入流程...
    
  } catch (error) {
    return `❌ 同步失败: ${error.message}`;
  }
}
```

### 3. 用户体验优化

```
好的 AI 回复：
✅ "已将项目 Rules 同步到 .cursor/rules/project-rules.mdc"
✅ "Rules 内容已更新，包含 15 条开发规范"
✅ "同步完成！重启 IDE 后生效"

避免的回复：
❌ "操作完成"（太简略）
❌ "文件已写入 C:\Users\...\project-rules.mdc"（路径太长）
```

---

## 📝 总结

**`get_rules_content` 的优势：**

1. ✅ **解耦设计**：后端不关心文件系统，只提供内容
2. ✅ **灵活适配**：支持任意 IDE 的 Rules 规范
3. ✅ **AI 友好**：AI 可以根据上下文智能处理
4. ✅ **易于扩展**：新增 IDE 无需修改后端
5. ✅ **用户可控**：用户可以要求 AI 保存到自定义路径

**推荐使用场景：**
- 所有支持 MCP 的 AI IDE（Cursor、Windsurf、Trae 等）
- AI 需要根据用户指令灵活处理 Rules 内容
- 需要自定义 Rules 文件路径或格式

**保留 `get_project_rules` 的原因：**
- MCP Client 后台自动同步（无需 AI 介入）
- 向后兼容现有实现
