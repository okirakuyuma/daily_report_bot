# Win32 API リファレンス

## 型定義

```powershell
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;

public static class Win32 {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern int GetWindowTextLength(IntPtr hWnd);

    [DllImport("user32.dll", SetLastError = true)]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder className, int maxCount);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool IsIconic(IntPtr hWnd);
}
"@
```

## フォアグラウンドウィンドウ情報取得

```powershell
function Get-ForegroundWindowInfo {
    $hWnd = [Win32]::GetForegroundWindow()
    if ($hWnd -eq [IntPtr]::Zero) { return $null }

    $length = [Win32]::GetWindowTextLength($hWnd)
    $sb = New-Object System.Text.StringBuilder($length + 1)
    [Win32]::GetWindowText($hWnd, $sb, $sb.Capacity) | Out-Null

    $processId = 0
    [Win32]::GetWindowThreadProcessId($hWnd, [ref]$processId) | Out-Null

    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue

    return [PSCustomObject]@{
        Handle      = $hWnd
        Title       = $sb.ToString()
        ProcessId   = $processId
        ProcessName = $process.ProcessName
    }
}
```

## ロック画面検出

```powershell
function Test-SessionLocked {
    $process = Get-Process -Name "LogonUI" -ErrorAction SilentlyContinue
    return $null -ne $process
}
```
