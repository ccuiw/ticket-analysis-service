"""
模型原始输出解析器。

将大模型返回的原始文本转换为 Python 字典。
当前为 json.loads 封装，后续将扩展处理：
- Markdown 代码块包裹（```json ... ```）
- 尾部多余逗号
- 未闭合引号等常见 JSON 错误
"""

import json
from app.domain.exceptions import AnalysisError


def parse_raw_output(raw: str) -> dict:
    """解析模型原始输出 JSON 为字典。

    Args:
        raw: 模型返回的原始文本。

    Returns:
        解析后的字典。

    Raises:
        AnalysisError: JSON 解析失败。
    """
    text = raw.strip()

    # 尝试去除 markdown 代码块包裹
    if text.startswith("```"):
        lines = text.split("\n")
        # 去掉开头 ```json 或 ```
        if lines[0].startswith("```"):
            lines = lines[1:]
        # 去掉结尾 ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AnalysisError(f"模型输出 JSON 解析失败：{exc}") from exc
