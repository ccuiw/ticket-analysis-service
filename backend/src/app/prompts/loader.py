"""
提示词加载器。

从 prompts/ 目录加载指定版本的提示词模板。
提示词正文不硬编码在 Python 源码中。
"""

import os
from pathlib import Path
from app.domain.exceptions import PromptNotFoundError


def _resolve_prompts_dir() -> Path:
    """解析 prompts 目录路径。

    优先级：
    1. 环境变量 PROMPTS_DIR
    2. 基于当前文件的相对路径（向上 4 级：loader.py → prompts → app → src → 项目根目录）
    """
    env_dir = os.getenv("PROMPTS_DIR")
    if env_dir:
        return Path(env_dir)

    # 从 src/app/prompts/loader.py 向上到项目根
    return Path(__file__).resolve().parents[3] / "prompts"


def load_prompt(name: str) -> str:
    """按名称加载提示词模板。

    Args:
        name: 提示词文件名（不含 .txt 扩展名），如 "ticket_analysis_v1"。

    Returns:
        提示词模板的完整文本。

    Raises:
        PromptNotFoundError: 提示词文件不存在。
    """
    prompts_dir = _resolve_prompts_dir()
    file_path = prompts_dir / f"{name}.txt"

    if not file_path.exists():
        raise PromptNotFoundError(f"提示词文件不存在：{file_path}")

    return file_path.read_text(encoding="utf-8")
