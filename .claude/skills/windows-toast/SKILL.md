# Windows Toast Notification Skill

Windows Toast通知を表示するスキル（PowerShell/Python）。

## Triggers

- Toast通知、Windows通知、デスクトップ通知
- 日報生成完了/失敗時の通知実装

## 基本情報

| 項目 | 内容 |
|------|------|
| 対象OS | Windows 10/11 |
| 方式 | BurntToast (PowerShell) / win10toast (Python) |
| 機能 | テキスト、ボタン、クリックアクション |

---

## PowerShell（BurntToast）

### インストール

```powershell
Install-Module -Name BurntToast -Force -Scope CurrentUser
```

### 基本的な通知

```powershell
Import-Module BurntToast

# シンプルな通知
New-BurntToastNotification -Text "日報出力完了", "本日の日報がNotionに保存されました"

# アイコン付き
New-BurntToastNotification `
    -Text "✅ 日報出力完了", "2025-01-15 / 240回キャプチャ" `
    -AppLogo "C:\path\to\icon.png"
```

### クリックでURL開く

```powershell
function Show-SuccessToast {
    param(
        [string]$Title = "日報出力完了",
        [string]$Message,
        [string]$Url
    )

    # ボタン作成
    $button = New-BTButton -Content "Notionで開く" -Arguments $Url

    # アクション作成
    $actions = New-BTAction -Buttons $button

    # Toast表示
    New-BurntToastNotification `
        -Text $Title, $Message `
        -Button $button `
        -Duration Short
}

# 使用例
Show-SuccessToast `
    -Title "✅ 日報出力完了" `
    -Message "2025-01-15 / 240回キャプチャ" `
    -Url "https://notion.so/page-id"
```

### エラー通知

```powershell
function Show-ErrorToast {
    param(
        [string]$Title = "日報出力失敗",
        [string]$Message,
        [string]$LogPath
    )

    # ログを開くボタン
    $button = New-BTButton -Content "ログを確認" -Arguments $LogPath

    # 警告音付き
    $audio = New-BTAudio -Source 'ms-winsoundevent:Notification.Default'

    New-BurntToastNotification `
        -Text "❌ $Title", $Message `
        -Button $button `
        -Sound $audio `
        -Duration Long
}

# 使用例
Show-ErrorToast `
    -Title "日報出力失敗" `
    -Message "Notion API接続エラー" `
    -LogPath "C:\logs\error.log"
```

### 進捗通知

```powershell
function Show-ProgressToast {
    param(
        [string]$Title,
        [string]$Status,
        [double]$Progress  # 0.0 - 1.0
    )

    $progressBar = New-BTProgressBar `
        -Status $Status `
        -Value $Progress

    New-BurntToastNotification `
        -Text $Title `
        -ProgressBar $progressBar `
        -UniqueIdentifier "DailyReportProgress"
}

# 使用例（更新可能）
Show-ProgressToast -Title "日報生成中..." -Status "ログ読込" -Progress 0.25
Start-Sleep -Seconds 2
Show-ProgressToast -Title "日報生成中..." -Status "LLM要約" -Progress 0.5
Start-Sleep -Seconds 2
Show-ProgressToast -Title "日報生成中..." -Status "Notion出力" -Progress 0.75
Start-Sleep -Seconds 2
Show-ProgressToast -Title "日報生成中..." -Status "完了" -Progress 1.0
```

---

## Python（win10toast / win10toast-click）

### インストール

```bash
pip install win10toast-click
```

### 基本的な通知

```python
from win10toast_click import ToastNotifier

toaster = ToastNotifier()

# シンプルな通知
toaster.show_toast(
    title="✅ 日報出力完了",
    msg="2025-01-15 / 240回キャプチャ",
    duration=5,
    threaded=True
)
```

### クリックでURL開く

```python
import webbrowser
from win10toast_click import ToastNotifier

def open_url(url: str):
    def callback():
        webbrowser.open(url)
    return callback

def show_success_toast(date: str, capture_count: int, page_url: str):
    toaster = ToastNotifier()

    toaster.show_toast(
        title="✅ 日報出力完了",
        msg=f"{date} / {capture_count}回キャプチャ",
        duration=5,
        callback_on_click=open_url(page_url),
        threaded=True
    )

# 使用例
show_success_toast(
    date="2025-01-15",
    capture_count=240,
    page_url="https://notion.so/page-id"
)
```

### エラー通知

```python
import os
from win10toast_click import ToastNotifier

def open_file(path: str):
    def callback():
        os.startfile(path)
    return callback

def show_error_toast(error_message: str, log_path: str):
    toaster = ToastNotifier()

    toaster.show_toast(
        title="❌ 日報出力失敗",
        msg=error_message[:50],  # 長すぎる場合は切り詰め
        duration=10,
        callback_on_click=open_file(log_path),
        threaded=True
    )

# 使用例
show_error_toast(
    error_message="Notion API connection timeout",
    log_path=r"C:\logs\error.log"
)
```

---

## 日報生成統合例（Python）

```python
import webbrowser
import os
from datetime import datetime
from win10toast_click import ToastNotifier
from typing import Optional

class NotificationService:
    def __init__(self):
        self.toaster = ToastNotifier()

    def notify_success(
        self,
        date: str,
        capture_count: int,
        page_url: str,
        duration_min: int
    ):
        """日報生成成功通知"""
        msg = f"{date} / {capture_count}回キャプチャ / {duration_min}分"

        self.toaster.show_toast(
            title="✅ 日報出力完了",
            msg=msg,
            duration=5,
            callback_on_click=lambda: webbrowser.open(page_url),
            threaded=True
        )

    def notify_failure(
        self,
        error: str,
        log_path: Optional[str] = None
    ):
        """日報生成失敗通知"""
        callback = None
        if log_path and os.path.exists(log_path):
            callback = lambda: os.startfile(log_path)

        self.toaster.show_toast(
            title="❌ 日報出力失敗",
            msg=error[:100],
            duration=10,
            callback_on_click=callback,
            threaded=True
        )

    def notify_partial_success(
        self,
        date: str,
        local_path: str
    ):
        """部分成功（ローカル保存）通知"""
        self.toaster.show_toast(
            title="⚠️ 日報をローカルに保存",
            msg=f"{date} / Notion接続失敗、ローカルに保存しました",
            duration=10,
            callback_on_click=lambda: os.startfile(os.path.dirname(local_path)),
            threaded=True
        )

# 使用例
notifier = NotificationService()

# 成功時
notifier.notify_success(
    date="2025-01-15",
    capture_count=240,
    page_url="https://notion.so/xxx",
    duration_min=478
)

# 失敗時
notifier.notify_failure(
    error="Notion API rate limited",
    log_path=r"C:\DailyReportBot\logs\error.log"
)
```

---

## Windows Native API（高度な制御）

### .NET直接使用

```powershell
# WinRT ToastNotification使用
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null

$AppId = "DailyReportBot"

$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>✅ 日報出力完了</text>
            <text>2025-01-15 / 240回キャプチャ</text>
        </binding>
    </visual>
    <actions>
        <action content="Notionで開く" arguments="https://notion.so/xxx" activationType="protocol"/>
        <action content="閉じる" arguments="dismiss" activationType="system"/>
    </actions>
    <audio src="ms-winsoundevent:Notification.Default"/>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)

$toast = New-Object Windows.UI.Notifications.ToastNotification($xml)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($AppId)
$notifier.Show($toast)
```

---

## 設定パラメータ

```json
{
  "toast": {
    "enabled": true,
    "duration_success": 5,
    "duration_failure": 10,
    "open_page_on_click": true,
    "sound_enabled": true,
    "progress_notifications": false
  }
}
```

---

## トラブルシューティング

| 問題 | 原因 | 解決策 |
|------|------|--------|
| 通知が表示されない | 通知設定OFF | Windows設定で有効化 |
| クリックが反応しない | スレッド終了 | `threaded=True`使用 |
| アイコンが表示されない | パスが無効 | 絶対パス使用 |
| 音が鳴らない | サウンド設定 | Windows設定確認 |

### 通知許可確認

```powershell
# 通知設定確認
Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Notifications\Settings\*" |
    Select-Object PSChildName, Enabled
```

---

## 依存関係

### PowerShell
```powershell
# BurntToast
Install-Module -Name BurntToast -Force
```

### Python
```bash
# 基本
pip install win10toast

# クリック対応版（推奨）
pip install win10toast-click
```
