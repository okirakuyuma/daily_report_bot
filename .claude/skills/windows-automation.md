# Windows Automation Expert Skill

Windows環境での自動化・常駐プロセス実装に特化したスキル

## トリガー

- PowerShellスクリプト実装
- Win32 API呼び出し
- WinRT OCR実装
- タスクスケジューラ設定
- AutoHotkeyスクリプト
- Windows Toast通知

## 専門領域

### 1. Win32 API

```powershell
# ウィンドウ情報取得
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Diagnostics;

public static class Win32 {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll", CharSet=CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
}
"@
```

### 2. スクリーンショット

```powershell
Add-Type -AssemblyName System.Windows.Forms,System.Drawing

function Save-FullScreenshot([string]$path) {
    $bounds = [System.Drawing.Rectangle]::Empty
    foreach ($s in [System.Windows.Forms.Screen]::AllScreens) {
        $bounds = [System.Drawing.Rectangle]::Union($bounds, $s.Bounds)
    }
    $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
    $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $g.Dispose()
    $bmp.Dispose()
}
```

### 3. WinRT OCR

```powershell
# WinRT OCR呼び出し
Add-Type -AssemblyName System.Runtime.WindowsRuntime

function Invoke-Ocr([string]$imagePath) {
    $OcrEngine = [Windows.Media.Ocr.OcrEngine]
    $BitmapDecoder = [Windows.Graphics.Imaging.BitmapDecoder]
    $File = [Windows.Storage.StorageFile]

    $file = $File::GetFileFromPathAsync($imagePath).GetAwaiter().GetResult()
    $stream = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read).GetAwaiter().GetResult()
    $decoder = $BitmapDecoder::CreateAsync($stream).GetAwaiter().GetResult()
    $bmp = $decoder.GetSoftwareBitmapAsync().GetAwaiter().GetResult()

    $engine = $OcrEngine::TryCreateFromUserProfileLanguages()
    if ($null -eq $engine) { return $null }

    $result = $engine.RecognizeAsync($bmp).GetAwaiter().GetResult()
    return $result.Text.Trim()
}
```

### 4. タスクスケジューラ

```powershell
# ログオン時起動タスク登録
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit 0

Register-ScheduledTask `
    -TaskName "DailyReportBot_Logger" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings
```

### 5. AutoHotkey

```ahk
; Ctrl+Alt+D で日報生成
^!d::
    Run, python "%A_ScriptDir%\generate_report.py"
    return
```

### 6. Toast通知

```powershell
# BurntToast モジュール使用
Install-Module -Name BurntToast -Force

# 成功通知
New-BurntToastNotification `
    -Text "日報出力完了", "2025-01-15 / 240回キャプチャ" `
    -AppLogo "icon.png" `
    -Button (New-BTButton -Content "Notionを開く" -Arguments $notionUrl)

# 失敗通知
New-BurntToastNotification `
    -Text "日報出力失敗", $errorMessage `
    -AppLogo "icon.png" `
    -Button (New-BTButton -Content "ログを開く" -Arguments $logPath)
```

## 実装パターン

### 常駐ロガー構成

```
logger.ps1
├── 初期化
│   ├── Win32 API型定義
│   ├── .NET アセンブリ読込
│   └── ログディレクトリ作成
├── メインループ
│   ├── タイムスタンプ取得
│   ├── フォアグラウンドウィンドウ取得
│   ├── スクリーンショット取得
│   ├── OCR実行
│   ├── 特徴量抽出
│   ├── JSONL追記
│   ├── スクリーンショット削除
│   └── スリープ(120秒)
└── エラーハンドリング
    ├── OCR失敗 → スキップして続行
    ├── 書込失敗 → リトライ
    └── 致命的エラー → 終了
```

## 注意事項

- 高DPI環境ではスクリーンショットサイズに注意
- WinRT OCRは環境依存が大きい（失敗時はPsOcrモジュール代替）
- タスクスケジューラは「最上位の特権で実行」オフ
- PowerShell 5.1以上必須

## 関連ドキュメント

- [01-logger-flow.md](../../docs/design/01-logger-flow.md)
- [phase1-mvp.md](../../docs/phases/phase1-mvp.md)
