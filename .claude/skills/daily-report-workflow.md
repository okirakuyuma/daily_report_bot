# Daily Report Workflow Skill

日報生成ワークフロー全体を統括するスキル

## トリガー

- `/drb:generate` - 日報生成
- `/drb:status` - ロガー状態確認
- `/drb:setup` - 初期セットアップ
- `/drb:test` - 各コンポーネントテスト

## コマンド

### /drb:generate

日報生成を実行

```bash
# 当日
python generate_report.py

# 日付指定
python generate_report.py --date 2025-01-15
```

**フロー:**
```
1. raw.jsonl 読込
2. 集計処理 → features.json
3. LLM要約 → report.json
4. Notion出力
5. Toast通知
```

### /drb:status

システム状態を確認

```powershell
# ロガー状態
Get-ScheduledTask -TaskName "DailyReportBot_Logger" | Select-Object State

# 本日のログ件数
$logFile = "$env:LOCALAPPDATA\DailyReportBot\logs\$(Get-Date -Format 'yyyy-MM-dd').jsonl"
if (Test-Path $logFile) {
    (Get-Content $logFile | Measure-Object -Line).Lines
}
```

### /drb:setup

初期セットアップを実行

```
1. 依存関係インストール
   - Python パッケージ
   - PowerShell モジュール (BurntToast)
   - AutoHotkey

2. ディレクトリ作成
   - %LOCALAPPDATA%/DailyReportBot/logs
   - %LOCALAPPDATA%/DailyReportBot/features
   - %LOCALAPPDATA%/DailyReportBot/reports

3. 環境変数設定
   - NOTION_TOKEN
   - NOTION_DATABASE_ID
   - OPENAI_API_KEY

4. タスクスケジューラ登録
   - DailyReportBot_Logger (ログオン時起動)

5. ショートカット設定
   - AutoHotkey スクリプト配置
```

### /drb:test

各コンポーネントをテスト

```
1. ロガーテスト
   - ウィンドウ取得
   - スクリーンショット
   - OCR

2. 集計テスト
   - JSONL読込
   - セッション化
   - features.json生成

3. LLMテスト
   - API接続
   - 要約生成

4. Notionテスト
   - 認証確認
   - テストページ作成/削除
```

## アーキテクチャ

```
daily_report_bot/
├── logger/                    # 常駐ロガー
│   ├── logger.ps1            # メインスクリプト
│   ├── win32.ps1             # Win32 API
│   ├── screenshot.ps1        # スクショ取得
│   └── ocr.ps1               # OCR処理
├── generator/                 # 日報生成
│   ├── __init__.py
│   ├── main.py               # エントリポイント
│   ├── aggregator.py         # 集計処理
│   ├── summarizer.py         # LLM要約
│   └── notion_writer.py      # Notion出力
├── shared/                    # 共通
│   ├── config.py             # 設定管理
│   ├── models.py             # データモデル
│   └── toast.py              # 通知
├── scripts/                   # セットアップ
│   ├── setup.ps1             # 初期セットアップ
│   ├── install_task.ps1      # タスク登録
│   └── hotkey.ahk            # AutoHotkey
└── tests/                     # テスト
    ├── test_logger.py
    ├── test_aggregator.py
    ├── test_summarizer.py
    └── test_notion.py
```

## 実装フェーズ

### Phase 1: MVP

```
[x] プロジェクト構成
[x] ドキュメント作成
[ ] logger.ps1 実装
[ ] aggregator.py 実装
[ ] notion_writer.py 実装 (LLMなし)
[ ] toast.py 実装
[ ] setup.ps1 実装
```

### Phase 2: 安定運用

```
[ ] プロセス名取得追加
[ ] セッション化実装
[ ] 時間ブロック生成
[ ] 再生成機能 (--date)
[ ] 直近除外オプション
```

### Phase 3: LLM導入

```
[ ] summarizer.py 実装
[ ] プロンプト設計
[ ] 構造化出力
[ ] フォールバック
[ ] プライバシー処理
```

## サブエージェント連携

| タスク | サブエージェント | スキル |
|--------|----------------|--------|
| ロガー実装 | - | windows-automation |
| 集計実装 | python-expert | - |
| LLM実装 | python-expert | llm-integration |
| Notion実装 | python-expert | notion-integration |
| テスト | quality-engineer | /sc:test |
| レビュー | code-reviewer | - |
| Git操作 | github-workflow-manager | /sc:git |

## クイックスタート

```bash
# 1. セットアップ
/drb:setup

# 2. ロガー開始確認
/drb:status

# 3. 数時間作業後、日報生成
/drb:generate

# 4. Notionで確認
```

## トラブルシューティング

### ロガーが動かない

```powershell
# タスク状態確認
Get-ScheduledTask -TaskName "DailyReportBot_Logger"

# 手動実行テスト
powershell -File "C:\path\to\logger.ps1"

# ログ確認
Get-Content "$env:LOCALAPPDATA\DailyReportBot\logs\error.log"
```

### OCRが失敗する

```
1. WinRT OCR環境確認
2. PsOcrモジュールで代替
3. OCR無効化して続行
```

### Notion接続エラー

```
1. NOTION_TOKEN確認
2. データベース共有設定確認
3. ネットワーク確認
```

## 関連ドキュメント

- [README.md](../../docs/README.md)
- [architecture/overview.md](../../docs/architecture/overview.md)
- [phases/phase1-mvp.md](../../docs/phases/phase1-mvp.md)
