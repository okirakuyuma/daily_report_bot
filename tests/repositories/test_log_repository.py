"""LogRepositoryのテスト"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from src.repositories import (
    LogFileEmptyError,
    LogFileNotFoundError,
    LogParseError,
    LogRepository,
)


class TestLogRepository:
    """LogRepositoryのテストスイート"""

    @pytest.fixture
    def temp_log_dir(self, tmp_path: Path) -> Path:
        """一時ログディレクトリ"""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        return log_dir

    @pytest.fixture
    def repository(self, temp_log_dir: Path) -> LogRepository:
        """テスト用リポジトリインスタンス"""
        return LogRepository(base_path=temp_log_dir)

    @pytest.fixture
    def sample_date(self) -> date:
        """テスト用の日付"""
        return date(2025, 1, 15)

    @pytest.fixture
    def sample_raw_logs(self) -> list[dict[str, Any]]:
        """テスト用の生ログデータ"""
        return [
            {
                "ts": "2025-01-15T09:00:00.000+09:00",
                "window_title": "main.py - Visual Studio Code",
                "process_name": "Code.exe",
                "keywords": ["Python", "def", "class"],
                "files": ["main.py"],
            },
            {
                "ts": "2025-01-15T09:02:00.000+09:00",
                "window_title": "Stack Overflow - Google Chrome",
                "process_name": "chrome.exe",
                "keywords": ["Python", "error"],
                "urls": ["stackoverflow.com"],
            },
        ]

    @pytest.fixture
    def sample_features(self) -> dict[str, Any]:
        """テスト用の特徴量データ"""
        return {
            "meta": {
                "date": "2025-01-15",
                "capture_count": 2,
                "total_duration_min": 4,
                "first_capture": "2025-01-15T09:00:00.000+09:00",
                "last_capture": "2025-01-15T09:02:00.000+09:00",
            },
            "time_blocks": [],
            "app_summary": [],
            "global_keywords": {"top_keywords": [], "domains": []},
            "global_files": [],
        }

    def test_get_log_path(
        self, repository: LogRepository, sample_date: date, temp_log_dir: Path
    ) -> None:
        """get_log_path: 正しいログファイルパスを返す"""
        expected = temp_log_dir / "2025-01-15.jsonl"
        actual = repository.get_log_path(sample_date)
        assert actual == expected

    def test_get_features_path(
        self, repository: LogRepository, sample_date: date, temp_log_dir: Path
    ) -> None:
        """get_features_path: 正しい特徴量ファイルパスを返す"""
        expected = temp_log_dir / "2025-01-15_features.json"
        actual = repository.get_features_path(sample_date)
        assert actual == expected

    def test_read_raw_logs_success(
        self,
        repository: LogRepository,
        sample_date: date,
        sample_raw_logs: list[dict[str, Any]],
    ) -> None:
        """read_raw_logs: 正常なJSONLファイルを読み込める"""
        log_path = repository.get_log_path(sample_date)

        # JSONL形式でファイルを作成
        with open(log_path, "w", encoding="utf-8") as f:
            for record in sample_raw_logs:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # 読み込み
        logs = repository.read_raw_logs(sample_date)

        assert len(logs) == 2
        assert logs[0]["window_title"] == "main.py - Visual Studio Code"
        assert logs[1]["window_title"] == "Stack Overflow - Google Chrome"

    def test_read_raw_logs_with_invalid_lines(
        self,
        repository: LogRepository,
        sample_date: date,
        sample_raw_logs: list[dict[str, Any]],
    ) -> None:
        """read_raw_logs: 不正な行をスキップして読み込む"""
        log_path = repository.get_log_path(sample_date)

        # 正常な行と不正な行が混在
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(sample_raw_logs[0], ensure_ascii=False) + "\n")
            f.write("invalid json line\n")  # 不正な行
            f.write("{incomplete json\n")  # 不正な行
            f.write(json.dumps(sample_raw_logs[1], ensure_ascii=False) + "\n")

        # 不正な行はスキップされ、正常な2レコードのみ取得
        logs = repository.read_raw_logs(sample_date)
        assert len(logs) == 2

    def test_read_raw_logs_with_empty_lines(
        self,
        repository: LogRepository,
        sample_date: date,
        sample_raw_logs: list[dict[str, Any]],
    ) -> None:
        """read_raw_logs: 空行を無視して読み込む"""
        log_path = repository.get_log_path(sample_date)

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(sample_raw_logs[0], ensure_ascii=False) + "\n")
            f.write("\n")  # 空行
            f.write("  \n")  # 空白のみの行
            f.write(json.dumps(sample_raw_logs[1], ensure_ascii=False) + "\n")

        logs = repository.read_raw_logs(sample_date)
        assert len(logs) == 2

    def test_read_raw_logs_file_not_found(
        self, repository: LogRepository, sample_date: date
    ) -> None:
        """read_raw_logs: ファイル不存在時にLogFileNotFoundErrorを発生"""
        with pytest.raises(LogFileNotFoundError) as exc_info:
            repository.read_raw_logs(sample_date)

        assert exc_info.value.file_path == repository.get_log_path(sample_date)

    def test_read_raw_logs_empty_file(
        self, repository: LogRepository, sample_date: date
    ) -> None:
        """read_raw_logs: 空ファイルでLogFileEmptyErrorを発生"""
        log_path = repository.get_log_path(sample_date)
        log_path.touch()  # 空ファイル作成

        with pytest.raises(LogFileEmptyError) as exc_info:
            repository.read_raw_logs(sample_date)

        assert exc_info.value.file_path == log_path

    def test_read_raw_logs_only_empty_lines(
        self, repository: LogRepository, sample_date: date
    ) -> None:
        """read_raw_logs: 空行のみのファイルでLogFileEmptyErrorを発生"""
        log_path = repository.get_log_path(sample_date)

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n\n  \n\n")

        with pytest.raises(LogFileEmptyError):
            repository.read_raw_logs(sample_date)

    def test_read_raw_logs_all_invalid(
        self, repository: LogRepository, sample_date: date
    ) -> None:
        """read_raw_logs: 全行不正でLogParseErrorを発生"""
        log_path = repository.get_log_path(sample_date)

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("invalid line 1\n")
            f.write("invalid line 2\n")
            f.write("{broken json\n")

        with pytest.raises(LogParseError) as exc_info:
            repository.read_raw_logs(sample_date)

        assert exc_info.value.file_path == log_path
        assert exc_info.value.total_lines == 3

    def test_save_features_success(
        self,
        repository: LogRepository,
        sample_date: date,
        sample_features: dict[str, Any],
    ) -> None:
        """save_features: 特徴量を正常に保存できる"""
        saved_path = repository.save_features(sample_date, sample_features)

        assert saved_path.exists()
        assert saved_path == repository.get_features_path(sample_date)

        # 保存内容を検証
        with open(saved_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded["meta"]["date"] == "2025-01-15"
        assert loaded["meta"]["capture_count"] == 2

    def test_save_features_creates_directory(
        self, tmp_path: Path, sample_date: date, sample_features: dict[str, Any]
    ) -> None:
        """save_features: 親ディレクトリが存在しない場合は自動作成"""
        non_existent_dir = tmp_path / "new_logs_dir"
        repository = LogRepository(base_path=non_existent_dir)

        saved_path = repository.save_features(sample_date, sample_features)

        assert non_existent_dir.exists()
        assert saved_path.exists()

    def test_save_features_overwrites_existing(
        self,
        repository: LogRepository,
        sample_date: date,
        sample_features: dict[str, Any],
    ) -> None:
        """save_features: 既存ファイルを上書きできる"""
        # 最初の保存
        repository.save_features(sample_date, sample_features)

        # 内容を変更して再保存
        updated_features = sample_features.copy()
        updated_features["meta"]["capture_count"] = 100

        repository.save_features(sample_date, updated_features)

        # 上書きされていることを確認
        loaded = repository.load_features(sample_date)
        assert loaded is not None
        assert loaded["meta"]["capture_count"] == 100

    def test_load_features_success(
        self,
        repository: LogRepository,
        sample_date: date,
        sample_features: dict[str, Any],
    ) -> None:
        """load_features: 保存済み特徴量を読み込める"""
        repository.save_features(sample_date, sample_features)

        loaded = repository.load_features(sample_date)

        assert loaded is not None
        assert loaded["meta"]["date"] == "2025-01-15"
        assert loaded["meta"]["capture_count"] == 2

    def test_load_features_not_found(
        self, repository: LogRepository, sample_date: date
    ) -> None:
        """load_features: ファイル不存在時にNoneを返す"""
        loaded = repository.load_features(sample_date)
        assert loaded is None

    def test_load_features_broken_json(
        self, repository: LogRepository, sample_date: date
    ) -> None:
        """load_features: 破損JSONでJSONDecodeErrorを発生"""
        features_path = repository.get_features_path(sample_date)

        with open(features_path, "w", encoding="utf-8") as f:
            f.write("{broken json content")

        with pytest.raises(json.JSONDecodeError):
            repository.load_features(sample_date)

    def test_default_base_path(self) -> None:
        """__init__: base_path未指定時にデフォルトパスを使用"""
        repository = LogRepository()

        # Windows環境のLOCALAPPDATAを想定
        assert "DailyReportBot" in str(repository.base_path)
        assert "logs" in str(repository.base_path)

    def test_utf8_encoding(
        self,
        repository: LogRepository,
        sample_date: date,
    ) -> None:
        """read_raw_logs/save_features: UTF-8エンコーディングを正しく処理"""
        # 日本語を含むログデータ
        japanese_log = {
            "ts": "2025-01-15T09:00:00.000+09:00",
            "window_title": "ドキュメント.txt - メモ帳",
            "keywords": ["日本語", "テスト"],
        }

        log_path = repository.get_log_path(sample_date)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(japanese_log, ensure_ascii=False) + "\n")

        # 読み込み
        logs = repository.read_raw_logs(sample_date)
        assert logs[0]["window_title"] == "ドキュメント.txt - メモ帳"
        assert logs[0]["keywords"] == ["日本語", "テスト"]

        # 特徴量も日本語対応確認
        japanese_features = {
            "meta": {"date": "2025-01-15"},
            "global_keywords": {"top_keywords": ["日本語", "キーワード"]},
        }

        repository.save_features(sample_date, japanese_features)
        loaded = repository.load_features(sample_date)

        assert loaded is not None
        assert loaded["global_keywords"]["top_keywords"] == ["日本語", "キーワード"]
