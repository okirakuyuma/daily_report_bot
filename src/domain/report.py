"""Report - 日報レポートエンティティ

LLM要約結果とルールベース処理結果を統合した日報データ構造を定義。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from .features import AppRank


class MainTask(BaseModel):
    """メイン作業項目

    Attributes:
        title: タスクのタイトル（動詞で終わる）
        description: 具体的な成果・進捗
    """

    title: str = Field(description="タスクのタイトル（動詞で終わる）")
    description: str = Field(description="具体的な成果・進捗")


class InsightCategory(str, Enum):
    """知見カテゴリ."""

    TECHNICAL = "技術"  # 技術的な知見・学び
    PROCESS = "プロセス"  # 作業プロセスの改善点
    OTHER = "その他"  # その他のメモ


class Insight(BaseModel):
    """知見・メモ

    Attributes:
        category: カテゴリ（技術/プロセス/その他）
        content: 知見の内容
    """

    category: InsightCategory = Field(description="知見カテゴリ")
    content: str = Field(description="知見の内容", min_length=1)


class AppUsage(BaseModel):
    """アプリ使用状況

    Attributes:
        name: アプリケーション名
        duration_min: 使用時間（分）
        rank: 使用頻度ランク
        purpose: 用途（オプション）
    """

    name: str = Field(description="アプリケーション名", min_length=1)
    duration_min: int = Field(description="使用時間（分）", ge=0)
    rank: AppRank = Field(description="使用頻度ランク")
    purpose: str | None = Field(default=None, description="用途の説明")


class LLMSummary(BaseModel):
    """LLM生成サマリー

    Gemini APIからの構造化出力結果を格納。
    """

    main_tasks: list[MainTask] = Field(default_factory=list, max_length=3)
    insights: list[Insight] = Field(default_factory=list)
    work_summary: str = Field(default="", description="1-2文の作業サマリー")


class ReportMeta(BaseModel):
    """レポートメタデータ

    Attributes:
        date: 日付 (YYYY-MM-DD)
        generated_at: 生成日時
        llm_model: 使用LLMモデル
        llm_success: LLM呼び出し成功フラグ
        llm_error: LLMエラーメッセージ（失敗時）
    """

    date: str
    generated_at: datetime = Field(default_factory=datetime.now)
    llm_model: str = "gemini-2.5-flash"
    llm_success: bool = True
    llm_error: str | None = None


class Report(BaseModel):
    """日報レポート

    LLM要約結果とルールベース処理結果を統合した完全な日報データ。

    Attributes:
        meta: レポートメタデータ
        main_tasks: メイン作業リスト（LLM生成）
        insights: 知見リスト（LLM生成）
        work_summary: 作業サマリー（LLM生成）
        app_usage: アプリ使用状況（ルールベース）
        files: 作業ファイル一覧（ルールベース）
    """

    meta: ReportMeta
    main_tasks: list[MainTask] = Field(default_factory=list)
    insights: list[Insight] = Field(default_factory=list)
    work_summary: str = ""
    app_usage: list[AppUsage] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)

    @classmethod
    def from_llm_summary(
        cls,
        summary: LLMSummary,
        meta: ReportMeta,
        app_usage: list[AppUsage],
        files: list[str],
    ) -> Report:
        """LLMサマリーからレポートを生成

        Args:
            summary: LLM生成サマリー
            meta: レポートメタデータ
            app_usage: アプリ使用状況
            files: ファイル一覧

        Returns:
            完成したレポート
        """
        return cls(
            meta=meta,
            main_tasks=summary.main_tasks,
            insights=summary.insights,
            work_summary=summary.work_summary,
            app_usage=app_usage,
            files=files,
        )

    @classmethod
    def create_fallback(
        cls,
        date: str,
        error: str,
        app_usage: list[AppUsage],
        files: list[str],
    ) -> Report:
        """フォールバックレポートを生成

        LLM呼び出しが失敗した場合に使用するテンプレートレポート。

        Args:
            date: 日付
            error: エラーメッセージ
            app_usage: アプリ使用状況
            files: ファイル一覧

        Returns:
            フォールバックレポート
        """
        return cls(
            meta=ReportMeta(
                date=date,
                llm_success=False,
                llm_error=error,
            ),
            main_tasks=[
                MainTask(
                    title="作業記録",
                    description="本日の作業内容は自動要約できませんでした。"
                    "詳細はアプリ使用状況をご確認ください。",
                )
            ],
            insights=[],
            work_summary="（自動要約に失敗しました）",
            app_usage=app_usage,
            files=files,
        )
