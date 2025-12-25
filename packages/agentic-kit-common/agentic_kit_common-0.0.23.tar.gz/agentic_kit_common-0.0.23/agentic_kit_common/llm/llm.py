import inspect
import logging
import os
from typing import Any, Dict, Literal, get_args, Optional

import httpx
from dotenv import load_dotenv, find_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from agentic_kit_common.config import ConfigManager

load_dotenv(find_dotenv(usecwd=True))

logger = logging.getLogger(__name__)

LLMType = Literal["basic", "vision"]


class LLMManager:
    """
    LLM 管理器 - 支持从配置、ConfigManager 和环境变量读取，支持多模型切换
    
    支持的配置方式（优先级从高到低）：
    1. 环境变量（BASIC_MODEL_api_key 等）
    2. 初始化时传入的 config 参数
    3. 配置管理器 (config_manager)
    
    环境变量格式（使用 _ 表示层级，model 名称可以包含 -）：
        # 单模型
        BASIC_MODEL_api_key=sk-xxx
        BASIC_MODEL_base_url=http://example.com/v1
        BASIC_MODEL_model=qwen-model
        
        # 多模型（多层级配置）
        BASIC_MODEL_default=qwen3-235b-a22b
        BASIC_MODEL_models_qwen3-235b-a22b_api_key=sk-xxx
        BASIC_MODEL_models_qwen3-235b-a22b_base_url=http://example.com/v1
        BASIC_MODEL_models_qwen3-235b-a22b_model=qwen-model
        BASIC_MODEL_models_gpt4_api_key=sk-yyy
        BASIC_MODEL_models_gpt4_base_url=https://api.openai.com/v1
        BASIC_MODEL_models_gpt4_model=gpt-4
    
    Config 格式：
        # 单模型配置
        {
            "BASIC_MODEL": {
                "base_url": "http://example.com/v1",
                "model": "qwen-model",
                "api_key": "sk-xxx",
                "temperature": 0.1
            }
        }
        
        # 多模型配置
        {
            "BASIC_MODEL": {
                "default": "qwen3-235b-a22b",
                "models": {
                    "qwen3-235b-a22b": {
                        "base_url": "http://example.com/v1",
                        "model": "qwen-model",
                        "api_key": "sk-xxx"
                    },
                    "gpt4": {
                        "base_url": "https://api.openai.com/v1",
                        "model": "gpt-4",
                        "api_key": "sk-yyy"
                    }
                }
            },
            "VISION_MODEL": {
                "default": "qwen3-vl-235b-instruct",
                "models": {
                    "qwen3-vl-235b-instruct": {...},
                    "llm_ocr": {...}
                }
            }
        }
    """
    
    def __init__(
        self, 
        config: Optional[Dict[str, Any]] = None,
        config_manager: Optional[ConfigManager] = None,
        use_cache: bool = True
    ):
        """
        初始化 LLM 管理器
        
        Args:
            config: 外部传入的配置字典（可选）
            config_manager: 配置管理器实例（可选）
            use_cache: 是否使用缓存（默认True）
        
        Examples:
            # 方式1: 只使用环境变量
            manager = LLMManager()
            llm = manager.get_llm()
            
            # 方式2: 传入配置
            manager = LLMManager(config={
                "BASIC_MODEL": {
                    "base_url": "http://example.com/v1",
                    "model": "qwen",
                    "api_key": "sk-xxx"
                }
            })
            llm = manager.get_llm()
            
            # 方式3: 使用配置管理器
            from agentic_kit_common.config import ConfigManager
            config_mgr = ConfigManager(config={...})
            manager = LLMManager(config_manager=config_mgr)
            llm = manager.get_llm()
            
            # 方式4: 混合使用（环境变量会覆盖 config）
            manager = LLMManager(config={...})
            # 同时设置环境变量 BASIC_MODEL_temperature=0.5
            llm = manager.get_llm()  # temperature 会使用环境变量的值
            
            # 方式5: 多模型配置
            manager = LLMManager(config={
                "VISION_MODEL": {
                    "default": "qwen3-vl-235b-instruct",
                    "models": {
                        "qwen3-vl-235b-instruct": {...},
                        "llm_ocr": {...}
                    }
                }
            })
            llm = manager.get_llm(llm_type="vision")  # 使用默认模型
            llm_ocr = manager.get_llm(llm_type="vision", model_name="llm_ocr")  # 切换到 llm_ocr
        """
        self._config = config or {}
        self._config_manager = config_manager
        self._use_cache = use_cache
        self._llm_cache: dict[tuple, BaseChatModel] = {}
        
    def _get_llm_type_config_key(self, llm_type: str) -> str:
        """获取 LLM 类型对应的配置键"""
        return f"{llm_type.upper()}_MODEL"
    
    def _get_config_llm_conf(self, llm_type: str) -> Dict[str, Any]:
        """
        从传入的 config 或 config_manager 获取 LLM 配置
        
        Args:
            llm_type: LLM 类型（basic 或 vision）
            
        Returns:
            配置字典
        """
        config_key = self._get_llm_type_config_key(llm_type)
        
        # 优先使用直接传入的 config
        if self._config:
            return self._config.get(config_key, {}).copy() if isinstance(self._config.get(config_key), dict) else {}
        
        # 使用 config_manager
        if self._config_manager:
            return self._config_manager.get_llm_config(config_key)
        
        return {}
    
    def _get_env_llm_conf(self, llm_type: str) -> Dict[str, Any]:
        """
        从环境变量获取 LLM 配置（支持单模型和多模型）
        
        环境变量格式（_ 表示层级，model 名称可以包含 -）: 
        - 单模型: {LLM_TYPE}_MODEL_{KEY}
        - 多模型: {LLM_TYPE}_MODEL_models_{MODEL_NAME}_{KEY}
        
        例如: 
        - BASIC_MODEL_api_key
        - BASIC_MODEL_models_qwen3-235b-a22b_api_key
        """
        prefix = f"{llm_type.upper()}_MODEL_"
        conf = {}
        models_conf = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # 移除前缀，得到配置路径
                # 例如: models_qwen3-235b-a22b_base_url
                path = key[len(prefix):]
                
                # 按 _ 分割路径
                parts = path.split('_')
                
                # 检查是否是多模型配置（以 models_ 开头）
                if len(parts) >= 3 and parts[0] == 'models':
                    # 多模型配置: models_{model_name}_{config_key}
                    # 需要找到 model_name 的结束位置
                    
                    # 从第二个部分开始，找到第一个已知的配置键
                    known_config_keys = {
                        'api_key', 'base_url', 'model', 'temperature', 
                        'max_tokens', 'max_retries', 'timeout', 
                        'parallel_tool_calls', 'verify_ssl', 'streaming'
                    }
                    model_parts = []
                    config_key_parts = []
                    found_config_key = False
                    
                    for i in range(len(parts) - 1, 0, -1):  # 从后往前，跳过第一个 'models'
                        part = parts[i]
                        # 尝试组合成已知的配置键
                        current_key = '_'.join([part] + config_key_parts)
                        
                        if current_key in known_config_keys:
                            # 找到了完整的配置键
                            config_key_parts.insert(0, part)
                            # 剩余的都是 model_name
                            model_parts = parts[1:i]
                            found_config_key = True
                            break
                        else:
                            config_key_parts.insert(0, part)
                    
                    if found_config_key and model_parts:
                        # model_name 可能包含 - 和 _，我们保持原样
                        model_name = '_'.join(model_parts)
                        config_key = '_'.join(config_key_parts)
                        
                        if model_name not in models_conf:
                            models_conf[model_name] = {}
                        
                        # 类型转换
                        if config_key in ['temperature', 'max_tokens', 'max_retries', 'timeout']:
                            try:
                                if '.' in value:
                                    models_conf[model_name][config_key] = float(value)
                                else:
                                    models_conf[model_name][config_key] = int(value)
                            except ValueError:
                                models_conf[model_name][config_key] = value
                        elif config_key in ['parallel_tool_calls', 'verify_ssl', 'streaming']:
                            models_conf[model_name][config_key] = value.lower() in ('true', '1', 'yes')
                        else:
                            models_conf[model_name][config_key] = value
                    else:
                        # 无法解析，跳过
                        logger.warning(f"无法解析环境变量: {key}")
                else:
                    # 单模型配置或顶层配置（如 default）
                    config_key = '_'.join(parts)
                    
                    # 类型转换
                    if config_key in ['temperature', 'max_tokens', 'max_retries', 'timeout']:
                        try:
                            if '.' in value:
                                conf[config_key] = float(value)
                            else:
                                conf[config_key] = int(value)
                        except ValueError:
                            conf[config_key] = value
                    elif config_key in ['parallel_tool_calls', 'verify_ssl', 'streaming']:
                        conf[config_key] = value.lower() in ('true', '1', 'yes')
                    else:
                        conf[config_key] = value
        
        # 如果有多模型配置，构建多模型结构
        if models_conf:
            if 'default' not in conf:
                # 如果没有指定 default，使用第一个模型
                conf['default'] = list(models_conf.keys())[0]
            conf['models'] = models_conf
        
        return conf
    
    def _get_merged_llm_conf(self, llm_type: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取合并后的 LLM 配置（config/config_manager + 环境变量）
        
        支持单模型和多模型配置：
        - 单模型：直接返回配置
        - 多模型：根据 model_name 选择对应的模型配置
        
        优先级：环境变量 > config > config_manager
        
        Args:
            llm_type: LLM 类型（basic 或 vision）
            model_name: 模型名称（用于多模型配置）
            
        Returns:
            合并后的配置字典
        """
        # 先从 config 或 config_manager 获取
        config_conf = self._get_config_llm_conf(llm_type)
        
        # 再从环境变量获取
        env_conf = self._get_env_llm_conf(llm_type)
        
        # 合并配置（环境变量优先级更高）
        # 先合并顶层配置
        merged_conf = {**config_conf, **env_conf}
        
        # 检查是否是多模型配置
        is_multi_model = 'models' in merged_conf and isinstance(merged_conf.get('models'), dict)
        
        if is_multi_model:
            models = merged_conf['models']
            default_model = merged_conf.get('default')
            target_model_name = model_name or default_model
            
            if not target_model_name:
                available_models = list(models.keys())
                raise ValueError(
                    f"多模型配置需要指定 model_name 或设置 default。\n"
                    f"可用模型: {available_models}"
                )
            
            if target_model_name not in models:
                available_models = list(models.keys())
                raise ValueError(
                    f"模型 '{target_model_name}' 未在 '{llm_type}' 配置中找到。\n"
                    f"可用模型: {available_models}"
                )
            
            # 返回选中的模型配置
            return models[target_model_name]
        else:
            # 单模型配置
            if model_name:
                logger.warning(
                    f"指定了 model_name='{model_name}'，但配置为单模型，将忽略 model_name"
                )
            return merged_conf
    
    def _create_llm(self, llm_type: LLMType, llm_conf: Dict[str, Any]) -> BaseChatModel:
        """根据配置创建 LLM 实例"""
        if not llm_conf:
            raise ValueError(
                f"未找到 LLM 类型 '{llm_type}' 的配置。\n"
                f"请通过以下方式之一提供配置：\n"
                f"1. 设置环境变量，例如：{llm_type.upper()}_MODEL_api_key, "
                f"{llm_type.upper()}_MODEL_base_url, {llm_type.upper()}_MODEL_model\n"
                f"2. 初始化时传入 config 参数"
            )
        
        llm_conf = llm_conf.copy()
        
        # 设置默认值
        llm_conf.setdefault("max_retries", 3)
        llm_conf.setdefault("parallel_tool_calls", False)
        
        # 处理 SSL 验证
        verify_ssl = llm_conf.pop("verify_ssl", True)
        if not verify_ssl:
            llm_conf["http_client"] = httpx.Client(verify=False)
            llm_conf["http_async_client"] = httpx.AsyncClient(verify=False)
        
        # 过滤只保留 ChatOpenAI 支持的参数
        constructor_params = inspect.signature(ChatOpenAI).parameters
        filtered_conf = {k: v for k, v in llm_conf.items() if k in constructor_params}
        
        logger.info(f"创建LLM实例: type={llm_type}, model={filtered_conf.get('model')}, "
                   f"base_url={filtered_conf.get('base_url')}")
        
        return ChatOpenAI(**filtered_conf)
    
    def get_llm(
        self,
        llm_type: LLMType = "basic",
        model_name: Optional[str] = None,
        force_new_instance: bool = False,
    ) -> BaseChatModel:
        """
        获取 LLM 实例（从 config/config_manager 或环境变量读取配置）
        
        配置优先级：环境变量 > config 参数 > config_manager
        
        Args:
            llm_type: LLM 类型 ('basic' 或 'vision')，默认 'basic'
            model_name: 模型名称（用于多模型配置时切换模型）
            force_new_instance: 是否强制创建新实例（忽略缓存）
            
        Returns:
            BaseChatModel 实例
            
        Examples:
            # 单模型使用
            manager = LLMManager()
            llm = manager.get_llm()
            
            # 多模型配置
            manager = LLMManager(config={
                "VISION_MODEL": {
                    "default": "qwen3-vl-235b-instruct",
                    "models": {
                        "qwen3-vl-235b-instruct": {
                            "base_url": "http://example.com/v1",
                            "model": "qwen-vl",
                            "api_key": "sk-xxx"
                        },
                        "llm_ocr": {
                            "base_url": "https://dashscope.aliyuncs.com/v1",
                            "model": "qwen-vl-ocr-latest",
                            "api_key": "sk-yyy"
                        }
                    }
                }
            })
            
            # 使用默认模型
            llm_default = manager.get_llm(llm_type="vision")
            
            # 切换到 llm_ocr
            llm_ocr = manager.get_llm(llm_type="vision", model_name="llm_ocr")
            
        环境变量示例:
            # 单模型
            export BASIC_MODEL_api_key=sk-xxx
            export BASIC_MODEL_base_url=http://example.com/v1
            export BASIC_MODEL_model=qwen-model
            
            # 多模型（_ 表示层级，model 名称可以包含 -）
            export VISION_MODEL_default=qwen3-vl-235b-instruct
            export VISION_MODEL_models_qwen3-vl-235b-instruct_api_key=sk-xxx
            export VISION_MODEL_models_qwen3-vl-235b-instruct_base_url=http://example.com/v1
            export VISION_MODEL_models_qwen3-vl-235b-instruct_model=Qwen3-VL
            export VISION_MODEL_models_llm-ocr_api_key=sk-yyy
            export VISION_MODEL_models_llm-ocr_base_url=https://dashscope.aliyuncs.com/v1
            export VISION_MODEL_models_llm-ocr_model=qwen-vl-ocr-latest
        """
        # 检查缓存
        cache_key = (llm_type, model_name)
        if self._use_cache and not force_new_instance and cache_key in self._llm_cache:
            logger.debug(f"使用缓存的LLM实例: type={llm_type}, model={model_name}")
            return self._llm_cache[cache_key]
        
        # 获取合并后的配置（config/config_manager + 环境变量）
        llm_conf = self._get_merged_llm_conf(llm_type, model_name)
        
        # 创建新实例
        llm = self._create_llm(llm_type, llm_conf)
        
        # 存入缓存
        if self._use_cache and not force_new_instance:
            self._llm_cache[cache_key] = llm
        
        return llm
    
    def get_basic_llm(
        self,
        model_name: Optional[str] = None,
        force_new_instance: bool = False,
    ) -> BaseChatModel:
        """
        快捷方法：获取 basic 类型的 LLM
        
        这是最常用的方法，等同于 get_llm(llm_type="basic", ...)
        
        Args:
            model_name: 模型名称（用于多模型配置）
            force_new_instance: 是否强制创建新实例
        """
        return self.get_llm("basic", model_name, force_new_instance)
    
    def get_vision_llm(
        self,
        model_name: Optional[str] = None,
        force_new_instance: bool = False,
    ) -> BaseChatModel:
        """
        快捷方法：获取 vision 类型的 LLM
        
        等同于 get_llm(llm_type="vision", ...)
        
        Args:
            model_name: 模型名称（用于多模型配置）
            force_new_instance: 是否强制创建新实例
        """
        return self.get_llm("vision", model_name, force_new_instance)
    
    def get_configured_models(self) -> dict[str, dict]:
        """
        获取所有已配置的模型信息（从 config/config_manager 和环境变量）
        
        Returns:
            字典，按 LLM 类型分组
            
            单模型格式：
            {
                "basic": {
                    "model": "qwen-model",
                    "base_url": "http://example.com/v1"
                }
            }
            
            多模型格式：
            {
                "vision": {
                    "default": "qwen3-vl-235b-instruct",
                    "models": {
                        "qwen3-vl-235b-instruct": {...},
                        "llm_ocr": {...}
                    }
                }
            }
        
        Examples:
            models = manager.get_configured_models()
            
            # 单模型
            if 'model' in models.get('basic', {}):
                print(f"Basic 模型: {models['basic']['model']}")
            
            # 多模型
            if 'models' in models.get('vision', {}):
                print(f"Vision 默认模型: {models['vision']['default']}")
                print(f"Vision 可用模型: {list(models['vision']['models'].keys())}")
        """
        try:
            configured_models: dict[str, dict] = {}
            
            for llm_type in get_args(LLMType):
                try:
                    # 获取原始配置（不展开多模型）
                    config_conf = self._get_config_llm_conf(llm_type)
                    env_conf = self._get_env_llm_conf(llm_type)
                    merged_conf = {**config_conf, **env_conf}
                    
                    # 检查是否有配置
                    if merged_conf:
                        # 检查是多模型还是单模型
                        if 'models' in merged_conf:
                            # 多模型配置
                            configured_models[llm_type] = merged_conf
                        elif merged_conf.get("model"):
                            # 单模型配置
                            configured_models[llm_type] = merged_conf
                except Exception:
                    # 如果某个类型配置不存在，跳过
                    continue
            
            return configured_models
        
        except Exception as e:
            logger.error(f"获取 LLM 配置失败: {e}")
            return {}
    
    def clear_cache(self):
        """清除 LLM 实例缓存"""
        self._llm_cache.clear()
        logger.info("LLM缓存已清除")
    
    def __repr__(self) -> str:
        """返回 LLMManager 的字符串表示"""
        has_config = bool(self._config)
        has_config_manager = self._config_manager is not None
        cache_size = len(self._llm_cache)
        return (
            f"LLMManager(has_config={has_config}, has_config_manager={has_config_manager}, "
            f"use_cache={self._use_cache}, cached_instances={cache_size})"
        )
