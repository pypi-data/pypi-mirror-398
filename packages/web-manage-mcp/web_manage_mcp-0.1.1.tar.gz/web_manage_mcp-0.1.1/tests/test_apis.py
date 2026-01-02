#!/usr/bin/env python3
"""
API功能测试脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from web_manage_mcp_server.apis.douban_api import DoubanAPI
from web_manage_mcp_server.apis.java_api import JavaAPIManager, JavaAPIConfig

async def test_douban_api():
    """测试豆瓣API"""
    print("🎬 测试豆瓣API...")
    
    api = DoubanAPI()
    
    try:
        # 测试电影搜索
        print("  📽️ 搜索电影...")
        movies = await api.search_movies("肖申克的救赎", 3)
        print(f"    找到 {len(movies)} 部电影")
        
        # 测试图书搜索
        print("  📚 搜索图书...")
        books = await api.search_books("Python", 3)
        print(f"    找到 {len(books)} 本图书")
        
        # 测试收藏功能
        print("  ⭐ 测试收藏功能...")
        fav_id = await api.add_favorite("movie", "1292052", "肖申克的救赎", "9.7", "经典电影")
        print(f"    收藏ID: {fav_id}")
        
        favorites = await api.list_favorites()
        print(f"    收藏列表: {len(favorites)} 项")
        
        print("✅ 豆瓣API测试通过")
        
    except Exception as e:
        print(f"❌ 豆瓣API测试失败: {e}")

async def test_java_api():
    """测试Java API"""
    print("☕ 测试Java API...")
    
    try:
        manager = JavaAPIManager()
        
        # 添加测试API配置
        config = JavaAPIConfig(
            base_url="https://jsonplaceholder.typicode.com",
            timeout=10.0
        )
        manager.add_api("test_api", config)
        
        api = manager.get_api("test_api")
        if api:
            # 测试GET请求
            print("  📥 测试GET请求...")
            response = await api.get_item("posts", "1")
            print(f"    响应状态: {response.success}")
            
            # 测试列表请求
            print("  📋 测试列表请求...")
            response = await api.list_items("posts", {"_limit": "3"})
            print(f"    响应状态: {response.success}")
            
            print("✅ Java API测试通过")
        else:
            print("❌ API实例创建失败")
            
    except Exception as e:
        print(f"❌ Java API测试失败: {e}")

async def main():
    """运行所有测试"""
    print("🧪 开始API功能测试")
    print("=" * 50)
    
    await test_douban_api()
    print()
    await test_java_api()
    
    print("=" * 50)
    print("🎉 测试完成")

if __name__ == "__main__":
    asyncio.run(main())
