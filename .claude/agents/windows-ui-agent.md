# Windows UI Agent

## 概要

Windows固有のUI機能に特化したエージェント。Toast通知、システムトレイ、設定UIを担当。

## 起動条件

- Toast通知の実装依頼
- システムトレイアイコン
- 設定UI開発
- Windows固有UI機能

## 責務

### 技術領域

| 項目 | 内容 |
|------|------|
| Toast | BurntToast (PowerShell) / win10toast (Python) |
| トレイ | System.Windows.Forms.NotifyIcon |
| 設定UI | WPF (.NET 6) / Electron |
| インストーラ | Inno Setup / WiX |

### 主要タスク

1. **Toast通知**
   - 成功通知（NotionページURL付き）
   - 失敗通知（エラー内容）
   - クリックアクション（ページを開く/ログフォルダを開く）
   - 表示時間設定

2. **システムトレイ（Phase 5）**
   - トレイアイコン表示
   - コンテキストメニュー
   - 本日の統計表示
   - 一時停止/再開

3. **設定UI（Phase 5）**
   - サンプリング間隔設定
   - 除外アプリ設定
   - Notion接続テスト
   - LLM APIキー設定

## 参照ドキュメント

- `docs/design/04-notion-flow.md` - Toast通知設計
- `docs/phases/phase2-stability.md` - Toast強化仕様
- `docs/phases/phase5-production.md` - 設定UI仕様

## Toast実装例

```python
# 成功通知
def notify_success(page_url: str, date: str, capture_count: int):
    toaster.show_toast(
        title="✅ 日報出力完了",
        msg=f"{date} / {capture_count}回キャプチャ",
        duration=5,
        callback_on_click=lambda: webbrowser.open(page_url)
    )

# 失敗通知
def notify_failure(error: str, log_path: str):
    toaster.show_toast(
        title="❌ 日報出力失敗",
        msg=error[:50],
        duration=10,
        callback_on_click=lambda: os.startfile(log_path)
    )
```

## 品質基準

- Toast表示成功
- クリックでNotion/ログフォルダが開く
- 設定変更が即座に反映
