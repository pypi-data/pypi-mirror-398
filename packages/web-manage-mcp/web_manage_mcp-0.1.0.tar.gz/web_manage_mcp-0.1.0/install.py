#!/usr/bin/env python3
"""
Web Manage MCP Server 快速安装脚本
支持通过 uvx 直接安装和配置 MCP 服务器
"""

import json
import os
import sys
import platform
from pathlib import Path

def get_config_path():
    """获取 Claude Desktop 配置文件路径"""
    system = platform.system()
    
    if system == "Windows":
        return Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        return Path.home() / ".config" / "claude" / "claude_desktop_config.json"

def create_mcp_config():
    """创建 MCP 服务器配置"""
    config = {
        "mcpServers": {
            "web-manage-mcp": {
                "command": "uvx",
                "args": ["web-manage-mcp"],
                "env": {}
            }
        }
    }
    return config

def update_claude_config():
    """更新 Claude Desktop 配置"""
    config_path = get_config_path()
    
    # 确保配置目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 读取现有配置或创建新配置
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            try:
                existing_config = json.load(f)
            except json.JSONDecodeError:
                existing_config = {}
    else:
        existing_config = {}
    
    # 添加或更新 MCP 服务器配置
    if "mcpServers" not in existing_config:
        existing_config["mcpServers"] = {}
    
    existing_config["mcpServers"]["web-manage-mcp"] = {
        "command": "uvx",
        "args": ["web-manage-mcp"],
        "env": {}
    }
    
    # 写入配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(existing_config, f, indent=2, ensure_ascii=False)
    
    return config_path

def print_installation_guide():
    """打印安装指南"""
    print("🚀 Web Manage MCP Server 安装指南")
    print("=" * 50)
    print()
    print("1. 通过 uvx 安装:")
    print("   uvx install web-manage-mcp")
    print()
    print("2. 或者从本地安装:")
    print("   uvx install .")
    print()
    print("3. 直接运行 (无需安装):")
    print("   uvx run web-manage-mcp")
    print()
    print("4. 测试安装:")
    print("   web-manage-mcp --help")
    print()
    print("📋 MCP 客户端配置:")
    print("-" * 30)
    
    config_path = get_config_path()
    print(f"配置文件位置: {config_path}")
    print()
    print("配置内容:")
    config = create_mcp_config()
    print(json.dumps(config, indent=2, ensure_ascii=False))
    print()
    
    print("🔧 自动配置 Claude Desktop:")
    print("   python install.py --configure")
    print()
    
    print("💡 使用示例:")
    print("   # 搜索电影")
    print("   search_movies({\"query\": \"肖申克的救赎\"})")
    print()
    print("   # 添加 API 配置")
    print("   java_add_api({\"name\": \"my_api\", \"base_url\": \"https://api.example.com\"})")

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--configure":
        try:
            config_path = update_claude_config()
            print(f"✅ 已成功更新 Claude Desktop 配置: {config_path}")
            print("🔄 请重启 Claude Desktop 以应用配置")
        except Exception as e:
            print(f"❌ 配置更新失败: {e}")
            sys.exit(1)
    else:
        print_installation_guide()

if __name__ == "__main__":
    main()
