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
}
"@

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
        全画面のスクリーンショットを取得してPNGファイルとして保存

    .OUTPUTS
        String - 保存したファイルのパス（失敗時はnull）
    #>
    $screenshotPath = $null

    try {
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing

        # 画面サイズ取得
        $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)

        # スクリーンショット取得
        $graphics.CopyFromScreen(
            $bounds.Location,
            [System.Drawing.Point]::Empty,
            $bounds.Size
        )

        # 一時ファイルとして保存
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $screenshotPath = Join-Path $script:TempDirectory "screenshot_$timestamp.png"
        $bitmap.Save($screenshotPath, [System.Drawing.Imaging.ImageFormat]::Png)

        # リソース解放
        $graphics.Dispose()
        $bitmap.Dispose()

        Write-Verbose "スクリーンショットを保存しました: $screenshotPath"
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
        WinRT OcrEngineを使用して画像からテキストを抽出

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
        # WinRT アセンブリ読み込み
        [void][Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]
        [void][Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
        [void][Windows.Foundation.IAsyncOperation`1, Windows.Foundation, ContentType=WindowsRuntime]
        [void][Windows.Graphics.Imaging.SoftwareBitmap, Windows.Foundation, ContentType=WindowsRuntime]

        # 非同期処理のヘルパー関数
        Add-Type -AssemblyName System.Runtime.WindowsRuntime
        $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
            $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
        })[0]

        function Await($WinRtTask, $ResultType) {
            $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
            $netTask = $asTask.Invoke($null, @($WinRtTask))
            $netTask.Wait() | Out-Null
            return $netTask.Result
        }

        # OCRエンジン初期化（日本語）
        $ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage(
            [Windows.Globalization.Language]::new($script:OcrLanguage)
        )

        if (-not $ocrEngine) {
            # フォールバック: 利用可能な最初の言語を使用
            $availableLanguage = [Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages[0]
            $ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($availableLanguage)
        }

        if (-not $ocrEngine) {
            Write-Warning "OCRエンジンを初期化できませんでした"
            return $null
        }

        # 画像ファイル読み込み
        $fileTask = [Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)
        $file = Await $fileTask ([Windows.Storage.StorageFile])

        $streamTask = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read)
        $stream = Await $streamTask ([Windows.Storage.Streams.IRandomAccessStream])

        $decoderTask = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
        $decoder = Await $decoderTask ([Windows.Graphics.Imaging.BitmapDecoder])

        $bitmapTask = $decoder.GetSoftwareBitmapAsync()
        $bitmap = Await $bitmapTask ([Windows.Graphics.Imaging.SoftwareBitmap])

        # OCR実行
        $ocrResultTask = $ocrEngine.RecognizeAsync($bitmap)
        $ocrResult = Await $ocrResultTask ([Windows.Media.Ocr.OcrResult])

        # テキスト抽出
        $extractedText = $ocrResult.Text

        # リソース解放
        if ($stream) { $stream.Dispose() }
        if ($bitmap) { $bitmap.Dispose() }

        Write-Verbose "OCR処理完了: $($extractedText.Length) 文字"
        return $extractedText
    }
    catch {
        Write-Warning "OCR処理に失敗しました（スキップして続行）: $_"
        return $null
    }
}

# ============================================================
# 特徴量抽出
# ============================================================
function Get-ExtractedFeatures {
    <#
    .SYNOPSIS
        テキストから特徴量（キーワード、URL、ファイル、数値）を抽出

    .PARAMETER Text
        抽出対象のテキスト

    .OUTPUTS
        HashTable - keywords, urls, files, numbers の配列を含む
    #>
    param(
        [Parameter(Mandatory=$false)]
        [string]$Text = ""
    )

    $features = @{
        keywords = @()
        urls = @()
        files = @()
        numbers = @()
    }

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $features
    }

    # URL抽出
    $urlPattern = 'https?://[^\s<>"{}|\\^`\[\]]+'
    $urlMatches = [regex]::Matches($Text, $urlPattern)
    $features.urls = $urlMatches | ForEach-Object { $_.Value } | Select-Object -Unique

    # ファイルパス抽出
    $filePatterns = @(
        '[A-Za-z]:\\[^\s<>"|?*]+',  # Windows絶対パス
        '/[^\s<>"|?*]+',             # Unix-like絶対パス
        '\w+\.(py|js|ts|tsx|jsx|json|md|txt|csv|xlsx|yml|yaml|xml|html|css|java|cs|cpp|h|go|rs|rb|php|sh|ps1|bat|cmd)'  # 拡張子付きファイル
    )

    foreach ($pattern in $filePatterns) {
        $fileMatches = [regex]::Matches($Text, $pattern)
        $features.files += $fileMatches | ForEach-Object { $_.Value }
    }
    $features.files = $features.files | Select-Object -Unique

    # 数値抽出（パーセント、金額、大きな数値）
    $numberPatterns = @(
        '\d+(\.\d+)?%',           # パーセント
        '¥[\d,]+',                # 日本円
        '[$€][\d,.]+',           # ドル・ユーロ
        '\b\d{3,}\b'              # 3桁以上の数値
    )

    foreach ($pattern in $numberPatterns) {
        $numberMatches = [regex]::Matches($Text, $pattern)
        $features.numbers += $numberMatches | ForEach-Object { $_.Value }
    }
    $features.numbers = $features.numbers | Select-Object -Unique

    # キーワード抽出（プログラミング言語、ツール、頻出単語）
    $keywords = @(
        # プログラミング言語
        'Python', 'JavaScript', 'TypeScript', 'Java', 'C#', 'C\+\+', 'Go', 'Rust', 'Ruby', 'PHP', 'Swift', 'Kotlin',
        # フレームワーク・ライブラリ
        'React', 'Vue', 'Angular', 'Next\.js', 'Express', 'Django', 'Flask', 'Spring', '\.NET',
        # ツール
        'Git', 'GitHub', 'GitLab', 'Docker', 'Kubernetes', 'Jenkins', 'VSCode', 'Visual Studio',
        'Slack', 'Notion', 'Jira', 'Confluence',
        # キーワード
        'def', 'class', 'function', 'import', 'export', 'const', 'let', 'var', 'async', 'await',
        'if', 'else', 'for', 'while', 'return', 'try', 'catch', 'throw',
        # データベース
        'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SELECT', 'INSERT', 'UPDATE', 'DELETE',
        # その他
        'API', 'REST', 'GraphQL', 'JSON', 'XML', 'YAML', 'CSV', 'HTML', 'CSS'
    )

    foreach ($keyword in $keywords) {
        if ($Text -match $keyword) {
            $features.keywords += $keyword
        }
    }
    $features.keywords = $features.keywords | Select-Object -Unique

    return $features
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
                    window_title = $null  # プライバシー保護のため記録しない
                    process_name = $windowInfo.process_name
                    keywords = @()
                    urls = @()
                    files = @()
                    numbers = @()
                }
                Save-LogRecord -Record $record
                Write-Host "[$timestamp] [SKIPPED] $($windowInfo.process_name)"
                Start-Sleep -Seconds $script:SamplingIntervalSec
                continue
            }

            # 3. スクリーンショット取得
            $screenshotPath = Get-Screenshot

            # 4. OCR実行
            $ocrText = $null
            if ($screenshotPath) {
                $ocrText = Invoke-OCR -ImagePath $screenshotPath
            }

            # 5. 特徴量抽出
            $features = Get-ExtractedFeatures -Text $ocrText

            # 6. レコード作成
            $record = @{
                ts = $timestamp
                window_title = $windowInfo.window_title
                process_name = $windowInfo.process_name
                keywords = $features.keywords
                urls = $features.urls
                files = $features.files
                numbers = $features.numbers
            }

            # 7. JSONL保存
            Save-LogRecord -Record $record

            # 8. スクリーンショット削除
            if ($screenshotPath -and (Test-Path $screenshotPath)) {
                try {
                    Remove-Item -Path $screenshotPath -Force -ErrorAction Stop
                    Write-Verbose "スクリーンショットを削除しました: $screenshotPath"
                }
                catch {
                    Write-Warning "スクリーンショットの削除に失敗しました: $_"
                }
            }

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
try {
    Initialize-Logger
    Start-LoggerMainLoop
}
catch {
    Write-Error "致命的なエラーが発生しました: $_"
    Write-Error $_.ScriptStackTrace
    exit 1
}
