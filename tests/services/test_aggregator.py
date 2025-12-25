"""LogAggregationService のユニットテスト"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.domain.features import AppRank, Features
from src.repositories.log_repository import (
    LogFileEmptyError,
    LogFileNotFoundError,
    LogRepository,
)
from src.services.aggregator import (
    DEFAULT_CONFIG,
    LogAggregationService,
    _build_app_summary,
    _build_global_keywords,
    _build_meta,
    _build_time_blocks,
    _filter_recent,
    _group_by_time_block,
    create_aggregator,
)
from src.utils.time_utils import JST


class TestFilterRecent:
    """_filter_recent のテスト"""

    def test_empty_records(self) -> None:
        """空のレコードリストは空を返す"""
        result = _filter_recent([])
        assert result == []

    def test_filters_recent_records(self) -> None:
        """直近N秒のレコードを除外"""
        now = datetime.now(JST)
        old_time = (now - timedelta(minutes=10)).isoformat()
        recent_time = (now - timedelta(seconds=30)).isoformat()

        records = [
            {"ts": old_time, "data": "old"},
            {"ts": recent_time, "data": "recent"},
        ]

        result = _filter_recent(records, exclude_sec=120)

        assert len(result) == 1
        assert result[0]["data"] == "old"

    def test_keeps_all_old_records(self) -> None:
        """古いレコードは全て保持"""
        now = datetime.now(JST)
        records = [
            {"ts": (now - timedelta(hours=1)).isoformat(), "data": "1"},
            {"ts": (now - timedelta(hours=2)).isoformat(), "data": "2"},
            {"ts": (now - timedelta(hours=3)).isoformat(), "data": "3"},
        ]

        result = _filter_recent(records, exclude_sec=120)

        assert len(result) == 3

    def test_skips_invalid_timestamps(self) -> None:
        """無効なタイムスタンプはスキップ"""
        now = datetime.now(JST)
        valid_time = (now - timedelta(hours=1)).isoformat()

        records = [
            {"ts": valid_time, "data": "valid"},
            {"ts": "invalid-timestamp", "data": "invalid"},
            {"data": "no-ts"},  # ts フィールドなし
        ]

        result = _filter_recent(records)

        assert len(result) == 1
        assert result[0]["data"] == "valid"


class TestGroupByTimeBlock:
    """_group_by_time_block のテスト"""

    def test_empty_records(self) -> None:
        """空のレコードは空辞書を返す"""
        result = _group_by_time_block([])
        assert result == {}

    def test_groups_by_30min_blocks(self) -> None:
        """30分ブロックでグループ化"""
        base_date = "2024-01-15"
        records = [
            {"ts": f"{base_date}T09:10:00+09:00", "data": "1"},
            {"ts": f"{base_date}T09:20:00+09:00", "data": "2"},
            {"ts": f"{base_date}T09:40:00+09:00", "data": "3"},
            {"ts": f"{base_date}T10:05:00+09:00", "data": "4"},
        ]

        result = _group_by_time_block(records, block_min=30)

        assert ("09:00", "09:30") in result
        assert ("09:30", "10:00") in result
        assert ("10:00", "10:30") in result
        assert len(result[("09:00", "09:30")]) == 2
        assert len(result[("09:30", "10:00")]) == 1
        assert len(result[("10:00", "10:30")]) == 1


class TestBuildTimeBlocks:
    """_build_time_blocks のテスト"""

    def test_empty_groups(self) -> None:
        """空のグループは空リストを返す"""
        result = _build_time_blocks({})
        assert result == []

    def test_builds_time_blocks_with_apps(self) -> None:
        """TimeBlockを正しく構築"""
        grouped = {
            ("09:00", "09:30"): [
                {"process_name": "Code.exe", "keywords": ["Python"], "files": []},
                {"process_name": "Code.exe", "keywords": ["Flask"], "files": []},
                {"process_name": "chrome.exe", "keywords": [], "files": []},
            ],
        }

        result = _build_time_blocks(grouped)

        assert len(result) == 1
        block = result[0]
        assert block.start == "09:00"
        assert block.end == "09:30"
        assert len(block.apps) == 2
        # Visual Studio Code が最多（2/3 = 66.7%）
        assert block.apps[0].name == "Visual Studio Code"
        assert block.apps[0].percent > 60

    def test_time_blocks_sorted_by_time(self) -> None:
        """TimeBlockは時刻順でソート"""
        grouped = {
            ("14:00", "14:30"): [{"process_name": "chrome.exe"}],
            ("09:00", "09:30"): [{"process_name": "Code.exe"}],
            ("11:00", "11:30"): [{"process_name": "slack.exe"}],
        }

        result = _build_time_blocks(grouped)

        assert result[0].start == "09:00"
        assert result[1].start == "11:00"
        assert result[2].start == "14:00"


class TestBuildAppSummary:
    """_build_app_summary のテスト"""

    def test_empty_records(self) -> None:
        """空レコードは空リストを返す"""
        result = _build_app_summary([])
        assert result == []

    def test_builds_app_summary(self) -> None:
        """AppSummaryを正しく構築"""
        records = [
            {"process_name": "Code.exe", "keywords": ["Python"], "files": ["main.py"]},
            {"process_name": "Code.exe", "keywords": ["Flask"], "files": ["app.py"]},
            {"process_name": "chrome.exe", "keywords": ["docs"], "urls": ["python.org"]},
        ]

        result = _build_app_summary(records, sampling_interval_sec=120)

        assert len(result) == 2
        # 使用時間降順でソート
        assert result[0].name == "Visual Studio Code"
        assert result[0].count == 2
        assert result[0].duration_min == 4.0  # 2 * 120 / 60
        assert result[1].name == "Google Chrome"
        assert result[1].count == 1

    def test_rank_calculation(self) -> None:
        """ランクが正しく計算される"""
        # 10件中 4件(40%) = high, 2件(20%) = medium, 1件(10%) = medium
        records = [{"process_name": "Code.exe"} for _ in range(4)]
        records += [{"process_name": "chrome.exe"} for _ in range(2)]
        records += [{"process_name": "slack.exe"} for _ in range(1)]
        records += [{"process_name": "notepad.exe"} for _ in range(3)]

        result = _build_app_summary(records)

        app_by_name = {app.name: app for app in result}
        assert app_by_name["Visual Studio Code"].rank == AppRank.HIGH  # 40%
        assert app_by_name["Notepad"].rank == AppRank.HIGH  # 30%
        assert app_by_name["Google Chrome"].rank == AppRank.MEDIUM  # 20%
        assert app_by_name["Slack"].rank == AppRank.MEDIUM  # 10%


class TestBuildGlobalKeywords:
    """_build_global_keywords のテスト"""

    def test_empty_records(self) -> None:
        """空レコードは空のGlobalKeywordsを返す"""
        result = _build_global_keywords([])
        assert result.top_keywords == []
        assert result.top_urls == []
        assert result.top_files == []

    def test_merges_all_keywords(self) -> None:
        """全レコードからキーワードをマージ"""
        records = [
            {"keywords": ["Python", "Flask"], "urls": ["python.org"], "files": ["main.py"]},
            {"keywords": ["Python", "API"], "urls": ["github.com"], "files": ["app.py"]},
            {"keywords": ["Docker"], "urls": ["python.org"], "files": []},
        ]

        result = _build_global_keywords(records)

        # Pythonが最頻出
        assert "Python" in result.top_keywords
        assert "python.org" in result.top_urls
        assert "main.py" in result.top_files


class TestBuildMeta:
    """_build_meta のテスト"""

    def test_builds_meta_correctly(self) -> None:
        """メタデータを正しく構築"""
        target_date = date(2024, 1, 15)
        records = [
            {"ts": "2024-01-15T09:00:00+09:00"},
            {"ts": "2024-01-15T10:00:00+09:00"},
            {"ts": "2024-01-15T11:00:00+09:00"},
        ]

        result = _build_meta(target_date, records)

        assert result.date == "2024-01-15"
        assert result.capture_count == 3
        assert result.first_capture == "09:00:00"
        assert result.last_capture == "11:00:00"
        assert result.total_duration_min > 0

    def test_empty_records_meta(self) -> None:
        """空レコードのメタデータ"""
        target_date = date(2024, 1, 15)

        result = _build_meta(target_date, [])

        assert result.capture_count == 0
        assert result.first_capture == "00:00:00"
        assert result.last_capture == "00:00:00"


class TestLogAggregationService:
    """LogAggregationService のテスト"""

    @pytest.fixture
    def mock_repository(self) -> MagicMock:
        """モックリポジトリ"""
        return MagicMock(spec=LogRepository)

    @pytest.fixture
    def sample_records(self) -> list[dict[str, Any]]:
        """テスト用サンプルレコード（過去の日付）"""
        base_date = "2024-01-15"
        return [
            {
                "ts": f"{base_date}T09:00:00+09:00",
                "window_title": "main.py - VSCode",
                "process_name": "Code.exe",
                "keywords": ["Python", "def"],
                "urls": [],
                "files": ["main.py"],
            },
            {
                "ts": f"{base_date}T09:02:00+09:00",
                "window_title": "main.py - VSCode",
                "process_name": "Code.exe",
                "keywords": ["Python", "class"],
                "urls": [],
                "files": ["main.py"],
            },
            {
                "ts": f"{base_date}T09:04:00+09:00",
                "window_title": "Stack Overflow - Chrome",
                "process_name": "chrome.exe",
                "keywords": ["Python", "error"],
                "urls": ["stackoverflow.com"],
                "files": [],
            },
        ]

    def test_aggregate_returns_features(
        self, mock_repository: MagicMock, sample_records: list[dict[str, Any]]
    ) -> None:
        """aggregate メソッドがFeaturesを返す"""
        mock_repository.read_raw_logs.return_value = sample_records

        service = LogAggregationService(
            repository=mock_repository,
            config={"exclude_recent_sec": 0},  # フィルタリングを無効化
        )

        result = service.aggregate(date(2024, 1, 15))

        assert isinstance(result, Features)
        assert result.meta.capture_count == 3
        assert len(result.app_summary) == 2

    def test_aggregate_uses_default_date(
        self, mock_repository: MagicMock, sample_records: list[dict[str, Any]]
    ) -> None:
        """target_date=None で当日を使用"""
        mock_repository.read_raw_logs.return_value = sample_records

        service = LogAggregationService(
            repository=mock_repository,
            config={"exclude_recent_sec": 0},
        )

        with patch("src.services.aggregator.date") as mock_date:
            mock_date.today.return_value = date(2024, 1, 15)
            service.aggregate(None)

        mock_repository.read_raw_logs.assert_called_once_with(date(2024, 1, 15))

    def test_aggregate_handles_file_not_found(
        self, mock_repository: MagicMock
    ) -> None:
        """ファイル不存在エラーを伝播"""
        mock_repository.read_raw_logs.side_effect = LogFileNotFoundError(
            Path("/test/2024-01-15.jsonl")
        )

        service = LogAggregationService(repository=mock_repository)

        with pytest.raises(LogFileNotFoundError):
            service.aggregate(date(2024, 1, 15))

    def test_aggregate_handles_empty_file(
        self, mock_repository: MagicMock
    ) -> None:
        """空ファイルエラーを伝播"""
        mock_repository.read_raw_logs.side_effect = LogFileEmptyError(
            Path("/test/2024-01-15.jsonl")
        )

        service = LogAggregationService(repository=mock_repository)

        with pytest.raises(LogFileEmptyError):
            service.aggregate(date(2024, 1, 15))

    def test_aggregate_and_save(
        self, mock_repository: MagicMock, sample_records: list[dict[str, Any]]
    ) -> None:
        """aggregate_and_save がFeaturesを保存"""
        mock_repository.read_raw_logs.return_value = sample_records
        mock_repository.save_features.return_value = Path("/test/features.json")

        service = LogAggregationService(
            repository=mock_repository,
            config={"exclude_recent_sec": 0},
        )

        features, path = service.aggregate_and_save(date(2024, 1, 15))

        assert isinstance(features, Features)
        assert path == Path("/test/features.json")
        mock_repository.save_features.assert_called_once()


class TestCreateAggregator:
    """create_aggregator のテスト"""

    def test_creates_service_with_defaults(self) -> None:
        """デフォルト設定でサービスを作成"""
        service = create_aggregator()

        assert isinstance(service, LogAggregationService)
        assert service.config == DEFAULT_CONFIG

    def test_creates_service_with_custom_config(self) -> None:
        """カスタム設定でサービスを作成"""
        custom_config = {"exclude_recent_sec": 60}

        service = create_aggregator(config=custom_config)

        assert service.config["exclude_recent_sec"] == 60
        # その他はデフォルト値
        assert service.config["time_block_min"] == DEFAULT_CONFIG["time_block_min"]

    def test_creates_service_with_custom_path(self, tmp_path: Path) -> None:
        """カスタムパスでサービスを作成"""
        service = create_aggregator(base_path=tmp_path)

        assert service.repository.base_path == tmp_path
