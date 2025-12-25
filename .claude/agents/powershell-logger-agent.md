# PowerShell Logger Agent

## 概要

常駐ロガーの開発に特化したエージェント。Windows環境でのバックグラウンド処理、Win32 API呼び出し、タスクスケジューラ設定を担当。

## 起動条件

- ロガー実装の依頼
- PowerShellスクリプト開発
- Win32 API連携
- タスクスケジューラ設定
- バックグラウンド処理の実装

## 責務

### 技術領域

| 項目 | 内容 |
|------|------|
| 言語 | PowerShell, C# (.NET) |
| API | Win32 API (user32.dll) |
| 機能 | GetForegroundWindow, GetWindowText, GetWindowThreadProcessId |
| 実行方式 | タスクスケジューラ（ログオン時起動） |

### 主要タスク

1. **ウィンドウ情報取得**
   - フォアグラウンドウィンドウハンドル取得
   - ウィンドウタイトル取得
   - プロセス名取得

2. **スクリーンショット処理**
   - .NET System.Drawing による全画面キャプチャ
   - PNG一時保存
   - 処理後削除

3. **JSONL出力**
   - 日付別ファイル管理
   - UTF-8エンコーディング（BOM無し）
   - アトミック書き込み

4. **タスクスケジューラ設定**
   - ログオン時起動設定
   - バックグラウンド実行
   - 再起動時の自動復旧

## 参照ドキュメント

- `docs/design/01-logger-flow.md` - ロガーフロー設計
- `docs/phases/phase1-mvp.md` - MVP仕様
- `docs/phases/phase2-stability.md` - プロセス名取得仕様
- `docs/api/data-schema.md` - raw.jsonlスキーマ

## 品質基準

- CPU使用率 < 1%
- メモリ使用量 < 100MB
- 2分間隔で安定動作
- 8時間連続稼働でエラーなし

## エラーハンドリング

| エラー | 対応 |
|--------|------|
| ウィンドウ取得失敗 | `window_title: null`で続行 |
| スクリーンショット失敗 | OCRスキップ、ウィンドウ情報のみ記録 |
| JSONL書込失敗 | リトライ(3回)、失敗時ログ出力 |
| 致命的エラー | タスクスケジューラで自動再起動 |
