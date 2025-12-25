# PowerShell Win32 API Skill

PowerShellからWin32 APIを呼び出してウィンドウ・プロセス情報を取得するスキル。

## Triggers

- Win32 API、ウィンドウ取得、プロセス情報、フォアグラウンドウィンドウ
- 常駐ロガーの実装時

## 基本情報

| 項目 | 内容 |
|------|------|
| 対象OS | Windows 10/11 |
| 実行環境 | PowerShell 5.1+ / PowerShell 7+ |
| 必要権限 | 標準ユーザー（管理者不要） |

---

## Win32 API 型定義

### 基本的なAPI定義

```powershell
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Diagnostics;

public static class Win32 {
    // フォアグラウンドウィンドウのハンドル取得
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    // ウィンドウタイトル取得
    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    // ウィンドウタイトルの長さ取得
    [DllImport("user32.dll", SetLastError = true)]
    public static extern int GetWindowTextLength(IntPtr hWnd);

    // ウィンドウのプロセスID取得
    [DllImport("user32.dll", SetLastError = true)]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

    // ウィンドウクラス名取得
    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder className, int maxCount);

    // ウィンドウの表示状態確認
    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    // ウィンドウが最小化されているか
    [DllImport("user32.dll")]
    public static extern bool IsIconic(IntPtr hWnd);

    // ウィンドウの矩形取得
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
}

[StructLayout(LayoutKind.Sequential)]
public struct RECT {
    public int Left;
    public int Top;
    public int Right;
    public int Bottom;
}
"@
```

---

## 基本操作

### フォアグラウンドウィンドウ情報取得

```powershell
function Get-ForegroundWindowInfo {
    # ハンドル取得
    $hWnd = [Win32]::GetForegroundWindow()

    if ($hWnd -eq [IntPtr]::Zero) {
        return $null
    }

    # タイトル取得
    $length = [Win32]::GetWindowTextLength($hWnd)
    $sb = New-Object System.Text.StringBuilder($length + 1)
    [Win32]::GetWindowText($hWnd, $sb, $sb.Capacity) | Out-Null
    $title = $sb.ToString()

    # プロセスID取得
    $processId = 0
    [Win32]::GetWindowThreadProcessId($hWnd, [ref]$processId) | Out-Null

    # プロセス情報取得
    $process = $null
    $processName = $null
    try {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        $processName = $process.ProcessName
    } catch {}

    # クラス名取得
    $classNameSb = New-Object System.Text.StringBuilder(256)
    [Win32]::GetClassName($hWnd, $classNameSb, 256) | Out-Null
    $className = $classNameSb.ToString()

    return [PSCustomObject]@{
        Handle      = $hWnd
        Title       = $title
        ProcessId   = $processId
        ProcessName = $processName
        ClassName   = $className
        IsVisible   = [Win32]::IsWindowVisible($hWnd)
        IsMinimized = [Win32]::IsIconic($hWnd)
    }
}
```

### 使用例

```powershell
$windowInfo = Get-ForegroundWindowInfo
Write-Host "Title: $($windowInfo.Title)"
Write-Host "Process: $($windowInfo.ProcessName)"
```

---

## ウィンドウ列挙

### 全ウィンドウ取得

```powershell
Add-Type @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class WindowEnumerator {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    public static List<IntPtr> Windows = new List<IntPtr>();

    public static bool EnumCallback(IntPtr hWnd, IntPtr lParam) {
        if (IsWindowVisible(hWnd)) {
            StringBuilder sb = new StringBuilder(256);
            GetWindowText(hWnd, sb, 256);
            if (sb.Length > 0) {
                Windows.Add(hWnd);
            }
        }
        return true;
    }

    public static IntPtr[] GetVisibleWindows() {
        Windows.Clear();
        EnumWindows(EnumCallback, IntPtr.Zero);
        return Windows.ToArray();
    }
}
"@

function Get-AllVisibleWindows {
    $handles = [WindowEnumerator]::GetVisibleWindows()

    $windows = @()
    foreach ($hWnd in $handles) {
        $sb = New-Object System.Text.StringBuilder(256)
        [Win32]::GetWindowText($hWnd, $sb, 256) | Out-Null

        $processId = 0
        [Win32]::GetWindowThreadProcessId($hWnd, [ref]$processId) | Out-Null

        $processName = $null
        try {
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            $processName = $process.ProcessName
        } catch {}

        $windows += [PSCustomObject]@{
            Handle      = $hWnd
            Title       = $sb.ToString()
            ProcessId   = $processId
            ProcessName = $processName
        }
    }

    return $windows
}
```

---

## 常駐ロガー実装例

### メインループ

```powershell
# 設定
$SamplingIntervalSec = 120
$LogDir = "$env:LOCALAPPDATA\DailyReportBot\logs"
$ExcludedProcesses = @("LockApp", "ScreenClippingHost")

# ログディレクトリ作成
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# メインループ
while ($true) {
    try {
        $timestamp = Get-Date -Format "o"
        $windowInfo = Get-ForegroundWindowInfo

        # 除外プロセスチェック
        if ($windowInfo -and $windowInfo.ProcessName -notin $ExcludedProcesses) {
            $record = [PSCustomObject]@{
                ts           = $timestamp
                window_title = $windowInfo.Title
                process_name = $windowInfo.ProcessName
                keywords     = @()
                urls         = @()
                files        = @()
            }

            # JSONLファイルに追記
            $logFile = Join-Path $LogDir "$(Get-Date -Format 'yyyy-MM-dd').jsonl"
            $record | ConvertTo-Json -Compress | Add-Content -Path $logFile -Encoding UTF8
        }
    }
    catch {
        Write-Warning "Error: $_"
    }

    Start-Sleep -Seconds $SamplingIntervalSec
}
```

### タスクスケジューラ登録

```powershell
# タスク作成
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"C:\Scripts\logger.ps1`""

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask `
    -TaskName "DailyReportBot-Logger" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Daily Report Bot Background Logger"
```

---

## スクリーンショット取得

```powershell
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Get-Screenshot {
    param(
        [string]$OutputPath
    )

    # 画面サイズ取得
    $screen = [System.Windows.Forms.Screen]::PrimaryScreen
    $bounds = $screen.Bounds

    # ビットマップ作成
    $bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)

    # 画面キャプチャ
    $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)

    # 保存
    $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)

    # クリーンアップ
    $graphics.Dispose()
    $bitmap.Dispose()

    return $OutputPath
}

# 使用例
$screenshotPath = Get-Screenshot -OutputPath "$env:TEMP\screenshot.png"
```

---

## マルチモニター対応

```powershell
function Get-AllScreensScreenshot {
    param(
        [string]$OutputPath
    )

    # 全画面の範囲を計算
    $screens = [System.Windows.Forms.Screen]::AllScreens

    $minX = ($screens | Measure-Object -Property { $_.Bounds.X } -Minimum).Minimum
    $minY = ($screens | Measure-Object -Property { $_.Bounds.Y } -Minimum).Minimum
    $maxX = ($screens | Measure-Object -Property { $_.Bounds.X + $_.Bounds.Width } -Maximum).Maximum
    $maxY = ($screens | Measure-Object -Property { $_.Bounds.Y + $_.Bounds.Height } -Maximum).Maximum

    $width = $maxX - $minX
    $height = $maxY - $minY

    # ビットマップ作成
    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)

    # キャプチャ
    $graphics.CopyFromScreen($minX, $minY, 0, 0, [System.Drawing.Size]::new($width, $height))

    # 保存
    $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)

    $graphics.Dispose()
    $bitmap.Dispose()

    return $OutputPath
}
```

---

## エラーハンドリング

### ロック画面検出

```powershell
function Test-SessionLocked {
    $process = Get-Process -Name "LogonUI" -ErrorAction SilentlyContinue
    return $null -ne $process
}

# 使用例
if (Test-SessionLocked) {
    Write-Host "Screen is locked, skipping capture"
    return
}
```

### 全画面アプリ検出

```powershell
function Test-FullscreenApp {
    $hWnd = [Win32]::GetForegroundWindow()

    $rect = New-Object RECT
    [Win32]::GetWindowRect($hWnd, [ref]$rect) | Out-Null

    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds

    return ($rect.Left -eq $screen.Left -and
            $rect.Top -eq $screen.Top -and
            $rect.Right -eq $screen.Right -and
            $rect.Bottom -eq $screen.Bottom)
}
```

---

## 設定パラメータ

```json
{
  "logger": {
    "sampling_interval_sec": 120,
    "excluded_processes": ["LockApp", "ScreenClippingHost", "SearchApp"],
    "excluded_window_titles": ["*password*", "*credential*", "*secret*"],
    "log_dir": "%LOCALAPPDATA%\\DailyReportBot\\logs",
    "temp_dir": "%TEMP%\\DailyReportBot",
    "log_retention_days": 30
  }
}
```

---

## トラブルシューティング

| 問題 | 原因 | 解決策 |
|------|------|--------|
| ウィンドウタイトルが空 | 権限不足/UWPアプリ | 管理者権限で実行 |
| プロセス名がnull | アクセス拒否 | SilentlyContinue で処理 |
| スクリーンショット真っ黒 | ハードウェアアクセラレーション | GDI+で再取得 |
| 高DPIで位置ずれ | DPI非対応 | SetProcessDPIAware呼び出し |
