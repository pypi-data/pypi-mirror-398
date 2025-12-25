import logging
import os
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)


load_dotenv(find_dotenv(usecwd=True))
_config_root_path = os.getenv("DELTA_CONFIG_PATH", None)


class ConfigManager:
    """
    配置管理器 - 支持多种配置源
    
    支持的配置方式（优先级从高到低）：
    1. 环境变量（最高优先级）
    2. 初始化时传入的 config 参数
    3. 配置文件（config_path 或默认的 conf.yaml）
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None
    ):
        """
        初始化配置管理器
        
        Args:
            config: 直接传入的配置字典（适合外部 SDK 调用）
                格式示例：
                {
                    "BASIC_MODEL": {
                        "base_url": "http://...",
                        "model": "qwen",
                        "api_key": "sk-xxx"
                    },
                    "VISION_MODEL": {
                        "base_url": "http://...",
                        "model": "vision",
                        "api_key": "sk-xxx"
                    },
                    "RAG_CLIENT": {
                        "base_url": "http://...",
                        "timeout": 120
                    },
                    "DATABASE_CLIENT": {
                        "base_url": "http://...",
                        "timeout": 120
                    },
                    "MCP_SETTINGS": {
                        "default_servers": {
                            "file-processor": {
                                "transport": "streamable_http",
                                "url": "http://...",
                                "enabled_tools": ["convert_to_markdown"]
                            }
                        }
                    }
                }
            
            config_path: 配置文件路径（可选）
                - 如果不提供，默认使用项目根目录的 conf.yaml
                - 如果提供，使用指定路径的配置文件
        
        Examples:
            # 方式1: 直接传入配置（外部 SDK 推荐）
            config_mgr = ConfigManager(config={
                "BASIC_MODEL": {...},
                "RAG_CLIENT": {...}
            })
            
            # 方式2: 指定配置文件路径
            config_mgr = ConfigManager(config_path="/path/to/conf.yaml")
            
            # 方式3: 使用默认配置文件（项目根目录/conf.yaml）
            config_mgr = ConfigManager()
        """
        self._external_config = config or {}
        self._config_path = config_path or _config_root_path
        self._config_cache: Optional[Dict[str, Any]] = None
    
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载配置（带缓存）
        
        Args:
            force_reload: 是否强制重新加载
            
        Returns:
            Dict[str, Any]: 完整配置字典
        """
        if self._config_cache is not None and not force_reload:
            return self._config_cache
        
        # 如果有外部配置，直接使用
        if self._external_config:
            self._config_cache = self._external_config.copy()
            logger.info("使用外部传入的配置")
            return self._config_cache
        
        # 从配置文件加载
        conf_path = self._config_path
        
        if not os.path.exists(conf_path):
            logger.warning(f"配置文件不存在: {conf_path}，使用空配置")
            self._config_cache = {}
            return self._config_cache
        
        try:
            with open(conf_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            self._config_cache = config
            logger.info(f"成功加载配置文件: {conf_path}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._config_cache = {}
        
        return self._config_cache
    
    def get_llm_config(self, model_type: str = "BASIC_MODEL") -> Dict[str, Any]:
        """
        获取LLM配置
        
        Args:
            model_type: 模型类型，可选 "BASIC_MODEL", "VISION_MODEL"
            
        Returns:
            Dict[str, Any]: LLM配置
        """
        config = self.load_config()
        base_config = config.get(model_type, {}).copy() if isinstance(config.get(model_type), dict) else {}
        
        # 环境变量覆盖（优先级最高）
        prefix = f"{model_type}__"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                conf_key = key[len(prefix):].lower()
                base_config[conf_key] = value
        
        return base_config
    
    def get_rag_config(self) -> Dict[str, Any]:
        """
        获取RAG客户端配置
        
        Returns:
            Dict[str, Any]: RAG配置
        """
        config = self.load_config()
        rag_config = config.get("RAG_CLIENT", {}).copy() if isinstance(config.get("RAG_CLIENT"), dict) else {}
        
        # 支持环境变量覆盖
        env_overrides = {
            "base_url": os.getenv("RAG_CLIENT__base_url"),
            "timeout": os.getenv("RAG_CLIENT__timeout"),
            "max_retries": os.getenv("RAG_CLIENT__max_retries"),
        }
        
        for key, value in env_overrides.items():
            if value is not None:
                rag_config[key] = value
        
        return rag_config
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """
        获取MCP服务器配置
        
        Returns:
            Dict[str, Any]: MCP配置
        """
        config = self.load_config()
        return config.get("MCP_SETTINGS", {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        获取数据库客户端配置

        Returns:
            Dict[str, Any]: 数据库配置
        """
        config = self.load_config()
        db_config = config.get("DATABASE_CLIENT", {}).copy() if isinstance(config.get("DATABASE_CLIENT"), dict) else {}

        # 支持环境变量覆盖
        env_overrides = {
            "base_url": os.getenv("DATABASE_CLIENT__base_url"),
            "timeout": os.getenv("DATABASE_CLIENT__timeout"),
        }

        for key, value in env_overrides.items():
            if value is not None:
                db_config[key] = value

        return db_config
    
    def get_full_config(self) -> Dict[str, Any]:
        """
        获取完整配置
        
        Returns:
            Dict[str, Any]: 完整配置字典
        """
        return self.load_config()
    
    def reload_config(self):
        """重新加载配置（清除缓存）"""
        self._config_cache = None
        logger.info("配置已重新加载")


# ============================================================================
# 全局默认配置管理器（向后兼容）
# ============================================================================

_default_config_manager: Optional[ConfigManager] = None


def _get_default_config_manager() -> ConfigManager:
    """获取默认配置管理器实例"""
    global _default_config_manager
    if _default_config_manager is None:
        _default_config_manager = ConfigManager()
    return _default_config_manager


def set_config_manager(config_manager: ConfigManager):
    """
    设置全局配置管理器（用于外部 SDK）
    
    Args:
        config_manager: ConfigManager 实例
        
    Example:
        # 在外部 SDK 中设置自定义配置
        config_mgr = ConfigManager(config={...})
        set_config_manager(config_mgr)
    """
    global _default_config_manager
    _default_config_manager = config_manager
    logger.info("已设置全局配置管理器")


# ============================================================================
# 向后兼容的函数接口
# ============================================================================

def load_config(force_reload: bool = False) -> Dict[str, Any]:
    """
    加载配置文件（带缓存）
    
    Args:
        force_reload: 是否强制重新加载
        
    Returns:
        Dict[str, Any]: 完整配置字典
    """
    return _get_default_config_manager().load_config(force_reload)


def get_llm_config(model_type: str = "BASIC_MODEL") -> Dict[str, Any]:
    """
    获取LLM配置
    
    Args:
        model_type: 模型类型，可选 "BASIC_MODEL", "VISION_MODEL"
        
    Returns:
        Dict[str, Any]: LLM配置
    """
    return _get_default_config_manager().get_llm_config(model_type)


def get_rag_config() -> Dict[str, Any]:
    """
    获取RAG客户端配置
    
    Returns:
        Dict[str, Any]: RAG配置
    """
    return _get_default_config_manager().get_rag_config()


def get_database_config() -> Dict[str, Any]:
    """
    获取数据库客户端配置

    Returns:
        Dict[str, Any]: 数据库配置
    """
    return _get_default_config_manager().get_database_config()


def get_full_config() -> Dict[str, Any]:
    """
    获取完整配置
    
    Returns:
        Dict[str, Any]: 完整配置字典
    """
    return _get_default_config_manager().get_full_config()


def reload_config():
    """重新加载配置（清除缓存）"""
    _get_default_config_manager().reload_config()
