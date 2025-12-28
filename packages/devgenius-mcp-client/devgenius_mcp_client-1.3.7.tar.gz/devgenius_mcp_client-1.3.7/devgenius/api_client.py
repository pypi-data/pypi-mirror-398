"""
DevGenius API 客户端

负责：
- HTTP API 调用
- 请求/响应处理
- 错误处理
"""

import logging
from typing import Dict, Any, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

try:
    import httpx
except ImportError:
    logger.error("httpx 未安装，请运行: pip install httpx")
    raise


class DevGeniusAPIClient:
    """DevGenius API 客户端"""
    
    def __init__(self, token: str, api_url: str, verify_ssl: bool):
        """
        初始化 API 客户端
        
        Args:
            token: MCP Token
            api_url: DevGenius API 基础 URL
            verify_ssl: 是否验证 SSL 证书
        """
        self.token = token
        self.api_url = api_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        self.verify_ssl = verify_ssl
        if not self.verify_ssl:
            logger.warning("⚠️ SSL 证书校验已禁用 (DEVGENIUS_VERIFY_SSL=false)")
        logger.info(f"✅ API 客户端初始化完成，API: {api_url}")
    
    async def fetch_rendered_rules(
        self,
        project_id: int,
        ide_type: str,
        member_name: str,
        member_role: str
    ) -> Optional[str]:
        """
        从后端获取渲染后的 Rules 内容
        
        Args:
            project_id: 项目 ID（实际不使用，通过 Token 自动识别）
            ide_type: IDE 类型
            member_name: 成员名称（实际不使用，通过 Token 自动识别）
            member_role: 成员角色（实际不使用，通过 Token 自动识别）
            
        Returns:
            渲染后的 Rules 内容，如果失败则返回 None
        """
        try:
            # 使用 MCP API 端点（自动通过 Token 识别项目和成员）
            async with httpx.AsyncClient(timeout=30.0, verify=self.verify_ssl) as client:
                response = await client.post(
                    f"{self.api_url}/rules/render",
                    headers=self.headers,
                    json={"ide_type": ide_type}
                )
                
                if response.status_code == 404:
                    logger.warning(f"⚠️ 项目未配置 {ide_type} 的 Rules")
                    return None
                
                response.raise_for_status()
                result = response.json()
                
                if result.get("success"):
                    return result.get("rules_content")
                else:
                    logger.error(f"❌ 获取 Rules 失败: {result.get('error')}")
                    return None
                    
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP 错误: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 获取 Rules 失败: {e}", exc_info=True)
            return None
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用 MCP 工具
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具调用结果
        """
        logger.info(f"🔧 调用工具: {name}, 参数: {arguments}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0, verify=self.verify_ssl) as client:
                # 根据工具名称调用对应的 API
                if name == "get_project_context":
                    response = await client.get(
                        f"{self.api_url}/context",
                        headers=self.headers,
                        params={"include_tasks": arguments.get("include_tasks", True)}
                    )
                
                elif name == "get_project_summary":
                    response = await client.get(
                        f"{self.api_url}/summary",
                        headers=self.headers
                    )
                
                elif name == "list_project_milestones":
                    params = {}
                    if "status" in arguments and arguments["status"]:
                        params["status"] = arguments["status"]
                    response = await client.get(
                        f"{self.api_url}/milestones",
                        headers=self.headers,
                        params=params
                    )
                
                elif name == "get_milestone_detail":
                    milestone_id = arguments["milestone_id"]
                    params = {"include_tasks": arguments.get("include_tasks", True)}
                    response = await client.get(
                        f"{self.api_url}/milestones/{milestone_id}",
                        headers=self.headers,
                        params=params
                    )
                
                elif name == "create_milestone":
                    response = await client.post(
                        f"{self.api_url}/milestones",
                        headers=self.headers,
                        json=arguments
                    )
                
                elif name == "create_milestone_tasks":
                    response = await client.post(
                        f"{self.api_url}/milestones/tasks",
                        headers=self.headers,
                        json=arguments
                    )
                
                elif name == "delete_milestone_task":
                    task_id = arguments["task_id"]
                    response = await client.delete(
                        f"{self.api_url}/milestones/tasks/{task_id}",
                        headers=self.headers
                    )
                
                elif name == "delete_milestone":
                    milestone_id = arguments["milestone_id"]
                    response = await client.delete(
                        f"{self.api_url}/milestones/{milestone_id}",
                        headers=self.headers
                    )
                
                elif name == "get_task_detail":
                    task_id = arguments["task_id"]
                    response = await client.get(
                        f"{self.api_url}/tasks/{task_id}/detail",
                        headers=self.headers
                    )
                
                elif name == "get_my_tasks":
                    params = {}
                    if "status_filter" in arguments and arguments["status_filter"]:
                        params["status_filter"] = arguments["status_filter"]
                    response = await client.get(
                        f"{self.api_url}/tasks",
                        headers=self.headers,
                        params=params
                    )
                
                elif name == "list_project_tasks":
                    params = {}
                    if "status" in arguments and arguments["status"]:
                        params["status"] = arguments["status"]
                    if "milestone_id" in arguments and arguments["milestone_id"]:
                        params["milestone_id"] = arguments["milestone_id"]
                    if "title_keyword" in arguments and arguments["title_keyword"]:
                        params["title_keyword"] = arguments["title_keyword"]
                    if "include_subtasks" in arguments:
                        params["include_subtasks"] = arguments["include_subtasks"]
                    if "include_details" in arguments:
                        params["include_details"] = arguments["include_details"]
                    if "limit" in arguments:
                        params["limit"] = arguments["limit"]
                    response = await client.get(
                        f"{self.api_url}/tasks/list",
                        headers=self.headers,
                        params=params
                    )
                
                elif name == "claim_task":
                    response = await client.post(
                        f"{self.api_url}/tasks/claim",
                        headers=self.headers,
                        json=arguments
                    )
                
                elif name == "update_task_status":
                    response = await client.post(
                        f"{self.api_url}/tasks/update-status",
                        headers=self.headers,
                        json=arguments
                    )
                
                elif name == "split_task_into_subtasks":
                    response = await client.post(
                        f"{self.api_url}/tasks/split",
                        headers=self.headers,
                        json=arguments,
                        timeout=30.0
                    )
                
                elif name == "get_task_subtasks":
                    task_id = arguments["task_id"]
                    response = await client.get(
                        f"{self.api_url}/tasks/{task_id}/subtasks",
                        headers=self.headers
                    )
                
                elif name == "update_subtask_status":
                    response = await client.post(
                        f"{self.api_url}/subtasks/update-status",
                        headers=self.headers,
                        json=arguments
                    )
                
                elif name == "get_document_categories":
                    response = await client.get(
                        f"{self.api_url}/documents/categories",
                        headers=self.headers
                    )
                
                elif name == "create_document_category":
                    response = await client.post(
                        f"{self.api_url}/documents/categories",
                        headers=self.headers,
                        json=arguments
                    )
                
                elif name == "list_documents":
                    response = await client.get(
                        f"{self.api_url}/documents",
                        headers=self.headers
                    )
                
                elif name == "search_documents":
                    response = await client.get(
                        f"{self.api_url}/documents/search",
                        headers=self.headers,
                        params=arguments
                    )
                
                elif name == "create_document":
                    response = await client.post(
                        f"{self.api_url}/documents",
                        headers=self.headers,
                        json=arguments
                    )
                
                elif name == "get_document_by_id":
                    document_id = arguments["document_id"]
                    response = await client.get(
                        f"{self.api_url}/documents/{document_id}",
                        headers=self.headers
                    )
                
                elif name == "update_document_by_id":
                    response = await client.put(
                        f"{self.api_url}/documents/by-id",
                        headers=self.headers,
                        json=arguments
                    )
                
                elif name == "delete_document_by_id":
                    document_id = arguments["document_id"]
                    response = await client.delete(
                        f"{self.api_url}/documents/by-id/{document_id}",
                        headers=self.headers
                    )
                
                elif name == "get_document_versions":
                    title = arguments["title"]
                    encoded_title = quote(title, safe='')
                    response = await client.get(
                        f"{self.api_url}/documents/{encoded_title}/versions",
                        headers=self.headers
                    )
                
                elif name == "get_rules_content":
                    response = await client.post(
                        f"{self.api_url}/rules/render",
                        headers=self.headers,
                        json={"ide_type": arguments.get("ide_type")}
                    )
                
                else:
                    return {"error": f"未知工具: {name}"}
                
                # 检查响应状态
                if response.status_code >= 400:
                    # 尝试解析错误详情
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("detail", str(response.text))
                        
                        # 如果 detail 是字典（结构化错误），提取详细信息
                        if isinstance(error_detail, dict):
                            error_message = error_detail.get("message", "操作失败")
                            error_reason = error_detail.get("reason", "")
                            error_suggestion = error_detail.get("suggestion", "")
                            current_status = error_detail.get("current_status", "")
                            required_status = error_detail.get("required_status", "")
                        else:
                            error_message = str(error_detail)
                            error_reason = ""
                            error_suggestion = ""
                            current_status = ""
                            required_status = ""
                    except:
                        error_message = response.text or f"HTTP {response.status_code}"
                        error_reason = ""
                        error_suggestion = ""
                        current_status = ""
                        required_status = ""
                    
                    # 针对不同状态码返回友好的错误信息
                    if response.status_code == 403:
                        logger.warning(f"⚠️ 权限不足: {error_message}")
                        
                        # 构建友好的错误响应
                        error_response = {
                            "success": False,
                            "error": error_message,
                            "error_type": "permission_denied",
                            "status_code": 403
                        }
                        
                        # 添加详细信息（如果有）
                        if error_reason:
                            error_response["reason"] = error_reason
                        if error_suggestion:
                            error_response["suggestion"] = error_suggestion
                        if current_status:
                            error_response["current_status"] = current_status
                        if required_status:
                            error_response["required_status"] = required_status
                        
                        return error_response
                    elif response.status_code == 404:
                        logger.warning(f"⚠️ 资源不存在: {error_message}")
                        return {
                            "success": False,
                            "error": f"资源不存在: {error_message}",
                            "error_type": "not_found",
                            "status_code": 404
                        }
                    elif response.status_code == 400:
                        logger.warning(f"⚠️ 请求参数错误: {error_message}")
                        return {
                            "success": False,
                            "error": f"请求参数错误: {error_message}",
                            "error_type": "bad_request",
                            "status_code": 400
                        }
                    else:
                        logger.error(f"❌ HTTP 错误 {response.status_code}: {error_message}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status_code}: {error_message}",
                            "error_type": "http_error",
                            "status_code": response.status_code
                        }
                
                # 成功响应
                result = response.json()
                logger.info(f"✅ 工具调用成功: {name}")
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP 错误: {e}")
            return {
                "success": False,
                "error": f"网络请求失败: {str(e)}",
                "error_type": "network_error"
            }
        except Exception as e:
            logger.error(f"❌ 调用失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"调用失败: {str(e)}",
                "error_type": "unknown_error"
            }
