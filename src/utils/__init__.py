"""Utils - 共通ユーティリティモジュール

時間計算、テキスト処理、Notionブロック生成などの汎用ヘルパー関数を提供。
"""

from .block_builder import (
    build_app_table,
    build_report_blocks,
    build_report_blocks_from_dict,
    build_report_blocks_from_report,
    bulleted_list_item,
    divider,
    heading_2,
    numbered_list_item,
    paragraph,
    rank_to_emoji,
)
from .text_utils import (
    PROCESS_TO_APP_NAME,
    calculate_rank,
    merge_keywords,
    normalize_app_name,
)
from .time_utils import (
    JST,
    calculate_duration_min,
    filter_recent_records,
    get_time_block,
    parse_ts,
)

__all__ = [
    # Time utilities
    "JST",
    "parse_ts",
    "filter_recent_records",
    "get_time_block",
    "calculate_duration_min",
    # Text utilities
    "merge_keywords",
    "calculate_rank",
    "normalize_app_name",
    "PROCESS_TO_APP_NAME",
    # Block builder utilities
    "heading_2",
    "paragraph",
    "numbered_list_item",
    "bulleted_list_item",
    "divider",
    "rank_to_emoji",
    "build_app_table",
    "build_report_blocks",
    "build_report_blocks_from_report",
    "build_report_blocks_from_dict",
]
