import json
from typing import Any, List
from mcp.types import Tool, TextContent
from ..apis.douban_api import DoubanAPI

class DoubanTools:
    """豆瓣API相关的MCP工具"""
    
    def __init__(self):
        self.douban_api = DoubanAPI()
    
    def get_tools(self) -> List[Tool]:
        """获取所有豆瓣相关工具"""
        return [
            Tool(
                name="search_movies",
                description="搜索豆瓣电影",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词"
                        },
                        "count": {
                            "type": "integer",
                            "description": "返回结果数量，默认10",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_movie_detail",
                description="获取电影详细信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "movie_id": {
                            "type": "string",
                            "description": "电影ID"
                        }
                    },
                    "required": ["movie_id"]
                }
            ),
            Tool(
                name="search_books",
                description="搜索豆瓣图书",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词"
                        },
                        "count": {
                            "type": "integer",
                            "description": "返回结果数量，默认10",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="add_favorite",
                description="添加收藏",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_type": {
                            "type": "string",
                            "description": "类型：movie 或 book"
                        },
                        "item_id": {
                            "type": "string",
                            "description": "项目ID"
                        },
                        "title": {
                            "type": "string",
                            "description": "标题"
                        },
                        "rating": {
                            "type": "string",
                            "description": "评分（可选）"
                        },
                        "comment": {
                            "type": "string",
                            "description": "评论（可选）"
                        }
                    },
                    "required": ["item_type", "item_id", "title"]
                }
            ),
            Tool(
                name="get_favorite",
                description="获取收藏详情",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "favorite_id": {
                            "type": "string",
                            "description": "收藏ID"
                        }
                    },
                    "required": ["favorite_id"]
                }
            ),
            Tool(
                name="list_favorites",
                description="列出收藏列表",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "item_type": {
                            "type": "string",
                            "description": "过滤类型：movie 或 book（可选）"
                        }
                    }
                }
            ),
            Tool(
                name="update_favorite",
                description="更新收藏",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "favorite_id": {
                            "type": "string",
                            "description": "收藏ID"
                        },
                        "rating": {
                            "type": "string",
                            "description": "新评分（可选）"
                        },
                        "comment": {
                            "type": "string",
                            "description": "新评论（可选）"
                        }
                    },
                    "required": ["favorite_id"]
                }
            ),
            Tool(
                name="delete_favorite",
                description="删除收藏",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "favorite_id": {
                            "type": "string",
                            "description": "收藏ID"
                        }
                    },
                    "required": ["favorite_id"]
                }
            )
        ]
    
    async def handle_tool_call(self, name: str, arguments: dict[str, Any]) -> List[TextContent]:
        """处理豆瓣工具调用"""
        try:
            if name == "search_movies":
                query = arguments["query"]
                count = arguments.get("count", 10)
                movies = await self.douban_api.search_movies(query, count)
                result = [movie.dict() for movie in movies]
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
            elif name == "get_movie_detail":
                movie_id = arguments["movie_id"]
                movie = await self.douban_api.get_movie_detail(movie_id)
                return [TextContent(type="text", text=json.dumps(movie.dict(), ensure_ascii=False, indent=2))]
            
            elif name == "search_books":
                query = arguments["query"]
                count = arguments.get("count", 10)
                books = await self.douban_api.search_books(query, count)
                result = [book.dict() for book in books]
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
            elif name == "add_favorite":
                item_type = arguments["item_type"]
                item_id = arguments["item_id"]
                title = arguments["title"]
                rating = arguments.get("rating")
                comment = arguments.get("comment")
                
                favorite_id = await self.douban_api.add_favorite(item_type, item_id, title, rating, comment)
                return [TextContent(type="text", text=f"收藏添加成功，ID: {favorite_id}")]
            
            elif name == "get_favorite":
                favorite_id = arguments["favorite_id"]
                favorite = await self.douban_api.get_favorite(favorite_id)
                if favorite:
                    return [TextContent(type="text", text=json.dumps(favorite.dict(), ensure_ascii=False, indent=2))]
                else:
                    return [TextContent(type="text", text="收藏不存在")]
            
            elif name == "list_favorites":
                item_type = arguments.get("item_type")
                favorites = await self.douban_api.list_favorites(item_type)
                result = [fav.dict() for fav in favorites]
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            
            elif name == "update_favorite":
                favorite_id = arguments["favorite_id"]
                rating = arguments.get("rating")
                comment = arguments.get("comment")
                
                success = await self.douban_api.update_favorite(favorite_id, rating, comment)
                if success:
                    return [TextContent(type="text", text="收藏更新成功")]
                else:
                    return [TextContent(type="text", text="收藏不存在")]
            
            elif name == "delete_favorite":
                favorite_id = arguments["favorite_id"]
                success = await self.douban_api.delete_favorite(favorite_id)
                if success:
                    return [TextContent(type="text", text="收藏删除成功")]
                else:
                    return [TextContent(type="text", text="收藏不存在")]
            
            else:
                raise ValueError(f"未知工具: {name}")
        
        except Exception as e:
            return [TextContent(type="text", text=f"错误: {str(e)}")]
