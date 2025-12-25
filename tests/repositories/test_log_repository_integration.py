"""LogRepository統合テスト - 実際のワークフロー検証"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from src.domain.features import Features, FeaturesMeta, GlobalKeywords
from src.repositories import LogRepository


class TestLogRepositoryIntegration:
    """実際の使用シナリオに基づく統合テスト"""

    @pytest.fixture
    def temp_log_dir(self, tmp_path: Path) -> Path:
        """一時ログディレクトリ"""
        log_dir = tmp_path / "integration_logs"
        log_dir.mkdir()
        return log_dir

    @pytest.fixture
    def repository(self, temp_log_dir: Path) -> LogRepository:
        """テスト用リポジトリ"""
        return LogRepository(base_path=temp_log_dir)

    def test_daily_report_generation_workflow(
        self, repository: LogRepository
    ) -> None:
        """日報生成の典型的なワークフロー

        1. PowerShellロガーがraw.jsonlを生成
        2. Aggregatorがraw.jsonlを読み込み
        3. Aggregatorがfeatures.jsonを保存
        4. LLM SummarizerがfeaturesをロードしてLLM処理
        """
        target_date = date(2025, 1, 15)

        # Phase 1: PowerShellロガーがraw.jsonlを生成（模擬）
        raw_logs = [
            {
                "ts": "2025-01-15T09:00:00+09:00",
                "window_title": "app.py - VSCode",
                "process_name": "Code.exe",
                "keywords": ["Python", "Flask"],
                "files": ["app.py"],
            },
            {
                "ts": "2025-01-15T09:02:00+09:00",
                "window_title": "Flask Documentation - Chrome",
                "process_name": "chrome.exe",
                "keywords": ["Flask", "API"],
                "urls": ["flask.palletsprojects.com"],
            },
            {
                "ts": "2025-01-15T09:04:00+09:00",
                "window_title": "app.py - VSCode",
                "process_name": "Code.exe",
                "keywords": ["Python", "def", "route"],
                "files": ["app.py"],
            },
        ]

        log_path = repository.get_log_path(target_date)
        with open(log_path, "w", encoding="utf-8") as f:
            for record in raw_logs:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # Phase 2: Aggregatorがraw.jsonlを読み込み
        loaded_logs = repository.read_raw_logs(target_date)
        assert len(loaded_logs) == 3
        assert all("ts" in log for log in loaded_logs)

        # Phase 3: Aggregatorが特徴量を計算して保存（模擬）
        features_data = {
            "meta": {
                "date": target_date.isoformat(),
                "capture_count": len(loaded_logs),
                "total_duration_min": 6,
                "first_capture": raw_logs[0]["ts"],
                "last_capture": raw_logs[-1]["ts"],
            },
            "time_blocks": [
                {
                    "start": "09:00",
                    "end": "09:10",
                    "apps": [
                        {"name": "Visual Studio Code", "duration_min": 4},
                        {"name": "Google Chrome", "duration_min": 2},
                    ],
                    "keywords": ["Python", "Flask", "API"],
                }
            ],
            "app_summary": [
                {
                    "name": "Visual Studio Code",
                    "duration_min": 4,
                    "rank": "high",
                    "keywords": ["Python", "Flask", "def"],
                }
            ],
            "global_keywords": {
                "top_keywords": ["Python", "Flask", "API"],
                "domains": ["flask.palletsprojects.com"],
            },
            "global_files": ["app.py"],
        }

        saved_path = repository.save_features(target_date, features_data)
        assert saved_path.exists()

        # Phase 4: LLM Summarizerがfeaturesをロード
        loaded_features_dict = repository.load_features(target_date)
        assert loaded_features_dict is not None
        assert loaded_features_dict["meta"]["capture_count"] == 3
        assert loaded_features_dict["global_keywords"]["top_keywords"] == [
            "Python",
            "Flask",
            "API",
        ]

    def test_error_recovery_scenario(
        self, repository: LogRepository
    ) -> None:
        """エラーからの回復シナリオ

        1. 不正なデータを含むraw.jsonlを処理
        2. 部分的に正常なデータを抽出
        3. features.jsonを生成して次工程へ
        """
        target_date = date(2025, 1, 16)

        # 不正な行を含むログファイル
        log_path = repository.get_log_path(target_date)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write('{"ts":"2025-01-16T10:00:00+09:00","window_title":"valid1"}\n')
            f.write("invalid json line without proper format\n")
            f.write('{"ts":"2025-01-16T10:02:00+09:00"')  # 不完全JSON
            f.write("\n")
            f.write('{"ts":"2025-01-16T10:04:00+09:00","window_title":"valid2"}\n')

        # 不正な行はスキップされ、2件のみ読み込まれる
        logs = repository.read_raw_logs(target_date)
        assert len(logs) == 2
        assert logs[0]["window_title"] == "valid1"
        assert logs[1]["window_title"] == "valid2"

        # 有効なデータのみで特徴量を生成
        features_data = {
            "meta": {
                "date": target_date.isoformat(),
                "capture_count": len(logs),
                "total_duration_min": 4,
                "first_capture": logs[0]["ts"],
                "last_capture": logs[-1]["ts"],
            },
            "time_blocks": [],
            "app_summary": [],
            "global_keywords": {"top_keywords": [], "domains": []},
            "global_files": [],
        }

        repository.save_features(target_date, features_data)

        # 保存されたデータを確認
        loaded = repository.load_features(target_date)
        assert loaded is not None
        assert loaded["meta"]["capture_count"] == 2

    def test_multiple_days_workflow(
        self, repository: LogRepository
    ) -> None:
        """複数日のログを扱うワークフロー"""
        dates = [date(2025, 1, 10), date(2025, 1, 11), date(2025, 1, 12)]

        # 3日分のログとfeaturesを作成
        for i, target_date in enumerate(dates):
            # raw.jsonl作成
            log_path = repository.get_log_path(target_date)
            with open(log_path, "w", encoding="utf-8") as f:
                for j in range(3):
                    log = {
                        "ts": f"{target_date.isoformat()}T{9+j:02d}:00:00+09:00",
                        "window_title": f"Day{i+1}_Log{j+1}",
                    }
                    f.write(json.dumps(log, ensure_ascii=False) + "\n")

            # features.json作成
            features = {
                "meta": {
                    "date": target_date.isoformat(),
                    "capture_count": 3,
                },
                "time_blocks": [],
                "app_summary": [],
                "global_keywords": {"top_keywords": [], "domains": []},
                "global_files": [],
            }
            repository.save_features(target_date, features)

        # 各日のデータを読み込み確認
        for i, target_date in enumerate(dates):
            logs = repository.read_raw_logs(target_date)
            assert len(logs) == 3
            assert logs[0]["window_title"] == f"Day{i+1}_Log1"

            features_dict: dict[str, Any] | None = repository.load_features(target_date)
            assert features_dict is not None
            assert features_dict["meta"]["date"] == target_date.isoformat()

    def test_pydantic_model_compatibility(
        self, repository: LogRepository
    ) -> None:
        """Pydanticモデルとの互換性確認"""
        target_date = date(2025, 1, 20)

        # Pydanticモデルから生成したデータ
        meta = FeaturesMeta(
            date=target_date.isoformat(),
            generated_at="2025-01-20T09:00:00+09:00",
            capture_count=10,
            total_duration_min=20,
            first_capture="09:00:00",  # HH:MM:SS形式
            last_capture="09:18:00",  # HH:MM:SS形式
        )

        # Featuresモデルを明示的に全フィールド指定
        features = Features(
            meta=meta,
            time_blocks=[],
            app_summary=[],
            global_keywords=GlobalKeywords(
                top_keywords=[],
                top_urls=[],
                top_files=[],
            ),
        )

        # Pydanticモデルをdictに変換して保存
        repository.save_features(target_date, features.model_dump())

        # ロードしてPydanticモデルに復元
        loaded_dict = repository.load_features(target_date)
        assert loaded_dict is not None

        loaded_features = Features.model_validate(loaded_dict)
        assert loaded_features.meta.date == target_date.isoformat()
        assert loaded_features.meta.capture_count == 10
        assert loaded_features.meta.first_capture == "09:00:00"
        assert loaded_features.meta.last_capture == "09:18:00"
