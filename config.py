"""
配置文件管理模块
使用JSON存储用户配置，提供配置的加载、保存、验证等功能。
配置存储在：%USERPROFILE%/.deepseek-commit/config.json
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器，使用单例模式确保全局一致"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # 获取用户主目录
            self.user_home = Path(os.environ.get('USERPROFILE', os.path.expanduser('~')))
            self.config_dir = self.user_home / '.deepseek-commit'
            self.config_file = self.config_dir / 'config.json'
            
            # 默认配置
            self.default_config = {
                'api_key': '',
                'model': 'deepseek-chat',
                'language': 'zh-CN',
                'commit_style': 'conventional',
                'temperature': 0.7,
                'max_diff_length': 3000,
                'auto_suggest': True,
                'theme': 'light',
                'window_width': 900,
                'window_height': 700,
                'api_base_url': 'https://api.deepseek.com/v1/chat/completions'
            }
            
            self.config = self.default_config.copy()
            self._load()
            ConfigManager._initialized = True
    
    def _load(self) -> None:
        """从文件加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置，确保所有键都存在
                    self.config = {**self.default_config, **loaded_config}
                logger.info(f"配置已从 {self.config_file} 加载")
            else:
                logger.info("配置文件不存在，使用默认配置")
                self.save()  # 创建默认配置文件
        except json.JSONDecodeError as e:
            logger.error(f"配置文件JSON格式错误: {e}，使用默认配置")
            self.config = self.default_config.copy()
        except Exception as e:
            logger.error(f"加载配置时出错: {e}，使用默认配置")
            self.config = self.default_config.copy()
    
    def save(self) -> bool:
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到 {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"保存配置时出错: {e}")
            return False
    
    def validate(self, language: Optional[str] = None) -> Tuple[bool, str]:
        """
        验证配置是否有效
        返回: (是否有效, 错误信息)
        
        Args:
            language: 可选的语言代码，如果不提供则使用配置中的语言设置
        """
        # 获取语言设置
        lang = language or self.config.get('language', 'zh-CN')
        if lang not in ['zh-CN', 'en']:
            lang = 'zh-CN'
        
        # 错误信息字典
        error_messages = {
            'zh-CN': {
                'no_api_key': 'API Key未设置，请在配置中设置DeepSeek API Key',
                'no_model': '模型名称不能为空',
                'invalid_language': "语言设置无效，必须是 'zh-CN' 或 'en'",
                'invalid_commit_style': "提交风格无效，必须是 'conventional', 'simple' 或 'emoji'",
                'invalid_temperature': '随机性(temperature)必须在0.1-1.0之间',
                'invalid_max_diff_length': '最大差异长度必须至少为100',
            },
            'en': {
                'no_api_key': 'API Key not set, please configure DeepSeek API Key',
                'no_model': 'Model name cannot be empty',
                'invalid_language': "Invalid language setting, must be 'zh-CN' or 'en'",
                'invalid_commit_style': "Invalid commit style, must be 'conventional', 'simple' or 'emoji'",
                'invalid_temperature': 'Temperature must be between 0.1 and 1.0',
                'invalid_max_diff_length': 'Max diff length must be at least 100',
            }
        }
        
        errors = error_messages[lang]
        
        # 检查API Key
        if not self.config.get('api_key'):
            return False, errors['no_api_key']
        
        # 检查模型名称
        if not self.config.get('model'):
            return False, errors['no_model']
        
        # 检查语言
        if self.config.get('language') not in ['zh-CN', 'en']:
            return False, errors['invalid_language']
        
        # 检查提交风格
        if self.config.get('commit_style') not in ['conventional', 'simple', 'emoji']:
            return False, errors['invalid_commit_style']
        
        # 检查temperature范围
        temp = self.config.get('temperature', 0.7)
        if not isinstance(temp, (int, float)) or temp < 0.1 or temp > 1.0:
            return False, errors['invalid_temperature']
        
        # 检查max_diff_length
        max_len = self.config.get('max_diff_length', 3000)
        if not isinstance(max_len, int) or max_len < 100:
            return False, errors['invalid_max_diff_length']
        
        return True, ""
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        self.config[key] = value
    
    def get_api_key(self) -> str:
        """获取API密钥（安全方法）"""
        return self.config.get('api_key', '')
    
    def set_api_key(self, api_key: str) -> None:
        """设置API密钥"""
        self.config['api_key'] = api_key.strip()
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config.copy()
    
    def update(self, new_config: Dict[str, Any]) -> None:
        """更新配置（部分更新）"""
        self.config.update(new_config)
    
    def reset_to_default(self) -> None:
        """重置为默认配置"""
        self.config = self.default_config.copy()
        self.save()
    
    def get_config_path(self) -> str:
        """获取配置文件路径"""
        return str(self.config_file)


# 全局配置管理器实例
def get_config() -> ConfigManager:
    """获取全局配置管理器实例"""
    return ConfigManager()

