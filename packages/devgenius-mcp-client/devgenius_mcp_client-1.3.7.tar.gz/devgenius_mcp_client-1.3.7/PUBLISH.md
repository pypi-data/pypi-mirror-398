# 发布 DevGenius MCP Client 到 PyPI

## 📦 发布步骤

### 1. 清理旧的构建文件

```bash
cd mcp-client
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
```

### 2. 构建包

```bash
python -m build
```

这会在 `dist/` 目录生成：
- `devgenius_mcp_client-1.0.1-py3-none-any.whl`
- `devgenius_mcp_client-1.0.1.tar.gz`

### 3. 上传到 PyPI

```bash
python -m twine upload dist/*
```

输入你的 PyPI API Token。

### 4. 验证

```bash
# 测试安装
uvx --from devgenius-mcp-client devgenius-mcp --help

# 或
pip install devgenius-mcp-client
devgenius-mcp --help
```

---

## ✅ 版本更新清单

发布新版本前检查：

- [ ] 更新 `pyproject.toml` 中的版本号
- [ ] 测试本地脚本运行正常
- [ ] 清理旧的 dist 目录
- [ ] 构建新包
- [ ] 上传到 PyPI
- [ ] 测试 uvx 安装
- [ ] 更新文档中的版本号

---

## 🔧 当前版本

**v1.3.5** ⭐ (最新)
- 🔒 HTTP 请求支持 `DEVGENIUS_VERIFY_SSL` 环境变量，默认校验证书，可在自签场景下显式关闭
- 📚 文档更新：补充 SSL 校验开关说明

**v1.3.3**
- 🧹 移除冗余的文档和规则接口，优化 API 结构
  - 移除 `get_document_by_title`、`update_document`、`delete_document` 三个冗余端点
  - 移除 `UpdateDocumentRequest` 模型，统一使用基于 ID 的更新接口
  - 移除 `get_project_rules` 导入，统一使用 `get_rules_content` 获取规则内容
- ✨ 新增项目任务列表查询功能
  - 新增 `list_project_tasks` 端点，支持按状态、优先级、里程碑等条件筛选任务
  - 优化文档列表过滤逻辑
- 🚀 优化里程碑创建功能，支持同时创建里程碑和任务
  - `create_milestone` 新增 `tasks` 参数，支持批量创建任务
  - 自动生成任务 ID（格式：M{index}-T{seq}）
  - 提高工作效率，一次性完成里程碑和任务规划

**v1.3.1**
- 📚 增强 `update_task_status` 和 `update_subtask_status` 工具文档说明
- ⚠️ **重要提示**：完成任务/子任务时**必须**在 `notes` 参数中提供总结报告
- 💡 添加总结报告格式说明和示例
- 🎯 帮助 AI 理解需要记录完成内容、关键变更、测试情况等信息
- ✅ 确保团队成员能够了解任务完成情况，提供有价值的文档记录

**v1.3.0**
- ✨ 新增里程碑管理工具（2个）：
  - `list_project_milestones` - 获取项目里程碑列表
  - `get_milestone_detail` - 获取里程碑详情（含任务列表）
- ✨ 新增任务详情工具（1个）：
  - `get_task_detail` - 获取完整任务信息（含子任务、验收标准）
- 📊 工具总数：18 → 21 个
- 🎯 完善开发者工作流：查看里程碑 → 选择任务 → 查看详情 → 认领任务
- 🔧 后端新增 3 个 MCP API 端点
- 📚 更新工具分类和文档

**v1.2.5**
- 📚 增强 `get_my_tasks` 工具文档说明
- ✨ 添加 `status_filter` 参数支持（pending/in_progress/completed/cancelled）
- 💡 添加详细的使用场景说明和示例
- 🔧 优化 API Client 参数传递逻辑
- ✅ 帮助 AI 更好地理解如何获取不同状态的任务

**v1.2.4**
- 🐛 修复 `search_documents` 工具参数错误：keyword → query
- ✨ 添加 `search_documents` 的 category 和 limit 参数
- ✅ 与后端 API 参数完全一致

**v1.2.3**
- ✨ 新增 `create_document_category` 工具 - 创建自定义文档分类
- 🔧 修正 `get_document_categories` API 端点 URL
- 📚 文档工具从 7 个增加到 9 个，总工具数 18 个
- ✅ 完整的文档分类管理能力

**v1.2.2**
- 🐛 修复 entry point 模块导入错误
- 📦 同时打包 `devgenius/` 目录和 `devgenius_mcp_client.py` 文件
- ✅ 完整解决 uvx 安装和运行问题

**v1.2.1**
- 🐛 修复 uvx 安装时 `devgenius` 包导入错误
- 📦 添加 hatchling 包配置，确保 `devgenius/` 目录被正确打包

**v1.2.0**
- ✨ 新增 Rules 自动同步功能
- 🎯 自动检测 IDE 类型和项目路径
- 📝 自动写入 `.cursorrules` / `.windsurfrules` 等文件
- 🔄 支持变量渲染和备份机制

**v1.0.1**
- 修复 async main 函数问题
- 正确的入口点配置
- 完整的日志支持

**v1.0.0**
- 初始发布
- 支持所有 10 个 MCP 工具
- 中文编码支持

---

## 📝 PyPI 链接

https://pypi.org/project/devgenius-mcp-client/
