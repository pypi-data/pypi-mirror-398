import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                self.config = {}
        else:
            self.config = self._get_default_config()
            self.save_config()
    
    def save_config(self) -> None:
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "server": {
                "name": "web-manage-mcp",
                "version": "1.0.0",
                "debug": False
            },
            "apis": {
                "douban": {
                    "enabled": True,
                    "rate_limit": 10
                },
                "java": {
                    "enabled": True,
                    "rate_limit": 30
                }
            },
            "storage": {
                "type": "memory",  # memory, file, database
                "file_path": "data.json"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    def update(self, updates: Dict[str, Any]) -> None:
        """批量更新配置"""
        def deep_update(base_dict: Dict, update_dict: Dict) -> None:
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(self.config, updates)
        self.save_config()

# 全局配置实例
config_manager = ConfigManager()
