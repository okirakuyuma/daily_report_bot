"""Features ドメインモデルのユニットテスト."""

import pytest
from pydantic import ValidationError

from src.domain.features import (
    AppRank,
    AppSummary,
    AppUsage,
    Features,
    FeaturesMeta,
    GlobalKeywords,
    TimeBlock,
)


class TestAppUsageValidation:
    """AppUsage のバリデーションテスト."""

    def test_valid_app_usage(self) -> None:
        """有効な AppUsage を作成できる."""
        usage = AppUsage(name="Chrome", percent=45.5)

        assert usage.name == "Chrome"
        assert usage.percent == 45.5

    def test_percent_rounded(self) -> None:
        """パーセント値は小数点1桁に丸められる."""
        usage = AppUsage(name="Chrome", percent=45.567)

        assert usage.percent == 45.6

    def test_percent_below_zero_raises_error(self) -> None:
        """0未満のパーセント値でエラー."""
        with pytest.raises(ValidationError):
            AppUsage(name="Chrome", percent=-1.0)

    def test_percent_above_hundred_raises_error(self) -> None:
        """100超のパーセント値でエラー."""
        with pytest.raises(ValidationError):
            AppUsage(name="Chrome", percent=101.0)

    def test_empty_name_raises_error(self) -> None:
        """空のアプリ名でエラー."""
        with pytest.raises(ValidationError):
            AppUsage(name="", percent=50.0)


class TestTimeBlockValidation:
    """TimeBlock のバリデーションテスト."""

    def test_valid_time_block(self) -> None:
        """有効な TimeBlock を作成できる."""
        block = TimeBlock(
            start="09:00",
            end="10:00",
            apps=[AppUsage(name="Chrome", percent=50.0)],
            top_keywords=["test"],
            top_files=["file.txt"],
        )

        assert block.start == "09:00"
        assert block.end == "10:00"
        assert len(block.apps) == 1
        assert block.apps[0].name == "Chrome"

    def test_invalid_time_format_raises_error(self) -> None:
        """無効な時刻形式でエラー."""
        with pytest.raises(ValidationError):
            TimeBlock(start="25:00", end="10:00")

        with pytest.raises(ValidationError):
            TimeBlock(start="09:00", end="10:99")

    def test_apps_sorted_by_percent(self) -> None:
        """アプリは使用率降順にソートされる."""
        block = TimeBlock(
            start="09:00",
            end="10:00",
            apps=[
                AppUsage(name="App1", percent=30.0),
                AppUsage(name="App2", percent=50.0),
                AppUsage(name="App3", percent=20.0),
            ],
        )

        assert block.apps[0].name == "App2"
        assert block.apps[0].percent == 50.0
        assert block.apps[1].name == "App1"
        assert block.apps[2].name == "App3"

    def test_duration_minutes_property(self) -> None:
        """duration_minutes プロパティが正しく計算される."""
        block = TimeBlock(start="09:00", end="10:30")

        assert block.duration_minutes == 90

    def test_duration_minutes_across_hours(self) -> None:
        """時をまたぐ時間の計算."""
        block = TimeBlock(start="09:45", end="11:15")

        assert block.duration_minutes == 90


class TestAppSummaryValidation:
    """AppSummary のバリデーションテスト."""

    def test_valid_app_summary(self) -> None:
        """有効な AppSummary を作成できる."""
        summary = AppSummary(
            name="Google Chrome",
            process="chrome.exe",
            count=150,
            duration_min=120.5,
            rank=AppRank.HIGH,
            top_keywords=["search", "docs"],
        )

        assert summary.name == "Google Chrome"
        assert summary.process == "chrome.exe"
        assert summary.count == 150
        assert summary.duration_min == 120.5
        assert summary.rank == AppRank.HIGH

    def test_duration_rounded(self) -> None:
        """使用時間は小数点1桁に丸められる."""
        summary = AppSummary(
            name="Chrome",
            process="chrome.exe",
            count=100,
            duration_min=120.567,
            rank=AppRank.HIGH,
        )

        assert summary.duration_min == 120.6

    def test_count_must_be_positive(self) -> None:
        """観測回数は1以上."""
        with pytest.raises(ValidationError):
            AppSummary(
                name="Chrome",
                process="chrome.exe",
                count=0,
                duration_min=100.0,
                rank=AppRank.HIGH,
            )

    def test_optional_fields(self) -> None:
        """オプショナルフィールドはNone可能."""
        summary = AppSummary(
            name="Chrome",
            process="chrome.exe",
            count=100,
            duration_min=100.0,
            rank=AppRank.HIGH,
            top_files=None,
            top_urls=None,
        )

        assert summary.top_files is None
        assert summary.top_urls is None


class TestGlobalKeywordsValidation:
    """GlobalKeywords のバリデーションテスト."""

    def test_valid_global_keywords(self) -> None:
        """有効な GlobalKeywords を作成できる."""
        keywords = GlobalKeywords(
            top_keywords=["test", "python"],
            top_urls=["github.com"],
            top_files=["test.py"],
        )

        assert len(keywords.top_keywords) == 2
        assert len(keywords.top_urls) == 1
        assert len(keywords.top_files) == 1

    def test_empty_global_keywords(self) -> None:
        """空の GlobalKeywords を作成できる."""
        keywords = GlobalKeywords()

        assert keywords.top_keywords == []
        assert keywords.top_urls == []
        assert keywords.top_files == []


class TestFeaturesMetaValidation:
    """FeaturesMeta のバリデーションテスト."""

    def test_valid_features_meta(self) -> None:
        """有効な FeaturesMeta を作成できる."""
        meta = FeaturesMeta(
            date="2025-12-25",
            generated_at="2025-12-25T18:00:00+09:00",
            capture_count=240,
            first_capture="09:00:00",
            last_capture="18:00:00",
            total_duration_min=480.0,
        )

        assert meta.date == "2025-12-25"
        assert meta.capture_count == 240
        assert meta.total_duration_min == 480.0

    def test_invalid_date_format_raises_error(self) -> None:
        """無効な日付形式でエラー."""
        with pytest.raises(ValidationError) as exc_info:
            FeaturesMeta(
                date="2025/12/25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=0,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=0.0,
            )

        # パターンマッチエラーまたはバリデータエラーのいずれか
        error_msg = str(exc_info.value)
        assert "pattern" in error_msg or "無効な日付形式" in error_msg

    def test_invalid_timestamp_raises_error(self) -> None:
        """無効なタイムスタンプでエラー."""
        with pytest.raises(ValidationError) as exc_info:
            FeaturesMeta(
                date="2025-12-25",
                generated_at="invalid",
                capture_count=0,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=0.0,
            )

        assert "無効なISO 8601タイムスタンプ" in str(exc_info.value)

    def test_total_duration_rounded(self) -> None:
        """総記録時間は小数点1桁に丸められる."""
        meta = FeaturesMeta(
            date="2025-12-25",
            generated_at="2025-12-25T18:00:00+09:00",
            capture_count=240,
            first_capture="09:00:00",
            last_capture="18:00:00",
            total_duration_min=480.567,
        )

        assert meta.total_duration_min == 480.6

    def test_invalid_time_format_raises_error(self) -> None:
        """無効な時刻形式でエラー."""
        with pytest.raises(ValidationError):
            FeaturesMeta(
                date="2025-12-25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=0,
                first_capture="25:00:00",
                last_capture="18:00:00",
                total_duration_min=0.0,
            )


class TestFeaturesValidation:
    """Features のバリデーションテスト."""

    def test_valid_features(self) -> None:
        """有効な Features を作成できる."""
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
                TimeBlock(start="09:00", end="10:00"),
            ],
            app_summary=[
                AppSummary(
                    name="Chrome",
                    process="chrome.exe",
                    count=50,
                    duration_min=100.0,
                    rank=AppRank.HIGH,
                ),
            ],
            global_keywords=GlobalKeywords(),
        )

        assert features.meta.date == "2025-12-25"
        assert len(features.time_blocks) == 1
        assert len(features.app_summary) == 1

    def test_app_summary_sorted_by_duration(self) -> None:
        """アプリサマリは使用時間降順にソートされる."""
        features = Features(
            meta=FeaturesMeta(
                date="2025-12-25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=100,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=480.0,
            ),
            app_summary=[
                AppSummary(
                    name="App1",
                    process="app1.exe",
                    count=10,
                    duration_min=50.0,
                    rank=AppRank.LOW,
                ),
                AppSummary(
                    name="App2",
                    process="app2.exe",
                    count=20,
                    duration_min=150.0,
                    rank=AppRank.HIGH,
                ),
                AppSummary(
                    name="App3",
                    process="app3.exe",
                    count=15,
                    duration_min=100.0,
                    rank=AppRank.MEDIUM,
                ),
            ],
        )

        assert features.app_summary[0].name == "App2"
        assert features.app_summary[1].name == "App3"
        assert features.app_summary[2].name == "App1"

    def test_features_frozen(self) -> None:
        """Features は frozen（変更不可）."""
        features = Features(
            meta=FeaturesMeta(
                date="2025-12-25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=0,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=0.0,
            ),
        )

        with pytest.raises(ValidationError):
            features.meta = FeaturesMeta(  # type: ignore[misc]
                date="2025-12-26",
                generated_at="2025-12-26T18:00:00+09:00",
                capture_count=0,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=0.0,
            )


class TestFeaturesProperties:
    """Features のプロパティテスト."""

    def test_has_data_with_captures(self) -> None:
        """キャプチャがある場合 has_data は True."""
        features = Features(
            meta=FeaturesMeta(
                date="2025-12-25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=100,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=480.0,
            ),
            app_summary=[
                AppSummary(
                    name="Chrome",
                    process="chrome.exe",
                    count=50,
                    duration_min=100.0,
                    rank=AppRank.HIGH,
                ),
            ],
        )

        assert features.has_data is True

    def test_has_data_without_captures(self) -> None:
        """キャプチャがない場合 has_data は False."""
        features = Features(
            meta=FeaturesMeta(
                date="2025-12-25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=0,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=0.0,
            ),
        )

        assert features.has_data is False

    def test_top_app_property(self) -> None:
        """top_app は最も使用時間が長いアプリを返す."""
        features = Features(
            meta=FeaturesMeta(
                date="2025-12-25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=100,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=480.0,
            ),
            app_summary=[
                AppSummary(
                    name="App1",
                    process="app1.exe",
                    count=10,
                    duration_min=50.0,
                    rank=AppRank.LOW,
                ),
                AppSummary(
                    name="App2",
                    process="app2.exe",
                    count=20,
                    duration_min=150.0,
                    rank=AppRank.HIGH,
                ),
            ],
        )

        assert features.top_app is not None
        assert features.top_app.name == "App2"

    def test_top_app_none_when_empty(self) -> None:
        """アプリがない場合 top_app は None."""
        features = Features(
            meta=FeaturesMeta(
                date="2025-12-25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=0,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=0.0,
            ),
        )

        assert features.top_app is None

    def test_active_hours_property(self) -> None:
        """active_hours が正しく計算される."""
        features = Features(
            meta=FeaturesMeta(
                date="2025-12-25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=100,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=480.0,
            ),
        )

        assert features.active_hours == 8.0


class TestFeaturesMethods:
    """Features のメソッドテスト."""

    def test_get_apps_by_rank_high(self) -> None:
        """HIGH ランクのアプリをフィルタリング."""
        features = Features(
            meta=FeaturesMeta(
                date="2025-12-25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=100,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=480.0,
            ),
            app_summary=[
                AppSummary(
                    name="App1",
                    process="app1.exe",
                    count=10,
                    duration_min=150.0,
                    rank=AppRank.HIGH,
                ),
                AppSummary(
                    name="App2",
                    process="app2.exe",
                    count=20,
                    duration_min=100.0,
                    rank=AppRank.MEDIUM,
                ),
                AppSummary(
                    name="App3",
                    process="app3.exe",
                    count=15,
                    duration_min=50.0,
                    rank=AppRank.LOW,
                ),
            ],
        )

        high_apps = features.get_apps_by_rank(AppRank.HIGH)

        assert len(high_apps) == 1
        assert high_apps[0].name == "App1"

    def test_str_representation(self) -> None:
        """__str__ が読みやすい形式を返す."""
        features = Features(
            meta=FeaturesMeta(
                date="2025-12-25",
                generated_at="2025-12-25T18:00:00+09:00",
                capture_count=100,
                first_capture="09:00:00",
                last_capture="18:00:00",
                total_duration_min=480.0,
            ),
            app_summary=[
                AppSummary(
                    name="Chrome",
                    process="chrome.exe",
                    count=50,
                    duration_min=100.0,
                    rank=AppRank.HIGH,
                ),
            ],
        )

        result = str(features)

        assert "2025-12-25" in result
        assert "100 captures" in result
        assert "1 apps" in result
