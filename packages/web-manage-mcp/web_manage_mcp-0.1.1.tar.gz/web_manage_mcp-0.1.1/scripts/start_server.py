#!/usr/bin/env python3
"""
Web管理MCP服务器启动脚本
支持豆瓣API和Java API调用
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """启动MCP服务器"""
    # 确保在正确的目录中运行
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    
    print("=" * 60)
    print("🚀 Web管理MCP服务器")
    print("=" * 60)
    print("📋 支持的功能:")
    print("  • 豆瓣API调用 (电影/图书搜索、收藏管理)")
    print("  • Java API调用 (通用CRUD操作)")
    print("  • 配置管理")
    print("=" * 60)
    print("🔧 服务器将通过stdio与客户端通信")
    print("⏹️  按Ctrl+C停止服务器")
    print("=" * 60)
    
    try:
        # 检查依赖
        print("🔍 检查依赖...")
        result = subprocess.run([sys.executable, "-c", "import mcp, httpx, pydantic"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ 依赖检查失败，请运行: uv sync")
            sys.exit(1)
        
        print("✅ 依赖检查通过")
        print("🎯 启动服务器...")
        
        # 运行主程序
        subprocess.run([sys.executable, "web_manage_mcp_server/main.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
