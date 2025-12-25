"""Notion Gateway - Notion API連携

日報データをNotionデータベースに出力。
ページの作成・更新、ブロック生成、リトライ処理を含む。
"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime
from typing import Any

from notion_client import Client
from notion_client.errors import APIResponseError

from src.domain.report import Report

logger = logging.getLogger(__name__)


class NotionGateway:
    """Notion API連携ゲートウェイ

    Attributes:
        token: Notion Integration Token
        database_id: 日報データベースID
        retry_count: リトライ回数
        retry_delay_sec: リトライ間隔秒数
    """

    def __init__(
        self,
        token: str | None = None,
        database_id: str | None = None,
        retry_count: int = 3,
        retry_delay_sec: int = 5,
    ):
        """初期化

        Args:
            token: Notion Integration Token（Noneの場合は環境変数から取得）
            database_id: データベースID（Noneの場合は環境変数から取得）
            retry_count: リトライ回数
            retry_delay_sec: リトライ間隔秒数

        Raises:
            ValueError: トークンまたはデータベースIDが設定されていない場合
        """
        self.token = token or os.environ.get("NOTION_TOKEN")
        if not self.token:
            raise ValueError("NOTION_TOKEN environment variable is required")

        self.database_id = database_id or os.environ.get("NOTION_DATABASE_ID")
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID environment variable is required")

        self.retry_count = retry_count
        self.retry_delay_sec = retry_delay_sec
        self.client = Client(auth=self.token)

    def query_page_by_date(self, date: str) -> dict[str, Any] | None:
        """指定日付のページを検索

        Args:
            date: 検索対象日付 (YYYY-MM-DD)

        Returns:
            ページデータ（存在しない場合はNone）

        Raises:
            Exception: API呼び出しが全てのリトライで失敗した場合
        """
        last_error = None
        for attempt in range(self.retry_count + 1):
            try:
                response = self.client.databases.query(
                    database_id=self.database_id,
                    filter={"property": "日付", "date": {"equals": date}},
                )

                if response["results"]:
                    logger.info(f"Found existing page for date: {date}")
                    return response["results"][0]

                logger.info(f"No existing page found for date: {date}")
                return None

            except APIResponseError as e:
                last_error = e
                # レート制限の場合は60秒待機
                if e.status == 429:
                    logger.warning(f"Rate limited, waiting 60 seconds...")
                    time.sleep(60)
                    continue
                # その他のエラーは通常のリトライ
                if attempt < self.retry_count:
                    logger.warning(
                        f"Query failed (attempt {attempt + 1}/{self.retry_count + 1}): {e}"
                    )
                    time.sleep(self.retry_delay_sec)
                    continue

            except Exception as e:
                last_error = e
                if attempt < self.retry_count:
                    logger.warning(
                        f"Query failed (attempt {attempt + 1}/{self.retry_count + 1}): {e}"
                    )
                    time.sleep(self.retry_delay_sec)
                    continue

        # 全リトライ失敗
        raise Exception(
            f"Notion query failed after {self.retry_count + 1} attempts: {last_error}"
        )

    def create_page(
        self, properties: dict[str, Any], children: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """新規ページ作成

        Args:
            properties: ページプロパティ
            children: ページ本文ブロック

        Returns:
            作成されたページデータ

        Raises:
            Exception: API呼び出しが全てのリトライで失敗した場合
        """
        last_error = None
        for attempt in range(self.retry_count + 1):
            try:
                response = self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties,
                    children=children,
                )
                logger.info(f"Created new page: {response['id']}")
                return response

            except APIResponseError as e:
                last_error = e
                # レート制限の場合は60秒待機
                if e.status == 429:
                    logger.warning(f"Rate limited, waiting 60 seconds...")
                    time.sleep(60)
                    continue
                # その他のエラーは通常のリトライ
                if attempt < self.retry_count:
                    logger.warning(
                        f"Create failed (attempt {attempt + 1}/{self.retry_count + 1}): {e}"
                    )
                    time.sleep(self.retry_delay_sec)
                    continue

            except Exception as e:
                last_error = e
                if attempt < self.retry_count:
                    logger.warning(
                        f"Create failed (attempt {attempt + 1}/{self.retry_count + 1}): {e}"
                    )
                    time.sleep(self.retry_delay_sec)
                    continue

        # 全リトライ失敗
        raise Exception(
            f"Notion create failed after {self.retry_count + 1} attempts: {last_error}"
        )

    def update_page(
        self, page_id: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """ページプロパティ更新

        Args:
            page_id: ページID
            properties: 更新するプロパティ

        Returns:
            更新されたページデータ

        Raises:
            Exception: API呼び出しが全てのリトライで失敗した場合
        """
        last_error = None
        for attempt in range(self.retry_count + 1):
            try:
                response = self.client.pages.update(
                    page_id=page_id, properties=properties
                )
                logger.info(f"Updated page properties: {page_id}")
                return response

            except APIResponseError as e:
                last_error = e
                # レート制限の場合は60秒待機
                if e.status == 429:
                    logger.warning(f"Rate limited, waiting 60 seconds...")
                    time.sleep(60)
                    continue
                # その他のエラーは通常のリトライ
                if attempt < self.retry_count:
                    logger.warning(
                        f"Update failed (attempt {attempt + 1}/{self.retry_count + 1}): {e}"
                    )
                    time.sleep(self.retry_delay_sec)
                    continue

            except Exception as e:
                last_error = e
                if attempt < self.retry_count:
                    logger.warning(
                        f"Update failed (attempt {attempt + 1}/{self.retry_count + 1}): {e}"
                    )
                    time.sleep(self.retry_delay_sec)
                    continue

        # 全リトライ失敗
        raise Exception(
            f"Notion update failed after {self.retry_count + 1} attempts: {last_error}"
        )

    def replace_blocks(
        self, page_id: str, blocks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """ページのブロックを置換

        既存ブロックを削除してから新規ブロックを追加する。

        Args:
            page_id: ページID
            blocks: 新規ブロックリスト

        Returns:
            追加されたブロックリスト

        Raises:
            Exception: API呼び出しが全てのリトライで失敗した場合
        """
        # 1. 既存ブロック取得
        last_error = None
        for attempt in range(self.retry_count + 1):
            try:
                existing_blocks = self.client.blocks.children.list(block_id=page_id)
                break
            except Exception as e:
                last_error = e
                if attempt < self.retry_count:
                    logger.warning(
                        f"List blocks failed (attempt {attempt + 1}/{self.retry_count + 1}): {e}"
                    )
                    time.sleep(self.retry_delay_sec)
                    continue
                raise Exception(
                    f"Failed to list blocks after {self.retry_count + 1} attempts: {last_error}"
                )

        # 2. 既存ブロック削除
        for block in existing_blocks["results"]:
            for attempt in range(self.retry_count + 1):
                try:
                    self.client.blocks.delete(block_id=block["id"])
                    break
                except Exception as e:
                    last_error = e
                    if attempt < self.retry_count:
                        logger.warning(
                            f"Delete block failed (attempt {attempt + 1}/{self.retry_count + 1}): {e}"
                        )
                        time.sleep(self.retry_delay_sec)
                        continue
                    logger.error(f"Failed to delete block {block['id']}: {e}")
                    # 削除失敗は継続（次のブロックを試す）
                    break

        logger.info(f"Deleted {len(existing_blocks['results'])} existing blocks")

        # 3. 新規ブロック追加
        for attempt in range(self.retry_count + 1):
            try:
                response = self.client.blocks.children.append(
                    block_id=page_id, children=blocks
                )
                logger.info(f"Appended {len(blocks)} new blocks")
                return response["results"]

            except APIResponseError as e:
                last_error = e
                # レート制限の場合は60秒待機
                if e.status == 429:
                    logger.warning(f"Rate limited, waiting 60 seconds...")
                    time.sleep(60)
                    continue
                # その他のエラーは通常のリトライ
                if attempt < self.retry_count:
                    logger.warning(
                        f"Append blocks failed (attempt {attempt + 1}/{self.retry_count + 1}): {e}"
                    )
                    time.sleep(self.retry_delay_sec)
                    continue

            except Exception as e:
                last_error = e
                if attempt < self.retry_count:
                    logger.warning(
                        f"Append blocks failed (attempt {attempt + 1}/{self.retry_count + 1}): {e}"
                    )
                    time.sleep(self.retry_delay_sec)
                    continue

        # 全リトライ失敗
        raise Exception(
            f"Failed to append blocks after {self.retry_count + 1} attempts: {last_error}"
        )


# ブロック生成ヘルパー関数


def heading_2(text: str) -> dict[str, Any]:
    """見出し2ブロックを生成

    Args:
        text: 見出しテキスト

    Returns:
        見出し2ブロック
    """
    return {
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def paragraph(text: str) -> dict[str, Any]:
    """段落ブロックを生成

    Args:
        text: 段落テキスト

    Returns:
        段落ブロック
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
        番号付きリストアイテムブロック
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
        箇条書きリストアイテムブロック
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
        区切り線ブロック
    """
    return {"type": "divider", "divider": {}}


def build_app_table(app_usage: list[dict[str, Any]]) -> dict[str, Any]:
    """アプリ使用状況テーブルを生成

    Args:
        app_usage: アプリ使用状況リスト

    Returns:
        テーブルブロック
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
                        [{"type": "text", "text": {"content": app["name"]}}],
                        [
                            {
                                "type": "text",
                                "text": {"content": f"{app['duration_min']}分"},
                            }
                        ],
                        [
                            {
                                "type": "text",
                                "text": {"content": _rank_to_emoji(app["rank"])},
                            }
                        ],
                        [
                            {
                                "type": "text",
                                "text": {"content": app.get("purpose", "-")},
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


def _rank_to_emoji(rank: str) -> str:
    """ランクを絵文字に変換

    Args:
        rank: ランク（high/medium/low）

    Returns:
        絵文字付きテキスト
    """
    return {"high": "🔴 多", "medium": "🟡 中", "low": "🟢 少"}.get(rank, "-")


def build_report_blocks(report: Report) -> list[dict[str, Any]]:
    """レポートから本文ブロックを生成

    Args:
        report: 日報レポート

    Returns:
        ブロックリスト
    """
    blocks: list[dict[str, Any]] = []

    # 基本情報（メタデータから）
    blocks.append(heading_2("📊 基本情報"))
    meta_text = (
        f"生成日時: {report.meta.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"LLMモデル: {report.meta.llm_model}\n"
        f"LLM成功: {'✅ はい' if report.meta.llm_success else '❌ いいえ'}"
    )
    if report.meta.llm_error:
        meta_text += f"\nエラー: {report.meta.llm_error}"
    blocks.append(paragraph(meta_text))

    # 作業サマリー
    blocks.append(heading_2("📝 作業サマリー"))
    blocks.append(paragraph(report.work_summary))

    # メイン作業
    blocks.append(heading_2("🎯 本日のメイン作業"))
    if report.main_tasks:
        for i, task in enumerate(report.main_tasks, 1):
            blocks.append(numbered_list_item(f"{task.title}"))
            blocks.append(paragraph(f"  {task.description}"))
    else:
        blocks.append(paragraph("（メイン作業なし）"))

    # 知見・メモ
    blocks.append(heading_2("💡 知見・メモ"))
    if report.insights:
        for insight in report.insights:
            blocks.append(bulleted_list_item(f"[{insight.category}] {insight.content}"))
    else:
        blocks.append(paragraph("（知見なし）"))

    # アプリ使用状況
    blocks.append(heading_2("📱 アプリ使用状況"))
    if report.app_usage:
        app_usage_dicts = [
            {
                "name": app.name,
                "duration_min": app.duration_min,
                "rank": app.rank,
                "purpose": app.purpose,
            }
            for app in report.app_usage
        ]
        blocks.append(build_app_table(app_usage_dicts))
    else:
        blocks.append(paragraph("（アプリ使用記録なし）"))

    # 作業ファイル
    blocks.append(heading_2("📁 作業ファイル"))
    if report.files:
        for file in report.files[:20]:  # 最大20件
            blocks.append(bulleted_list_item(file))
    else:
        blocks.append(paragraph("（ファイル記録なし）"))

    # フッター
    blocks.append(divider())
    blocks.append(paragraph("🤖 Generated by Daily Report Bot"))

    return blocks


def build_page_properties(
    report: Report, capture_count: int = 0, total_duration_min: int = 0
) -> dict[str, Any]:
    """レポートからページプロパティを生成

    Args:
        report: 日報レポート
        capture_count: キャプチャ数
        total_duration_min: 総作業時間（分）

    Returns:
        プロパティ辞書
    """
    # メイン作業のタイトルをタグとして抽出（最大3件）
    main_work_tags = [task.title for task in report.main_tasks[:3]]

    return {
        "名前": {"title": [{"text": {"content": f"{report.meta.date} 日報"}}]},
        "日付": {"date": {"start": report.meta.date}},
        "ステータス": {"select": {"name": "自動生成"}},
        "キャプチャ数": {"number": capture_count},
        "作業時間(分)": {"number": total_duration_min},
        "メイン作業": {
            "multi_select": [{"name": tag} for tag in main_work_tags if tag]
        },
        "生成日時": {
            "date": {
                "start": report.meta.generated_at.isoformat(),
            }
        },
    }


def publish_report(
    report: Report,
    capture_count: int = 0,
    total_duration_min: int = 0,
    token: str | None = None,
    database_id: str | None = None,
) -> tuple[str, str]:
    """日報をNotionに出力

    既存ページがある場合は更新、ない場合は新規作成。

    Args:
        report: 日報レポート
        capture_count: キャプチャ数
        total_duration_min: 総作業時間（分）
        token: Notion Integration Token（オプション）
        database_id: データベースID（オプション）

    Returns:
        (ページID, ページURL)

    Raises:
        Exception: Notion API呼び出しが失敗した場合
    """
    gateway = NotionGateway(token=token, database_id=database_id)

    # プロパティとブロック生成
    properties = build_page_properties(report, capture_count, total_duration_min)
    blocks = build_report_blocks(report)

    # 既存ページ検索
    existing_page = gateway.query_page_by_date(report.meta.date)

    if existing_page:
        # 既存ページ更新
        page_id = existing_page["id"]
        gateway.update_page(page_id, properties)
        gateway.replace_blocks(page_id, blocks)
        page_url = existing_page["url"]
        logger.info(f"Updated existing page: {page_url}")
    else:
        # 新規ページ作成
        created_page = gateway.create_page(properties, blocks)
        page_id = created_page["id"]
        page_url = created_page["url"]
        logger.info(f"Created new page: {page_url}")

    return page_id, page_url
