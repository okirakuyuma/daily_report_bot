"""Summarizer Service - LLM要約サービス

Features を入力として受け取り、LLMを使用して日報レポートを生成。
LLM呼び出しが失敗した場合はフォールバックレポートを生成。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from src.domain.features import Features
from src.domain.report import AppUsage as ReportAppUsage
from src.domain.report import Report, ReportMeta

logger = logging.getLogger(__name__)


# システムプロンプト定義
SYSTEM_PROMPT = """あなたはPC作業ログから日報を生成するアシスタントです。

## 出力ルール

1. **本日のメイン作業** (最大3件)
   - 作業時間・重要度を考慮して選定
   - 具体的な成果物や進捗を含める
   - 「〜を実装した」「〜を調査した」など動詞で終わる

2. **知見・メモ**
   - 技術的な発見、学び、注意点を抽出
   - カテゴリ: 技術 / プロセス / その他

3. **作業サマリー**
   - 1文で本日の作業を要約

## 注意事項
- 推測で情報を補完しない
- 入力データにない内容は書かない
- 簡潔で読みやすい日本語で記述
"""


def _build_user_prompt(features: Features) -> str:
    """ユーザープロンプトを構築

    Args:
        features: 集計済み特徴量

    Returns:
        ユーザープロンプト文字列
    """
    meta = features.meta

    # 時間帯別作業（上位8件）
    time_blocks_lines = []
    for block in features.time_blocks[:8]:
        app_names = [app.name for app in block.apps[:2]]
        apps_str = ", ".join(app_names)
        time_blocks_lines.append(f"- {block.start}〜{block.end}: {apps_str}")
    time_blocks_text = (
        "\n".join(time_blocks_lines) if time_blocks_lines else "（データなし）"
    )

    # アプリ使用状況（上位5件）
    app_lines = []
    for app in features.app_summary[:5]:
        app_lines.append(f"- {app.name}: {app.duration_min}分 ({app.rank.value})")
    app_text = "\n".join(app_lines) if app_lines else "（データなし）"

    # 主なキーワード（上位10件）
    keywords_text = ", ".join(features.global_keywords.top_keywords[:10])
    if not keywords_text:
        keywords_text = "（データなし）"

    return f"""以下は本日の作業ログの要約です。日報を作成してください。

## 基本情報
- 日付: {meta.date}
- 記録期間: {meta.first_capture} 〜 {meta.last_capture}
- キャプチャ数: {meta.capture_count}回
- 総作業時間: {meta.total_duration_min}分

## 時間帯別作業
{time_blocks_text}

## アプリ使用状況
{app_text}

## 主なキーワード
{keywords_text}
"""


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

    def __init__(self, gemini_client: Any | None = None) -> None:
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

            # プロンプト構築
            user_prompt = _build_user_prompt(features)
            full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

            logger.debug("LLM呼び出し開始")
            logger.debug(f"プロンプト長: {len(full_prompt)} 文字")

            # GeminiClient を使用してLLM呼び出し
            llm_summary = self.gemini_client.generate_summary(full_prompt)

            logger.info("LLM要約成功")

            # Report メタデータ作成
            meta = ReportMeta(
                date=features.meta.date,
                generated_at=datetime.now(),
                llm_model=self.gemini_client.model_name
                if hasattr(self.gemini_client, "model_name")
                else "gemini-2.5-flash",
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
def create_summarizer(gemini_client: Any | None = None) -> SummarizerService:
    """SummarizerService インスタンスを生成

    Args:
        gemini_client: GeminiClientインスタンス（オプション）

    Returns:
        SummarizerService インスタンス
    """
    return SummarizerService(gemini_client=gemini_client)
