"""CaptureRecord ドメインモデルのユニットテスト."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.domain.capture import CaptureRecord


class TestCaptureRecordValidation:
    """CaptureRecord のバリデーションテスト."""

    def test_valid_minimal_record(self) -> None:
        """最小限の有効なレコードを作成できる."""
        record = CaptureRecord(ts="2025-12-25T14:30:00+09:00")

        assert record.ts == "2025-12-25T14:30:00+09:00"
        assert record.window_title is None
        assert record.process_name is None
        assert record.keywords == []
        assert record.urls == []
        assert record.files == []
        assert record.numbers == []

    def test_valid_full_record(self) -> None:
        """全フィールドを持つ有効なレコードを作成できる."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            window_title="Chrome - Google",
            process_name="chrome.exe",
            keywords=["login", "auth"],
            urls=["https://google.com"],
            files=["C:\\Users\\test.txt"],
            numbers=["123", "45.6"],
        )

        assert record.window_title == "Chrome - Google"
        assert record.process_name == "chrome.exe"
        assert len(record.keywords) == 2
        assert len(record.urls) == 1

    def test_invalid_timestamp_raises_error(self) -> None:
        """無効なタイムスタンプでバリデーションエラー."""
        with pytest.raises(ValidationError) as exc_info:
            CaptureRecord(ts="invalid-timestamp")

        assert "無効なISO 8601タイムスタンプ" in str(exc_info.value)

    def test_empty_string_normalized_to_none(self) -> None:
        """空文字列はNoneに正規化される."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            window_title="  ",
            process_name="",
        )

        assert record.window_title is None
        assert record.process_name is None

    def test_whitespace_trimmed_in_strings(self) -> None:
        """文字列の前後の空白はトリミングされる."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            window_title="  Chrome - Google  ",
            process_name="  chrome.exe  ",
        )

        assert record.window_title == "Chrome - Google"
        assert record.process_name == "chrome.exe"

    def test_duplicate_keywords_removed(self) -> None:
        """重複するキーワードは削除される."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            keywords=["login", "auth", "login", "auth"],
        )

        assert record.keywords == ["login", "auth"]

    def test_empty_strings_in_lists_removed(self) -> None:
        """リスト内の空文字列は削除される."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            keywords=["login", "", "  ", "auth"],
            urls=["https://google.com", "", "  "],
        )

        assert record.keywords == ["login", "auth"]
        assert record.urls == ["https://google.com"]


class TestCaptureRecordProperties:
    """CaptureRecord のプロパティテスト."""

    def test_timestamp_property(self) -> None:
        """timestamp プロパティが datetime を返す."""
        record = CaptureRecord(ts="2025-12-25T14:30:00+09:00")
        ts = record.timestamp

        assert isinstance(ts, datetime)
        assert ts.year == 2025
        assert ts.month == 12
        assert ts.day == 25
        assert ts.hour == 14
        assert ts.minute == 30

    def test_timestamp_with_z_suffix(self) -> None:
        """Z サフィックス付きタイムスタンプも正しく処理される."""
        record = CaptureRecord(ts="2025-12-25T14:30:00Z")
        ts = record.timestamp

        assert ts.tzinfo == timezone.utc

    def test_has_content_with_data(self) -> None:
        """データがある場合 has_content は True."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            window_title="Chrome",
        )

        assert record.has_content is True

    def test_has_content_without_data(self) -> None:
        """データがない場合 has_content は False."""
        record = CaptureRecord(ts="2025-12-25T14:30:00+09:00")

        assert record.has_content is False

    def test_has_content_with_keywords_only(self) -> None:
        """キーワードのみでも has_content は True."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            keywords=["test"],
        )

        assert record.has_content is True

    def test_app_identifier_from_process_name(self) -> None:
        """process_name がある場合はそれを使用."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            process_name="chrome.exe",
            window_title="Some Window",
        )

        assert record.app_identifier == "chrome"

    def test_app_identifier_from_window_title(self) -> None:
        """process_name がない場合は window_title から推定."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            window_title="VSCode - test.py",
        )

        # ハイフン区切りの最後の部分を使用
        assert record.app_identifier == "test.py"

    def test_app_identifier_unknown(self) -> None:
        """データがない場合は unknown."""
        record = CaptureRecord(ts="2025-12-25T14:30:00+09:00")

        assert record.app_identifier == "unknown"


class TestCaptureRecordMethods:
    """CaptureRecord のメソッドテスト."""

    def test_merge_features_combines_keywords(self) -> None:
        """merge_features でキーワードが結合される."""
        record1 = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            keywords=["login", "auth"],
        )
        record2 = CaptureRecord(
            ts="2025-12-25T14:31:00+09:00",
            keywords=["oauth", "token"],
        )

        record1.merge_features(record2)

        assert set(record1.keywords) == {"login", "auth", "oauth", "token"}

    def test_merge_features_removes_duplicates(self) -> None:
        """merge_features で重複が削除される."""
        record1 = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            keywords=["login", "auth"],
        )
        record2 = CaptureRecord(
            ts="2025-12-25T14:31:00+09:00",
            keywords=["auth", "token"],
        )

        record1.merge_features(record2)

        assert record1.keywords == ["login", "auth", "token"]

    def test_merge_features_preserves_timestamp(self) -> None:
        """merge_features でタイムスタンプは変更されない."""
        original_ts = "2025-12-25T14:30:00+09:00"
        record1 = CaptureRecord(ts=original_ts)
        record2 = CaptureRecord(ts="2025-12-25T14:31:00+09:00")

        record1.merge_features(record2)

        assert record1.ts == original_ts

    def test_merge_features_all_fields(self) -> None:
        """merge_features で全フィールドが結合される."""
        record1 = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            keywords=["k1"],
            urls=["url1"],
            files=["f1"],
            numbers=["1"],
        )
        record2 = CaptureRecord(
            ts="2025-12-25T14:31:00+09:00",
            keywords=["k2"],
            urls=["url2"],
            files=["f2"],
            numbers=["2"],
        )

        record1.merge_features(record2)

        assert record1.keywords == ["k1", "k2"]
        assert record1.urls == ["url1", "url2"]
        assert record1.files == ["f1", "f2"]
        assert record1.numbers == ["1", "2"]


class TestCaptureRecordStringRepresentation:
    """CaptureRecord の文字列表現テスト."""

    def test_str_with_full_data(self) -> None:
        """__str__ が読みやすい形式を返す."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            process_name="chrome.exe",
            window_title="Chrome - Google",
        )

        result = str(record)

        assert "[2025-12-25T14:30:00+09:00]" in result
        assert "chrome" in result
        assert "Chrome - Google" in result

    def test_str_without_title(self) -> None:
        """__str__ でタイトルなしの場合."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            process_name="chrome.exe",
        )

        result = str(record)

        assert "(タイトルなし)" in result

    def test_repr_shows_key_fields(self) -> None:
        """__repr__ がデバッグ情報を含む."""
        record = CaptureRecord(
            ts="2025-12-25T14:30:00+09:00",
            window_title="Test",
            process_name="test.exe",
        )

        result = repr(record)

        assert "CaptureRecord" in result
        assert "ts=" in result
        assert "window_title=" in result
        assert "process_name=" in result
