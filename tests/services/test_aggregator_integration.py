"""LogAggregationService の統合テスト

実際のファイル操作を伴う統合テスト。
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from src.domain.features import Features
from src.repositories.log_repository import LogFileEmptyError, LogFileNotFoundError
from src.services.aggregator import LogAggregationService, create_aggregator


class TestAggregatorIntegration:
    """統合テスト"""

    @pytest.fixture
    def temp_log_dir(self, tmp_path: Path) -> Path:
        """テスト用の一時ログディレクトリ"""
        log_dir = tmp_path / "logs"
        log_dir.mkdir(parents=True)
        return log_dir

    @pytest.fixture
    def sample_jsonl_content(self) -> str:
        """テスト用JSONL内容"""
        records = [
            {
                "ts": "2024-01-15T09:00:00+09:00",
                "window_title": "main.py - Visual Studio Code",
                "process_name": "Code.exe",
                "keywords": ["Python", "def", "function"],
                "urls": [],
                "files": ["main.py"],
            },
            {
                "ts": "2024-01-15T09:02:00+09:00",
                "window_title": "main.py - Visual Studio Code",
                "process_name": "Code.exe",
                "keywords": ["Python", "class", "import"],
                "urls": [],
                "files": ["main.py", "utils.py"],
            },
            {
                "ts": "2024-01-15T09:04:00+09:00",
                "window_title": "Stack Overflow - Google Chrome",
                "process_name": "chrome.exe",
                "keywords": ["Python", "error", "exception"],
                "urls": ["stackoverflow.com"],
                "files": [],
            },
            {
                "ts": "2024-01-15T09:06:00+09:00",
                "window_title": "main.py - Visual Studio Code",
                "process_name": "Code.exe",
                "keywords": ["Python", "test"],
                "urls": [],
                "files": ["test_main.py"],
            },
            {
                "ts": "2024-01-15T09:30:00+09:00",
                "window_title": "Slack",
                "process_name": "slack.exe",
                "keywords": ["meeting", "standup"],
                "urls": [],
                "files": [],
            },
        ]
        return "\n".join(json.dumps(r, ensure_ascii=False) for r in records)

    def test_full_aggregation_workflow(
        self, temp_log_dir: Path, sample_jsonl_content: str
    ) -> None:
        """完全な集計ワークフロー"""
        # ログファイル作成
        target_date = date(2024, 1, 15)
        log_file = temp_log_dir / f"{target_date.isoformat()}.jsonl"
        log_file.write_text(sample_jsonl_content, encoding="utf-8")

        # 集計実行
        service = create_aggregator(
            base_path=temp_log_dir,
            config={"exclude_recent_sec": 0},  # テスト用にフィルタリング無効化
        )
        features, saved_path = service.aggregate_and_save(target_date)

        # 検証: Features
        assert isinstance(features, Features)
        assert features.meta.date == "2024-01-15"
        assert features.meta.capture_count == 5

        # 検証: アプリサマリー
        assert len(features.app_summary) == 3
        app_names = [app.name for app in features.app_summary]
        assert "Visual Studio Code" in app_names
        assert "Google Chrome" in app_names
        assert "Slack" in app_names

        # 検証: 時間ブロック（09:00-09:30 と 09:30-10:00）
        assert len(features.time_blocks) >= 2

        # 検証: ファイル保存
        assert saved_path.exists()
        saved_content = json.loads(saved_path.read_text(encoding="utf-8"))
        assert saved_content["meta"]["date"] == "2024-01-15"

    def test_japanese_content(self, temp_log_dir: Path) -> None:
        """日本語コンテンツの処理"""
        records = [
            {
                "ts": "2024-01-15T10:00:00+09:00",
                "window_title": "議事録.docx - Microsoft Word",
                "process_name": "WINWORD.EXE",
                "keywords": ["議事録", "会議", "アジェンダ"],
                "urls": [],
                "files": ["議事録.docx"],
            },
            {
                "ts": "2024-01-15T10:02:00+09:00",
                "window_title": "企画書.xlsx - Microsoft Excel",
                "process_name": "EXCEL.EXE",
                "keywords": ["予算", "スケジュール"],
                "urls": [],
                "files": ["企画書.xlsx"],
            },
        ]

        target_date = date(2024, 1, 15)
        log_file = temp_log_dir / f"{target_date.isoformat()}.jsonl"
        log_file.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records),
            encoding="utf-8",
        )

        service = create_aggregator(
            base_path=temp_log_dir,
            config={"exclude_recent_sec": 0},
        )
        features = service.aggregate(target_date)

        # 日本語キーワードが正しく処理されている
        all_keywords = features.global_keywords.top_keywords
        assert "議事録" in all_keywords or "会議" in all_keywords

        # 日本語ファイル名が正しく処理されている
        all_files = features.global_keywords.top_files
        assert any("議事録" in f or "企画書" in f for f in all_files)

    def test_single_record(self, temp_log_dir: Path) -> None:
        """1件のみのレコード処理"""
        records = [
            {
                "ts": "2024-01-15T14:00:00+09:00",
                "window_title": "main.py - Visual Studio Code",
                "process_name": "Code.exe",
                "keywords": ["Python"],
                "urls": [],
                "files": ["main.py"],
            },
        ]

        target_date = date(2024, 1, 15)
        log_file = temp_log_dir / f"{target_date.isoformat()}.jsonl"
        log_file.write_text(
            json.dumps(records[0], ensure_ascii=False),
            encoding="utf-8",
        )

        service = create_aggregator(
            base_path=temp_log_dir,
            config={"exclude_recent_sec": 0},
        )
        features = service.aggregate(target_date)

        assert features.meta.capture_count == 1
        assert len(features.app_summary) == 1

    def test_same_app_all_day(self, temp_log_dir: Path) -> None:
        """全て同一アプリの場合"""
        records = [
            {
                "ts": f"2024-01-15T{h:02d}:00:00+09:00",
                "window_title": "project - Visual Studio Code",
                "process_name": "Code.exe",
                "keywords": ["Python"],
                "urls": [],
                "files": ["main.py"],
            }
            for h in range(9, 18)  # 9時から17時まで
        ]

        target_date = date(2024, 1, 15)
        log_file = temp_log_dir / f"{target_date.isoformat()}.jsonl"
        log_file.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records),
            encoding="utf-8",
        )

        service = create_aggregator(
            base_path=temp_log_dir,
            config={"exclude_recent_sec": 0},
        )
        features = service.aggregate(target_date)

        # 1つのアプリのみ
        assert len(features.app_summary) == 1
        assert features.app_summary[0].name == "Visual Studio Code"
        assert features.app_summary[0].rank.value == "high"

    def test_empty_keywords_urls_files(self, temp_log_dir: Path) -> None:
        """キーワード・URL・ファイルが全て空の場合"""
        records = [
            {
                "ts": "2024-01-15T09:00:00+09:00",
                "window_title": "Desktop",
                "process_name": "explorer.exe",
                "keywords": [],
                "urls": [],
                "files": [],
            },
            {
                "ts": "2024-01-15T09:02:00+09:00",
                "window_title": "Desktop",
                "process_name": "explorer.exe",
                "keywords": [],
                "urls": [],
                "files": [],
            },
        ]

        target_date = date(2024, 1, 15)
        log_file = temp_log_dir / f"{target_date.isoformat()}.jsonl"
        log_file.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records),
            encoding="utf-8",
        )

        service = create_aggregator(
            base_path=temp_log_dir,
            config={"exclude_recent_sec": 0},
        )
        features = service.aggregate(target_date)

        assert features.global_keywords.top_keywords == []
        assert features.global_keywords.top_urls == []
        assert features.global_keywords.top_files == []

    def test_file_not_found_error(self, temp_log_dir: Path) -> None:
        """ファイルが存在しない場合のエラー"""
        service = create_aggregator(base_path=temp_log_dir)

        with pytest.raises(LogFileNotFoundError):
            service.aggregate(date(2024, 1, 15))

    def test_empty_file_error(self, temp_log_dir: Path) -> None:
        """空ファイルの場合のエラー"""
        target_date = date(2024, 1, 15)
        log_file = temp_log_dir / f"{target_date.isoformat()}.jsonl"
        log_file.write_text("", encoding="utf-8")

        service = create_aggregator(base_path=temp_log_dir)

        with pytest.raises(LogFileEmptyError):
            service.aggregate(target_date)

    def test_large_dataset(self, temp_log_dir: Path) -> None:
        """大量レコード（1000件以上）の処理"""
        # 1000件のレコードを生成（約16時間分、1分間隔）
        records = []
        for i in range(1000):
            hour = 9 + (i // 60)
            minute = i % 60
            if hour >= 24:
                hour = hour % 24
            records.append(
                {
                    "ts": f"2024-01-15T{hour:02d}:{minute:02d}:00+09:00",
                    "window_title": f"file{i % 10}.py - VSCode",
                    "process_name": "Code.exe" if i % 3 != 0 else "chrome.exe",
                    "keywords": [f"keyword{i % 20}"],
                    "urls": [f"site{i % 5}.com"] if i % 3 == 0 else [],
                    "files": [f"file{i % 10}.py"],
                }
            )

        target_date = date(2024, 1, 15)
        log_file = temp_log_dir / f"{target_date.isoformat()}.jsonl"
        log_file.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in records),
            encoding="utf-8",
        )

        service = create_aggregator(
            base_path=temp_log_dir,
            config={"exclude_recent_sec": 0},
        )
        features = service.aggregate(target_date)

        # 正常に処理完了
        assert features.meta.capture_count == 1000
        assert len(features.app_summary) == 2  # Code.exe と chrome.exe
        assert len(features.time_blocks) > 0
