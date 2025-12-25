import json
import re
from typing import Any, Dict, List, Union

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage


def combine_simple_context(system: str, user: str = None):
    context: List[Union[BaseMessage, dict[str, Any]]] = [SystemMessage(content=system)]
    if user:
        context.append(HumanMessage(content=system))
    return context


def fix_json_response(text: str) -> Union[Dict, List, str, int, float, bool, None]:
    """
    去掉大模型返回的 ```json / ``` 等 markdown 标记，并安全反序列化 JSON。
    若解析失败，返回原字符串。

    参数
    ----
    text : str
        原始响应，可能包含 ```json ... ``` 或其他变体。

    返回
    ----
    Python 对象（dict / list / str / int / float / bool / None）
        解析失败时返回输入字符串本身。
    """
    if not isinstance(text, str):
        return text

    # 1. 去掉 ```json 或 ``` 包裹（支持开头、结尾、单行、多行）
    cleaned = re.sub(r'^\s*```(?:json|JSON)?\s*\n?', '', text)
    cleaned = re.sub(r'\n?\s*```\s*$', '', cleaned)

    # 2. 去掉首尾空白
    cleaned = cleaned.strip()

    # 3. 尝试 JSON 反序列化
    try:
        json.loads(cleaned)
        return cleaned
    except json.JSONDecodeError:
        # 4. 兜底：返回原字符串
        return text


# ----------------- 使用示例 -----------------
if __name__ == "__main__":
    demo_list = [
        '```json\n{"a": 1, "b": "hello"}\n```',
        "```JSON{'key': 'value'}```",
        "```\n[1, 2, 3]```",
        "plain text",
        {"already_dict": 1},
    ]
    for d in demo_list:
        print("原始:", repr(d))
        print("修复:", repr(fix_json_response(d)))
        print("-" * 30)
