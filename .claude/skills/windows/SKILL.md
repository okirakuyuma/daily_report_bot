---
name: windows-automation
description: Windows環境での自動化・常駐プロセス実装。PowerShellスクリプト、Win32 API、WinRT OCR、タスクスケジューラ、Toast通知、スクリーンショット取得時に使用。
---

# Windows Automation

Windows環境での自動化・常駐プロセス実装スキル。

## 対応領域

| 領域 | 用途 | 詳細 |
|------|------|------|
| Win32 API | ウィンドウ・プロセス情報取得 | [win32-api.md](references/win32-api.md) |
| OCR | 画像からテキスト抽出 | [ocr.md](references/ocr.md) |
| Toast | デスクトップ通知 | [toast.md](references/toast.md) |
| Screenshot | 画面キャプチャ | [screenshot.md](references/screenshot.md) |

## クイックスタート

### フォアグラウンドウィンドウ取得

```powershell
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;

public static class Win32 {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll", CharSet=CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
}
"@

$hWnd = [Win32]::GetForegroundWindow()
$sb = New-Object System.Text.StringBuilder(256)
[Win32]::GetWindowText($hWnd, $sb, 256) | Out-Null
$title = $sb.ToString()
```

### タスクスケジューラ登録

```powershell
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask -TaskName "DailyReportBot-Logger" `
    -Action $action -Trigger $trigger -Settings $settings
```

### Toast通知（BurntToast）

```powershell
Install-Module -Name BurntToast -Force -Scope CurrentUser

New-BurntToastNotification `
    -Text "✅ 日報出力完了", "2025-01-15 / 240回キャプチャ" `
    -Button (New-BTButton -Content "Notionで開く" -Arguments $notionUrl)
```

## 常駐ロガー構成

```
logger.ps1
├── 初期化（Win32 API型定義、ログディレクトリ作成）
├── メインループ（120秒間隔）
│   ├── フォアグラウンドウィンドウ取得
│   ├── スクリーンショット → OCR → 特徴量抽出
│   ├── JSONL追記
│   └── スクリーンショット削除
└── エラーハンドリング
```

## 注意事項

- PowerShell 5.1以上必須
- 高DPI環境ではスクリーンショットサイズに注意
- WinRT OCRは環境依存が大きい（失敗時はスキップ）
- タスクスケジューラは「最上位の特権で実行」オフ
