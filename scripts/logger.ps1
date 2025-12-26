#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

<#
.SYNOPSIS
    Daily Report Bot - PowerShell常駐ロガー

.DESCRIPTION
    2分間隔でフォアグラウンドウィンドウの情報をキャプチャし、
    OCRとキーワード抽出を行ってJSONL形式で記録する。

.NOTES
    実行間隔: 120秒
    出力形式: JSONL (UTF-8, BOM無し)
    実行モード: バックグラウンド（ウィンドウ非表示）
#>

# ============================================================
# Win32 API定義
# ============================================================
Add-Type @"
using System;
using System.Text;
using System.Runtime.InteropServices;

public static class Win32 {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll", CharSet=CharSet.Auto, SetLastError=true)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

    [DllImport("user32.dll", SetLastError=true)]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

    // DPI対応（高解像度スクリーンショット用）
    [DllImport("user32.dll")]
    public static extern bool SetProcessDPIAware();

    // 実際の画面解像度取得用
    [DllImport("user32.dll")]
    public static extern int GetSystemMetrics(int nIndex);

    public const int SM_CXSCREEN = 0;
    public const int SM_CYSCREEN = 1;
}
"@

# DPI対応を有効化（実際のピクセル解像度でキャプチャするため）
[Win32]::SetProcessDPIAware() | Out-Null

# ============================================================
# グローバル変数（設定パラメータ - 仕様書6章準拠）
# ============================================================
$script:LogDirectory = Join-Path $env:LOCALAPPDATA "DailyReportBot\logs"
$script:TempDirectory = Join-Path $env:TEMP "DailyReportBot"
$script:SamplingIntervalSec = 120
$script:OcrEnabled = $true
$script:OcrLanguage = "ja"
$script:LogRetentionDays = 30

# プライバシー保護: 除外設定（仕様書6章）
$script:ExcludedProcesses = @('LockApp.exe', 'ScreenClipping.exe')
$script:ExcludedWindowTitles = @('*password*', '*credential*', '*secret*', '*token*')

# ============================================================
# ログローテーション（仕様書5.2リカバリー準拠）
# ============================================================
function Remove-OldLogs {
    <#
    .SYNOPSIS
        古いログファイルを削除（30日以上）
    #>
    try {
        if (-not (Test-Path $script:LogDirectory)) {
            return
        }

        $cutoffDate = (Get-Date).AddDays(-$script:LogRetentionDays)
        $oldLogs = Get-ChildItem -Path $script:LogDirectory -Filter "*.jsonl" -ErrorAction SilentlyContinue |
                   Where-Object { $_.LastWriteTime -lt $cutoffDate }

        foreach ($log in $oldLogs) {
            try {
                Remove-Item -Path $log.FullName -Force
                Write-Host "古いログを削除しました: $($log.Name)"
            }
            catch {
                Write-Warning "ログファイルの削除に失敗しました: $($log.Name) - $_"
            }
        }
    }
    catch {
        Write-Warning "ログローテーション中にエラーが発生しました: $_"
    }
}

# ============================================================
# プライバシー保護: 除外チェック（仕様書6章準拠）
# ============================================================
function Test-ShouldSkipCapture {
    <#
    .SYNOPSIS
        キャプチャをスキップすべきかチェック

    .PARAMETER ProcessName
        プロセス名

    .PARAMETER WindowTitle
        ウィンドウタイトル

    .OUTPUTS
        Boolean - スキップすべき場合はTrue
    #>
    param(
        [Parameter(Mandatory=$false)]
        [string]$ProcessName,

        [Parameter(Mandatory=$false)]
        [string]$WindowTitle
    )

    # プロセス名チェック
    if ($ProcessName -and $script:ExcludedProcesses -contains $ProcessName) {
        Write-Verbose "除外プロセスのためスキップ: $ProcessName"
        return $true
    }

    # ウィンドウタイトルパターンチェック
    if ($WindowTitle) {
        foreach ($pattern in $script:ExcludedWindowTitles) {
            if ($WindowTitle -like $pattern) {
                Write-Verbose "除外パターンに一致するためスキップ: $WindowTitle"
                return $true
            }
        }
    }

    return $false
}

# ============================================================
# 初期化
# ============================================================
function Initialize-Logger {
    <#
    .SYNOPSIS
        ロガーの初期化処理
    #>
    try {
        # ディレクトリ作成
        if (-not (Test-Path $script:LogDirectory)) {
            New-Item -ItemType Directory -Path $script:LogDirectory -Force | Out-Null
            Write-Host "ログディレクトリを作成しました: $script:LogDirectory"
        }

        if (-not (Test-Path $script:TempDirectory)) {
            New-Item -ItemType Directory -Path $script:TempDirectory -Force | Out-Null
            Write-Host "一時ディレクトリを作成しました: $script:TempDirectory"
        }

        # ログローテーション実行（起動時に1回）
        Remove-OldLogs

        Write-Host "Daily Report Bot ロガーを起動しました"
        Write-Host "サンプリング間隔: $script:SamplingIntervalSec 秒"
        Write-Host "OCR有効: $script:OcrEnabled"
        Write-Host "ログ保持期間: $script:LogRetentionDays 日"
    }
    catch {
        Write-Error "初期化に失敗しました: $_"
        throw
    }
}

# ============================================================
# ウィンドウ情報取得
# ============================================================
function Get-ForegroundWindowInfo {
    <#
    .SYNOPSIS
        フォアグラウンドウィンドウの情報を取得

    .OUTPUTS
        HashTable - window_title, process_name を含むハッシュテーブル
    #>
    try {
        # ウィンドウハンドル取得
        $hwnd = [Win32]::GetForegroundWindow()

        if ($hwnd -eq [IntPtr]::Zero) {
            Write-Warning "フォアグラウンドウィンドウが取得できませんでした"
            return @{
                window_title = $null
                process_name = $null
            }
        }

        # ウィンドウタイトル取得
        $titleBuilder = New-Object System.Text.StringBuilder 256
        $length = [Win32]::GetWindowText($hwnd, $titleBuilder, $titleBuilder.Capacity)
        $windowTitle = if ($length -gt 0) { $titleBuilder.ToString() } else { $null }

        # プロセス名取得
        $processId = 0
        [Win32]::GetWindowThreadProcessId($hwnd, [ref]$processId) | Out-Null
        $processName = $null

        if ($processId -gt 0) {
            try {
                $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
                if ($process) {
                    $processName = $process.ProcessName + ".exe"
                }
            }
            catch {
                Write-Warning "プロセス名の取得に失敗しました: $_"
            }
        }

        return @{
            window_title = $windowTitle
            process_name = $processName
        }
    }
    catch {
        Write-Warning "ウィンドウ情報の取得中にエラーが発生しました: $_"
        return @{
            window_title = $null
            process_name = $null
        }
    }
}

# ============================================================
# スクリーンショット取得
# ============================================================
function Get-Screenshot {
    <#
    .SYNOPSIS
        全画面（動的マルチモニター対応）のスクリーンショットを取得してPNGファイルとして保存
        1画面でも2画面でも接続状況に応じて自動調整

    .OUTPUTS
        String - 保存したファイルのパス（失敗時はnull）
    #>
    $screenshotPath = $null
    $graphics = $null
    $bitmap = $null

    try {
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing

        # 接続中の全モニターのバウンディングボックスを動的に計算
        $allScreens = [System.Windows.Forms.Screen]::AllScreens
        $minX = [int]($allScreens | ForEach-Object { $_.Bounds.Left } | Measure-Object -Minimum).Minimum
        $minY = [int]($allScreens | ForEach-Object { $_.Bounds.Top } | Measure-Object -Minimum).Minimum
        $maxX = [int]($allScreens | ForEach-Object { $_.Bounds.Right } | Measure-Object -Maximum).Maximum
        $maxY = [int]($allScreens | ForEach-Object { $_.Bounds.Bottom } | Measure-Object -Maximum).Maximum

        $width = [int]($maxX - $minX)
        $height = [int]($maxY - $minY)

        # ビットマップ作成
        $bitmap = New-Object System.Drawing.Bitmap([int]$width, [int]$height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)

        # スクリーンショット取得（オフセットを考慮）
        $graphics.CopyFromScreen(
            [int]$minX, [int]$minY,
            0, 0,
            (New-Object System.Drawing.Size([int]$width, [int]$height))
        )

        # 一時ファイルとして保存
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $screenshotPath = Join-Path $script:TempDirectory "screenshot_$timestamp.png"
        $bitmap.Save($screenshotPath, [System.Drawing.Imaging.ImageFormat]::Png)

        # リソース解放
        $graphics.Dispose()
        $bitmap.Dispose()

        Write-Verbose "スクリーンショットを保存しました: $screenshotPath ($width x $height)"
        return $screenshotPath
    }
    catch {
        Write-Warning "スクリーンショットの取得に失敗しました: $_"

        # リソース解放
        if ($graphics) { $graphics.Dispose() }
        if ($bitmap) { $bitmap.Dispose() }

        return $null
    }
}

# ============================================================
# OCR実行
# ============================================================
function Invoke-OCR {
    <#
    .SYNOPSIS
        Tesseract OCRを使用して画像からテキストを抽出

    .PARAMETER ImagePath
        OCR対象の画像ファイルパス

    .OUTPUTS
        String - 抽出されたテキスト（失敗時はnull）
    #>
    param(
        [Parameter(Mandatory=$true)]
        [string]$ImagePath
    )

    if (-not $script:OcrEnabled) {
        return $null
    }

    try {
        # Tesseractのパスを確認
        $tesseractPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"
        if (-not (Test-Path $tesseractPath)) {
            Write-Warning "Tesseractが見つかりません: $tesseractPath"
            return $null
        }

        # 出力ファイルパス（Tesseractは自動で.txtを追加）
        $outputBase = [System.IO.Path]::Combine($script:TempDirectory, "ocr_output")
        $outputFile = "$outputBase.txt"

        # 既存の出力ファイルを削除
        if (Test-Path $outputFile) {
            Remove-Item $outputFile -Force
        }

        # Tesseract実行（日本語+英語、高精度モード）
        $arguments = @(
            "`"$ImagePath`"",
            "`"$outputBase`"",
            "-l", "jpn+eng",
            "--psm", "3",
            "--oem", "3"
        )

        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = $tesseractPath
        $processInfo.Arguments = $arguments -join " "
        $processInfo.RedirectStandardOutput = $true
        $processInfo.RedirectStandardError = $true
        $processInfo.UseShellExecute = $false
        $processInfo.CreateNoWindow = $true

        $process = [System.Diagnostics.Process]::Start($processInfo)
        [void]$process.WaitForExit(30000)  # 30秒タイムアウト

        if ($process.ExitCode -ne 0) {
            $stderr = $process.StandardError.ReadToEnd()
            Write-Warning "Tesseract実行エラー (exit code: $($process.ExitCode)): $stderr"
            return $null
        }

        # 結果ファイルを読み込み
        if (Test-Path $outputFile) {
            $extractedText = [string](Get-Content $outputFile -Raw -Encoding UTF8)
            if ([string]::IsNullOrEmpty($extractedText)) {
                $extractedText = ""
            }
            Remove-Item $outputFile -Force -ErrorAction SilentlyContinue

            Write-Verbose "OCR処理完了: $($extractedText.Length) 文字"
            return $extractedText
        }
        else {
            Write-Warning "OCR出力ファイルが見つかりません"
            return $null
        }
    }
    catch {
        Write-Warning "OCR処理に失敗しました（スキップして続行）: $_"
        return $null
    }
}

# ============================================================
# ウィンドウタイトル解析
# ============================================================
function Get-ParsedWindowTitle {
    <#
    .SYNOPSIS
        ウィンドウタイトルからプロジェクト名、ファイル名を抽出

    .PARAMETER WindowTitle
        解析対象のウィンドウタイトル

    .OUTPUTS
        HashTable - project, file を含む
    #>
    param(
        [Parameter(Mandatory=$false)]
        [string]$WindowTitle = ""
    )

    $parsed = @{
        project = $null
        file = $null
    }

    if ([string]::IsNullOrWhiteSpace($WindowTitle)) {
        return $parsed
    }

    # ファイル名抽出（拡張子付き、単語境界を考慮）
    # 長い拡張子を先に検索してマッチさせる
    $extensions = @(
        'jsonl', 'tsx', 'jsx', 'yml', 'yaml', 'html', 'css', 'java', 'cpp', 'vue', 'svelte',
        'py', 'js', 'ts', 'json', 'md', 'txt', 'csv', 'xlsx', 'xml', 'cs', 'go', 'rs', 'rb', 'php', 'sh', 'ps1', 'bat', 'cmd', 'h'
    )
    $extPattern = $extensions -join '|'
    $filePattern = "([\w\-\.]+\.($extPattern))(?:\s|$|[^a-zA-Z])"
    $fileMatch = [regex]::Match($WindowTitle, $filePattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if ($fileMatch.Success) {
        $parsed.file = $fileMatch.Groups[1].Value
    }

    # プロジェクト名抽出パターン
    $projectPatterns = @(
        # VSCode/Cursor: "file - project - App" or "folder - App"
        '[\w\-\.]+ - ([\w\-_]+) - (?:Visual Studio Code|Code|Cursor)',
        # JetBrains: "project – file"
        '([\w\-_]+)\s+[–\-]\s+[\w\-\.]+',
        # Git関連: "owner/repo"
        '([\w\-]+/[\w\-_]+)',
        # 一般的なパターン: フォルダ名っぽいもの
        '\b([\w\-_]{3,}(?:_bot|_app|_api|_web|_service|_project)?)\b'
    )

    foreach ($pattern in $projectPatterns) {
        $projectMatch = [regex]::Match($WindowTitle, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
        if ($projectMatch.Success -and $projectMatch.Groups.Count -gt 1) {
            $candidate = $projectMatch.Groups[1].Value
            # 除外ワード（一般的すぎるもの・拡張子）
            $excludeWords = @(
                'Untitled', 'Workspace', 'Code', 'Cursor', 'Chrome', 'Edge', 'Firefox', 'wsl', 'Window', 'File', 'Edit', 'View',
                'jsonl', 'json', 'txt', 'md', 'py', 'js', 'ts', 'tsx', 'jsx', 'html', 'css', 'yml', 'yaml', 'xml'
            )
            if ($candidate -notin $excludeWords -and $candidate.Length -ge 3) {
                $parsed.project = $candidate
                break
            }
        }
    }

    return $parsed
}

# ============================================================
# アプリカテゴリ分類
# ============================================================
function Get-AppCategory {
    <#
    .SYNOPSIS
        プロセス名からアプリカテゴリを判定

    .PARAMETER ProcessName
        プロセス名

    .OUTPUTS
        String - カテゴリ名
    #>
    param(
        [Parameter(Mandatory=$false)]
        [string]$ProcessName = ""
    )

    if ([string]::IsNullOrWhiteSpace($ProcessName)) {
        return "other"
    }

    $processLower = $ProcessName.ToLower()

    # カテゴリマッピング
    $categories = @{
        "development" = @('code', 'cursor', 'vim', 'nvim', 'emacs', 'idea', 'pycharm', 'webstorm', 'goland', 'rider', 'android studio', 'xcode', 'visual studio', 'sublime', 'atom', 'notepad++', 'powershell', 'terminal', 'iterm', 'warp', 'alacritty', 'windowsterminal')
        "browser" = @('chrome', 'firefox', 'edge', 'safari', 'opera', 'brave', 'vivaldi', 'msedge')
        "communication" = @('slack', 'teams', 'discord', 'zoom', 'meet', 'skype', 'webex', 'line', 'telegram', 'whatsapp')
        "document" = @('notion', 'obsidian', 'word', 'winword', 'excel', 'powerpoint', 'onenote', 'evernote', 'typora', 'marktext')
        "design" = @('figma', 'sketch', 'photoshop', 'illustrator', 'xd', 'canva', 'gimp', 'inkscape')
        "database" = @('dbeaver', 'datagrip', 'pgadmin', 'mysql workbench', 'mongodb compass', 'redis', 'tableplus', 'sequel')
        "devops" = @('docker', 'kubectl', 'terraform', 'ansible', 'jenkins', 'postman', 'insomnia')
    }

    foreach ($category in $categories.Keys) {
        foreach ($app in $categories[$category]) {
            if ($processLower -like "*$app*") {
                return $category
            }
        }
    }

    return "other"
}

# ============================================================
# アクティビティコンテキスト抽出
# ============================================================
function Get-ActivityContext {
    <#
    .SYNOPSIS
        OCRテキストからアクティビティの種類とキーワードを抽出

    .PARAMETER Text
        OCRで抽出したテキスト

    .PARAMETER AppCategory
        アプリカテゴリ

    .OUTPUTS
        HashTable - type, site, keywords を含む
    #>
    param(
        [Parameter(Mandatory=$false)]
        [string]$Text = "",

        [Parameter(Mandatory=$false)]
        [string]$AppCategory = "other"
    )

    $activity = @{
        type = $null
        site = $null
        keywords = @()
    }

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $activity
    }

    # アクティビティタイプ検出（優先度順）
    $activityPatterns = [ordered]@{
        # コミュニケーション
        "meeting" = @('会議', 'ミーティング', 'Meeting', '通話中', '参加者', 'Zoom', 'Teams', 'Google Meet', 'Webex')
        "chat" = @('Slack', 'Discord', 'Teams', '#channel', 'DM', 'メッセージ', 'チャット', '@')
        "email" = @('Gmail', 'Outlook', '受信トレイ', 'Inbox', '件名', 'Subject', 'Re:', '返信')

        # 情報収集
        "search" = @('Google', '検索結果', 'Search Results', 'Bing', 'DuckDuckGo')
        "learning" = @('Udemy', 'Coursera', 'YouTube', 'tutorial', '講座', 'チュートリアル')
        "docs" = @('Documentation', 'ドキュメント', 'docs', 'API Reference', 'マニュアル')
        "news" = @('ニュース', 'News', '記事', 'Article', 'ブログ', 'Blog')

        # SNS/エンタメ
        "sns" = @('Twitter', 'X.com', 'Instagram', 'Facebook', 'TikTok', 'LinkedIn', 'ツイート', 'いいね', 'フォロー')
        "video" = @('YouTube', 'Netflix', 'Prime Video', '再生中', 'Playing', '動画')
        "music" = @('Spotify', 'Apple Music', 'Amazon Music', '再生中', 'Now Playing')
        "game" = @('Steam', 'ゲーム', 'Game', 'プレイ中', 'Playing')

        # ドキュメント作業
        "document" = @('Word', 'Google Docs', 'ドキュメント', '編集中', 'Editing')
        "spreadsheet" = @('Excel', 'Google Sheets', 'スプレッドシート', 'セル', 'Cell')
        "presentation" = @('PowerPoint', 'Google Slides', 'スライド', 'Slide', 'プレゼン')
        "notes" = @('Notion', 'Obsidian', 'Evernote', 'OneNote', 'メモ', 'Note')

        # 開発作業
        "coding" = @('function', 'class', 'def ', 'const ', 'import ', 'export ', '=>', '(){')
        "error" = @('Error', 'Exception', 'failed', 'エラー', 'TypeError', 'SyntaxError', 'undefined')
        "git" = @('commit', 'push', 'pull', 'merge', 'branch', 'PR #', 'Pull Request')
        "build" = @('build', 'compile', 'bundle', 'npm run', 'yarn', 'passed', 'failed')
        "ai_assist" = @('Claude', 'ChatGPT', 'Copilot', 'Gemini', 'AI', 'プロンプト')

        # ファイル/システム
        "file_ops" = @('コピー', 'Copy', '移動', 'Move', '削除', 'Delete', '名前変更', 'Rename')
        "download" = @('ダウンロード', 'Download', '保存', 'Save')
        "settings" = @('設定', 'Settings', '環境設定', 'Preferences', 'オプション')
        "install" = @('インストール', 'Install', 'Setup', 'セットアップ')

        # 金融/ショッピング
        "shopping" = @('Amazon', '楽天', 'カート', 'Cart', '購入', 'Buy', '注文')
        "banking" = @('銀行', 'Bank', '振込', '残高', 'Balance', '口座')
    }

    # タイプ検出
    foreach ($type in $activityPatterns.Keys) {
        foreach ($pattern in $activityPatterns[$type]) {
            if ($Text -match [regex]::Escape($pattern)) {
                $activity.type = $type
                break
            }
        }
        if ($activity.type) { break }
    }

    # サイト/ドメイン抽出
    $domainPattern = '([\w\-]+\.(com|co\.jp|jp|org|net|io|dev|app|ai))'
    $domainMatch = [regex]::Match($Text, $domainPattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    if ($domainMatch.Success) {
        $activity.site = $domainMatch.Groups[1].Value.ToLower()
    }

    # 重要キーワード抽出（最大5個）
    $keywordPatterns = @(
        # エラー関連
        '(Error|Exception|failed|TypeError|エラー)[:：]?\s*[\w\s]{0,30}',
        # Git関連
        '(commit|push|pull|merge|branch)[\s:]+[\w\-/]+',
        '(PR|Pull Request)\s*#?\d+',
        # ステータス
        '(成功|完了|passed|failed|success)',
        # ファイル名
        '[\w\-]+\.(py|js|ts|tsx|jsx|json|md|yml|yaml|html|css)'
    )

    foreach ($pattern in $keywordPatterns) {
        $matches = [regex]::Matches($Text, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
        foreach ($match in $matches) {
            $keyword = $match.Value.Trim()
            if ($keyword.Length -le 50 -and $keyword -notin $activity.keywords) {
                $activity.keywords += $keyword
                if ($activity.keywords.Count -ge 5) { break }
            }
        }
        if ($activity.keywords.Count -ge 5) { break }
    }

    return $activity
}

# ============================================================
# JSONLレコード保存
# ============================================================
function Save-LogRecord {
    <#
    .SYNOPSIS
        ログレコードをJSONL形式で追記保存

    .PARAMETER Record
        保存するレコード（HashTable）
    #>
    param(
        [Parameter(Mandatory=$true)]
        [hashtable]$Record
    )

    $maxRetries = 3
    $retryCount = 0
    $success = $false

    # 日付別ファイル名
    $dateStr = Get-Date -Format "yyyy-MM-dd"
    $logFilePath = Join-Path $script:LogDirectory "$dateStr.jsonl"

    while (-not $success -and $retryCount -lt $maxRetries) {
        try {
            # JSONに変換（1行）
            $jsonLine = $Record | ConvertTo-Json -Compress -Depth 10

            # UTF-8（BOM無し）で追記
            $utf8NoBom = New-Object System.Text.UTF8Encoding $false
            [System.IO.File]::AppendAllText($logFilePath, "$jsonLine`n", $utf8NoBom)

            $success = $true
            Write-Verbose "ログレコードを保存しました: $logFilePath"
        }
        catch {
            $retryCount++
            Write-Warning "ログ保存に失敗しました（試行 $retryCount/$maxRetries）: $_"

            if ($retryCount -lt $maxRetries) {
                Start-Sleep -Seconds 1
            }
            else {
                Write-Error "ログ保存に失敗しました（最大リトライ回数に到達）: $_"
                throw
            }
        }
    }
}

# ============================================================
# メインループ
# ============================================================
function Start-LoggerMainLoop {
    <#
    .SYNOPSIS
        ロガーのメインループ処理
    #>
    Write-Host "メインループを開始します..."

    while ($true) {
        try {
            # 1. タイムスタンプ取得
            $timestamp = Get-Date -Format "o"

            # 2. フォアグラウンドウィンドウ情報取得
            $windowInfo = Get-ForegroundWindowInfo

            # 2.5. プライバシー保護: 除外チェック（仕様書6章準拠）
            if (Test-ShouldSkipCapture -ProcessName $windowInfo.process_name -WindowTitle $windowInfo.window_title) {
                # 除外対象: スクリーンショット・OCRをスキップし、最小限のレコードを記録
                $record = @{
                    ts = $timestamp
                    app = $null
                    category = "skipped"
                    window_title = "[REDACTED]"
                    activity = @{
                        type = $null
                        site = $null
                        project = $null
                        file = $null
                        keywords = @()
                    }
                }
                Save-LogRecord -Record $record
                Write-Host "[$timestamp] [SKIPPED] $($windowInfo.process_name)"
                Start-Sleep -Seconds $script:SamplingIntervalSec
                continue
            }

            # 3. ウィンドウタイトル解析
            $parsedTitle = Get-ParsedWindowTitle -WindowTitle $windowInfo.window_title

            # 4. アプリカテゴリ分類
            $category = Get-AppCategory -ProcessName $windowInfo.process_name

            # 5. アプリ名抽出（プロセス名から.exeを除去）
            $appName = if ($windowInfo.process_name) {
                $windowInfo.process_name -replace '\.exe$', ''
            } else { $null }

            # 6. スクリーンショット取得
            $screenshotPath = Get-Screenshot

            # 7. OCR実行 & アクティビティコンテキスト抽出
            $activity = @{
                type = $null
                site = $null
                keywords = @()
            }
            if ($screenshotPath) {
                $ocrText = Invoke-OCR -ImagePath $screenshotPath
                if ($ocrText) {
                    $activity = Get-ActivityContext -Text $ocrText -AppCategory $category
                }

                # スクリーンショット削除
                try {
                    Remove-Item -Path $screenshotPath -Force -ErrorAction Stop
                }
                catch {
                    Write-Warning "スクリーンショットの削除に失敗しました: $_"
                }
            }

            # 8. レコード作成（アクティビティベースフォーマット）
            $record = @{
                ts = $timestamp
                app = $appName
                category = $category
                window_title = $windowInfo.window_title
                activity = @{
                    type = $activity.type
                    site = $activity.site
                    project = $parsedTitle.project
                    file = $parsedTitle.file
                    keywords = $activity.keywords
                }
            }

            # 9. JSONL保存
            Save-LogRecord -Record $record

            # デバッグ出力
            $recordInfo = "[$timestamp] $($windowInfo.process_name) - $($windowInfo.window_title)"
            Write-Host $recordInfo

            # 9. スリープ
            Start-Sleep -Seconds $script:SamplingIntervalSec
        }
        catch {
            Write-Error "メインループでエラーが発生しました: $_"
            Write-Error $_.ScriptStackTrace

            # エラー発生時も続行（クリティカルエラー以外）
            Start-Sleep -Seconds $script:SamplingIntervalSec
        }
    }
}

# ============================================================
# エントリーポイント
# ============================================================
# テスト用: -WhatIf パラメータでドットソース時に実行をスキップ
if ($MyInvocation.InvocationName -ne '.') {
    try {
        Initialize-Logger
        Start-LoggerMainLoop
    }
    catch {
        Write-Error "致命的なエラーが発生しました: $_"
        Write-Error $_.ScriptStackTrace
        exit 1
    }
}
