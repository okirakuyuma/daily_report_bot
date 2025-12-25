"""Summarizer Service のテスト

LLM要約サービスの動作を検証。
"""

import pytest

from src.domain.features import (
    AppRank,
    AppSummary,
    AppUsage,
    Features,
    FeaturesMeta,
    GlobalKeywords,
    TimeBlock,
)
from src.domain.report import LLMSummary, MainTask, Report
from src.services.summarizer import (
    SummarizerService,
    _build_user_prompt,
    _convert_features_to_app_usage,
)


@pytest.fixture
def sample_features() -> Features:
    """テスト用 Features データ"""
    return Features(
        meta=FeaturesMeta(
            date="2025-12-25",
            generated_at="2025-12-25T18:00:00+09:00",
            capture_count=120,
            first_capture="09:00:00",
            last_capture="18:00:00",
            total_duration_min=480.0,
        ),
        time_blocks=[
            TimeBlock(
                start="09:00",
                end="10:00",
                apps=[
                    AppUsage(name="VSCode", percent=60.0),
                    AppUsage(name="Chrome", percent=30.0),
                ],
                top_keywords=["Python", "Flask"],
                top_files=["main.py"],
            ),
            TimeBlock(
                start="14:00",
                end="15:00",
                apps=[
                    AppUsage(name="Slack", percent=50.0),
                ],
                top_keywords=["meeting"],
                top_files=[],
            ),
        ],
        app_summary=[
            AppSummary(
                name="VSCode",
                process="code.exe",
                count=120,
                duration_min=240.0,
                rank=AppRank.HIGH,
                top_keywords=["Python", "development"],
            ),
            AppSummary(
                name="Chrome",
                process="chrome.exe",
                count=80,
                duration_min=160.0,
                rank=AppRank.HIGH,
                top_keywords=["documentation"],
            ),
            AppSummary(
                name="Slack",
                process="slack.exe",
                count=40,
                duration_min=80.0,
                rank=AppRank.MEDIUM,
                top_keywords=["communication"],
            ),
        ],
        global_keywords=GlobalKeywords(
            top_keywords=["Python", "Flask", "API", "テスト", "開発"],
            top_urls=["github.com", "stackoverflow.com"],
            top_files=["main.py", "test_app.py"],
        ),
    )


class TestBuildUserPrompt:
    """ユーザープロンプト構築のテスト"""

    def test_prompt_contains_basic_info(self, sample_features: Features):
        """基本情報が含まれているか"""
        prompt = _build_user_prompt(sample_features)

        assert "2025-12-25" in prompt
        assert "09:00:00" in prompt
        assert "18:00:00" in prompt
        assert "120回" in prompt
        assert "480.0分" in prompt

    def test_prompt_contains_time_blocks(self, sample_features: Features):
        """時間帯別作業が含まれているか"""
        prompt = _build_user_prompt(sample_features)

        assert "09:00〜10:00" in prompt
        assert "VSCode" in prompt
        assert "Chrome" in prompt

    def test_prompt_contains_app_usage(self, sample_features: Features):
        """アプリ使用状況が含まれているか"""
        prompt = _build_user_prompt(sample_features)

        assert "VSCode: 240.0分 (high)" in prompt
        assert "Chrome: 160.0分 (high)" in prompt

    def test_prompt_contains_keywords(self, sample_features: Features):
        """キーワードが含まれているか"""
        prompt = _build_user_prompt(sample_features)

        assert "Python" in prompt
        assert "Flask" in prompt
        assert "API" in prompt

    def test_prompt_with_empty_data(self):
        """データが空の場合"""
        empty_features = Features(
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
            global_keywords=GlobalKeywords(
                top_keywords=[],
                top_urls=[],
                top_files=[],
            ),
        )

        prompt = _build_user_prompt(empty_features)

        assert "（データなし）" in prompt


class TestConvertFeaturesToAppUsage:
    """Features から AppUsage 変換のテスト"""

    def test_conversion(self, sample_features: Features):
        """正しく変換されるか"""
        app_usage_list = _convert_features_to_app_usage(sample_features)

        assert len(app_usage_list) == 3
        assert app_usage_list[0].name == "VSCode"
        assert app_usage_list[0].duration_min == 240
        assert app_usage_list[0].rank == "high"
        assert app_usage_list[0].purpose is None

    def test_duration_conversion_to_int(self, sample_features: Features):
        """duration_min が int に変換されるか"""
        app_usage_list = _convert_features_to_app_usage(sample_features)

        for app in app_usage_list:
            assert isinstance(app.duration_min, int)


class TestSummarizerService:
    """SummarizerService のテスト"""

    def test_init_without_client(self):
        """GeminiClient なしで初期化できるか"""
        service = SummarizerService(gemini_client=None)
        assert service.gemini_client is None

    def test_generate_fallback_report(self, sample_features: Features):
        """フォールバックレポートが生成されるか"""
        service = SummarizerService(gemini_client=None)
        report = service.generate_report(sample_features)

        # メタデータ検証
        assert report.meta.date == "2025-12-25"
        assert report.meta.llm_success is False
        assert report.meta.llm_error is not None

        # フォールバックコンテンツ検証
        assert len(report.main_tasks) == 1
        assert "自動要約できませんでした" in report.main_tasks[0].description
        assert len(report.insights) == 0
        assert report.work_summary == "（自動要約に失敗しました）"

        # ルールベース処理結果が含まれているか
        assert len(report.app_usage) == 3
        assert len(report.files) == 2

    def test_generate_report_with_mock_client(self, sample_features: Features):
        """モック LLM クライアントで成功するか"""

        class MockGeminiClient:
            """テスト用モック GeminiClient"""

            model_name = "gemini-2.5-flash-test"

            def generate_summary(self, prompt: str) -> LLMSummary:
                """テスト用サマリーを返す"""
                return LLMSummary(
                    main_tasks=[
                        MainTask(
                            title="Python開発",
                            description="Flask APIの実装を行った",
                        )
                    ],
                    insights=[],
                    work_summary="本日はFlask API開発に注力した。",
                )

        service = SummarizerService(gemini_client=MockGeminiClient())
        report = service.generate_report(sample_features)

        # 成功検証
        assert report.meta.llm_success is True
        assert report.meta.llm_error is None
        assert report.meta.llm_model == "gemini-2.5-flash-test"

        # LLM生成コンテンツ検証
        assert len(report.main_tasks) == 1
        assert report.main_tasks[0].title == "Python開発"
        assert report.work_summary == "本日はFlask API開発に注力した。"

        # ルールベース処理結果も含まれているか
        assert len(report.app_usage) == 3
        assert len(report.files) == 2
