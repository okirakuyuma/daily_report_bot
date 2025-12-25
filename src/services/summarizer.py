"""Summarizer Service - LLM要約サービス

Features を入力として受け取り、LLMを使用して日報レポートを生成。
LLM呼び出しが失敗した場合はフォールバックレポートを生成。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Protocol

from src.domain.features import Features
from src.domain.report import AppUsage as ReportAppUsage
from src.domain.report import LLMSummary, Report, ReportMeta

logger = logging.getLogger(__name__)


# 定数定義
MAX_TIME_BLOCKS = 8
MAX_APP_SUMMARY = 5
MAX_KEYWORDS = 10


class GeminiClientProtocol(Protocol):
    """GeminiClient のインターフェース定義（型安全性確保）"""

    model_name: str

    def generate_summary(self, features: dict) -> LLMSummary:
        """features dict から LLMSummary を生成"""
        ...


def _convert_features_to_dict(features: Features) -> dict:
    """Features を dict に変換（GeminiGateway のインターフェースに合わせる）

    Args:
        features: 集計済み特徴量

    Returns:
        features dict（gemini.py の generate_summary() に渡す形式）
    """
    return {
        "meta": {
            "date": features.meta.date,
            "generated_at": features.meta.generated_at,
            "capture_count": features.meta.capture_count,
            "first_capture": features.meta.first_capture,
            "last_capture": features.meta.last_capture,
            "total_duration_min": features.meta.total_duration_min,
        },
        "time_blocks": [
            {
                "start": block.start,
                "end": block.end,
                "apps": [{"name": app.name, "percent": app.percent} for app in block.apps],
            }
            for block in features.time_blocks
        ],
        "app_summary": [
            {
                "name": app.name,
                "process": app.process,
                "count": app.count,
                "duration_min": app.duration_min,
                "rank": app.rank.value,
            }
            for app in features.app_summary
        ],
        "global_keywords": {
            "top_keywords": features.global_keywords.top_keywords,
            "top_urls": features.global_keywords.top_urls,
            "top_files": features.global_keywords.top_files,
        },
    }


def _convert_features_to_app_usage(features: Features) -> list[ReportAppUsage]:
    """Features から Report用 AppUsage リストを生成

    Args:
        features: 集計済み特徴量

    Returns:
        Report用 AppUsage リスト
    """
    return [
        ReportAppUsage(
            name=app.name,
            duration_min=int(app.duration_min),  # float から int に変換
            rank=app.rank.value,  # Enum から文字列値に変換
            purpose=None,  # LLMが用途を推定する場合は別途実装
        )
        for app in features.app_summary
    ]


class SummarizerService:
    """日報要約サービス

    LLMを使用してFeaturesから日報Reportを生成。
    失敗時はフォールバックレポートを返す。
    """

    def __init__(self, gemini_client: GeminiClientProtocol | None = None) -> None:
        """初期化

        Args:
            gemini_client: GeminiClientインスタンス（依存性注入）
        """
        self.gemini_client = gemini_client

    def generate_report(self, features: Features) -> Report:
        """日報レポートを生成

        Args:
            features: 集計済み特徴量

        Returns:
            日報レポート（LLM生成またはフォールバック）
        """
        logger.info(f"日報生成開始: {features.meta.date}")

        # アプリ使用状況とファイル一覧を準備（ルールベース処理）
        app_usage = _convert_features_to_app_usage(features)
        files = features.global_keywords.top_files

        # LLM呼び出しを試行
        try:
            if self.gemini_client is None:
                raise ValueError("GeminiClient が設定されていません")

            # Features を dict に変換してGeminiGateway に渡す
            features_dict = _convert_features_to_dict(features)

            logger.debug("LLM呼び出し開始")

            # GeminiGateway がプロンプト構築からLLM呼び出しまで完結
            llm_summary = self.gemini_client.generate_summary(features_dict)

            logger.info("LLM要約成功")

            # Report メタデータ作成
            meta = ReportMeta(
                date=features.meta.date,
                generated_at=datetime.now(),
                llm_model=self.gemini_client.model_name,
                llm_success=True,
            )

            # LLMサマリーからレポート生成
            report = Report.from_llm_summary(
                summary=llm_summary,
                meta=meta,
                app_usage=app_usage,
                files=files,
            )

            logger.info(
                f"日報生成完了: メイン作業{len(report.main_tasks)}件, "
                f"知見{len(report.insights)}件"
            )

            return report

        except Exception as e:
            logger.error(f"LLM要約失敗: {e}", exc_info=True)
            logger.warning("フォールバックレポートを生成します")

            # フォールバックレポート生成
            fallback_report = Report.create_fallback(
                date=features.meta.date,
                error=str(e),
                app_usage=app_usage,
                files=files,
            )

            logger.info("フォールバックレポート生成完了")

            return fallback_report


# 便利関数: クライアントなしでも動作するデフォルトインスタンス生成
def create_summarizer(
    gemini_client: GeminiClientProtocol | None = None,
) -> SummarizerService:
    """SummarizerService インスタンスを生成

    Args:
        gemini_client: GeminiClientインスタンス（オプション）

    Returns:
        SummarizerService インスタンス
    """
    return SummarizerService(gemini_client=gemini_client)
