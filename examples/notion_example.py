"""Notion Gateway使用例

このスクリプトは、NotionGatewayの基本的な使用方法を示します。
実行前に環境変数NOTION_TOKENとNOTION_DATABASE_IDを設定してください。
"""

from __future__ import annotations

import os
from datetime import datetime

from src.domain.report import AppUsage, Insight, MainTask, Report, ReportMeta
from src.gateways.notion import publish_report


def create_sample_report() -> Report:
    """サンプルレポートを作成

    Returns:
        サンプルの日報レポート
    """
    meta = ReportMeta(
        date="2025-01-15",
        generated_at=datetime.now(),
        llm_model="gemini-2.5-flash",
        llm_success=True,
    )

    main_tasks = [
        MainTask(
            title="Flask APIエンドポイントの実装",
            description="ユーザー認証用のREST APIを3エンドポイント実装した",
        ),
        MainTask(
            title="ドキュメント調査・レビュー",
            description="Stack OverflowとPython公式ドキュメントでFlaskの認証パターンを調査した",
        ),
        MainTask(
            title="コードレビュー対応",
            description="チームからのレビューコメントに対応し、修正を実施した",
        ),
    ]

    insights = [
        Insight(
            category="技術",
            content="Flask-JWTの設定でトークン有効期限のデフォルト値に注意が必要",
        ),
        Insight(
            category="プロセス",
            content="認証周りは早めにレビュー依頼すると手戻りが減る",
        ),
    ]

    app_usage = [
        AppUsage(
            name="Visual Studio Code",
            duration_min=240,
            rank="high",
            purpose="Python/Flask開発",
        ),
        AppUsage(
            name="Google Chrome",
            duration_min=160,
            rank="high",
            purpose="ドキュメント調査",
        ),
        AppUsage(
            name="Slack",
            duration_min=80,
            rank="medium",
            purpose="コードレビュー対応",
        ),
    ]

    files = [
        "main.py",
        "routes.py",
        "models.py",
        "auth.py",
        "tests/test_auth.py",
    ]

    return Report(
        meta=meta,
        main_tasks=main_tasks,
        insights=insights,
        work_summary="本日はFlask APIの認証機能実装に注力し、基本的なエンドポイントを完成させた。",
        app_usage=app_usage,
        files=files,
    )


def main() -> None:
    """メイン処理"""
    # 環境変数チェック
    if not os.environ.get("NOTION_TOKEN"):
        print("Error: NOTION_TOKEN environment variable is not set")
        print("Please set: export NOTION_TOKEN='secret_xxxxx'")
        return

    if not os.environ.get("NOTION_DATABASE_ID"):
        print("Error: NOTION_DATABASE_ID environment variable is not set")
        print("Please set: export NOTION_DATABASE_ID='xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'")
        return

    # サンプルレポート作成
    print("Creating sample report...")
    report = create_sample_report()

    # Notion出力
    print(f"Publishing report for {report.meta.date}...")
    try:
        page_id, page_url = publish_report(
            report=report,
            capture_count=240,
            total_duration_min=478,
        )
        print(f"✅ Success!")
        print(f"Page ID: {page_id}")
        print(f"Page URL: {page_url}")

    except Exception as e:
        print(f"❌ Failed to publish report: {e}")
        raise


if __name__ == "__main__":
    main()
