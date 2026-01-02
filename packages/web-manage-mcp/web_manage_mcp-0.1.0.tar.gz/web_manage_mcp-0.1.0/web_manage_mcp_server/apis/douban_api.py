import httpx
import asyncio
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from asyncio_throttle import Throttler
import json
import time

class DoubanMovie(BaseModel):
    id: str
    title: str
    year: Optional[str] = None
    rating: Optional[str] = None
    directors: List[str] = []
    actors: List[str] = []
    genres: List[str] = []
    summary: Optional[str] = None
    poster: Optional[str] = None

class DoubanBook(BaseModel):
    id: str
    title: str
    author: List[str] = []
    publisher: Optional[str] = None
    pubdate: Optional[str] = None
    rating: Optional[str] = None
    summary: Optional[str] = None
    image: Optional[str] = None

class FavoriteItem(BaseModel):
    id: str
    item_type: str  # movie, book
    item_id: str
    title: str
    rating: Optional[str] = None
    comment: Optional[str] = None
    created_at: str

class DoubanAPI:
    def __init__(self):
        self.base_url = "https://frodo2.douban.com/api/v2"
        self.throttler = Throttler(rate_limit=10, period=60)  # 每分钟最多10次请求
        self.favorites_storage = {}  # 简单的内存存储，实际应用中应使用数据库
        
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """发起HTTP请求"""
        async with self.throttler:
            headers = {
                "User-Agent": "api-client",
                "Referer": "https://www.douban.com"
            }
            
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        f"{self.base_url}{endpoint}",
                        params=params or {},
                        headers=headers,
                        timeout=30.0
                    )
                    response.raise_for_status()
                    return response.json()
                except httpx.HTTPError as e:
                    raise Exception(f"请求失败: {str(e)}")
    
    async def search_movies(self, query: str, count: int = 10) -> List[DoubanMovie]:
        """搜索电影"""
        params = {
            "q": query,
            "count": count
        }
        
        try:
            data = await self._make_request("/search/movie", params)
            movies = []
            
            for item in data.get("subjects", []):
                movie = DoubanMovie(
                    id=item.get("id", ""),
                    title=item.get("title", ""),
                    year=item.get("year", ""),
                    rating=str(item.get("rating", {}).get("average", "")),
                    directors=[d.get("name", "") for d in item.get("directors", [])],
                    actors=[a.get("name", "") for a in item.get("casts", [])[:3]],
                    genres=item.get("genres", []),
                    summary=item.get("summary", ""),
                    poster=item.get("images", {}).get("large", "")
                )
                movies.append(movie)
            
            return movies
        except Exception as e:
            raise Exception(f"搜索电影失败: {str(e)}")
    
    async def get_movie_detail(self, movie_id: str) -> DoubanMovie:
        """获取电影详情"""
        try:
            data = await self._make_request(f"/movie/{movie_id}")
            
            movie = DoubanMovie(
                id=data.get("id", ""),
                title=data.get("title", ""),
                year=data.get("year", ""),
                rating=str(data.get("rating", {}).get("average", "")),
                directors=[d.get("name", "") for d in data.get("directors", [])],
                actors=[a.get("name", "") for a in data.get("casts", [])],
                genres=data.get("genres", []),
                summary=data.get("summary", ""),
                poster=data.get("images", {}).get("large", "")
            )
            
            return movie
        except Exception as e:
            raise Exception(f"获取电影详情失败: {str(e)}")
    
    async def search_books(self, query: str, count: int = 10) -> List[DoubanBook]:
        """搜索图书"""
        params = {
            "q": query,
            "count": count
        }
        
        try:
            data = await self._make_request("/search/book", params)
            books = []
            
            for item in data.get("subjects", []):
                book = DoubanBook(
                    id=item.get("id", ""),
                    title=item.get("title", ""),
                    author=[a.get("name", "") for a in item.get("author", [])],
                    publisher=item.get("publisher", ""),
                    pubdate=item.get("pubdate", ""),
                    rating=str(item.get("rating", {}).get("average", "")),
                    summary=item.get("summary", ""),
                    image=item.get("images", {}).get("large", "")
                )
                books.append(book)
            
            return books
        except Exception as e:
            raise Exception(f"搜索图书失败: {str(e)}")
    
    # CRUD操作 - 收藏管理
    async def add_favorite(self, item_type: str, item_id: str, title: str, 
                          rating: Optional[str] = None, comment: Optional[str] = None) -> str:
        """添加收藏"""
        favorite_id = f"{item_type}_{item_id}_{int(time.time())}"
        
        favorite = FavoriteItem(
            id=favorite_id,
            item_type=item_type,
            item_id=item_id,
            title=title,
            rating=rating,
            comment=comment,
            created_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        self.favorites_storage[favorite_id] = favorite.dict()
        return favorite_id
    
    async def get_favorite(self, favorite_id: str) -> Optional[FavoriteItem]:
        """获取单个收藏"""
        if favorite_id in self.favorites_storage:
            return FavoriteItem(**self.favorites_storage[favorite_id])
        return None
    
    async def list_favorites(self, item_type: Optional[str] = None) -> List[FavoriteItem]:
        """列出所有收藏"""
        favorites = []
        for fav_data in self.favorites_storage.values():
            if item_type is None or fav_data["item_type"] == item_type:
                favorites.append(FavoriteItem(**fav_data))
        
        return sorted(favorites, key=lambda x: x.created_at, reverse=True)
    
    async def update_favorite(self, favorite_id: str, rating: Optional[str] = None, 
                            comment: Optional[str] = None) -> bool:
        """更新收藏"""
        if favorite_id not in self.favorites_storage:
            return False
        
        if rating is not None:
            self.favorites_storage[favorite_id]["rating"] = rating
        if comment is not None:
            self.favorites_storage[favorite_id]["comment"] = comment
        
        return True
    
    async def delete_favorite(self, favorite_id: str) -> bool:
        """删除收藏"""
        if favorite_id in self.favorites_storage:
            del self.favorites_storage[favorite_id]
            return True
        return False
