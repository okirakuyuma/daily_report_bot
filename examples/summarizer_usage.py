#!/usr/bin/env python3
"""Summarizer Service 使用例

LLM要約サービスの基本的な使用方法を示すサンプルコード。
"""

from src.domain.features import (
    AppRank,
    AppSummary,
    AppUsage,
    Features,
    FeaturesMeta,
    GlobalKeywords,
    TimeBlock,
)
from src.services.summarizer import SummarizerService


def create_sample_features() -> Features:
    """サンプル Features データを生成"""
    return Features(
        meta=FeaturesMeta(
            date="2025-12-25",
            generated_at="2025-12-25T18:00:00+09:00",
            capture_count=240,
            first_capture="09:00:00",
            last_capture="18:00:00",
            total_duration_min=480.0,
        ),
        time_blocks=[
            TimeBlock(
                start="09:00",
                end="10:00",
                apps=[
                    AppUsage(name="VSCode", percent=70.0),
                    AppUsage(name="Chrome", percent=20.0),
                ],
                top_keywords=["Python", "Flask", "API"],
                top_files=["main.py", "routes.py"],
            ),
            TimeBlock(
                start="14:00",
                end="15:00",
                apps=[
                    AppUsage(name="Chrome", percent=60.0),
                    AppUsage(name="Slack", percent=30.0),
                ],
                top_keywords=["documentation", "stackoverflow"],
                top_files=[],
            ),
        ],
        app_summary=[
            AppSummary(
                name="VSCode",
                process="code.exe",
                count=200,
                duration_min=320.0,
                rank=AppRank.HIGH,
                top_keywords=["Python", "Flask", "development"],
            ),
            AppSummary(
                name="Chrome",
                process="chrome.exe",
                count=150,
                duration_min=120.0,
                rank=AppRank.HIGH,
                top_keywords=["documentation", "stackoverflow"],
            ),
            AppSummary(
                name="Slack",
                process="slack.exe",
                count=50,
                duration_min=40.0,
                rank=AppRank.MEDIUM,
                top_keywords=["team", "communication"],
            ),
        ],
        global_keywords=GlobalKeywords(
            top_keywords=["Python", "Flask", "API", "開発", "テスト"],
            top_urls=["github.com", "stackoverflow.com", "python.org"],
            top_files=["main.py", "routes.py", "models.py", "test_app.py"],
        ),
    )


def main() -> None:
    """メイン処理"""
    print("=" * 60)
    print("Summarizer Service 使用例")
    print("=" * 60)

    # サンプルデータ生成
    features = create_sample_features()
    print(f"\n対象日付: {features.meta.date}")
    print(f"キャプチャ数: {features.meta.capture_count}回")
    print(f"総作業時間: {features.meta.total_duration_min}分")

    # SummarizerService インスタンス生成（GeminiClient なし）
    print("\n[1] GeminiClient なしでフォールバックレポート生成")
    service = SummarizerService(gemini_client=None)
    report = service.generate_report(features)

    print(f"  LLM成功: {report.meta.llm_success}")
    print(f"  エラー: {report.meta.llm_error}")
    print(f"  メイン作業数: {len(report.main_tasks)}件")
    print(f"  知見数: {len(report.insights)}件")
    print(f"  アプリ使用状況: {len(report.app_usage)}件")
    print(f"  ファイル数: {len(report.files)}件")

    # モック GeminiClient を使った例
    print("\n[2] モック GeminiClient で成功パターン")

    from src.domain.report import Insight, LLMSummary, MainTask

    class MockGeminiClient:
        """テスト用モック"""

        model_name = "gemini-2.5-flash"

        def generate_summary(self, prompt: str) -> LLMSummary:
            """モックサマリーを返す"""
            return LLMSummary(
                main_tasks=[
                    MainTask(
                        title="Flask API開発",
                        description="認証エンドポイントを3つ実装し、ユニットテストを作成した",
                    ),
                    MainTask(
                        title="技術調査",
                        description=(
                            "Stack OverflowでFlask-JWTの実装例を調査し、"
                            "公式ドキュメントで設定方法を確認した"
                        ),
                    ),
                    MainTask(
                        title="コードレビュー対応",
                        description="Slackでのレビューコメントに対応し、修正をコミットした",
                    ),
                ],
                insights=[
                    Insight(
                        category="技術",
                        content=(
                            "Flask-JWTのトークン有効期限はデフォルトで15分なので、"
                            "本番環境では明示的に設定が必要"
                        ),
                    ),
                    Insight(
                        category="プロセス",
                        content="認証周りは早めにレビュー依頼すると手戻りが減る",
                    ),
                ],
                work_summary="本日はFlask APIの認証機能実装に注力し、基本的なエンドポイントを完成させた。",
            )

    service_with_client = SummarizerService(gemini_client=MockGeminiClient())
    report_success = service_with_client.generate_report(features)

    print(f"  LLM成功: {report_success.meta.llm_success}")
    print(f"  使用モデル: {report_success.meta.llm_model}")
    print(f"\n  作業サマリー: {report_success.work_summary}")
    print(f"\n  メイン作業:")
    for i, task in enumerate(report_success.main_tasks, 1):
        print(f"    {i}. {task.title}")
        print(f"       {task.description}")
    print(f"\n  知見:")
    for insight in report_success.insights:
        print(f"    [{insight.category}] {insight.content}")

    print("\n" + "=" * 60)
    print("完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
