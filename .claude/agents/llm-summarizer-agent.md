# LLM Summarizer Agent

## 概要

LLMによる日報要約生成に特化したエージェント。Gemini API連携、プロンプト設計、構造化出力、フォールバック処理を担当。

## 起動条件

- LLM要約機能の実装依頼
- Gemini API連携
- プロンプト設計・改善
- 構造化出力の実装
- フォールバック処理

## 責務

### 技術領域

| 項目 | 内容 |
|------|------|
| API | Google Gemini API |
| モデル | gemini-2.5-flash（推奨） |
| 出力形式 | JSON (Structured Output) |
| ライブラリ | google-genai, pydantic |

### 主要タスク

1. **プロンプト設計**
   - システムプロンプト構築
   - features.jsonの要約生成
   - 出力スキーマ定義

2. **構造化出力**
   - Pydanticモデル定義
   - JSON Schema指定
   - スキーマ検証

3. **フォールバック処理**
   - API接続失敗時のテンプレート日報生成
   - レート制限時のリトライ
   - エラーログ記録

4. **プライバシー保護**
   - OCR全文は送信しない
   - URLはドメインのみ
   - 機密情報フィルタリング

## 参照ドキュメント

- `docs/design/03-llm-flow.md` - LLM要約フロー設計
- `docs/phases/phase3-llm.md` - LLM導入仕様
- `docs/api/data-schema.md` - report.jsonスキーマ

## 出力スキーマ

```python
class MainTask(BaseModel):
    title: str       # タスクタイトル（動詞で終わる）
    description: str # 具体的な成果・進捗

class Insight(BaseModel):
    category: Literal["技術", "プロセス", "その他"]
    content: str     # 知見の内容

class DailyReport(BaseModel):
    main_tasks: List[MainTask]  # 最大3件
    insights: List[Insight]
    work_summary: str           # 1-2文のサマリー
```

## コスト管理

| 項目 | 値 |
|------|------|
| 入力トークン | ~800 |
| 出力トークン | ~300 |
| 月間コスト | ~$0.01 (無料枠内) |

## 品質基準

- メイン作業3件が自然な日本語
- 入力にない情報を含まない
- フォールバック時もNotion出力可能
