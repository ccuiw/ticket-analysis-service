"""
提示词构建器。

负责：
1. 从磁盘加载提示词模板；
2. 渲染模板变量；
3. 构造 System 和 User 消息；
4. 用 <ticket> 标签隔离用户工单数据。
"""

from app.llm.messages import LLMMessage
from app.prompts.loader import load_prompt
from app.domain.exceptions import PromptRenderError

TICKET_TAG = "<ticket>"
TICKET_CLOSE_TAG = "</ticket>"


def build_messages(
    ticket_text: str,
    prompt_version: str,
) -> list[LLMMessage]:
    """构造发送给 LLM 的消息列表。

    从 prompts/ 目录加载指定版本的系统提示词，
    将工单文本放入独立 User 消息中，用 <ticket> 标签包裹。

    Args:
        ticket_text: 工单文本（原始用户输入）。
        prompt_version: 提示词版本（"v1" 或 "v2"）。

    Returns:
        [system_message, user_message] 列表。

    Raises:
        PromptNotFoundError: 提示词文件不存在。
        PromptRenderError: 模板变量异常。
    """
    # 加载系统提示词
    prompt_name = _prompt_version_to_filename(prompt_version)
    try:
        system_prompt = load_prompt(prompt_name)
    except Exception as exc:
        raise PromptRenderError(
            f"加载提示词失败（版本：{prompt_version}）：{exc}"
        )

    # 构造 user 消息，隔离工单数据
    user_content = f"{TICKET_TAG}\n{ticket_text}\n{TICKET_CLOSE_TAG}"

    return [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_content),
    ]


def _prompt_version_to_filename(version: str) -> str:
    """将提示词版本映射为文件名（不含扩展名）。

    Args:
        version: "v1" 或 "v2"。

    Returns:
        文件名，如 "ticket_analysis_v1"。
    """
    return f"ticket_analysis_{version}"
