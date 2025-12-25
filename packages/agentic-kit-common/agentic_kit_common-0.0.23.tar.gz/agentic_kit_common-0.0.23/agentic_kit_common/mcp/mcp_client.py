import logging
import os
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv, find_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool
from agentic_kit_common.config import ConfigManager

load_dotenv(find_dotenv(usecwd=True))

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class MCPToolsNotAvailableError(Exception):
    """MCP工具不可用异常"""
    pass


class MCPClient:
    """
    MCP (Model Context Protocol) 客户端
    
    支持的配置方式（优先级从高到低）：
    1. 环境变量（MCP_SERVERS_{SERVER_NAME}_{KEY}）
    2. 初始化时传入的 config 参数
    3. 配置管理器 (config_manager)
    
    环境变量格式（使用 _ 表示层级，服务器名可以包含 -）：
        MCP_SERVERS_{SERVER_NAME}_{KEY}
    
    例如：
        # 单个单词的服务器名
        export MCP_SERVERS_web_url=http://example.com/mcp
        export MCP_SERVERS_web_transport=streamable_http
        
        # 包含中划线的服务器名
        export MCP_SERVERS_web-search_url=http://example.com/mcp
        export MCP_SERVERS_web-search_transport=streamable_http
        export MCP_SERVERS_web-search_enabled_tools=web_search,crawl_page
        
        export MCP_SERVERS_file-processor_url=http://example.com/file
        export MCP_SERVERS_file-processor_transport=sse
    
    Config 格式：
        {
            "web-search": {
                "url": "http://your-server.com/mcp",
                "transport": "streamable_http",
                "enabled_tools": ["web_search", "crawl_page"]
            },
            "file-processor": {
                "url": "http://your-server.com/file",
                "transport": "sse"
            }
        }
    
    Examples:
        # 方式1: 只使用环境变量
        client = MCPClient()
        
        # 方式2: 直接传入配置（外部 SDK 推荐）
        client = MCPClient(config={
            "web-search": {
                "url": "http://your-server.com/mcp",
                "transport": "streamable_http",
                "enabled_tools": ["web_search", "crawl_page"]
            }
        })
        
        # 方式3: 使用配置管理器
        from agentic_kit_common.config import ConfigManager
        config_mgr = ConfigManager(config={
            "MCP_SERVERS": {
                "web-search": {...}
            }
        })
        client = MCPClient(config_manager=config_mgr)
        
        # 方式4: 混合使用（环境变量会覆盖 config）
        client = MCPClient(config={...})
        # 同时设置环境变量会覆盖 config 中的对应值
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        config_manager: Optional[ConfigManager] = None
    ):
        """
        初始化MCP客户端
        
        Args:
            config: 直接传入的配置字典（可选）
                格式示例：
                {
                    "web-search": {
                        "url": "http://...",
                        "transport": "sse" | "streamable_http",
                        "enabled_tools": ["tool1", "tool2"]  # 可选，不传则使用所有工具
                    },
                    "file-processor": {
                        "url": "http://...",
                        "transport": "sse"
                    }
                }
            config_manager: 配置管理器实例（可选）
        """
        self._config = config or {}
        self._config_manager = config_manager
        self._client: Optional[MultiServerMCPClient] = None
        self._initialized = False
        self._enabled_tools_map: Dict[str, List[str]] = {}  # 服务器名 -> 启用的工具列表
        self._server_tools_cache: Dict[str, List[BaseTool]] = {}  # 服务器名 -> 工具列表缓存
    
    def _get_env_mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        从环境变量获取 MCP 服务器配置
        
        环境变量格式（_ 表示层级，服务器名可以包含 -）: 
        MCP_SERVERS_{SERVER_NAME}_{KEY}
        例如: MCP_SERVERS_web-search_url
        
        Returns:
            服务器配置字典
        """
        servers = {}
        prefix = "MCP_SERVERS_"
        
        # 收集所有相关的环境变量
        mcp_env_vars = {k: v for k, v in os.environ.items() if k.startswith(prefix)}
        
        # 已知的配置键
        known_config_keys = {'url', 'transport', 'enabled_tools'}
        
        # 按服务器名分组
        for env_key, env_value in mcp_env_vars.items():
            # 移除前缀，得到路径
            # 例如: web-search_url
            path = env_key[len(prefix):]
            
            # 按 _ 分割路径
            parts = path.split('_')
            
            if len(parts) < 2:
                continue
            
            # 从后往前找，识别配置键
            # 例如: ['web-search', 'url'] 或 ['my-file-processor', 'enabled', 'tools']
            server_parts = []
            config_key_parts = []
            found_config_key = False
            
            for i in range(len(parts) - 1, -1, -1):
                part = parts[i]
                # 尝试组合成已知的配置键
                current_key = '_'.join([part] + config_key_parts)
                
                if current_key in known_config_keys:
                    # 找到了完整的配置键
                    config_key_parts.insert(0, part)
                    # 剩余的都是服务器名
                    server_parts = parts[:i]
                    found_config_key = True
                    break
                else:
                    config_key_parts.insert(0, part)
            
            if found_config_key and server_parts:
                # 服务器名可能包含 - 和 _，保持原样
                server_name = '_'.join(server_parts)
                config_key = '_'.join(config_key_parts)
                
                # 初始化服务器配置
                if server_name not in servers:
                    servers[server_name] = {}
                
                # 处理特殊字段
                if config_key == 'enabled_tools':
                    # enabled_tools 用逗号分隔
                    servers[server_name]['enabled_tools'] = [t.strip() for t in env_value.split(',') if t.strip()]
                else:
                    servers[server_name][config_key] = env_value
            else:
                # 无法解析，跳过
                logger.warning(f"无法解析环境变量: {env_key}")
        
        return servers
    
    def _get_config_mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        从传入的 config 或 config_manager 获取 MCP 服务器配置
        
        Returns:
            服务器配置字典
        """
        if self._config:
            return self._config
        
        if self._config_manager:
            mcp_config = self._config_manager.get_mcp_config()
            # ConfigManager 返回的可能还有 default_servers 包装，需要兼容
            if 'default_servers' in mcp_config:
                return mcp_config['default_servers']
            return mcp_config
        
        return {}
    
    def _get_merged_mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """
        获取合并后的 MCP 服务器配置（config + 环境变量）
        
        优先级：环境变量 > config
        
        Returns:
            合并后的服务器配置字典
        """
        # 先从 config 获取
        config_servers = self._get_config_mcp_servers()
        
        # 再从环境变量获取
        env_servers = self._get_env_mcp_servers()
        
        # 合并配置（环境变量优先级更高）
        merged_servers = {}
        
        # 先添加 config 中的服务器
        for server_name, server_config in config_servers.items():
            merged_servers[server_name] = server_config.copy() if isinstance(server_config, dict) else {}
        
        # 用环境变量覆盖或添加
        for server_name, server_config in env_servers.items():
            if server_name in merged_servers:
                # 合并配置（环境变量覆盖）
                merged_servers[server_name].update(server_config)
            else:
                # 新增服务器
                merged_servers[server_name] = server_config
        
        return merged_servers
    
    def _get_mcp_config(self) -> Dict[str, Any]:
        """
        获取 MCP 配置（包含合并后的服务器配置）
        
        Returns:
            Dict[str, Any]: MCP 配置（兼容旧格式，返回带 default_servers 包装）
        """
        merged_servers = self._get_merged_mcp_servers()
        # 为了兼容性，返回 default_servers 包装
        return {'default_servers': merged_servers}
    
    async def initialize(self):
        """初始化MCP客户端"""
        if self._initialized:
            return
        
        try:
            mcp_config = self._get_mcp_config()
            default_servers = mcp_config.get('default_servers', {})
            
            if not default_servers:
                logger.warning("配置文件中没有MCP服务器")
                return
            
            logger.info(f"开始初始化 {len(default_servers)} 个MCP服务器...")
            
            server_configs = {}
            for server_name, server_config in default_servers.items():
                url = server_config.get('url')
                transport = server_config.get('transport', 'sse')
                enabled_tools = server_config.get('enabled_tools')
                
                if not url:
                    logger.warning(f"服务器 {server_name} 缺少URL配置")
                    continue
                
                server_configs[server_name] = {
                    'url': url,
                    'transport': transport
                }
                
                if enabled_tools:
                    self._enabled_tools_map[server_name] = enabled_tools
                    logger.info(f"服务器 {server_name} 启用工具: {enabled_tools}")
                else:
                    logger.info(f"服务器 {server_name} 将使用所有可用工具")
            
            if not server_configs:
                logger.warning("没有有效的MCP服务器配置")
                return
            
            self._client = MultiServerMCPClient(server_configs)
            
            self._initialized = True
            
            tools = await self.get_all_tools()
            logger.info(f"成功初始化MCP客户端，加载了 {len(tools)} 个工具")
            
        except Exception as e:
            logger.error(f"MCP客户端初始化失败: {str(e)}", exc_info=True)
            raise MCPToolsNotAvailableError(f"初始化失败: {str(e)}") from e
    
    async def get_all_tools(self) -> List[BaseTool]:
        """
        获取所有MCP工具
        
        如果配置了 enabled_tools，只返回启用的工具；
        否则返回所有可用工具。
        
        Returns:
            List[BaseTool]: 所有可用工具的列表（LangChain工具）
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._client:
            logger.warning("MCP客户端未初始化")
            return []
        
        try:
            all_tools = await self._client.get_tools()
            
            if not self._enabled_tools_map:
                logger.debug(f"获取到 {len(all_tools)} 个MCP工具（使用所有工具）")
                return all_tools
            
            enabled_tools = []
            all_enabled_tool_names = set()
            
            for server_name, tool_names in self._enabled_tools_map.items():
                all_enabled_tool_names.update(tool_names)
            
            for tool in all_tools:
                if tool.name in all_enabled_tool_names:
                    enabled_tools.append(tool)
            
            logger.info(f"获取到 {len(all_tools)} 个MCP工具，启用了 {len(enabled_tools)} 个工具")
            if len(enabled_tools) < len(all_enabled_tool_names):
                missing_tools = all_enabled_tool_names - {t.name for t in enabled_tools}
                logger.warning(f"配置中的某些工具未找到: {missing_tools}")
            
            return enabled_tools
            
        except Exception as e:
            logger.error(f"获取MCP工具失败: {str(e)}", exc_info=True)
            return []

    async def get_tool_by_name(self, tool_name: str) -> Optional[BaseTool]:
        """
        根据名称获取特定工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具实例，如果未找到返回None
        """
        tools = await self.get_all_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None
    
    async def get_tools_by_server(self, server_names: str | List[str]) -> List[BaseTool]:
        """
        根据服务器名称获取工具（支持单个或多个服务器）
        
        Args:
            server_names: 服务器名称或服务器名称列表
            
        Returns:
            List[BaseTool]: 工具列表（如果是多个服务器，会合并去重）
            
        Examples:
            # 获取单个服务器的工具
            tools = await mcp_client.get_tools_by_server("web_search_server")
            
            # 获取多个服务器的工具
            tools = await mcp_client.get_tools_by_server(["web_search_server", "file-processor"])
            
            # 也支持传入逗号分隔的字符串
            tools = await mcp_client.get_tools_by_server("web_search_server,file-processor")
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._client:
            logger.warning("MCP客户端未初始化")
            return []
        
        # 统一处理输入格式
        if isinstance(server_names, str):
            # 支持逗号分隔的字符串
            if ',' in server_names:
                server_list = [s.strip() for s in server_names.split(',') if s.strip()]
            else:
                server_list = [server_names]
        else:
            server_list = server_names
        
        if not server_list:
            logger.warning("未提供有效的服务器名称")
            return []
        
        # 收集所有工具（去重）
        all_server_tools = []
        seen_tool_names = set()
        
        for server_name in server_list:
            # 检查缓存
            if server_name in self._server_tools_cache:
                logger.debug(f"使用缓存的服务器工具: {server_name}")
                server_tools = self._server_tools_cache[server_name]
            else:
                # 获取该服务器的工具
                server_tools = await self._get_single_server_tools(server_name)
                # 缓存结果
                self._server_tools_cache[server_name] = server_tools
            
            # 添加到结果中（去重）
            for tool in server_tools:
                if tool.name not in seen_tool_names:
                    all_server_tools.append(tool)
                    seen_tool_names.add(tool.name)
        
        if len(server_list) == 1:
            logger.info(f"服务器 {server_list[0]} 有 {len(all_server_tools)} 个工具")
        else:
            logger.info(f"从 {len(server_list)} 个服务器获取了 {len(all_server_tools)} 个工具（已去重）")
        
        return all_server_tools
    
    async def _get_single_server_tools(self, server_name: str) -> List[BaseTool]:
        """
        获取单个服务器的工具（内部方法）
        
        Args:
            server_name: 服务器名称
            
        Returns:
            List[BaseTool]: 该服务器的工具列表
        """
        try:
            all_tools = await self._client.get_tools()
            server_tools = []
            
            for tool in all_tools:
                # 方式1: 检查 tool.server 属性
                if hasattr(tool, 'server') and tool.server == server_name:
                    server_tools.append(tool)
                # 方式2: 检查 tool.metadata
                elif hasattr(tool, 'metadata') and tool.metadata is not None and tool.metadata.get('server') == server_name:
                    server_tools.append(tool)
                # 方式3: 检查 enabled_tools_map 配置
                elif server_name in self._enabled_tools_map:
                    if tool.name in self._enabled_tools_map[server_name]:
                        server_tools.append(tool)
            
            # 如果前面的方式都没找到，但配置了 enabled_tools，尝试按工具名匹配
            if not server_tools and server_name in self._enabled_tools_map:
                enabled_tool_names = self._enabled_tools_map[server_name]
                server_tools = [
                    tool for tool in all_tools 
                    if tool.name in enabled_tool_names
                ]
            
            logger.debug(f"服务器 {server_name} 有 {len(server_tools)} 个工具")
            return server_tools
            
        except Exception as e:
            logger.error(f"获取服务器 {server_name} 的工具失败: {str(e)}", exc_info=True)
            return []
    
    async def list_servers(self) -> List[str]:
        """
        列出所有配置的服务器名称
        
        Returns:
            List[str]: 服务器名称列表
            
        Examples:
            servers = await mcp_client.list_servers()
            print(f"已配置的服务器: {servers}")
        """
        mcp_config = self._get_mcp_config()
        default_servers = mcp_config.get('default_servers', {})
        return list(default_servers.keys())
    
    def close(self):
        """
        清理 MCP 客户端
        """
        if self._client and self._initialized:
            self._initialized = False
            self._client = None
            self._server_tools_cache.clear()
            logger.info("MCP客户端已清理")
