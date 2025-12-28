# DevGenius MCP Client - 模块化架构

## 📁 目录结构

```
devgenius/
├── __init__.py           # 包初始化，导出主要类
├── api_client.py         # HTTP API 客户端
├── mcp_server.py         # MCP Server 核心逻辑
├── rules_manager.py      # Rules 文件管理
├── tools_registry.py     # MCP 工具注册表
└── README.md            # 本文档
```

## 🔧 模块说明

### 1. `api_client.py` - HTTP API 客户端

**职责：**
- 与 DevGenius 后端 API 通信
- 处理所有 HTTP 请求/响应
- 错误处理和日志记录

**主要类：**
- `DevGeniusAPIClient`: API 客户端类

**核心方法：**
- `fetch_rendered_rules()`: 获取渲染后的 Rules 内容
- `call_tool()`: 调用 MCP 工具对应的 API

---

### 2. `mcp_server.py` - MCP Server 核心

**职责：**
- MCP 协议处理
- 请求/响应路由
- stdio 通信管理

**主要类：**
- `DevGeniusMCPServer`: MCP Server 核心类

**核心方法：**
- `handle_request()`: 处理 MCP 请求
- `run()`: 运行 stdio 服务器
- `write_rules_file()`: 自动写入 Rules 文件

---

### 3. `rules_manager.py` - Rules 文件管理

**职责：**
- IDE 类型检测
- 项目根目录检测
- Rules 文件写入和备份

**主要类：**
- `RulesManager`: Rules 管理器（静态方法）

**核心方法：**
- `detect_ide_type()`: 检测当前 IDE 类型
- `get_project_root()`: 获取项目根目录
- `get_rules_file_path()`: 获取 Rules 文件路径
- `write_rules_file()`: 写入 Rules 文件（带备份）

**支持的 IDE：**
- Cursor (`.cursorrules`)
- Windsurf (`.windsurfrules`)
- VS Code (`.vscode/cursor-rules.md`)
- Trae (`.trae/rules/project_rules.md`)

---

### 4. `tools_registry.py` - 工具注册表

**职责：**
- 定义所有 MCP 工具
- 管理工具列表

**主要类：**
- `ToolsRegistry`: 工具注册表（静态方法）

**核心方法：**
- `get_all_tools()`: 获取所有工具定义

**工具分类：**
1. **项目上下文** (1个)
   - `get_project_context`

2. **任务管理** (4个)
   - `get_my_tasks`
   - `claim_task`
   - `update_task_status`
   - `split_task_into_subtasks`

3. **子任务管理** (2个)
   - `get_task_subtasks`
   - `update_subtask_status`

4. **文档管理** (8个)
   - `get_document_categories`
   - `list_documents`
   - `get_document_by_title`
   - `search_documents`
   - `create_document`
   - `update_document`
   - `delete_document`
   - `get_document_versions`

---

## 🚀 使用方式

### 作为包导入

```python
from devgenius import DevGeniusMCPServer

# 创建服务器实例
server = DevGeniusMCPServer(
    token="mcp_your_token",
    api_url="http://localhost:8000/api/v1/mcp"
)

# 运行服务器
await server.run()
```

### 独立使用各模块

```python
from devgenius import RulesManager, DevGeniusAPIClient

# 使用 Rules 管理器
ide_type = RulesManager.detect_ide_type()
project_root = RulesManager.get_project_root()

# 使用 API 客户端
client = DevGeniusAPIClient(token, api_url)
result = await client.call_tool("get_my_tasks", {})
```

### 环境变量

- `DEVGENIUS_VERIFY_SSL`：控制 HTTP 请求的 SSL 证书校验，默认 `true`。在需要忽略自签名证书时设置为 `false`。

---

## 📦 依赖关系

```
devgenius_mcp_client.py (入口文件)
    ↓
DevGeniusMCPServer (mcp_server.py)
    ├── DevGeniusAPIClient (api_client.py)
    ├── RulesManager (rules_manager.py)
    └── ToolsRegistry (tools_registry.py)
```

---

## 🔄 数据流

```
AI IDE (stdio)
    ↓
devgenius_mcp_client.py
    ↓
DevGeniusMCPServer.handle_request()
    ├── initialize → RulesManager.write_rules_file()
    ├── tools/list → ToolsRegistry.get_all_tools()
    └── tools/call → DevGeniusAPIClient.call_tool()
        ↓
    DevGenius Backend API
```

---

## ✨ 优势

1. **模块化**: 每个模块职责单一，易于维护
2. **可测试**: 各模块可独立测试
3. **可扩展**: 新增功能只需修改对应模块
4. **可复用**: 各模块可在其他项目中复用
5. **清晰**: 代码结构清晰，易于理解

---

## 📝 版本历史

- **v1.2.0**: 完成模块化重构
  - 拆分为 4 个独立模块
  - 简化主入口文件
  - 添加完整文档

- **v1.1.1**: 单文件版本
  - 所有逻辑在一个文件中
  - 代码量 781 行

---

## 🛠️ 开发指南

### 添加新工具

1. 在 `tools_registry.py` 中添加工具定义
2. 在 `api_client.py` 的 `call_tool()` 方法中添加 API 调用逻辑

### 支持新 IDE

1. 在 `rules_manager.py` 的 `RULES_FILE_MAP` 中添加映射
2. 在 `detect_ide_type()` 中添加检测逻辑

### 添加新功能

根据功能类型，在对应模块中添加：
- API 相关 → `api_client.py`
- MCP 协议相关 → `mcp_server.py`
- Rules 相关 → `rules_manager.py`
- 工具相关 → `tools_registry.py`
