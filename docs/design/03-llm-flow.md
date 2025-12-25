# LLM要約フロー設計

## 1. 概要

### 1.1 目的

集計処理で生成されたfeatures.jsonをLLMに渡し、人間が読みやすい日報形式（report.json）に変換する。

### 1.2 LLMの役割

| 処理 | LLM | ルールベース |
|------|-----|-------------|
| 本日のメイン作業（3件） | ✅ | ❌ |
| 知見・メモ抽出 | ✅ | ❌ |
| アプリ使用状況テーブル | ❌ | ✅ |
| 作業ファイル一覧 | ❌ | ✅ |

### 1.3 使用モデル

| 項目 | 値 |
|------|------|
| プロバイダー | Google |
| モデル | gemini-2.5-flash（推奨） |
| 代替 | gemini-2.5-pro（高精度必要時） |
| 出力形式 | JSON (Structured Output) |

## 2. フロー詳細

### 2.1 処理ステップ

```
┌──────────────────────────────────────────────────────────────┐
│                        START                                  │
│                  (集計処理完了後)                              │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. features.json 読み込み                                     │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. プロンプト構築                                             │
│    - システムプロンプト（出力スキーマ指定）                     │
│    - ユーザープロンプト（features.json要約）                   │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Gemini API 呼び出し                                        │
│    - response_mime_type: application/json                     │
│    - response_json_schema: スキーマ指定                        │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────┴─────────┐
                    │                   │
                 成功                 失敗
                    │                   │
                    ▼                   ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│ 4a. レスポンス解析       │  │ 4b. フォールバック       │
│     JSON検証             │  │     テンプレート日報生成 │
└──────────────────────────┘  └──────────────────────────┘
                    │                   │
                    └─────────┬─────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. report.json 出力                                           │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                         END                                   │
│                  → Notion出力フローへ                          │
└──────────────────────────────────────────────────────────────┘
```

## 3. プロンプト設計

### 3.1 システムプロンプト

```
あなたはPC作業ログから日報を生成するアシスタントです。

以下のルールに従って、入力された作業ログの要約から日報を作成してください：

## 出力ルール

1. **本日のメイン作業**
   - 重要度・作業時間の長さを考慮して3件抽出
   - 具体的な成果物や進捗を含める
   - 「〜を実装した」「〜を調査した」「〜を修正した」など動詞で終わる

2. **知見・メモ**
   - 技術的な発見、学び、注意点を抽出
   - カテゴリ別に整理（技術/プロセス/その他）
   - 将来役立つ情報を優先

3. **注意事項**
   - 推測で情報を補完しない
   - 入力データにない内容は書かない
   - 簡潔で読みやすい日本語で記述

## 出力形式

指定されたJSONスキーマに従って出力してください。
```

### 3.2 ユーザープロンプト

```
以下は本日の作業ログの要約です。これをもとに日報を作成してください。

## 基本情報
- 日付: {date}
- 記録期間: {first_capture} 〜 {last_capture}
- キャプチャ数: {capture_count}回
- 総作業時間: {total_duration_min}分

## 時間帯別作業
{time_blocks_summary}

## アプリ使用状況
{app_summary}

## 主なキーワード
{global_keywords}

## 主なファイル
{global_files}
```

### 3.3 出力スキーマ

```json
{
  "type": "object",
  "properties": {
    "main_tasks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "title": {"type": "string"},
          "description": {"type": "string"}
        },
        "required": ["title", "description"]
      },
      "minItems": 1,
      "maxItems": 3
    },
    "insights": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "category": {"type": "string", "enum": ["技術", "プロセス", "その他"]},
          "content": {"type": "string"}
        },
        "required": ["category", "content"]
      }
    },
    "work_summary": {
      "type": "string"
    }
  },
  "required": ["main_tasks", "insights", "work_summary"]
}
```

## 4. データ仕様

### 4.1 入力: features.json（抜粋）

```json
{
  "meta": {
    "date": "2025-01-15",
    "capture_count": 240,
    "total_duration_min": 478
  },
  "time_blocks": [...],
  "app_summary": [...],
  "global_keywords": {
    "top_keywords": ["Python", "Flask", "API"]
  }
}
```

### 4.2 出力: report.json

```json
{
  "meta": {
    "date": "2025-01-15",
    "generated_at": "2025-01-15T18:05:00+09:00",
    "llm_model": "gemini-2.5-flash",
    "llm_success": true
  },
  "main_tasks": [
    {
      "title": "Flask APIエンドポイントの実装",
      "description": "ユーザー認証用のREST APIを3エンドポイント実装した"
    },
    {
      "title": "ドキュメント調査・レビュー",
      "description": "Stack Overflowとpython.orgでFlaskの認証パターンを調査した"
    },
    {
      "title": "Slackでのコードレビュー対応",
      "description": "チームからのレビューコメントに対応し、修正を実施した"
    }
  ],
  "insights": [
    {
      "category": "技術",
      "content": "Flask-JWTの設定でトークン有効期限のデフォルト値に注意"
    },
    {
      "category": "プロセス",
      "content": "認証周りは早めにレビュー依頼すると手戻りが減る"
    }
  ],
  "work_summary": "本日はFlask APIの認証機能実装に注力し、基本的なエンドポイントを完成させた。",
  "app_usage": [
    {
      "name": "Visual Studio Code",
      "duration_min": 240,
      "rank": "high",
      "purpose": "Python/Flask開発"
    },
    {
      "name": "Google Chrome",
      "duration_min": 160,
      "rank": "high",
      "purpose": "ドキュメント調査"
    },
    {
      "name": "Slack",
      "duration_min": 80,
      "rank": "medium",
      "purpose": "コードレビュー対応"
    }
  ],
  "files": ["main.py", "routes.py", "models.py", "auth.py"]
}
```

## 5. API呼び出し仕様

### 5.1 セットアップ

```bash
pip install google-genai
```

```python
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Literal

# スキーマ定義
class MainTask(BaseModel):
    title: str = Field(description="タスクのタイトル（動詞で終わる）")
    description: str = Field(description="具体的な成果・進捗")

class Insight(BaseModel):
    category: Literal["技術", "プロセス", "その他"]
    content: str = Field(description="知見の内容")

class DailyReport(BaseModel):
    main_tasks: List[MainTask] = Field(max_length=3)
    insights: List[Insight]
    work_summary: str = Field(description="1-2文の作業サマリー")

# クライアント初期化
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
```

### 5.2 リクエスト

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=f"{SYSTEM_PROMPT}\n\n{user_prompt}",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=DailyReport.model_json_schema(),
        temperature=0.3,
        max_output_tokens=1000,
    ),
)
```

### 5.3 レスポンス処理

```python
try:
    report = DailyReport.model_validate_json(response.text)
    report_dict = report.model_dump()
    report_dict["meta"]["llm_success"] = True
except Exception as e:
    report_dict = generate_fallback_report(features)
    report_dict["meta"]["llm_success"] = False
    report_dict["meta"]["llm_error"] = str(e)
```

## 6. フォールバック処理

### 6.1 テンプレート日報

LLM呼び出しが失敗した場合、以下のテンプレートで日報を生成：

```json
{
  "meta": {
    "llm_success": false,
    "llm_error": "API timeout"
  },
  "main_tasks": [
    {
      "title": "作業記録",
      "description": "本日の作業内容は自動要約できませんでした。詳細はアプリ使用状況をご確認ください。"
    }
  ],
  "insights": [],
  "work_summary": "（自動要約に失敗しました）",
  "app_usage": [...],  // features.jsonから転記
  "files": [...]       // features.jsonから転記
}
```

### 6.2 フォールバック条件

| 条件 | 対応 |
|------|------|
| API接続エラー | テンプレート日報 |
| レート制限 | 60秒待機後リトライ、失敗でテンプレート |
| JSON解析エラー | テンプレート日報 |
| スキーマ不一致 | テンプレート日報 |

## 7. セキュリティ考慮

### 7.1 送信データの制限

| データ | 送信 | 理由 |
|--------|------|------|
| 時間帯別要約 | ✅ | 作業パターン把握に必要 |
| アプリ名・使用時間 | ✅ | メイン作業推定に必要 |
| 上位キーワード（10件） | ✅ | 作業内容推定に必要 |
| OCR全文 | ❌ | 機密情報リスク |
| ファイル内容 | ❌ | 機密情報リスク |
| URL（ドメインのみ） | ✅ | 調査内容推定に必要 |

### 7.2 マスキング（Phase 5）

```python
MASK_PATTERNS = [
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    (r'\b\d{3}-\d{4}-\d{4}\b', '[PHONE]'),
    (r'password|secret|token|key', '[SENSITIVE]'),
]
```

## 8. 設定パラメータ

```json
{
  "llm": {
    "provider": "gemini",
    "model": "gemini-2.5-flash",
    "api_key_env": "GEMINI_API_KEY",
    "max_output_tokens": 1000,
    "temperature": 0.3,
    "timeout_sec": 30,
    "retry_count": 2,
    "retry_delay_sec": 5,
    "fallback_on_error": true
  }
}
```

## 9. コスト見積もり

### 9.1 トークン使用量（概算）

| 項目 | トークン数 |
|------|-----------|
| システムプロンプト | ~300 |
| ユーザープロンプト | ~500 |
| 出力 | ~300 |
| **合計** | **~1,100** |

### 9.2 月間コスト（gemini-2.5-flash）

```
1日1回生成 × 30日 = 30回/月
30回 × 1,100トークン = 33,000トークン/月

Gemini 2.5 Flash は無料枠内で十分対応可能
（有料利用時: 入力 $0.075/1M, 出力 $0.30/1M）
合計: 約 $0.003/月 または無料
```

## 10. テスト観点

### 10.1 単体テスト

- [ ] プロンプト構築が正しい
- [ ] API呼び出しが成功
- [ ] レスポンスJSONが正しく解析される
- [ ] スキーマ検証が機能

### 10.2 統合テスト

- [ ] 実際のfeatures.jsonで意味のある日報生成
- [ ] フォールバックが正しく動作
- [ ] タイムアウト時の挙動

### 10.3 品質テスト

- [ ] 生成された日報が読みやすい
- [ ] 入力データにない情報が含まれていない
- [ ] 日本語として自然
