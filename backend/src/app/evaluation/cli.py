"""CLI 参数解析。"""

import argparse


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="工单分析提示词评估工具"
    )
    parser.add_argument(
        "--provider",
        default="mock",
        choices=["mock", "openai_compatible"],
        help="LLM Provider（默认 mock）",
    )
    parser.add_argument(
        "--versions",
        nargs="+",
        default=["v1", "v2"],
        help="要评估的提示词版本（默认 v1 v2）",
    )
    parser.add_argument(
        "--dataset",
        default="data/test_cases.jsonl",
        help="测试数据集路径（默认 data/test_cases.jsonl）",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/evaluation",
        help="报告输出目录（默认 reports/evaluation）",
    )
    parser.add_argument(
        "--disable-repair",
        action="store_true",
        help="禁用输出修复",
    )
    return parser.parse_args(argv)
