"""
MCP Server 核心逻辑

负责：
- MCP 协议处理
- 请求/响应路由
- stdio 通信
"""

import sys
import json
import os
import logging
from typing import Dict, Any

from .api_client import DevGeniusAPIClient
from .rules_manager import RulesManager
from .tools_registry import ToolsRegistry

logger = logging.getLogger(__name__)


class DevGeniusMCPServer:
    """DevGenius MCP Server 核心"""
    
    def __init__(self, token: str, api_url: str, verify_ssl: bool):
        """
        初始化 MCP Server
        
        Args:
            token: MCP Token
            api_url: DevGenius API 基础 URL
            verify_ssl: 是否验证 SSL 证书
        """
        self.token = token
        self.api_url = api_url
        self.verify_ssl = verify_ssl
        self.api_client = DevGeniusAPIClient(token, api_url, self.verify_ssl)
        self.rules_manager = RulesManager()
        self.tools_registry = ToolsRegistry()
        
        logger.info(f"✅ DevGenius MCP Server 初始化完成")
    
    async def write_rules_file(
        self,
        project_id: int,
        member_name: str,
        member_role: str
    ) -> bool:
        """
        写入规则文件到项目目录（备份后覆盖策略）
        
        Args:
            project_id: 项目 ID
            member_name: 成员名称
            member_role: 成员角色
            
        Returns:
            是否成功写入
        """
        try:
            # 1. 检测 IDE 类型
            ide_type = self.rules_manager.detect_ide_type()
            
            # 2. 获取项目目录
            project_root = self.rules_manager.get_project_root()
            if not project_root:
                logger.error("❌ 无法确定项目目录")
                return False
            
            # 3. 调用后端 API 获取渲染后的 Rules
            logger.info(f"📡 正在获取 {ide_type} 的 Rules 配置...")
            rules_content = await self.api_client.fetch_rendered_rules(
                project_id=project_id,
                ide_type=ide_type,
                member_name=member_name,
                member_role=member_role
            )
            
            if not rules_content:
                logger.info("ℹ️ 项目未配置 Rules，跳过写入")
                return False
            
            # 4. 确定规则文件路径
            rules_file = self.rules_manager.get_rules_file_path(ide_type, project_root)
            logger.info(f"📝 规则文件路径: {rules_file}")
            
            # 5. 写入文件
            success = self.rules_manager.write_rules_file(rules_file, rules_content)
            
            if success:
                logger.info(f"📄 IDE 类型: {ide_type}")
                logger.info(f"👤 成员: {member_name} ({member_role})")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 写入 Rules 文件失败: {e}", exc_info=True)
            return False
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 MCP 请求
        
        Args:
            request: MCP 请求
            
        Returns:
            MCP 响应
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        logger.debug(f"📨 收到请求: method={method}, id={request_id}")
        
        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "devgenius", "version": "1.2.0"}
                }
                
                # 初始化后自动写入 Rules 文件
                auto_write = os.environ.get('DEVGENIUS_AUTO_WRITE_RULES', 'fasle').lower() == 'true'
                if auto_write:
                    logger.info("🎯 开始自动写入 Rules 文件...")
                    try:
                        # 先获取项目上下文以获取项目信息
                        context_result = await self.api_client.call_tool("get_project_context", {})
                        if context_result.get("success"):
                            project_info = context_result.get("project", {})
                            member_info = context_result.get("member", {})
                            
                            project_id = project_info.get("id")
                            member_name = member_info.get("name", "Unknown")
                            member_role = member_info.get("role_category", "developer")
                            
                            if project_id:
                                await self.write_rules_file(project_id, member_name, member_role)
                            else:
                                logger.warning("⚠️ 无法获取项目 ID，跳过 Rules 写入")
                        else:
                            logger.warning("⚠️ 无法获取项目上下文，跳过 Rules 写入")
                    except Exception as e:
                        logger.error(f"❌ 自动写入 Rules 失败: {e}")
                        # 不影响 MCP 正常初始化
                else:
                    logger.info("ℹ️ 自动写入 Rules 已禁用")
            
            elif method == "tools/list":
                result = {"tools": self.tools_registry.get_all_tools()}
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                tool_result = await self.api_client.call_tool(tool_name, arguments)
                result = {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(tool_result, ensure_ascii=False, indent=2)
                    }]
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
            
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
            
        except Exception as e:
            logger.error(f"❌ 处理请求失败: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": str(e)}
            }
    
    async def run(self):
        """运行 MCP Server（stdio 模式）"""
        logger.info("🚀 DevGenius MCP Server 启动，等待请求...")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)
                    
                    # 确保中文正确编码输出
                    response_str = json.dumps(response, ensure_ascii=False)
                    
                    # 写入并立即刷新
                    sys.stdout.write(response_str + '\n')
                    sys.stdout.flush()
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON 解析错误: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": "Parse error"}
                    }
                    print(json.dumps(error_response, ensure_ascii=False), flush=True)
                    
        except KeyboardInterrupt:
            logger.info("🛑 收到中断信号，退出...")
        except Exception as e:
            logger.error(f"❌ 运行时错误: {e}", exc_info=True)
