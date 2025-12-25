---
name: llm-integration
description: Gemini APIで日報要約を構造化JSON出力。LLM要約、構造化出力、プロンプト設計、日報生成エンジン実装時に使用。OpenAI APIからGemini APIへの移行も対応。
---

# LLM Integration

Gemini APIを使用した日報要約生成スキル。

## クイックリファレンス

| 項目 | 値 |
|------|-----|
| SDK | `google-genai` |
| 推奨モデル | `gemini-2.5-flash` |
| 認証 | `GEMINI_API_KEY` 環境変数 |
| 出力形式 | JSON (Structured Output) |

## セットアップ

```bash
pip install google-genai pydantic
```

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
```

## 構造化出力パターン

### Pydanticスキーマ定義

```python
from pydantic import BaseModel, Field
from typing import List, Literal

class MainTask(BaseModel):
    title: str = Field(description="タスクのタイトル")
    description: str = Field(description="タスクの詳細説明")

class Insight(BaseModel):
    category: Literal["技術", "プロセス", "その他"]
    content: str = Field(description="知見の内容")

class DailyReport(BaseModel):
    main_tasks: List[MainTask] = Field(max_length=3)
    insights: List[Insight]
    work_summary: str = Field(description="1-2文の作業サマリー")
```

### API呼び出し

```python
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=user_prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=DailyReport.model_json_schema(),
    ),
)

result = DailyReport.model_validate_json(response.text)
```

## フォールバック処理

```python
def generate_with_fallback(features: dict) -> dict:
    try:
        return generate_summary(features)
    except Exception as e:
        return {
            "main_tasks": [{"title": "作業記録", "description": "自動要約に失敗"}],
            "insights": [],
            "work_summary": "（自動要約に失敗しました）",
            "meta": {"llm_success": False, "llm_error": str(e)}
        }
```

## プライバシー保護

```python
MASK_PATTERNS = [
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    (r'(?i)(password|secret|token|key)\s*[:=]\s*\S+', '[SENSITIVE]'),
]

def mask_sensitive_data(text: str) -> str:
    for pattern, replacement in MASK_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text
```

## 詳細リファレンス

- [システムプロンプト](references/system-prompt.md)
- [ユーザープロンプトテンプレート](references/user-prompt.md)
