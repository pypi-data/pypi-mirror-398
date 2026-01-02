import json
from typing import Any, List, Dict
from mcp.types import Tool, TextContent
from ..apis.java_api import JavaAPIManager, JavaAPIConfig

class JavaTools:
    """Java API相关的MCP工具"""
    
    def __init__(self):
        self.api_manager = JavaAPIManager()
    
    def get_tools(self) -> List[Tool]:
        """获取所有Java API相关工具"""
        return [
            Tool(
                name="java_add_api",
                description="添加Java API配置",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "API名称"
                        },
                        "base_url": {
                            "type": "string",
                            "description": "API基础URL"
                        },
                        "auth_token": {
                            "type": "string",
                            "description": "认证令牌（可选）"
                        },
                        "timeout": {
                            "type": "number",
                            "description": "请求超时时间（秒），默认30",
                            "default": 30.0
                        },
                        "headers": {
                            "type": "object",
                            "description": "额外的请求头（可选）"
                        }
                    },
                    "required": ["name", "base_url"]
                }
            ),
            Tool(
                name="java_create_item",
                description="创建资源 (POST)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {
                            "type": "string",
                            "description": "API名称"
                        },
                        "endpoint": {
                            "type": "string",
                            "description": "API端点"
                        },
                        "data": {
                            "type": "object",
                            "description": "要创建的数据"
                        }
                    },
                    "required": ["api_name", "endpoint", "data"]
                }
            ),
            Tool(
                name="java_get_item",
                description="获取资源 (GET)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {
                            "type": "string",
                            "description": "API名称"
                        },
                        "endpoint": {
                            "type": "string",
                            "description": "API端点"
                        },
                        "item_id": {
                            "type": "string",
                            "description": "资源ID（可选）"
                        },
                        "params": {
                            "type": "object",
                            "description": "查询参数（可选）"
                        }
                    },
                    "required": ["api_name", "endpoint"]
                }
            ),
            Tool(
                name="java_update_item",
                description="更新资源 (PUT)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {
                            "type": "string",
                            "description": "API名称"
                        },
                        "endpoint": {
                            "type": "string",
                            "description": "API端点"
                        },
                        "item_id": {
                            "type": "string",
                            "description": "资源ID"
                        },
                        "data": {
                            "type": "object",
                            "description": "要更新的数据"
                        }
                    },
                    "required": ["api_name", "endpoint", "item_id", "data"]
                }
            ),
            Tool(
                name="java_patch_item",
                description="部分更新资源 (PATCH)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {
                            "type": "string",
                            "description": "API名称"
                        },
                        "endpoint": {
                            "type": "string",
                            "description": "API端点"
                        },
                        "item_id": {
                            "type": "string",
                            "description": "资源ID"
                        },
                        "data": {
                            "type": "object",
                            "description": "要更新的数据"
                        }
                    },
                    "required": ["api_name", "endpoint", "item_id", "data"]
                }
            ),
            Tool(
                name="java_delete_item",
                description="删除资源 (DELETE)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {
                            "type": "string",
                            "description": "API名称"
                        },
                        "endpoint": {
                            "type": "string",
                            "description": "API端点"
                        },
                        "item_id": {
                            "type": "string",
                            "description": "资源ID"
                        }
                    },
                    "required": ["api_name", "endpoint", "item_id"]
                }
            ),
            Tool(
                name="java_list_items",
                description="列出资源列表",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {
                            "type": "string",
                            "description": "API名称"
                        },
                        "endpoint": {
                            "type": "string",
                            "description": "API端点"
                        },
                        "params": {
                            "type": "object",
                            "description": "查询参数（可选）"
                        }
                    },
                    "required": ["api_name", "endpoint"]
                }
            ),
            Tool(
                name="java_search_items",
                description="搜索资源",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {
                            "type": "string",
                            "description": "API名称"
                        },
                        "endpoint": {
                            "type": "string",
                            "description": "API端点"
                        },
                        "query": {
                            "type": "string",
                            "description": "搜索关键词"
                        },
                        "params": {
                            "type": "object",
                            "description": "额外查询参数（可选）"
                        }
                    },
                    "required": ["api_name", "endpoint", "query"]
                }
            ),
            Tool(
                name="java_batch_operation",
                description="批量操作",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "api_name": {
                            "type": "string",
                            "description": "API名称"
                        },
                        "endpoint": {
                            "type": "string",
                            "description": "API端点"
                        },
                        "operation": {
                            "type": "string",
                            "description": "操作类型"
                        },
                        "items": {
                            "type": "array",
                            "description": "操作项目列表"
                        }
                    },
                    "required": ["api_name", "endpoint", "operation", "items"]
                }
            ),
            Tool(
                name="java_list_apis",
                description="列出所有已配置的Java API",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> List[TextContent]:
        """处理Java API工具调用"""
        try:
            if name == "java_add_api":
                api_name = arguments["name"]
                base_url = arguments["base_url"]
                auth_token = arguments.get("auth_token")
                timeout = arguments.get("timeout", 30.0)
                headers = arguments.get("headers", {})
                
                config = JavaAPIConfig(
                    base_url=base_url,
                    timeout=timeout,
                    headers=headers,
                    auth_token=auth_token
                )
                
                self.api_manager.add_api(api_name, config)
                return [TextContent(type="text", text=f"Java API '{api_name}' 配置成功")]
            
            elif name == "java_create_item":
                api_name = arguments["api_name"]
                endpoint = arguments["endpoint"]
                data = arguments["data"]
                
                api = self.api_manager.get_api(api_name)
                if not api:
                    return [TextContent(type="text", text=f"API '{api_name}' 不存在")]
                
                response = await api.create_item(endpoint, data)
                return [TextContent(type="text", text=json.dumps(response.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_get_item":
                api_name = arguments["api_name"]
                endpoint = arguments["endpoint"]
                item_id = arguments.get("item_id")
                params = arguments.get("params")
                
                api = self.api_manager.get_api(api_name)
                if not api:
                    return [TextContent(type="text", text=f"API '{api_name}' 不存在")]
                
                response = await api.get_item(endpoint, item_id, params)
                return [TextContent(type="text", text=json.dumps(response.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_update_item":
                api_name = arguments["api_name"]
                endpoint = arguments["endpoint"]
                item_id = arguments["item_id"]
                data = arguments["data"]
                
                api = self.api_manager.get_api(api_name)
                if not api:
                    return [TextContent(type="text", text=f"API '{api_name}' 不存在")]
                
                response = await api.update_item(endpoint, item_id, data)
                return [TextContent(type="text", text=json.dumps(response.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_patch_item":
                api_name = arguments["api_name"]
                endpoint = arguments["endpoint"]
                item_id = arguments["item_id"]
                data = arguments["data"]
                
                api = self.api_manager.get_api(api_name)
                if not api:
                    return [TextContent(type="text", text=f"API '{api_name}' 不存在")]
                
                response = await api.patch_item(endpoint, item_id, data)
                return [TextContent(type="text", text=json.dumps(response.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_delete_item":
                api_name = arguments["api_name"]
                endpoint = arguments["endpoint"]
                item_id = arguments["item_id"]
                
                api = self.api_manager.get_api(api_name)
                if not api:
                    return [TextContent(type="text", text=f"API '{api_name}' 不存在")]
                
                response = await api.delete_item(endpoint, item_id)
                return [TextContent(type="text", text=json.dumps(response.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_list_items":
                api_name = arguments["api_name"]
                endpoint = arguments["endpoint"]
                params = arguments.get("params")
                
                api = self.api_manager.get_api(api_name)
                if not api:
                    return [TextContent(type="text", text=f"API '{api_name}' 不存在")]
                
                response = await api.list_items(endpoint, params)
                return [TextContent(type="text", text=json.dumps(response.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_search_items":
                api_name = arguments["api_name"]
                endpoint = arguments["endpoint"]
                query = arguments["query"]
                params = arguments.get("params")
                
                api = self.api_manager.get_api(api_name)
                if not api:
                    return [TextContent(type="text", text=f"API '{api_name}' 不存在")]
                
                response = await api.search_items(endpoint, query, params)
                return [TextContent(type="text", text=json.dumps(response.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_batch_operation":
                api_name = arguments["api_name"]
                endpoint = arguments["endpoint"]
                operation = arguments["operation"]
                items = arguments["items"]
                
                api = self.api_manager.get_api(api_name)
                if not api:
                    return [TextContent(type="text", text=f"API '{api_name}' 不存在")]
                
                response = await api.batch_operation(endpoint, operation, items)
                return [TextContent(type="text", text=json.dumps(response.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "java_list_apis":
                apis = self.api_manager.list_apis()
                return [TextContent(type="text", text=json.dumps(apis, ensure_ascii=False, indent=2))]
            
            else:
                raise ValueError(f"未知工具: {name}")
        
        except Exception as e:
            return [TextContent(type="text", text=f"错误: {str(e)}")]
