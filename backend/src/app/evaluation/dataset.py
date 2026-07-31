"""测试数据集加载与校验。"""

import json
import hashlib
from pathlib import Path
from app.evaluation.models import TestCase


REQUIRED_FIELDS = {"id", "input", "expected", "case_type"}


def load_dataset(path: str | Path) -> list[TestCase]:
    """从 JSONL 文件加载测试数据集。

    Args:
        path: JSONL 文件路径。

    Returns:
        TestCase 列表。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: 格式错误、ID 重复或字段不合法。
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"测试数据文件不存在：{file_path}")

    cases: list[TestCase] = []
    seen_ids: set[str] = set()

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            # 解析 JSON
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"第 {line_num} 行 JSON 解析失败：{exc}"
                )

            # 校验必填字段
            missing = REQUIRED_FIELDS - set(data.keys())
            if missing:
                raise ValueError(
                    f"第 {line_num} 行（id={data.get('id', '?')}）缺少必填字段：{missing}"
                )

            # 校验 expected 是 dict
            if not isinstance(data["expected"], dict):
                raise ValueError(
                    f"第 {line_num} 行（id={data['id']}）expected 必须是对象"
                )

            case_id = data["id"]
            if case_id in seen_ids:
                raise ValueError(f"重复的 case id：{case_id}")
            seen_ids.add(case_id)

            cases.append(TestCase(
                id=case_id,
                input=data["input"],
                expected=data["expected"],
                case_type=data["case_type"],
                notes=data.get("notes", ""),
            ))

    if not cases:
        raise ValueError("数据集为空")

    return cases


def compute_dataset_hash(path: str | Path) -> str:
    """计算数据集文件的 SHA-256 哈希。"""
    content = Path(path).read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]
