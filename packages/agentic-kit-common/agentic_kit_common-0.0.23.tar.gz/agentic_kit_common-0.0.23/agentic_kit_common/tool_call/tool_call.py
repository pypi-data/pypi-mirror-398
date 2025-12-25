import asyncio
import logging
from typing import Any, List, Dict, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


async def call_tool_with_llm(
    llm: BaseChatModel,
    tools: List[Any],
    prompt: str,
    system_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    让 LLM 自主选择并调用工具（直接调用，不使用 ToolNode）
    
    流程：
    1. LLM 根据 prompt 选择工具
    2. 直接调用工具的 ainvoke 方法
    3. 返回统一格式的结果
    
    Args:
        llm: 语言模型
        tools: 可用工具列表
        prompt: 用户 prompt（告诉 LLM 要做什么）
        system_message: 系统消息（可选）
        
    Returns:
        {
            'success': bool,
            'content': str,
            'tool_name': str,
            'tool_args': dict,
            'error': str  # 如果失败
        }
    
    使用示例:
        result = await call_tool_with_llm(
            llm=self.llm,
            tools=self.tools,
            prompt="处理这个PDF文件: /path/to/file.pdf"
        )
    """
    try:
        logger.info(f"开始工具调用: prompt={prompt[:100]}...")
        
        # 构建消息
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        
        # 绑定工具到 LLM
        llm_with_tools = llm.bind_tools(tools)
        
        # 步骤 1: LLM 选择工具
        logger.debug("步骤 1: LLM 正在选择工具...")
        response = await llm_with_tools.ainvoke(messages)
        
        # 检查是否有工具调用
        if not hasattr(response, 'tool_calls') or not response.tool_calls:
            logger.warning("LLM 没有调用任何工具")
            return {
                'success': False,
                'error': 'LLM 未能选择合适的工具',
                'llm_response': response.content if hasattr(response, 'content') else str(response)
            }
        
        tool_call = response.tool_calls[0]
        tool_name = tool_call.get('name')
        tool_args = tool_call.get('args', {})
        
        logger.info(f"步骤 2: LLM 选择了工具 '{tool_name}，参数: {tool_args}'")
        logger.debug(f"工具参数: {tool_args}")
        
        # 步骤 2: 查找并执行工具
        logger.debug("步骤 3: 执行工具...")
        
        # 查找工具
        selected_tool = None
        for tool in tools:
            if tool.name == tool_name:
                selected_tool = tool
                break
        
        if not selected_tool:
            raise ValueError(f"工具不存在: {tool_name}")
        
        # 直接调用工具
        result = await selected_tool.ainvoke(tool_args)
        
        # 处理结果 - 智能识别不同工具的返回格式
        logger.debug(f"工具返回原始类型: {type(result)}")
        logger.debug(f"工具返回原始内容(前200字符): {str(result)[:200]}")
        
        if isinstance(result, str):
            try:
                import json
                parsed = json.loads(result)
                if isinstance(parsed, dict):
                    content = (
                        parsed.get("content") or
                        parsed.get("result") or
                        result  # 保留原字符串
                    )
                else:
                    content = parsed
                logger.debug(f"JSON解析成功，解析后类型: {type(content)}")
            except (json.JSONDecodeError, ValueError):
                content = result
                logger.debug("无法解析为JSON，保持原字符串")
        elif isinstance(result, list):
            content = result
        elif isinstance(result, dict):
            content = (
                result.get("content") or
                result.get("result") or
                str(result)
            )
        else:
            content = str(result)
        
        logger.info(f"步骤 4: 工具调用成功，返回内容类型: {type(content)}, 长度: {len(str(content))}")
        
        return {
            'success': True,
            'content': content,
            'tool_name': tool_name,
            'tool_args': tool_args
        }
        
    except Exception as e:
        logger.error(f"工具调用失败: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


async def call_tool_directly(
    tools: List[Any],
    tool_name: str,
    tool_args: Dict[str, Any]
) -> Dict[str, Any]:
    """
    直接调用指定的工具（不通过 LLM 选择）
    
    Args:
        tools: 工具列表
        tool_name: 工具名称
        tool_args: 工具参数
        
    Returns:
        {
            'success': bool,
            'content': str,
            'tool_name': str,
            'error': str
        }
    
    使用示例:
        result = await call_tool_directly(
            tools=self.tools,
            tool_name="pdf_reader",
            tool_args={"file_path": "/path/to/file.pdf"}
        )
    """
    try:
        logger.info(f"直接调用工具: {tool_name}")
        logger.debug(f"工具参数: {tool_args}")
        
        # 查找工具
        selected_tool = None
        for tool in tools:
            if tool.name == tool_name:
                selected_tool = tool
                break
        
        if not selected_tool:
            raise ValueError(f"工具不存在: {tool_name}")
        
        result = await selected_tool.ainvoke(tool_args)
        
        logger.debug(f"工具返回原始类型: {type(result)}")
        logger.debug(f"工具返回原始内容(前200字符): {str(result)[:200]}")
        
        if isinstance(result, str):
            try:
                import json
                parsed = json.loads(result)
                if isinstance(parsed, dict):
                    content = (
                        parsed.get("content") or
                        parsed.get("result") or
                        result  
                    )
                else:
                    content = parsed
                logger.debug(f"JSON解析成功，解析后类型: {type(content)}")
            except (json.JSONDecodeError, ValueError):
                content = result
                logger.debug("无法解析为JSON，保持原字符串")
        elif isinstance(result, list):
            content = result
        elif isinstance(result, dict):
            content = (
                result.get("content") or
                result.get("result") or
                str(result)
            )
        else:
            content = str(result)
        
        logger.info(f"工具调用成功，返回内容类型: {type(content)}, 长度: {len(str(content))}")
        
        return {
            'success': True,
            'content': content,
            'tool_name': tool_name
        }
        
    except Exception as e:
        logger.error(f"直接调用工具失败: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'tool_name': tool_name
        }


async def call_multiple_tools_with_llm(
    llm: BaseChatModel,
    tools: List[Any],
    prompt: str,
    required_tools: Optional[List[str]] = None,
    system_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    让 LLM 依次调用多个工具（顺序执行）
    
    流程：
    1. LLM 根据 prompt 选择第一个工具
    2. 执行工具
    3. 继续让 LLM 选择下一个工具（基于前面的结果）
    4. 重复直到完成所有所需工具调用
    
    Args:
        llm: 语言模型
        tools: 可用工具列表
        prompt: 用户 prompt（告诉 LLM 要做什么）
        required_tools: 必须调用的工具列表（可选）
        system_message: 系统消息（可选）
        
    Returns:
        {
            'success': bool,
            'combined_content': str,  # 所有工具结果的组合
            'tools_used': List[str],  # 使用的工具列表
            'individual_results': List[Dict],  # 每个工具的单独结果
            'error': str  # 如果失败
        }
    
    使用示例:
        result = await call_multiple_tools_with_llm(
            llm=self.llm,
            tools=self.tools,
            prompt="处理这个图片，既要描述也要提取文字",
            required_tools=['img_to_text', 'convert_to_markdown']
        )
    """
    try:
        logger.info(f"开始顺序多工具调用: prompt={prompt[:100]}...")
        if required_tools:
            logger.info(f"必须调用的工具: {required_tools}")
        
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=prompt))
        
        llm_with_tools = llm.bind_tools(tools)
        
        tool_map = {tool.name: tool for tool in tools}
        
        all_results = []
        tools_used = []
        max_iterations = len(required_tools) if required_tools else 5
        
        for iteration in range(max_iterations):
            logger.debug(f"迭代 {iteration + 1}/{max_iterations}")
            
            response = await llm_with_tools.ainvoke(messages)
            
            if not hasattr(response, 'tool_calls') or not response.tool_calls:
                logger.info(f"迭代 {iteration + 1}: LLM 没有调用工具，可能已完成")
                break
            
            tool_call = response.tool_calls[0]
            tool_name = tool_call.get('name')
            tool_args = tool_call.get('args', {})
            
            logger.info(f"迭代 {iteration + 1}: LLM 选择了工具 '{tool_name}，参数: {tool_args}'")
            
            if tool_name not in tool_map:
                raise ValueError(f"工具不存在: {tool_name}")
            
            tool = tool_map[tool_name]
            result = await tool.ainvoke(tool_args)
            
            if isinstance(result, str):
                content = result
            elif isinstance(result, dict):
                content = (
                    result.get("content") or
                    result.get("result") or
                    str(result)
                )
            else:
                content = str(result)
            
            logger.info(f"工具 {tool_name} 调用成功，返回内容长度: {len(content)}")
            
            result_dict = {
                'tool_name': tool_name,
                'tool_args': tool_args,
                'content': content
            }
            all_results.append(result_dict)
            tools_used.append(tool_name)
            
            if required_tools:
                remaining_tools = [t for t in required_tools if t not in tools_used]
                if not remaining_tools:
                    logger.info("所有必须的工具都已调用完成")
                    break
                
                messages = messages + [
                    HumanMessage(content=f"已完成 {tool_name}，请继续调用: {', '.join(remaining_tools)}")
                ]
            else:
                messages = messages + [
                    HumanMessage(content="如果需要调用更多工具，请继续。如果任务已完成，可以结束。")
                ]
        
        if not all_results:
            return {
                'success': False,
                'error': 'LLM 未能调用任何工具'
            }
        
        combined_parts = []
        for i, result in enumerate(all_results, 1):
            tool_name = result['tool_name']
            content = result['content']
            combined_parts.append(f"## 工具 {i}: {tool_name}\n\n{content}")
        
        combined_content = "\n\n".join(combined_parts)
        
        logger.info(f"顺序多工具调用成功: 使用了 {len(tools_used)} 个工具 {tools_used}")
        
        return {
            'success': True,
            'combined_content': combined_content,
            'tools_used': tools_used,
            'individual_results': all_results
        }
        
    except Exception as e:
        logger.error(f"顺序多工具调用失败: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


async def call_multiple_tools_parallel(
    llm: BaseChatModel,
    tools: List[Any],
    prompt: str,
    required_tools: Optional[List[str]] = None,
    system_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    并行调用多个工具（适用于工具之间无依赖的场景）
    
    流程：
    1. LLM 根据 prompt 一次性选择所有工具
    2. 使用 asyncio.gather 并行执行所有工具
    3. 收集所有结果并返回
    
    Args:
        llm: 语言模型
        tools: 可用工具列表
        prompt: 用户 prompt（告诉 LLM 要做什么，应该在 prompt 中明确说明要用哪些工具）
        required_tools: 必须调用的工具列表（可选，如果为 None，完全由 LLM 根据 prompt 决定）
        system_message: 系统消息（可选）
        
    Returns:
        {
            'success': bool,
            'combined_content': str,  # 所有工具结果的组合
            'tools_used': List[str],  # 使用的工具列表
            'individual_results': List[Dict],  # 每个工具的单独结果
            'failed_tools': List[str],  # 失败的工具列表
            'error': str  # 如果失败
        }
    
    使用示例:
        # 方式1：完全由 prompt 控制（推荐）
        result = await call_multiple_tools_parallel(
            llm=self.llm,
            tools=self.tools,
            prompt="处理这个图片，请使用 img_to_text 和 ocr_image_from_url 工具"
        )
        
        # 方式2：显式指定工具列表
        result = await call_multiple_tools_parallel(
            llm=self.llm,
            tools=self.tools,
            prompt="处理这个图片",
            required_tools=['img_to_text', 'ocr_image_from_url']
        )
    """
    try:
        logger.info(f"开始并行多工具调用: prompt={prompt[:100]}...")
        if required_tools:
            logger.info(f"显式指定的工具: {required_tools}")
        else:
            logger.info("完全由 LLM 根据 prompt 自主选择工具")
        
        # 步骤1: 构建消息并让 LLM 生成工具调用
        messages = []
        if system_message:
            messages.append(SystemMessage(content=system_message))
        
        if required_tools:
            enhanced_prompt = (
                f"{prompt}\n"
                f"请同时调用以下工具：{', '.join(required_tools)}\n"
                f"为每个工具生成正确的参数。"
            )
            messages.append(HumanMessage(content=enhanced_prompt))
        else:
            messages.append(HumanMessage(content=prompt))
        
        llm_with_tools = llm.bind_tools(tools)
        
        logger.info("步骤 1: LLM 正在生成所有工具调用...")
        response = await llm_with_tools.ainvoke(messages)
        
        if not hasattr(response, 'tool_calls') or not response.tool_calls:
            logger.warning("LLM 没有调用任何工具")
            return {
                'success': False,
                'error': 'LLM 未能生成工具调用'
            }
        
        # 步骤2: 准备并行执行工具
        tool_map = {tool.name: tool for tool in tools}
        
        # 步骤3: 并行执行所有工具
        logger.info(f"步骤 2: 并行执行 {len(response.tool_calls)} 个工具...")
        results = await asyncio.gather(
            *[_execute_single_tool_for_parallel(tc, tool_map) for tc in response.tool_calls],
            return_exceptions=True
        )
        
        # 步骤4: 处理结果
        all_results = []
        tools_used = []
        failed_tools = []
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"工具调用发生异常: {result}")
                continue
            
            if result.get('success'):
                all_results.append(result)
                tools_used.append(result['tool_name'])
            else:
                failed_tools.append(result['tool_name'])
        
        # 检查是否所有工具都失败
        if not all_results:
            return {
                'success': False,
                'error': f'所有工具调用失败。失败的工具: {failed_tools}'
            }
        
        # 检查必须的工具是否都成功调用
        if required_tools:
            missing_required = [t for t in required_tools if t not in tools_used]
            if missing_required:
                logger.warning(f"部分必须工具未成功调用: {missing_required}")
        
        # 合并所有结果
        combined_parts = [
            f"## 工具 {i}: {result['tool_name']}\n\n{result['content']}"
            for i, result in enumerate(all_results, 1)
        ]
        combined_content = "\n\n".join(combined_parts)
        
        logger.info(f"并行多工具调用成功: 使用了 {len(tools_used)} 个工具 {tools_used}")
        if failed_tools:
            logger.warning(f"失败的工具: {failed_tools}")
        
        return {
            'success': True,
            'combined_content': combined_content,
            'tools_used': tools_used,
            'individual_results': all_results,
            'failed_tools': failed_tools
        }
        
    except Exception as e:
        logger.error(f"并行多工具调用失败: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def _parse_tool_result(result: Any, tool_name: str = "") -> str:
    """
    统一解析工具返回结果
    
    Args:
        result: 工具返回的原始结果
        tool_name: 工具名称（用于日志）
        
    Returns:
        解析后的内容字符串
        
    Raises:
        ValueError: 如果工具返回错误状态
    """
    import json
    
    logger.debug(f"工具 {tool_name} 原始返回类型: {type(result)}")
    
    if isinstance(result, str):
        # 尝试解析 JSON 字符串
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict):
                # 检查错误状态
                if parsed.get('status') == 'error':
                    error_msg = parsed.get('message') or parsed.get('error') or '未知错误'
                    raise ValueError(f"工具返回错误: {error_msg}")
                # 提取内容
                content = parsed.get("content") or parsed.get("result") or result
            else:
                content = parsed
        except json.JSONDecodeError:
            content = result
    elif isinstance(result, list):
        content = result
    elif isinstance(result, dict):
        if result.get('status') == 'error':
            error_msg = result.get('message') or result.get('error') or '未知错误'
            raise ValueError(f"工具返回错误: {error_msg}")
        content = result.get("content") or result.get("result") or str(result)
    else:
        content = str(result)
    
    return content


async def _execute_single_tool_for_parallel(
    tool_call: Dict[str, Any],
    tool_map: Dict[str, Any]
) -> Dict[str, Any]:
    """
    执行单个工具并返回标准化结果（用于并行调用）
    
    Args:
        tool_call: 工具调用信息，包含 name 和 args
        tool_map: 工具名称到工具对象的映射
        
    Returns:
        标准化的工具执行结果
    """
    tool_name = tool_call.get('name')
    tool_args = tool_call.get('args', {})
    
    logger.info(f"调用工具: {tool_name}, 参数: {tool_args}")
    
    try:
        if tool_name not in tool_map:
            raise ValueError(f"工具不存在: {tool_name}")
        
        tool = tool_map[tool_name]
        result = await tool.ainvoke(tool_args)
        
        content = _parse_tool_result(result, tool_name)
        
        logger.info(f"工具 {tool_name} 成功，返回长度: {len(str(content))}")
        
        return {
            'tool_name': tool_name,
            'tool_args': tool_args,
            'content': content,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"工具 {tool_name} 失败: {e}", exc_info=True)
        return {
            'tool_name': tool_name,
            'tool_args': tool_args,
            'content': '',
            'success': False,
            'error': str(e)
        }


def get_tool_names(tools: List[Any]) -> List[str]:
    """
    获取所有可用工具的名称
    
    Args:
        tools: 工具列表
        
    Returns:
        工具名称列表
    """
    return [tool.name for tool in tools]


def has_tool(tools: List[Any], tool_name: str) -> bool:
    """
    检查是否存在指定的工具
    
    Args:
        tools: 工具列表
        tool_name: 工具名称
        
    Returns:
        是否存在
    """
    return any(tool.name == tool_name for tool in tools)



class ToolCallHelper:
    """
    工具调用辅助类

    Args:
        llm: 语言模型
        tools: 可用工具列表

    Example:
        helper = ToolCallHelper(llm, tools)
        result = await helper.call_tool_with_llm(prompt, system_message)
        result = await helper.call_multiple_tools_with_llm(prompt, required_tools, system_message)
        result = await helper.call_multiple_tools_parallel(prompt, required_tools, system_message)
        result = await helper.call_tool_directly(tool_name, tool_args)
        tool_names = helper.get_tool_names()
        has_tool = helper.has_tool(tool_name)
    """
    
    def __init__(self, llm: BaseChatModel, tools: List[Any]):
        self.llm = llm
        self.tools = tools
    
    async def call_tool_with_llm(
        self, 
        prompt: str,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        return await call_tool_with_llm(
            self.llm, 
            self.tools, 
            prompt, 
            system_message
        )
    
    async def call_multiple_tools_with_llm(
        self,
        prompt: str,
        required_tools: Optional[List[str]] = None,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        return await call_multiple_tools_with_llm(
            self.llm,
            self.tools,
            prompt,
            required_tools,
            system_message
        )
    
    async def call_multiple_tools_parallel(
        self,
        prompt: str,
        required_tools: Optional[List[str]] = None,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        return await call_multiple_tools_parallel(
            self.llm,
            self.tools,
            prompt,
            required_tools,
            system_message
        )
    
    async def call_tool_directly(
        self, 
        tool_name: str,
        tool_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        return await call_tool_directly(
            self.tools,
            tool_name,
            tool_args
        )
    
    def get_tool_names(self) -> List[str]:
        return get_tool_names(self.tools)
    
    def has_tool(self, tool_name: str) -> bool:
        return has_tool(self.tools, tool_name)