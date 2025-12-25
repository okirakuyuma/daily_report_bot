#Requires -Version 5.1
#Requires -RunAsAdministrator
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

<#
.SYNOPSIS
    Daily Report Bot のタスクスケジューラ登録スクリプト

.DESCRIPTION
    ログオン時に常駐ロガーを自動起動するタスクをタスクスケジューラに登録する。

.PARAMETER Action
    実行するアクション（Register: 登録, Unregister: 解除, Status: 状態確認）

.EXAMPLE
    .\register_task.ps1 -Action Register
    .\register_task.ps1 -Action Unregister
    .\register_task.ps1 -Action Status

.NOTES
    管理者権限で実行する必要があります
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('Register', 'Unregister', 'Status')]
    [string]$Action = 'Status'
)

# ============================================================
# 設定
# ============================================================
$script:TaskName = "DailyReportBot_Logger"
$script:TaskPath = "\DailyReportBot\"
$script:Description = "Daily Report Bot - PC作業自動記録ロガー（2分間隔）"

# スクリプトパスを取得
$script:ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$script:LoggerPath = Join-Path $script:ScriptDir "logger.ps1"

# ============================================================
# 関数定義
# ============================================================

function Register-LoggerTask {
    <#
    .SYNOPSIS
        ロガータスクを登録
    #>

    Write-Host "タスクの登録を開始します..." -ForegroundColor Cyan

    # ロガースクリプトの存在確認
    if (-not (Test-Path $script:LoggerPath)) {
        Write-Error "ロガースクリプトが見つかりません: $script:LoggerPath"
        throw "ロガースクリプトが存在しません"
    }

    # 既存タスクの確認
    $existingTask = Get-ScheduledTask -TaskName $script:TaskName -TaskPath $script:TaskPath -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Warning "タスクは既に登録されています。一度削除して再登録します。"
        Unregister-ScheduledTask -TaskName $script:TaskName -TaskPath $script:TaskPath -Confirm:$false
    }

    # トリガー: ログオン時
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

    # アクション: PowerShellでロガー起動
    $actionArgs = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-WindowStyle", "Hidden",
        "-File", "`"$script:LoggerPath`""
    )
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument ($actionArgs -join " ") `
        -WorkingDirectory $script:ScriptDir

    # 設定
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Seconds 0) `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -RestartCount 3 `
        -MultipleInstances IgnoreNew

    # プリンシパル（非管理者権限で実行）
    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Limited

    # タスク登録
    try {
        Register-ScheduledTask `
            -TaskName $script:TaskName `
            -TaskPath $script:TaskPath `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description $script:Description `
            -Force | Out-Null

        Write-Host ""
        Write-Host "タスクを正常に登録しました" -ForegroundColor Green
        Write-Host ""
        Write-Host "タスク名: $script:TaskPath$script:TaskName"
        Write-Host "トリガー: ログオン時"
        Write-Host "スクリプト: $script:LoggerPath"
        Write-Host ""
        Write-Host "次回ログオン時に自動的に起動します。"
        Write-Host "今すぐ起動するには: Start-ScheduledTask -TaskName '$script:TaskName' -TaskPath '$script:TaskPath'"
    }
    catch {
        Write-Error "タスクの登録に失敗しました: $_"
        throw
    }
}

function Unregister-LoggerTask {
    <#
    .SYNOPSIS
        ロガータスクを解除
    #>

    Write-Host "タスクの解除を開始します..." -ForegroundColor Cyan

    $existingTask = Get-ScheduledTask -TaskName $script:TaskName -TaskPath $script:TaskPath -ErrorAction SilentlyContinue

    if (-not $existingTask) {
        Write-Warning "タスクが見つかりません: $script:TaskPath$script:TaskName"
        return
    }

    try {
        # タスクが実行中の場合は停止
        if ($existingTask.State -eq 'Running') {
            Write-Host "実行中のタスクを停止しています..."
            Stop-ScheduledTask -TaskName $script:TaskName -TaskPath $script:TaskPath
        }

        # タスク削除
        Unregister-ScheduledTask -TaskName $script:TaskName -TaskPath $script:TaskPath -Confirm:$false

        Write-Host ""
        Write-Host "タスクを正常に解除しました" -ForegroundColor Green
        Write-Host ""
    }
    catch {
        Write-Error "タスクの解除に失敗しました: $_"
        throw
    }
}

function Get-LoggerTaskStatus {
    <#
    .SYNOPSIS
        ロガータスクの状態を確認
    #>

    Write-Host "タスクの状態を確認しています..." -ForegroundColor Cyan
    Write-Host ""

    $existingTask = Get-ScheduledTask -TaskName $script:TaskName -TaskPath $script:TaskPath -ErrorAction SilentlyContinue

    if (-not $existingTask) {
        Write-Host "タスクは登録されていません" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "登録するには: .\register_task.ps1 -Action Register"
        return
    }

    # 詳細情報取得
    $taskInfo = Get-ScheduledTaskInfo -TaskName $script:TaskName -TaskPath $script:TaskPath -ErrorAction SilentlyContinue

    Write-Host "=== タスク情報 ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "タスク名: $script:TaskPath$script:TaskName"
    Write-Host "状態: $($existingTask.State)"
    Write-Host "説明: $script:Description"
    Write-Host ""

    if ($taskInfo) {
        Write-Host "=== 実行履歴 ===" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "最終実行時刻: $($taskInfo.LastRunTime)"
        Write-Host "最終実行結果: $($taskInfo.LastTaskResult)"
        Write-Host "次回実行時刻: $($taskInfo.NextRunTime)"
        Write-Host ""
    }

    # ロガープロセス確認（Get-CimInstanceでCommandLine取得）
    Write-Host "=== プロセス状況 ===" -ForegroundColor Cyan
    Write-Host ""
    $loggerProcess = Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" -ErrorAction SilentlyContinue |
                     Where-Object { $_.CommandLine -like "*logger.ps1*" }

    if ($loggerProcess) {
        Write-Host "ロガープロセスは実行中です" -ForegroundColor Green
        Write-Host "PID: $($loggerProcess.ProcessId)"
        if ($loggerProcess.CreationDate) {
            Write-Host "起動時刻: $($loggerProcess.CreationDate)"
        }
    }
    else {
        Write-Host "ロガープロセスは実行されていません" -ForegroundColor Yellow
    }

    Write-Host ""

    # ログファイル確認
    $logDir = Join-Path $env:LOCALAPPDATA "DailyReportBot\logs"
    if (Test-Path $logDir) {
        $today = Get-Date -Format "yyyy-MM-dd"
        $todayLog = Join-Path $logDir "$today.jsonl"

        Write-Host "=== ログ状況 ===" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "ログディレクトリ: $logDir"

        if (Test-Path $todayLog) {
            $lineCount = (Get-Content $todayLog | Measure-Object -Line).Lines
            $fileSize = (Get-Item $todayLog).Length
            Write-Host "本日のログ: $todayLog"
            Write-Host "レコード数: $lineCount"
            Write-Host "ファイルサイズ: $([math]::Round($fileSize / 1024, 2)) KB"
        }
        else {
            Write-Host "本日のログファイルはまだ作成されていません"
        }
    }
    else {
        Write-Host ""
        Write-Host "ログディレクトリが存在しません: $logDir" -ForegroundColor Yellow
    }

    Write-Host ""
}

# ============================================================
# メイン処理
# ============================================================
try {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host " Daily Report Bot - タスク管理" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""

    switch ($Action) {
        'Register' { Register-LoggerTask }
        'Unregister' { Unregister-LoggerTask }
        'Status' { Get-LoggerTaskStatus }
    }
}
catch {
    Write-Error "エラーが発生しました: $_"
    Write-Error $_.ScriptStackTrace
    exit 1
}
