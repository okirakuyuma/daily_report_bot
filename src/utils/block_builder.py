"""Block Builder - Notion APIブロック生成ヘルパー

日報データからNotion APIのブロック構造を生成するユーティリティ。
"""

from __future__ import annotations

from typing import Any

from ..domain.report import AppUsage, Insight, MainTask, Report


def heading_2(text: str) -> dict[str, Any]:
    """見出し2ブロックを生成

    Args:
        text: 見出しテキスト

    Returns:
        Notion APIのheading_2ブロック

    Examples:
        >>> heading_2("📊 基本情報")
        {'type': 'heading_2', 'heading_2': {'rich_text': [...]}}
    """
    return {
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def paragraph(text: str) -> dict[str, Any]:
    """段落ブロックを生成

    Args:
        text: 段落テキスト（改行含む可）

    Returns:
        Notion APIのparagraphブロック

    Examples:
        >>> paragraph("記録期間: 09:00 〜 18:00\\nキャプチャ数: 240回")
        {'type': 'paragraph', 'paragraph': {'rich_text': [...]}}
    """
    return {
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def numbered_list_item(text: str) -> dict[str, Any]:
    """番号付きリストアイテムを生成

    Args:
        text: リストアイテムテキスト

    Returns:
        Notion APIのnumbered_list_itemブロック

    Examples:
        >>> numbered_list_item("データ集計処理を実装")
        {'type': 'numbered_list_item', 'numbered_list_item': {'rich_text': [...]}}
    """
    return {
        "type": "numbered_list_item",
        "numbered_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        },
    }


def bulleted_list_item(text: str) -> dict[str, Any]:
    """箇条書きリストアイテムを生成

    Args:
        text: リストアイテムテキスト

    Returns:
        Notion APIのbulleted_list_itemブロック

    Examples:
        >>> bulleted_list_item("[技術] Pydanticの型検証が便利")
        {'type': 'bulleted_list_item', 'bulleted_list_item': {'rich_text': [...]}}
    """
    return {
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text}}]
        },
    }


def divider() -> dict[str, Any]:
    """区切り線ブロックを生成

    Returns:
        Notion APIのdividerブロック

    Examples:
        >>> divider()
        {'type': 'divider', 'divider': {}}
    """
    return {"type": "divider", "divider": {}}


def rank_to_emoji(rank: str) -> str:
    """使用頻度ランクを絵文字表記に変換

    Args:
        rank: ランク値 ("high", "medium", "low")

    Returns:
        絵文字付きランク表記

    Examples:
        >>> rank_to_emoji("high")
        '🔴 多'
        >>> rank_to_emoji("medium")
        '🟡 中'
        >>> rank_to_emoji("low")
        '🟢 少'
        >>> rank_to_emoji("unknown")
        '-'
    """
    return {"high": "🔴 多", "medium": "🟡 中", "low": "🟢 少"}.get(rank, "-")


def build_app_table(app_usage: list[AppUsage]) -> dict[str, Any]:
    """アプリ使用状況テーブルを生成

    Args:
        app_usage: アプリ使用状況リスト

    Returns:
        Notion APIのtableブロック

    Examples:
        >>> app = AppUsage(name="VS Code", duration_min=120, rank="high", purpose="開発")
        >>> table = build_app_table([app])
        >>> table["type"]
        'table'
        >>> table["table"]["table_width"]
        4
    """
    rows = []

    # ヘッダー行
    rows.append(
        {
            "type": "table_row",
            "table_row": {
                "cells": [
                    [{"type": "text", "text": {"content": "アプリ"}}],
                    [{"type": "text", "text": {"content": "時間"}}],
                    [{"type": "text", "text": {"content": "頻度"}}],
                    [{"type": "text", "text": {"content": "主な用途"}}],
                ]
            },
        }
    )

    # データ行
    for app in app_usage:
        rows.append(
            {
                "type": "table_row",
                "table_row": {
                    "cells": [
                        [{"type": "text", "text": {"content": app.name}}],
                        [
                            {
                                "type": "text",
                                "text": {"content": f"{app.duration_min}分"},
                            }
                        ],
                        [
                            {
                                "type": "text",
                                "text": {"content": rank_to_emoji(app.rank)},
                            }
                        ],
                        [
                            {
                                "type": "text",
                                "text": {"content": app.purpose or "-"},
                            }
                        ],
                    ]
                },
            }
        )

    return {
        "type": "table",
        "table": {
            "table_width": 4,
            "has_column_header": True,
            "has_row_header": False,
            "children": rows,
        },
    }


def build_report_blocks_from_report(report: Report) -> list[dict[str, Any]]:
    """Reportエンティティから本文ブロックを生成

    Args:
        report: 日報レポートエンティティ

    Returns:
        Notion APIブロックのリスト

    Examples:
        >>> from domain.report import Report, ReportMeta
        >>> report = Report(
        ...     meta=ReportMeta(date="2025-01-15"),
        ...     main_tasks=[],
        ...     insights=[],
        ...     work_summary="",
        ...     app_usage=[],
        ...     files=[]
        ... )
        >>> blocks = build_report_blocks_from_report(report)
        >>> len(blocks) > 0
        True
    """
    blocks: list[dict[str, Any]] = []

    # 📊 基本情報
    blocks.append(heading_2("📊 基本情報"))
    basic_info_lines = [
        f"作業サマリー: {report.work_summary or '（データなし）'}",
        f"生成日時: {report.meta.generated_at.strftime('%Y-%m-%d %H:%M')}",
    ]

    # LLMエラーの場合は表示
    if not report.meta.llm_success and report.meta.llm_error:
        basic_info_lines.append(f"⚠️ LLM要約失敗: {report.meta.llm_error}")

    blocks.append(paragraph("\n".join(basic_info_lines)))

    # 🎯 本日のメイン作業
    blocks.append(heading_2("🎯 本日のメイン作業"))
    if report.main_tasks:
        for task in report.main_tasks:
            blocks.append(numbered_list_item(task.title))
            if task.description:
                blocks.append(paragraph(task.description))
    else:
        blocks.append(paragraph("（メイン作業が記録されていません）"))

    # 💡 知見・メモ
    blocks.append(heading_2("💡 知見・メモ"))
    if report.insights:
        for insight in report.insights:
            blocks.append(
                bulleted_list_item(f"[{insight.category}] {insight.content}")
            )
    else:
        blocks.append(paragraph("（知見が記録されていません）"))

    # 📱 アプリ使用状況
    blocks.append(heading_2("📱 アプリ使用状況"))
    if report.app_usage:
        blocks.append(build_app_table(report.app_usage))
    else:
        blocks.append(paragraph("（アプリ使用状況が記録されていません）"))

    # 📁 作業ファイル
    blocks.append(heading_2("📁 作業ファイル"))
    if report.files:
        for file in report.files:
            blocks.append(bulleted_list_item(file))
    else:
        blocks.append(paragraph("（作業ファイルが検出されていません）"))

    # フッター
    blocks.append(divider())
    blocks.append(paragraph("🤖 Generated by Daily Report Bot"))

    return blocks


def build_report_blocks_from_dict(report: dict[str, Any]) -> list[dict[str, Any]]:
    """辞書形式のレポートから本文ブロックを生成

    Args:
        report: 日報レポート辞書

    Returns:
        Notion APIブロックのリスト

    Examples:
        >>> report = {
        ...     "meta": {"date": "2025-01-15", "generated_at": "2025-01-15T18:00:00"},
        ...     "main_tasks": [],
        ...     "insights": [],
        ...     "work_summary": "テスト作業",
        ...     "app_usage": [],
        ...     "files": []
        ... }
        >>> blocks = build_report_blocks_from_dict(report)
        >>> len(blocks) > 0
        True
    """
    blocks: list[dict[str, Any]] = []

    meta = report.get("meta", {})
    main_tasks = report.get("main_tasks", [])
    insights = report.get("insights", [])
    work_summary = report.get("work_summary", "")
    app_usage = report.get("app_usage", [])
    files = report.get("files", [])

    # 📊 基本情報
    blocks.append(heading_2("📊 基本情報"))
    basic_info_lines = [
        f"作業サマリー: {work_summary or '（データなし）'}",
        f"生成日時: {meta.get('generated_at', '不明')}",
    ]

    # LLMエラーの場合は表示
    if not meta.get("llm_success", True) and meta.get("llm_error"):
        basic_info_lines.append(f"⚠️ LLM要約失敗: {meta['llm_error']}")

    blocks.append(paragraph("\n".join(basic_info_lines)))

    # 🎯 本日のメイン作業
    blocks.append(heading_2("🎯 本日のメイン作業"))
    if main_tasks:
        for task in main_tasks:
            title = task.get("title", "タイトルなし")
            description = task.get("description", "")
            blocks.append(numbered_list_item(title))
            if description:
                blocks.append(paragraph(description))
    else:
        blocks.append(paragraph("（メイン作業が記録されていません）"))

    # 💡 知見・メモ
    blocks.append(heading_2("💡 知見・メモ"))
    if insights:
        for insight in insights:
            category = insight.get("category", "その他")
            content = insight.get("content", "")
            blocks.append(bulleted_list_item(f"[{category}] {content}"))
    else:
        blocks.append(paragraph("（知見が記録されていません）"))

    # 📱 アプリ使用状況
    blocks.append(heading_2("📱 アプリ使用状況"))
    if app_usage:
        # 辞書形式をAppUsageに変換
        app_usage_objects = [
            AppUsage(
                name=app.get("name", "不明"),
                duration_min=app.get("duration_min", 0),
                rank=app.get("rank", "low"),
                purpose=app.get("purpose"),
            )
            for app in app_usage
        ]
        blocks.append(build_app_table(app_usage_objects))
    else:
        blocks.append(paragraph("（アプリ使用状況が記録されていません）"))

    # 📁 作業ファイル
    blocks.append(heading_2("📁 作業ファイル"))
    if files:
        for file in files:
            blocks.append(bulleted_list_item(file))
    else:
        blocks.append(paragraph("（作業ファイルが検出されていません）"))

    # フッター
    blocks.append(divider())
    blocks.append(paragraph("🤖 Generated by Daily Report Bot"))

    return blocks


def build_report_blocks(
    report: Report | dict[str, Any]
) -> list[dict[str, Any]]:
    """日報レポートから本文ブロックを生成（統合インターフェース）

    Reportエンティティまたは辞書形式のどちらでも受け付ける。

    Args:
        report: 日報レポート（Reportエンティティまたは辞書）

    Returns:
        Notion APIブロックのリスト

    Examples:
        >>> from domain.report import Report, ReportMeta
        >>> report = Report(
        ...     meta=ReportMeta(date="2025-01-15"),
        ...     main_tasks=[],
        ...     insights=[],
        ...     work_summary="作業完了",
        ...     app_usage=[],
        ...     files=[]
        ... )
        >>> blocks = build_report_blocks(report)
        >>> len(blocks) > 0
        True
    """
    if isinstance(report, Report):
        return build_report_blocks_from_report(report)
    else:
        return build_report_blocks_from_dict(report)
