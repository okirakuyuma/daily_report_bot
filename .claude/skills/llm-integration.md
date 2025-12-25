# LLM Integration Expert Skill

OpenAI APIを使用した日報要約生成に特化したスキル

## トリガー

- OpenAI API連携実装
- プロンプトエンジニアリング
- 構造化出力（JSON Schema）
- フォールバック処理

## 専門領域

### 1. セットアップ

```python
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
```

### 2. システムプロンプト

```python
SYSTEM_PROMPT = """あなたはPC作業ログから日報を生成するアシスタントです。

## 出力ルール

1. **本日のメイン作業** (最大3件)
   - 作業時間・重要度を考慮して選定
   - 具体的な成果物や進捗を含める
   - 「〜を実装した」「〜を調査した」「〜を修正した」など動詞で終わる

2. **知見・メモ**
   - 技術的な発見、学び、注意点を抽出
   - カテゴリ: 技術 / プロセス / その他
   - 将来役立つ情報を優先

3. **作業サマリー**
   - 1文で本日の作業を要約

## 注意事項
- 推測で情報を補完しない
- 入力データにない内容は書かない
- 簡潔で読みやすい日本語で記述
"""
```

### 3. 出力スキーマ

```python
REPORT_SCHEMA = {
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
                "required": ["title", "description"],
                "additionalProperties": False
            },
            "minItems": 1,
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
                "required": ["category", "content"],
                "additionalProperties": False
            }
        },
        "work_summary": {"type": "string"}
    },
    "required": ["main_tasks", "insights", "work_summary"],
    "additionalProperties": False
}
```

### 4. ユーザープロンプト生成

```python
def build_user_prompt(features: dict) -> str:
    """features.jsonからユーザープロンプトを生成"""
    meta = features["meta"]

    # 時間帯別作業
    time_blocks_text = "\n".join([
        f"- {b['start']}〜{b['end']}: "
        f"{', '.join([a['name'] for a in b['apps'][:2]])}"
        for b in features.get("time_blocks", [])[:8]  # 最大8ブロック
    ])

    # アプリ使用状況
    app_text = "\n".join([
        f"- {a['name']}: {a['duration_min']}分 ({a['rank']})"
        for a in features.get("app_summary", [])[:5]
    ])

    # キーワード
    keywords = features.get("global_keywords", {})
    keywords_text = ", ".join(keywords.get("top_keywords", [])[:10])
    files_text = ", ".join(keywords.get("top_files", [])[:5])

    return f"""以下は本日の作業ログの要約です。これをもとに日報を作成してください。

## 基本情報
- 日付: {meta['date']}
- 記録期間: {meta.get('first_capture', 'N/A')} 〜 {meta.get('last_capture', 'N/A')}
- キャプチャ数: {meta['capture_count']}回
- 総作業時間: {meta['total_duration_min']}分

## 時間帯別作業
{time_blocks_text}

## アプリ使用状況
{app_text}

## 主なキーワード
{keywords_text}

## 主なファイル
{files_text}
"""
```

### 5. API呼び出し

```python
def generate_summary(features: dict) -> dict:
    """LLMで日報要約を生成"""
    user_prompt = build_user_prompt(features)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "daily_report",
                "schema": REPORT_SCHEMA,
                "strict": True
            }
        },
        max_tokens=1000,
        temperature=0.3
    )

    content = response.choices[0].message.content
    return json.loads(content)
```

### 6. フォールバック処理

```python
def generate_report_with_fallback(features: dict) -> dict:
    """フォールバック付き日報生成"""
    report = {
        "meta": {
            "date": features["meta"]["date"],
            "generated_at": datetime.now().isoformat(),
            "capture_count": features["meta"]["capture_count"],
            "total_duration_min": features["meta"]["total_duration_min"],
            "first_capture": features["meta"].get("first_capture"),
            "last_capture": features["meta"].get("last_capture"),
        },
        "app_usage": features.get("app_summary", []),
        "files": features.get("global_keywords", {}).get("top_files", [])
    }

    try:
        llm_result = generate_summary(features)
        report.update(llm_result)
        report["meta"]["llm_model"] = "gpt-4o-mini"
        report["meta"]["llm_success"] = True

    except Exception as e:
        # フォールバック: テンプレート日報
        report["main_tasks"] = [{
            "title": "作業記録",
            "description": "自動要約に失敗しました。アプリ使用状況をご確認ください。"
        }]
        report["insights"] = []
        report["work_summary"] = "（自動要約に失敗しました）"
        report["meta"]["llm_success"] = False
        report["meta"]["llm_error"] = str(e)

    return report
```

### 7. プライバシー保護

```python
import re

MASK_PATTERNS = [
    # メールアドレス
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    # 電話番号
    (r'\b\d{2,4}-\d{2,4}-\d{4}\b', '[PHONE]'),
    # APIキー風の文字列
    (r'\b[A-Za-z0-9]{32,}\b', '[TOKEN]'),
    # パスワード関連
    (r'(?i)(password|secret|token|key)\s*[:=]\s*\S+', '[SENSITIVE]'),
]

def mask_sensitive_data(text: str) -> str:
    """機密情報をマスク"""
    for pattern, replacement in MASK_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text

def sanitize_features(features: dict) -> dict:
    """features.jsonの機密情報をマスク"""
    # URLをドメインのみに
    if "global_keywords" in features:
        features["global_keywords"]["top_urls"] = [
            re.sub(r'^https?://([^/]+).*', r'\1', url)
            for url in features["global_keywords"].get("top_urls", [])
        ]

    # キーワードをマスク
    if "global_keywords" in features:
        features["global_keywords"]["top_keywords"] = [
            mask_sensitive_data(kw)
            for kw in features["global_keywords"].get("top_keywords", [])
        ]

    return features
```

## コスト管理

```python
def estimate_cost(features: dict) -> float:
    """API呼び出しコストを見積もり"""
    user_prompt = build_user_prompt(features)

    # トークン概算（日本語は1文字≒1.5トークン）
    input_tokens = len(SYSTEM_PROMPT) // 4 + len(user_prompt) // 2
    output_tokens = 300  # 固定見積もり

    # gpt-4o-mini pricing (2024)
    cost = (input_tokens / 1_000_000 * 0.15) + (output_tokens / 1_000_000 * 0.60)
    return cost

# 月間コスト: 30回 × $0.0003 ≈ $0.01
```

## 関連ドキュメント

- [03-llm-flow.md](../../docs/design/03-llm-flow.md)
- [data-schema.md](../../docs/api/data-schema.md)
