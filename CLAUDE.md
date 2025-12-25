# Daily Report Bot - プロジェクト設定

Windows向けPC作業自動記録・日報生成システム

---

## 言語設定 / Language Settings

- 返答: 日本語
- コード: 英語（コメントは日本語可）

---

## 重要な制約

| 制約 | 説明 |
|------|------|
| `src/lib/`編集禁止 | 共通ライブラリは変更不可。handler.js側で対処 |
| handlerのみS3操作 | S3保存はhandler.jsのみで実装 |

---

## プロジェクト概要

| 項目 | 内容 |
|------|------|
| 目的 | PC作業を自動記録し、日報をNotionに出力 |
| 対象OS | Windows 10/11 |
| 主要言語 | PowerShell (ロガー), Python (生成) |

```
daily_report_bot/
├── docs/                      # 仕様書
│   ├── architecture/         # アーキテクチャ
│   ├── design/               # フロー設計
│   └── phases/               # フェーズ仕様
├── logger/                    # 常駐ロガー (PowerShell)
├── generator/                 # 日報生成 (Python)
├── shared/                    # 共通モジュール
├── scripts/                   # セットアップスクリプト
└── tests/                     # テスト
```

---

## スキル一覧

### プロジェクトスキル

| コマンド | 説明 |
|----------|------|
| `/drb:generate` | 日報生成を実行 |
| `/drb:status` | ロガー状態確認 |
| `/drb:setup` | 初期セットアップ |
| `/drb:test` | コンポーネントテスト |

### 技術スキル

| スキル | 用途 |
|--------|------|
| windows-automation | PowerShell, Win32 API, OCR, タスクスケジューラ |
| notion-integration | Notion API, ブロック生成 |
| llm-integration | OpenAI API, プロンプト設計 |
| daily-report-workflow | ワークフロー統括 |

---

## プロジェクト専用エージェント

`.claude/agents/` に定義されたプロジェクト固有のエージェント:

| エージェント | 起動条件 | 担当領域 |
|--------------|----------|----------|
| `powershell-logger-agent` | ロガー実装依頼 | Win32 API, Task Scheduler, JSONL出力 |
| `python-aggregator-agent` | 集計処理依頼 | セッション化, 時間ブロック, アプリ集計 |
| `llm-summarizer-agent` | LLM要約依頼 | Gemini API, 構造化出力, フォールバック |
| `notion-writer-agent` | Notion出力依頼 | ページ作成/更新, ブロック生成 |
| `windows-ui-agent` | Toast/UI依頼 | BurntToast, システムトレイ, 設定UI |
| `ocr-extractor-agent` | OCR/抽出依頼 | WinRT OCR, 正規表現, 特徴量抽出 |

---

## 汎用サブエージェント

| エージェント | 用途 |
|--------------|------|
| `python-expert` | Python実装全般 |
| `quality-engineer` | テスト戦略・品質保証 |
| `security-engineer` | APIキー管理、プライバシー |
| `code-reviewer` | コードレビュー |
| `github-workflow-manager` | Issue/PR管理 |

---

## 開発フェーズ

| Phase | 状態 | 内容 |
|-------|------|------|
| 1. MVP | 🔵 進行中 | ログ収集 → 集計 → Notion出力 |
| 2. 安定運用 | ⚪ 未着手 | セッション化・再生成・Toast強化 |
| 3. LLM導入 | ⚪ 未着手 | 構造化要約・画像例再現 |
| 4. 高精度化 | ⚪ 未着手 | ファイル検出・メモ抽出精度向上 |
| 5. プロダクト化 | ⚪ 未着手 | 設定UI・監査・週次レポート |

---

## 環境変数

```bash
NOTION_TOKEN=secret_xxxxx
NOTION_DATABASE_ID=xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxxxx
```

---

## Slack通知

| 通知タイプ | タイミング |
|------------|------------|
| エラー通知 | ロガー異常終了、API失敗時 |
| 日報生成完了 | 日報のNotion投稿成功時 |
| 警告通知 | データ欠損、異常値検出時 |

**実装パターン:**
```python
# エラー時
await post_error_slack(error_message, context)

# 成功時
await post_success_slack(report_url)
```

---

## コーディング規約

### PowerShell

- `Set-StrictMode -Version Latest`
- エラー時: 続行可能ならWarn、不可ならThrow
- 関数名: 動詞-名詞形式 (例: `Get-WindowTitle`, `Save-Screenshot`)

### Python

- Python 3.10+
- Type hints必須
- フォーマット: Black + isort + mypy
- テスト: pytest

---

## 設計判断

| 決定 | 理由 |
|------|------|
| OCR全文はLLMに送信しない | プライバシー保護 |
| フォールバック必須 | LLM失敗時もテンプレート日報を出力 |
| 2分間隔 | 粒度とリソースのバランス |
| ショートカットトリガー | ユーザー制御を優先 |

---

## 参照ドキュメント

- [仕様書トップ](docs/README.md)
- [アーキテクチャ概要](docs/architecture/overview.md)
- [Phase 1 MVP仕様](docs/phases/phase1-mvp.md)
- [データスキーマ](docs/api/data-schema.md)
