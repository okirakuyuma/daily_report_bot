"""Block Builder - ユニットテスト"""

import pytest

from src.domain.report import AppUsage, Insight, MainTask, Report, ReportMeta
from src.utils.block_builder import (
    build_app_table,
    build_report_blocks,
    build_report_blocks_from_dict,
    build_report_blocks_from_report,
    bulleted_list_item,
    divider,
    heading_2,
    numbered_list_item,
    paragraph,
    rank_to_emoji,
)


class TestBasicBlocks:
    """基本ブロック生成のテスト"""

    def test_heading_2(self):
        block = heading_2("テスト見出し")
        assert block["type"] == "heading_2"
        assert block["heading_2"]["rich_text"][0]["text"]["content"] == "テスト見出し"

    def test_paragraph(self):
        block = paragraph("テスト段落")
        assert block["type"] == "paragraph"
        assert block["paragraph"]["rich_text"][0]["text"]["content"] == "テスト段落"

    def test_paragraph_with_newlines(self):
        text = "行1\n行2\n行3"
        block = paragraph(text)
        assert block["paragraph"]["rich_text"][0]["text"]["content"] == text

    def test_numbered_list_item(self):
        block = numbered_list_item("番号付き項目")
        assert block["type"] == "numbered_list_item"
        assert (
            block["numbered_list_item"]["rich_text"][0]["text"]["content"]
            == "番号付き項目"
        )

    def test_bulleted_list_item(self):
        block = bulleted_list_item("箇条書き項目")
        assert block["type"] == "bulleted_list_item"
        assert (
            block["bulleted_list_item"]["rich_text"][0]["text"]["content"]
            == "箇条書き項目"
        )

    def test_divider(self):
        block = divider()
        assert block["type"] == "divider"
        assert block["divider"] == {}


class TestRankEmoji:
    """ランク絵文字変換のテスト"""

    def test_rank_high(self):
        assert rank_to_emoji("high") == "🔴 多"

    def test_rank_medium(self):
        assert rank_to_emoji("medium") == "🟡 中"

    def test_rank_low(self):
        assert rank_to_emoji("low") == "🟢 少"

    def test_rank_unknown(self):
        assert rank_to_emoji("unknown") == "-"

    def test_rank_empty(self):
        assert rank_to_emoji("") == "-"


class TestAppTable:
    """アプリテーブル生成のテスト"""

    def test_build_app_table_basic(self):
        apps = [
            AppUsage(
                name="VS Code", duration_min=120, rank="high", purpose="開発"
            ),
            AppUsage(
                name="Chrome", duration_min=60, rank="medium", purpose="調査"
            ),
        ]
        table = build_app_table(apps)

        assert table["type"] == "table"
        assert table["table"]["table_width"] == 4
        assert table["table"]["has_column_header"] is True
        assert table["table"]["has_row_header"] is False
        assert len(table["table"]["children"]) == 3  # header + 2 data rows

    def test_build_app_table_with_none_purpose(self):
        apps = [
            AppUsage(
                name="Terminal", duration_min=30, rank="low", purpose=None
            )
        ]
        table = build_app_table(apps)

        data_row = table["table"]["children"][1]  # First data row after header
        purpose_cell = data_row["table_row"]["cells"][3][0]["text"]["content"]
        assert purpose_cell == "-"

    def test_build_app_table_empty_list(self):
        apps = []
        table = build_app_table(apps)

        assert table["type"] == "table"
        assert len(table["table"]["children"]) == 1  # Only header row


class TestReportBlocksFromReport:
    """Reportエンティティからのブロック生成テスト"""

    def test_full_report(self):
        report = Report(
            meta=ReportMeta(date="2025-01-15"),
            main_tasks=[
                MainTask(title="タスク1", description="詳細1"),
                MainTask(title="タスク2", description="詳細2"),
            ],
            insights=[
                Insight(category="技術", content="知見1"),
                Insight(category="プロセス", content="知見2"),
            ],
            work_summary="作業サマリー",
            app_usage=[
                AppUsage(
                    name="App1", duration_min=100, rank="high", purpose="目的1"
                )
            ],
            files=["file1.py", "file2.py"],
        )

        blocks = build_report_blocks_from_report(report)

        # ブロック数の確認（各セクション + フッター）
        assert len(blocks) > 10

        # 見出しの確認
        headings = [b for b in blocks if b["type"] == "heading_2"]
        assert len(headings) == 5  # 基本情報, メイン作業, 知見, アプリ, ファイル

    def test_empty_report(self):
        report = Report(
            meta=ReportMeta(date="2025-01-15"),
            main_tasks=[],
            insights=[],
            work_summary="",
            app_usage=[],
            files=[],
        )

        blocks = build_report_blocks_from_report(report)

        # 空リストの場合でもブロックは生成される
        assert len(blocks) > 0

        # 各セクションに「記録されていません」メッセージがある
        paragraphs = [
            b["paragraph"]["rich_text"][0]["text"]["content"]
            for b in blocks
            if b["type"] == "paragraph"
        ]
        assert any("記録されていません" in p for p in paragraphs)

    def test_llm_failure_report(self):
        report = Report(
            meta=ReportMeta(
                date="2025-01-15",
                llm_success=False,
                llm_error="API timeout",
            ),
            main_tasks=[],
            insights=[],
            work_summary="",
            app_usage=[],
            files=[],
        )

        blocks = build_report_blocks_from_report(report)

        # 基本情報にエラーメッセージが含まれる
        basic_info_block = blocks[1]  # 最初のparagraph
        content = basic_info_block["paragraph"]["rich_text"][0]["text"]["content"]
        assert "LLM要約失敗" in content
        assert "API timeout" in content


class TestReportBlocksFromDict:
    """辞書形式からのブロック生成テスト"""

    def test_full_dict_report(self):
        report = {
            "meta": {"date": "2025-01-15", "generated_at": "2025-01-15T18:00:00"},
            "main_tasks": [
                {"title": "タスク1", "description": "詳細1"},
            ],
            "insights": [
                {"category": "技術", "content": "知見1"},
            ],
            "work_summary": "作業サマリー",
            "app_usage": [
                {"name": "App1", "duration_min": 100, "rank": "high", "purpose": "目的1"}
            ],
            "files": ["file1.py"],
        }

        blocks = build_report_blocks_from_dict(report)
        assert len(blocks) > 0

    def test_empty_dict_report(self):
        report = {
            "meta": {},
            "main_tasks": [],
            "insights": [],
            "work_summary": "",
            "app_usage": [],
            "files": [],
        }

        blocks = build_report_blocks_from_dict(report)
        assert len(blocks) > 0

    def test_missing_fields_in_dict(self):
        # フィールドが欠けている場合でも動作する
        report = {}

        blocks = build_report_blocks_from_dict(report)
        assert len(blocks) > 0


class TestBuildReportBlocks:
    """統合インターフェースのテスト"""

    def test_with_report_entity(self):
        report = Report(
            meta=ReportMeta(date="2025-01-15"),
            main_tasks=[],
            insights=[],
            work_summary="",
            app_usage=[],
            files=[],
        )

        blocks = build_report_blocks(report)
        assert len(blocks) > 0

    def test_with_dict(self):
        report = {
            "meta": {"date": "2025-01-15"},
            "main_tasks": [],
            "insights": [],
            "work_summary": "",
            "app_usage": [],
            "files": [],
        }

        blocks = build_report_blocks(report)
        assert len(blocks) > 0
