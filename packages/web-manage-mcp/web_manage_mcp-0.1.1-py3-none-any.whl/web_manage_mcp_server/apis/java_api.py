import httpx
import asyncio
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel
from asyncio_throttle import Throttler
import json

class JavaAPIConfig(BaseModel):
    """Java API配置"""
    base_url: str
    timeout: float = 30.0
    headers: Dict[str, str] = {}
    auth_token: Optional[str] = None

class JavaAPIResponse(BaseModel):
    """Java API响应模型"""
    success: bool
    data: Any = None
    message: str = ""
    code: int = 200

class JavaAPI:
    """Java API调用客户端"""
    
    def __init__(self, config: JavaAPIConfig):
        self.config = config
        self.throttler = Throttler(rate_limit=30, period=60)  # 每分钟最多30次请求
        
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **self.config.headers
        }
        
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
            
        return headers
    
    async def _make_request(self, method: str, endpoint: str, 
                          data: Optional[Dict] = None, 
                          params: Optional[Dict] = None) -> JavaAPIResponse:
        """发起HTTP请求"""
        async with self.throttler:
            headers = self._get_headers()
            url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.request(
                        method=method.upper(),
                        url=url,
                        json=data,
                        params=params,
                        headers=headers,
                        timeout=self.config.timeout
                    )
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    return JavaAPIResponse(
                        success=True,
                        data=result,
                        message="请求成功",
                        code=response.status_code
                    )
                    
                except httpx.HTTPError as e:
                    return JavaAPIResponse(
                        success=False,
                        message=f"请求失败: {str(e)}",
                        code=getattr(e.response, 'status_code', 500) if hasattr(e, 'response') else 500
                    )
                except Exception as e:
                    return JavaAPIResponse(
                        success=False,
                        message=f"未知错误: {str(e)}",
                        code=500
                    )
    
    # CRUD操作
    async def create_item(self, endpoint: str, data: Dict) -> JavaAPIResponse:
        """创建资源 (POST)"""
        return await self._make_request("POST", endpoint, data=data)
    
    async def get_item(self, endpoint: str, item_id: Optional[str] = None, 
                      params: Optional[Dict] = None) -> JavaAPIResponse:
        """获取资源 (GET)"""
        if item_id:
            endpoint = f"{endpoint}/{item_id}"
        return await self._make_request("GET", endpoint, params=params)
    
    async def update_item(self, endpoint: str, item_id: str, data: Dict) -> JavaAPIResponse:
        """更新资源 (PUT)"""
        endpoint = f"{endpoint}/{item_id}"
        return await self._make_request("PUT", endpoint, data=data)
    
    async def patch_item(self, endpoint: str, item_id: str, data: Dict) -> JavaAPIResponse:
        """部分更新资源 (PATCH)"""
        endpoint = f"{endpoint}/{item_id}"
        return await self._make_request("PATCH", endpoint, data=data)
    
    async def delete_item(self, endpoint: str, item_id: str) -> JavaAPIResponse:
        """删除资源 (DELETE)"""
        endpoint = f"{endpoint}/{item_id}"
        return await self._make_request("DELETE", endpoint)
    
    async def list_items(self, endpoint: str, params: Optional[Dict] = None) -> JavaAPIResponse:
        """列出资源列表 (GET)"""
        return await self._make_request("GET", endpoint, params=params)
    
    async def search_items(self, endpoint: str, query: str, 
                          params: Optional[Dict] = None) -> JavaAPIResponse:
        """搜索资源"""
        search_params = {"q": query, **(params or {})}
        return await self._make_request("GET", f"{endpoint}/search", params=search_params)
    
    async def batch_operation(self, endpoint: str, operation: str, 
                            items: List[Dict]) -> JavaAPIResponse:
        """批量操作"""
        data = {
            "operation": operation,
            "items": items
        }
        return await self._make_request("POST", f"{endpoint}/batch", data=data)

class JavaAPIManager:
    """Java API管理器，支持多个API实例"""
    
    def __init__(self):
        self.apis: Dict[str, JavaAPI] = {}
    
    def add_api(self, name: str, config: JavaAPIConfig) -> None:
        """添加API实例"""
        self.apis[name] = JavaAPI(config)
    
    def get_api(self, name: str) -> Optional[JavaAPI]:
        """获取API实例"""
        return self.apis.get(name)
    
    def list_apis(self) -> List[str]:
        """列出所有API名称"""
        return list(self.apis.keys())
    
    def remove_api(self, name: str) -> bool:
        """移除API实例"""
        if name in self.apis:
            del self.apis[name]
            return True
        return False

