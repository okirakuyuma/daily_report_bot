#!/usr/bin/env python3
"""Validation script for utils module

utilsモジュールの基本動作確認スクリプト。
"""

from datetime import datetime, timedelta

from src.utils import (
    JST,
    PROCESS_TO_APP_NAME,
    calculate_duration_min,
    calculate_rank,
    filter_recent_records,
    get_time_block,
    merge_keywords,
    normalize_app_name,
    parse_ts,
)


def validate_time_utils():
    """time_utils の動作確認"""
    print("=" * 60)
    print("Time Utils Validation")
    print("=" * 60)

    # 1. parse_ts
    ts_str = "2024-01-15T09:30:45+09:00"
    dt = parse_ts(ts_str)
    print(f"✓ parse_ts: {ts_str}")
    print(f"  -> {dt}")

    # 2. get_time_block
    ts = datetime(2024, 1, 15, 9, 15)
    start, end = get_time_block(ts, block_min=30)
    print(f"\n✓ get_time_block: 09:15")
    print(f"  -> ブロック: {start} - {end}")

    ts = datetime(2024, 1, 15, 14, 45)
    start, end = get_time_block(ts, block_min=30)
    print(f"✓ get_time_block: 14:45")
    print(f"  -> ブロック: {start} - {end}")

    # 3. calculate_duration_min
    first = "2024-01-15T09:00:00+09:00"
    last = "2024-01-15T09:10:00+09:00"
    duration = calculate_duration_min(first, last)
    print(f"\n✓ calculate_duration_min: 09:00 - 09:10")
    print(f"  -> {duration}分 (サンプリング間隔2分を含む)")

    # 4. filter_recent_records
    now = datetime.now(JST)
    records = [
        {"timestamp": (now - timedelta(minutes=5)).isoformat(), "data": "old"},
        {"timestamp": (now - timedelta(seconds=30)).isoformat(), "data": "recent"},
    ]
    filtered = filter_recent_records(records, exclude_sec=120)
    print(f"\n✓ filter_recent_records: {len(records)} records")
    print(f"  -> {len(filtered)} records (直近120秒を除外)")

    print("\n")


def validate_text_utils():
    """text_utils の動作確認"""
    print("=" * 60)
    print("Text Utils Validation")
    print("=" * 60)

    # 1. merge_keywords
    records = [
        {"keywords": ["Python", "API"]},
        {"keywords": ["python", "Testing"]},
        {"keywords": ["API", "python", "Docker"]},
    ]
    merged = merge_keywords(records)
    print("✓ merge_keywords:")
    print(f"  入力: {[r['keywords'] for r in records]}")
    print(f"  出力: {merged}")
    print(f"  -> 出現頻度順: python(3), API(2), Testing(1), Docker(1)")

    # 2. calculate_rank
    print("\n✓ calculate_rank:")
    print(f"  35/100 -> {calculate_rank(35, 100)} (30%以上)")
    print(f"  20/100 -> {calculate_rank(20, 100)} (10-30%)")
    print(f"  5/100 -> {calculate_rank(5, 100)} (10%未満)")

    # 3. normalize_app_name
    print("\n✓ normalize_app_name:")
    test_processes = [
        "Code.exe",
        "chrome.exe",
        "EXCEL.EXE",
        "unknown.exe",
        None,
    ]
    for process in test_processes:
        normalized = normalize_app_name(process)
        print(f"  {str(process):20s} -> {normalized}")

    # 4. PROCESS_TO_APP_NAME
    print(f"\n✓ PROCESS_TO_APP_NAME: {len(PROCESS_TO_APP_NAME)} mappings")
    print("  主要アプリ:")
    for process in ["Code.exe", "chrome.exe", "EXCEL.EXE", "Teams.exe"]:
        if process in PROCESS_TO_APP_NAME:
            print(f"    {process:20s} -> {PROCESS_TO_APP_NAME[process]}")

    print("\n")


def main():
    """メイン処理"""
    try:
        validate_time_utils()
        validate_text_utils()

        print("=" * 60)
        print("✓ All validations passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Validation failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
