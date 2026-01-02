import asyncio
import json
from typing import Any, List
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent

from web_manage_mcp_server.tools.douban_tools import DoubanTools
from web_manage_mcp_server.tools.java_tools import JavaTools
from web_manage_mcp_server.utils.config import config_manager

# 创建MCP服务器实例
server = Server("web-manage-mcp")

# 初始化工具模块
douban_tools = DoubanTools()
java_tools = JavaTools()

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """列出可用资源"""
    return [
        Resource(
            uri="douban://favorites",
            name="豆瓣收藏列表",
            description="用户的豆瓣收藏列表",
            mimeType="application/json",
        ),
        Resource(
            uri="config://server",
            name="服务器配置",
            description="MCP服务器配置信息",
            mimeType="application/json",
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """读取资源内容"""
    if uri == "douban://favorites":
        favorites = await douban_tools.douban_api.list_favorites()
        return json.dumps([fav.dict() for fav in favorites], ensure_ascii=False, indent=2)
    elif uri == "config://server":
        return json.dumps(config_manager.config, ensure_ascii=False, indent=2)
    else:
        raise ValueError(f"未知资源: {uri}")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """列出可用工具"""
    tools = []
    
    # 添加豆瓣工具
    if config_manager.get("apis.douban.enabled", True):
        tools.extend(douban_tools.get_tools())
    
    # 添加Java API工具
    if config_manager.get("apis.java.enabled", True):
        tools.extend(java_tools.get_tools())
    
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> List[TextContent]:
    """处理工具调用"""
    try:
        # 豆瓣工具
        douban_tool_names = [
            "search_movies", "get_movie_detail", "search_books",
            "add_favorite", "get_favorite", "list_favorites", 
            "update_favorite", "delete_favorite"
        ]
        
        # Java API工具
        java_tool_names = [
            "java_add_api", "java_create_item", "java_get_item",
            "java_update_item", "java_patch_item", "java_delete_item",
            "java_list_items", "java_search_items", "java_batch_operation",
            "java_list_apis"
        ]
        
        if name in douban_tool_names:
            return await douban_tools.handle_tool_call(name, arguments)
        elif name in java_tool_names:
            return await java_tools.handle_tool_call(name, arguments)
        else:
            raise ValueError(f"未知工具: {name}")
    
    except Exception as e:
        return [TextContent(type="text", text=f"错误: {str(e)}")]

async def run_server():
    """启动MCP服务器"""
    from mcp.server.stdio import stdio_server
    
    server_name = config_manager.get("server.name", "web-manage-mcp")
    server_version = config_manager.get("server.version", "1.0.0")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=server_name,
                server_version=server_version,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

def main():
    """同步入口点，用于 uvx 和命令行调用"""
    asyncio.run(run_server())

if __name__ == "__main__":
    main()
