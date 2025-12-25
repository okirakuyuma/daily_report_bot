"""ドメインモデルのJSON シリアライゼーションテスト."""

import json

import pytest

from src.domain import (
    AppRank,
    AppSummary,
    AppUsage,
    CaptureRecord,
    Features,
    FeaturesMeta,
    GlobalKeywords,
    TimeBlock,
)


class TestCaptureRecordSerialization:
    """CaptureRecord のシリアライゼーションテスト."""

    def test_capture_record_to_json(self) -> None:
        """CaptureRecord を JSON に変換できる."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            window_title="Chrome - Google",
            process_name="chrome.exe",
            keywords=["search", "google"],
            urls=["https://google.com"],
            files=["C:\\test.txt"],
            numbers=["123"],
        )

        json_str = record.model_dump_json()
        data = json.loads(json_str)

        assert data["ts"] == "2025-12-25T14:30:00+09:00"
        assert data["window_title"] == "Chrome - Google"
        assert data["process_name"] == "chrome.exe"
        assert data["keywords"] == ["search", "google"]

    def test_capture_record_from_json(self) -> None:
        """JSON から CaptureRecord を生成できる."""
        json_data = {
            "ts": "2025-12-25T14:30:00+09:00",
            "window_title": "Chrome - Google",
            "process_name": "chrome.exe",
            "keywords": ["search"],
            "urls": ["https://google.com"],
            "files": [],
            "numbers": [],
        }

        record = CaptureRecord.model_validate(json_data)

        assert record.ts == "2025-12-25T14:30:00+09:00"
        assert record.window_title == "Chrome - Google"
        assert record.keywords == ["search"]

    def test_capture_record_roundtrip(self) -> None:
        """CaptureRecord の JSON 往復変換."""
        original = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            window_title="Test",
            keywords=["test", "python"],
        )

        json_str = original.model_dump_json()
        restored = CaptureRecord.model_validate_json(json_str)

        assert restored.ts == original.ts
        assert restored.window_title == original.window_title
        assert restored.keywords == original.keywords

    def test_capture_record_minimal_json(self) -> None:
        """最小限の JSON から CaptureRecord を生成."""
        json_data = {"ts": "2025-12-25T14:30:00+09:00"}

        record = CaptureRecord.model_validate(json_data)

        assert record.ts == "2025-12-25T14:30:00+09:00"
        assert record.window_title is None
        assert record.keywords == []


class TestFeaturesSerialization:
    """Features のシリアライゼーションテスト."""

    def test_features_to_json(self) -> None:
        """Features を JSON に変換できる."""
        features = Features(
            meta=FeaturesMeta(
                date="2025-12-25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=100,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=480.0,
            ),
            time_blocks=[
                TimeBlock(
                    start="09:00",
                    end="10:00",
                    apps=[AppUsage(name="Chrome", percent=60.5)],
                    top_keywords=["search"],
                    top_files=["test.txt"],
                ),
            ],
            app_summary=[
                AppSummary(
                    name="Google Chrome",
                    process="chrome.exe",
                    count=50,
                    duration_min=100.5,
                    rank=AppRank.HIGH,
                    top_keywords=["search", "docs"],
                    top_files=["file1.txt"],
                    top_urls=["google.com"],
                ),
            ],
            global_keywords=GlobalKeywords(
                top_keywords=["search", "python"],
                top_urls=["google.com"],
                top_files=["test.py"],
            ),
        )

        json_str = features.model_dump_json(indent=2)
        data = json.loads(json_str)

        assert data["meta"]["date"] == "2025-12-25"
        assert data["meta"]["capture_count"] == 100
        assert len(data["time_blocks"]) == 1
        assert len(data["app_summary"]) == 1
        assert data["app_summary"][0]["rank"] == "high"

    def test_features_from_json(self) -> None:
        """JSON から Features を生成できる."""
        json_data = {
            "meta": {
                "date": "2025-12-25",
                "generated_at": "2025-12-25T18:00:00+09:00",
                "capture_count": 100,
                "first_capture": "09:00:00",
                "last_capture": "18:00:00",
                "total_duration_min": 480.0,
            },
            "time_blocks": [
                {
                    "start": "09:00",
                    "end": "10:00",
                    "apps": [{"name": "Chrome", "percent": 60.0}],
                    "top_keywords": ["search"],
                    "top_files": [],
                }
            ],
            "app_summary": [
                {
                    "name": "Chrome",
                    "process": "chrome.exe",
                    "count": 50,
                    "duration_min": 100.0,
                    "rank": "high",
                    "top_keywords": ["search"],
                }
            ],
            "global_keywords": {
                "top_keywords": ["search"],
                "top_urls": [],
                "top_files": [],
            },
        }

        features = Features.model_validate(json_data)

        assert features.meta.date == "2025-12-25"
        assert features.meta.capture_count == 100
        assert len(features.time_blocks) == 1
        assert len(features.app_summary) == 1
        assert features.app_summary[0].rank == AppRank.HIGH

    def test_features_roundtrip(self) -> None:
        """Features の JSON 往復変換."""
        original = Features(
            meta=FeaturesMeta(
                date="2025-12-25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=50,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=240.0,
            ),
            app_summary=[
                AppSummary(
                    name="VSCode",
                    process="code.exe",
                    count=30,
                    duration_min=120.0,
                    rank=AppRank.MEDIUM,
                    top_keywords=["python"],
                ),
            ],
        )

        json_str = original.model_dump_json()
        restored = Features.model_validate_json(json_str)

        assert restored.meta.date == original.meta.date
        assert restored.meta.capture_count == original.meta.capture_count
        assert len(restored.app_summary) == len(original.app_summary)
        assert restored.app_summary[0].name == original.app_summary[0].name

    def test_features_minimal_json(self) -> None:
        """最小限の JSON から Features を生成."""
        json_data = {
            "meta": {
                "date": "2025-12-25",
                "generated_at": "2025-12-25T18:00:00+09:00",
                "capture_count": 0,
                "first_capture": "00:00:00",
                "last_capture": "00:00:00",
                "total_duration_min": 0.0,
            }
        }

        features = Features.model_validate(json_data)

        assert features.meta.date == "2025-12-25"
        assert features.time_blocks == []
        assert features.app_summary == []

    def test_app_rank_enum_serialization(self) -> None:
        """AppRank Enum が正しくシリアライズされる."""
        summary = AppSummary(
            name="Chrome",
            process="chrome.exe",
            count=50,
            duration_min=100.0,
            rank=AppRank.HIGH,
        )

        data = summary.model_dump()

        assert data["rank"] == "high"
        assert isinstance(data["rank"], str)

    def test_app_rank_enum_deserialization(self) -> None:
        """文字列から AppRank Enum にデシリアライズされる."""
        json_data = {
            "name": "Chrome",
            "process": "chrome.exe",
            "count": 50,
            "duration_min": 100.0,
            "rank": "medium",
        }

        summary = AppSummary.model_validate(json_data)

        assert summary.rank == AppRank.MEDIUM
        assert isinstance(summary.rank, AppRank)


class TestEdgeCases:
    """エッジケースのシリアライゼーションテスト."""

    def test_capture_record_with_none_values(self) -> None:
        """None 値を含む CaptureRecord のシリアライゼーション."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            window_title=None,
            process_name=None,
        )

        json_str = record.model_dump_json()
        data = json.loads(json_str)

        assert data["window_title"] is None
        assert data["process_name"] is None

    def test_features_with_empty_lists(self) -> None:
        """空リストを含む Features のシリアライゼーション."""
        features = Features(
            meta=FeaturesMeta(
                date="2025-12-25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=0,
                first_capture="00:00:00",
                last_capture="00:00:00",
                total_duration_min=0.0,
            ),
            time_blocks=[],
            app_summary=[],
        )

        json_str = features.model_dump_json()
        data = json.loads(json_str)

        assert data["time_blocks"] == []
        assert data["app_summary"] == []

    def test_unicode_handling(self) -> None:
        """Unicode 文字の正しい処理."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            window_title="メモ帳 - テスト.txt",
            keywords=["日本語", "テスト"],
        )

        json_str = record.model_dump_json()
        restored = CaptureRecord.model_validate_json(json_str)

        assert restored.window_title == "メモ帳 - テスト.txt"
        assert "日本語" in restored.keywords
        assert "テスト" in restored.keywords
