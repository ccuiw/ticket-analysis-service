"""
模型原始输出解析器。

将大模型返回的原始文本转换为 Python 字典。
本阶段只处理纯 JSON —— Markdown 代码块、尾随逗号等
修复逻辑将在后续 repair 阶段实现。
"""

import json
from app.domain.exceptions import OutputParseError


def parse_raw_output(raw: str) -> dict:
    """解析模型原始输出 JSON 为字典。

    Args:
        raw: 模型返回的原始文本。

    Returns:
        解析后的字典。

    Raises:
        OutputParseError: JSON 解析失败或结果不是字典。
    """
    text = raw.strip()

    if not text:
        raise OutputParseError("模型返回了空输出")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise OutputParseError(f"模型输出 JSON 解析失败：{exc}") from exc

    if not isinstance(data, dict):
        raise OutputParseError(
            f"模型输出应为 JSON 对象，实际为：{type(data).__name__}"
        )

    return data
