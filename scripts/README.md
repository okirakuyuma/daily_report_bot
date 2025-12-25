# Daily Report Bot - Scripts

## 概要

このディレクトリには、Daily Report Botのロガースクリプトが含まれています。

## ファイル一覧

- `logger.ps1` - PowerShell常駐ロガー（メインスクリプト）

## logger.ps1 - PowerShell常駐ロガー

### 機能

2分間隔でPC作業状態をキャプチャし、JSONL形式でログ記録を行います。

- フォアグラウンドウィンドウのタイトルとプロセス名取得
- 全画面スクリーンショット取得（一時保存）
- WinRT OCRによるテキスト抽出
- 正規表現による特徴量抽出（キーワード、URL、ファイルパス、数値）
- JSONL形式での日付別ログ保存

### 実行要件

- Windows 10/11
- PowerShell 5.1以上
- .NET Framework 4.5以上
- WinRT OCR（Windows標準機能）

### 手動実行方法

```powershell
# 管理者権限不要で実行可能
powershell.exe -ExecutionPolicy Bypass -File "C:\path\to\logger.ps1"
```

### タスクスケジューラ設定

#### 設定手順

1. タスクスケジューラを起動
2. 「タスクの作成」を選択
3. 以下のように設定:

**全般タブ**
- 名前: `DailyReportBot Logger`
- 説明: `PC作業自動記録ロガー`
- ユーザーがログオンしているときのみ実行
- 最上位の特権で実行: オフ

**トリガータブ**
- 新規トリガー作成
- タスクの開始: `ログオン時`
- 設定: `特定のユーザー`
- 有効: チェック

**操作タブ**
- 操作: `プログラムの開始`
- プログラム/スクリプト: `powershell.exe`
- 引数の追加:
```
-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\full\path\to\scripts\logger.ps1"
```

**条件タブ**
- コンピューターをAC電源で使用している場合のみタスクを開始する: オフ
- タスクを実行するためにスリープを解除する: オン（任意）

**設定タブ**
- タスクが失敗した場合の再起動の間隔: `1分`
- タスクを停止するまでの時間: `なし`（無制限）
- 既に実行中のインスタンスが存在する場合: `新しいインスタンスを開始しない`

### 出力ファイル

```
%LOCALAPPDATA%\DailyReportBot\logs\
├── 2025-01-15.jsonl
├── 2025-01-16.jsonl
└── ...
```

### レコード形式

```json
{
  "ts": "2025-01-15T14:30:00.000+09:00",
  "window_title": "daily_report_bot - Visual Studio Code",
  "process_name": "Code.exe",
  "keywords": ["Python", "def", "class", "import"],
  "urls": ["https://docs.python.org"],
  "files": ["main.py", "config.json"],
  "numbers": ["100%", "3.14"]
}
```

### エラーハンドリング

| エラー種別 | 対応 |
|-----------|------|
| ウィンドウ取得失敗 | `window_title: null`で続行、警告ログ出力 |
| スクリーンショット失敗 | OCRスキップ、ウィンドウ情報のみ記録 |
| OCR失敗 | 空配列で続行、警告ログ出力 |
| JSONL書込失敗 | 3回リトライ、失敗時エラーログ |
| 致命的エラー | プロセス終了（タスクスケジューラが再起動） |

### トラブルシューティング

#### OCRが動作しない

WinRT OCRは環境によって動作が不安定な場合があります。OCR失敗時はスキップして続行するため、ログ記録自体は継続されます。

#### ログが記録されない

1. タスクスケジューラで実行状態を確認
2. イベントビューアで PowerShell ログを確認
3. 手動実行してエラーメッセージを確認

#### メモリ使用量が増加する

スクリーンショットの一時ファイルは毎回削除されますが、何らかの理由で削除に失敗する場合があります。
`%TEMP%\DailyReportBot\` ディレクトリを定期的にクリーンアップしてください。

### 設定カスタマイズ

`logger.ps1` の以下の変数を編集することで動作をカスタマイズできます:

```powershell
$script:SamplingIntervalSec = 120  # サンプリング間隔（秒）
$script:OcrEnabled = $true         # OCR有効/無効
$script:OcrLanguage = "ja"         # OCR言語（ja/en等）
```

### セキュリティ注意事項

- スクリーンショットは一時保存後すぐに削除されます
- OCRテキストはログに保存されません（特徴量のみ抽出）
- パスワード画面等の除外機能は今後実装予定

## 開発者向け情報

### デバッグ実行

```powershell
# 詳細ログ出力
$VerbosePreference = "Continue"
.\logger.ps1
```

### テスト

各機能は独立した関数として実装されているため、個別にテスト可能です:

```powershell
# ウィンドウ情報取得テスト
. .\logger.ps1
Get-ForegroundWindowInfo

# 特徴量抽出テスト
$testText = "Python def class import https://github.com main.py 100%"
Get-ExtractedFeatures -Text $testText
```

## 参照

- [設計ドキュメント](../docs/design/01-logger-flow.md)
- [アーキテクチャ概要](../docs/architecture/overview.md)
