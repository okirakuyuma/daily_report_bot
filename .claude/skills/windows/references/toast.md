# Toast通知 リファレンス

## PowerShell（BurntToast）

### インストール

```powershell
Install-Module -Name BurntToast -Force -Scope CurrentUser
```

### 成功通知

```powershell
function Show-SuccessToast {
    param([string]$Message, [string]$Url)

    New-BurntToastNotification `
        -Text "✅ 日報出力完了", $Message `
        -Button (New-BTButton -Content "Notionで開く" -Arguments $Url) `
        -Duration Short
}
```

### エラー通知

```powershell
function Show-ErrorToast {
    param([string]$Message, [string]$LogPath)

    New-BurntToastNotification `
        -Text "❌ 日報出力失敗", $Message `
        -Button (New-BTButton -Content "ログを確認" -Arguments $LogPath) `
        -Sound (New-BTAudio -Source 'ms-winsoundevent:Notification.Default') `
        -Duration Long
}
```

## Python（win10toast-click）

```bash
pip install win10toast-click
```

```python
import webbrowser
from win10toast_click import ToastNotifier

toaster = ToastNotifier()

def show_success(date: str, count: int, url: str):
    toaster.show_toast(
        title="✅ 日報出力完了",
        msg=f"{date} / {count}回キャプチャ",
        duration=5,
        callback_on_click=lambda: webbrowser.open(url),
        threaded=True
    )
```

## トラブルシューティング

| 問題 | 解決策 |
|------|--------|
| 通知が表示されない | Windows設定で通知を有効化 |
| クリックが反応しない | `threaded=True`使用 |
