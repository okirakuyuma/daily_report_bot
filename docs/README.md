# Daily Report Bot - 仕様書

Windows向けPC作業自動記録・日報生成システム

## ドキュメント構成

```
docs/
├── README.md                     # 本ファイル（ドキュメント索引）
├── architecture/
│   └── overview.md               # システムアーキテクチャ概要
├── design/
│   ├── 01-logger-flow.md         # 常駐ロガーフロー設計
│   ├── 02-aggregation-flow.md    # 集計処理フロー設計
│   ├── 03-llm-flow.md            # LLM要約フロー設計
│   └── 04-notion-flow.md         # Notion出力フロー設計
├── phases/
│   ├── phase1-mvp.md             # Phase 1: MVP仕様
│   ├── phase2-stability.md       # Phase 2: 安定運用仕様
│   ├── phase3-llm.md             # Phase 3: LLM導入仕様
│   ├── phase4-precision.md       # Phase 4: 高精度化仕様
│   └── phase5-production.md      # Phase 5: プロダクト化仕様
└── api/
    ├── data-schema.md            # データスキーマ定義
    └── notion-api.md             # Notion API仕様
```

## システム概要

### 目的

PC作業を自動で記録し、日次レポート（日報）を生成してNotionに保存する。

### 主要機能

1. **常駐ロガー**: 2分間隔でアクティブウィンドウ情報・スクリーンショット・OCRを取得
2. **日報生成**: ショートカットキー押下でログを集計し、LLMで要約
3. **Notion出力**: 日報をNotionページとして作成・更新
4. **通知**: Windows Toastで成功/失敗を通知

### 技術スタック

| コンポーネント | 技術 |
|--------------|------|
| 常駐ロガー | PowerShell / C# (.NET) |
| OCR | Windows.Media.Ocr (WinRT) |
| ショートカット | AutoHotkey |
| 日報生成 | Python |
| LLM | OpenAI API |
| 出力先 | Notion API |
| 通知 | Windows Toast (BurntToast) |

## クイックリファレンス

### ワークフロー

```
[常駐ロガー] → raw.jsonl
     ↓ (ショートカット押下)
[集計処理] → features.json
     ↓
[LLM要約] → report.json
     ↓
[Notion出力] → Notionページ + Toast通知
```

### 開発フェーズ

| Phase | 名称 | 主要機能 |
|-------|------|---------|
| 1 | MVP | ログ収集 → 集計 → Notion出力（LLMなし） |
| 2 | 安定運用 | セッション化・再生成・Toast強化 |
| 3 | LLM導入 | 構造化要約・画像例再現 |
| 4 | 高精度化 | ファイル検出・メモ抽出精度向上 |
| 5 | プロダクト化 | 設定UI・監査・週次/月次レポート |
