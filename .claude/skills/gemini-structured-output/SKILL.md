# Gemini Structured Output Skill

Google Gemini APIで構造化JSON出力を生成するためのスキル。

## Triggers

- Gemini API、LLM要約、構造化出力、JSON Schema使用時
- 日報生成エンジンのLLM要約フロー実装時

## 基本情報

| 項目 | 値 |
|------|-----|
| ベースURL | `https://generativelanguage.googleapis.com/v1beta` |
| 推奨モデル | `gemini-2.5-flash` / `gemini-2.0-flash` |
| 認証 | API Key (`x-goog-api-key` header) |
| 出力形式 | JSON (Structured Output) |

---

## Python SDK セットアップ

### インストール

```bash
pip install google-genai
```

### クライアント初期化

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
```

---

## 構造化出力の実装

### 基本パターン（Pydantic使用）

```python
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

# スキーマ定義
class MainTask(BaseModel):
    title: str = Field(description="タスクのタイトル")
    description: str = Field(description="タスクの詳細説明")

class Insight(BaseModel):
    category: str = Field(description="カテゴリ: 技術/プロセス/その他")
    content: str = Field(description="知見の内容")

class DailyReport(BaseModel):
    main_tasks: List[MainTask] = Field(description="本日のメイン作業（最大3件）")
    insights: List[Insight] = Field(description="知見・メモ")
    work_summary: str = Field(description="作業サマリー（1-2文）")

# API呼び出し
client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=user_prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=DailyReport.model_json_schema(),
    ),
)

# レスポンス解析
result = DailyReport.model_validate_json(response.text)
print(result.main_tasks[0].title)
```

### 直接JSON Schema指定

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_json_schema": {
            "type": "object",
            "properties": {
                "main_tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "タスクタイトル"},
                            "description": {"type": "string", "description": "詳細説明"}
                        },
                        "required": ["title", "description"]
                    },
                    "maxItems": 3
                },
                "insights": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": ["技術", "プロセス", "その他"]
                            },
                            "content": {"type": "string"}
                        },
                        "required": ["category", "content"]
                    }
                },
                "work_summary": {"type": "string"}
            },
            "required": ["main_tasks", "insights", "work_summary"]
        }
    }
)
```

---

## REST API 直接呼び出し

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{
    "contents": [{
      "parts": [{"text": "本日の作業ログから日報を生成してください..."}]
    }],
    "generationConfig": {
      "responseMimeType": "application/json",
      "responseJsonSchema": {
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
            }
          },
          "work_summary": {"type": "string"}
        },
        "required": ["main_tasks", "work_summary"]
      }
    }
  }'
```

---

## 日報生成用プロンプト設計

### システムプロンプト

```python
SYSTEM_PROMPT = """あなたはPC作業ログから日報を生成するアシスタントです。

## 出力ルール

1. **本日のメイン作業**
   - 重要度・作業時間を考慮して3件抽出
   - 「〜を実装した」「〜を調査した」など動詞で終わる
   - 推測で情報を補完しない

2. **知見・メモ**
   - 技術的な発見、学び、注意点を抽出
   - カテゴリ: 技術/プロセス/その他

3. **注意事項**
   - 入力データにない内容は書かない
   - 簡潔で読みやすい日本語で記述
"""
```

### ユーザープロンプトテンプレート

```python
USER_PROMPT_TEMPLATE = """以下は本日の作業ログの要約です。日報を作成してください。

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
"""
```

---

## 日報生成スキーマ

```python
from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime

class MainTask(BaseModel):
    title: str = Field(description="タスクのタイトル（動詞で終わる）")
    description: str = Field(description="具体的な成果・進捗")

class Insight(BaseModel):
    category: Literal["技術", "プロセス", "その他"]
    content: str = Field(description="知見の内容")

class ReportMeta(BaseModel):
    date: str
    generated_at: str
    llm_model: str = "gemini-2.5-flash"
    llm_success: bool = True

class DailyReport(BaseModel):
    meta: ReportMeta
    main_tasks: List[MainTask] = Field(max_length=3)
    insights: List[Insight]
    work_summary: str = Field(description="1-2文の作業サマリー")
```

---

## エラーハンドリング

```python
import json
from google.api_core import exceptions

def generate_report(features: dict) -> dict:
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=build_prompt(features),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=DailyReport.model_json_schema(),
            ),
        )

        report = DailyReport.model_validate_json(response.text)
        return report.model_dump()

    except exceptions.ResourceExhausted:
        # レート制限
        time.sleep(60)
        return generate_report(features)  # リトライ

    except exceptions.InvalidArgument as e:
        # スキーマエラー
        return generate_fallback_report(features, str(e))

    except json.JSONDecodeError as e:
        # JSON解析エラー
        return generate_fallback_report(features, str(e))
```

### フォールバック処理

```python
def generate_fallback_report(features: dict, error: str) -> dict:
    """LLM失敗時のテンプレート日報"""
    return {
        "meta": {
            "date": features["meta"]["date"],
            "generated_at": datetime.now().isoformat(),
            "llm_model": "fallback",
            "llm_success": False,
            "llm_error": error
        },
        "main_tasks": [{
            "title": "作業記録",
            "description": "自動要約に失敗しました。アプリ使用状況をご確認ください。"
        }],
        "insights": [],
        "work_summary": "（自動要約に失敗しました）"
    }
```

---

## 設定パラメータ

```json
{
  "llm": {
    "provider": "gemini",
    "model": "gemini-2.5-flash",
    "api_key_env": "GEMINI_API_KEY",
    "timeout_sec": 30,
    "retry_count": 2,
    "retry_delay_sec": 5,
    "fallback_on_error": true,
    "temperature": 0.3,
    "max_output_tokens": 1000
  }
}
```

---

## モデル比較

| モデル | 速度 | 精度 | コスト | 推奨用途 |
|--------|------|------|--------|---------|
| `gemini-2.5-flash` | 高速 | 高 | 低 | 日常的な日報生成 |
| `gemini-2.0-flash` | 高速 | 中 | 低 | シンプルな要約 |
| `gemini-2.5-pro` | 中速 | 最高 | 高 | 複雑な分析が必要な場合 |

---

## JSON Schema サポート型

| 型 | 説明 | 例 |
|-----|------|-----|
| `string` | テキスト | `{"type": "string"}` |
| `integer` | 整数 | `{"type": "integer"}` |
| `number` | 小数 | `{"type": "number"}` |
| `boolean` | 真偽 | `{"type": "boolean"}` |
| `array` | 配列 | `{"type": "array", "items": {...}}` |
| `object` | オブジェクト | `{"type": "object", "properties": {...}}` |
| `enum` | 列挙 | `{"type": "string", "enum": ["a", "b"]}` |
| `nullable` | null許容 | `{"type": ["string", "null"]}` |

---

## 制限事項

- `maxItems`, `minItems` は参考値（厳密に強制されない場合あり）
- ネストが深すぎるスキーマは避ける（3階層程度が推奨）
- 日本語のenum値はサポートされる
- `description` を詳細に書くと出力品質が向上
