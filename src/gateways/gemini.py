"""Gemini Gateway - Gemini API連携

features.jsonをLLMで要約し、構造化JSONとして日報を生成。
フォールバック機能、リトライ処理、タイムアウト対応を含む。
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from google import genai
from google.genai import types

from src.domain.report import LLMSummary, MainTask, Insight


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


class GeminiGateway:
    """Gemini API連携ゲートウェイ

    Attributes:
        api_key: Gemini APIキー
        model: 使用モデル名
        timeout_sec: タイムアウト秒数
        retry_count: リトライ回数
        retry_delay_sec: リトライ間隔秒数
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash",
        timeout_sec: int = 30,
        retry_count: int = 2,
        retry_delay_sec: int = 5,
    ):
        """初期化

        Args:
            api_key: Gemini APIキー（Noneの場合は環境変数から取得）
            model: 使用モデル名
            timeout_sec: タイムアウト秒数
            retry_count: リトライ回数
            retry_delay_sec: リトライ間隔秒数

        Raises:
            ValueError: APIキーが設定されていない場合
        """
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        self.model = model
        self.timeout_sec = timeout_sec
        self.retry_count = retry_count
        self.retry_delay_sec = retry_delay_sec
        self.client = genai.Client(api_key=self.api_key)

    def generate_summary(self, features: dict[str, Any]) -> LLMSummary:
        """作業ログから日報サマリーを生成

        Args:
            features: 集計済み作業ログデータ (features.json)

        Returns:
            LLM生成サマリー

        Raises:
            Exception: API呼び出しが全てのリトライで失敗した場合
        """
        user_prompt = self._build_user_prompt(features)
        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
        schema = LLMSummary.model_json_schema()

        # リトライループ
        last_error = None
        for attempt in range(self.retry_count + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_json_schema=schema,
                        temperature=0.3,
                        max_output_tokens=1000,
                    ),
                )

                # レスポンスをパース
                summary = LLMSummary.model_validate_json(response.text)
                return summary

            except Exception as e:
                last_error = e
                if attempt < self.retry_count:
                    time.sleep(self.retry_delay_sec)
                    continue

        # 全リトライ失敗
        raise Exception(f"Gemini API call failed after {self.retry_count + 1} attempts: {last_error}")

    def _build_user_prompt(self, features: dict[str, Any]) -> str:
        """ユーザープロンプトを構築

        Args:
            features: 集計済み作業ログデータ

        Returns:
            プロンプト文字列
        """
        meta = features.get("meta", {})

        # 時間帯別作業（上位8件）
        time_blocks = features.get("time_blocks", [])[:8]
        time_blocks_text = "\n".join([
            f"- {block['start']}〜{block['end']}: "
            f"{', '.join([app['name'] for app in block.get('apps', [])[:2]])}"
            for block in time_blocks
        ])

        # アプリ使用状況（上位5件）
        app_summary = features.get("app_summary", [])[:5]
        app_text = "\n".join([
            f"- {app['name']}: {app['duration_min']}分 ({app['rank']})"
            for app in app_summary
        ])

        # 主なキーワード（上位10件）
        global_keywords = features.get("global_keywords", {})
        keywords = global_keywords.get("top_keywords", [])[:10]
        keywords_text = ", ".join(keywords)

        # 主なファイル（上位10件）
        global_files = features.get("global_files", {})
        files = global_files.get("top_files", [])[:10]
        files_text = "\n".join([f"- {f}" for f in files])

        return f"""以下は本日の作業ログの要約です。日報を作成してください。

## 基本情報
- 日付: {meta.get('date', 'N/A')}
- 記録期間: {meta.get('first_capture', 'N/A')} 〜 {meta.get('last_capture', 'N/A')}
- キャプチャ数: {meta.get('capture_count', 0)}回
- 総作業時間: {meta.get('total_duration_min', 0)}分

## 時間帯別作業
{time_blocks_text}

## アプリ使用状況
{app_text}

## 主なキーワード
{keywords_text}

## 主なファイル
{files_text}
"""


def generate_summary_with_fallback(
    features: dict[str, Any],
    api_key: str | None = None,
) -> tuple[LLMSummary, bool, str | None]:
    """フォールバック付きでサマリーを生成

    LLM呼び出しが失敗した場合、テンプレートサマリーを返す。

    Args:
        features: 集計済み作業ログデータ
        api_key: Gemini APIキー（オプション）

    Returns:
        (サマリー, 成功フラグ, エラーメッセージ)
    """
    try:
        gateway = GeminiGateway(api_key=api_key)
        summary = gateway.generate_summary(features)
        return summary, True, None
    except Exception as e:
        error_msg = str(e)
        fallback_summary = LLMSummary(
            main_tasks=[
                MainTask(
                    title="作業記録",
                    description="本日の作業内容は自動要約できませんでした。"
                    "詳細はアプリ使用状況をご確認ください。",
                )
            ],
            insights=[],
            work_summary="（自動要約に失敗しました）",
        )
        return fallback_summary, False, error_msg
