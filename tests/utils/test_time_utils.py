"""Tests for time_utils module

時間計算ユーティリティのテストケース。
"""

from datetime import datetime, timedelta

import pytest

from src.utils.time_utils import (
    JST,
    calculate_duration_min,
    filter_recent_records,
    get_time_block,
    parse_ts,
)


class TestParseTs:
    """parse_ts関数のテスト"""

    def test_parse_iso8601_with_timezone(self):
        """タイムゾーン付きISO 8601文字列をパース"""
        ts_str = "2024-01-15T09:30:45+09:00"
        result = parse_ts(ts_str)

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 9
        assert result.minute == 30
        assert result.second == 45

    def test_parse_iso8601_utc(self):
        """UTC ISO 8601文字列をパース"""
        ts_str = "2024-01-15T00:30:45Z"
        result = parse_ts(ts_str)

        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 30

    def test_parse_invalid_format(self):
        """無効なフォーマットでValueErrorを発生"""
        with pytest.raises(ValueError):
            parse_ts("invalid-timestamp")


class TestFilterRecentRecords:
    """filter_recent_records関数のテスト"""

    def test_filter_recent_records_default(self):
        """デフォルト120秒で直近レコードを除外"""
        now = datetime.now(JST)
        records = [
            {"timestamp": (now - timedelta(minutes=5)).isoformat()},  # 5分前: OK
            {"timestamp": (now - timedelta(minutes=3)).isoformat()},  # 3分前: OK
            {"timestamp": (now - timedelta(seconds=90)).isoformat()},  # 90秒前: NG
            {"timestamp": (now - timedelta(seconds=30)).isoformat()},  # 30秒前: NG
        ]

        result = filter_recent_records(records, exclude_sec=120)

        assert len(result) == 2
        # 5分前と3分前のレコードのみ残る

    def test_filter_recent_records_custom_duration(self):
        """カスタム除外時間を指定"""
        now = datetime.now(JST)
        records = [
            {"timestamp": (now - timedelta(minutes=10)).isoformat()},  # 10分前: OK
            {"timestamp": (now - timedelta(minutes=5)).isoformat()},  # 5分前: OK
            {"timestamp": (now - timedelta(minutes=2)).isoformat()},  # 2分前: NG
        ]

        result = filter_recent_records(records, exclude_sec=180)  # 3分除外

        assert len(result) == 2

    def test_filter_empty_list(self):
        """空リストを処理"""
        result = filter_recent_records([])
        assert result == []

    def test_filter_invalid_timestamp(self):
        """無効なタイムスタンプを含むレコードをスキップ"""
        now = datetime.now(JST)
        records = [
            {"timestamp": (now - timedelta(minutes=5)).isoformat()},  # 有効
            {"timestamp": "invalid"},  # 無効: スキップ
            {"other_field": "no_timestamp"},  # timestampなし: スキップ
        ]

        result = filter_recent_records(records, exclude_sec=120)

        assert len(result) == 1
        assert "timestamp" in result[0]


class TestGetTimeBlock:
    """get_time_block関数のテスト"""

    def test_time_block_30min_start(self):
        """30分ブロックの開始時刻"""
        ts = datetime(2024, 1, 15, 9, 0)
        start, end = get_time_block(ts, block_min=30)

        assert start == "09:00"
        assert end == "09:30"

    def test_time_block_30min_middle(self):
        """30分ブロックの途中の時刻"""
        ts = datetime(2024, 1, 15, 9, 15)
        start, end = get_time_block(ts, block_min=30)

        assert start == "09:00"
        assert end == "09:30"

    def test_time_block_30min_end(self):
        """30分ブロックの終了時刻付近"""
        ts = datetime(2024, 1, 15, 9, 29)
        start, end = get_time_block(ts, block_min=30)

        assert start == "09:00"
        assert end == "09:30"

    def test_time_block_30min_next_block(self):
        """次の30分ブロック"""
        ts = datetime(2024, 1, 15, 9, 45)
        start, end = get_time_block(ts, block_min=30)

        assert start == "09:30"
        assert end == "10:00"

    def test_time_block_60min(self):
        """60分ブロック"""
        ts = datetime(2024, 1, 15, 14, 20)
        start, end = get_time_block(ts, block_min=60)

        assert start == "14:00"
        assert end == "15:00"

    def test_time_block_15min(self):
        """15分ブロック"""
        ts = datetime(2024, 1, 15, 10, 47)
        start, end = get_time_block(ts, block_min=15)

        assert start == "10:45"
        assert end == "11:00"


class TestCalculateDurationMin:
    """calculate_duration_min関数のテスト"""

    def test_duration_10_minutes(self):
        """10分間の記録"""
        first = "2024-01-15T09:00:00+09:00"
        last = "2024-01-15T09:10:00+09:00"

        result = calculate_duration_min(first, last)

        # 10分 + 2分（サンプリング間隔） = 12分
        assert result == 12

    def test_duration_2_hours(self):
        """2時間の記録"""
        first = "2024-01-15T09:00:00+09:00"
        last = "2024-01-15T11:00:00+09:00"

        result = calculate_duration_min(first, last)

        # 120分 + 2分 = 122分
        assert result == 122

    def test_duration_with_custom_interval(self):
        """カスタムサンプリング間隔"""
        first = "2024-01-15T09:00:00+09:00"
        last = "2024-01-15T09:30:00+09:00"

        result = calculate_duration_min(first, last, sampling_interval_sec=60)

        # 30分 + 1分 = 31分
        assert result == 31

    def test_duration_minimum_value(self):
        """最小値は1分"""
        first = "2024-01-15T09:00:00+09:00"
        last = "2024-01-15T09:00:00+09:00"  # 同時刻

        result = calculate_duration_min(first, last)

        # 0分 + 2分 = 2分（切り上げ）
        assert result >= 1

    def test_duration_invalid_timestamp(self):
        """無効なタイムスタンプ時はフォールバック"""
        result = calculate_duration_min("invalid", "invalid")

        assert result == 1  # フォールバック値
