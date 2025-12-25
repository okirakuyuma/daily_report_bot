# Windows OCR Skill

WinRT Windows.Media.Ocr APIを使用して画像からテキストを抽出するスキル。

## Triggers

- OCR、テキスト抽出、画像認識、スクリーンショット解析
- 常駐ロガーのOCR処理実装時

## 基本情報

| 項目 | 内容 |
|------|------|
| API | Windows.Media.Ocr (WinRT) |
| 対象OS | Windows 10 1809+ / Windows 11 |
| 言語パック | 日本語、英語など（OS設定で追加） |
| 精度 | 高（日本語対応） |

---

## PowerShell実装

### WinRT OCRの読み込み

```powershell
# WinRT型の読み込み
Add-Type -AssemblyName System.Runtime.WindowsRuntime

# 非同期メソッドのヘルパー
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]

function Await {
    param([object]$WinRTTask, [Type]$ResultType)

    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRTTask))
    $netTask.Wait(-1) | Out-Null
    return $netTask.Result
}

# OCRエンジンの初期化
[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
```

### OCR実行関数

```powershell
function Invoke-WindowsOcr {
    param(
        [Parameter(Mandatory)]
        [string]$ImagePath,

        [string]$Language = "ja"
    )

    try {
        # 言語設定
        $ocrLanguage = [Windows.Globalization.Language]::new($Language)

        # OCRエンジン作成
        $ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($ocrLanguage)

        if ($null -eq $ocrEngine) {
            Write-Warning "OCR engine not available for language: $Language"
            return $null
        }

        # 画像ファイル読み込み
        $storageFile = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)) `
            ([Windows.Storage.StorageFile])

        # ストリーム開く
        $stream = Await ($storageFile.OpenAsync([Windows.Storage.FileAccessMode]::Read)) `
            ([Windows.Storage.Streams.IRandomAccessStream])

        # デコーダー作成
        $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) `
            ([Windows.Graphics.Imaging.BitmapDecoder])

        # SoftwareBitmap取得
        $softwareBitmap = Await ($decoder.GetSoftwareBitmapAsync()) `
            ([Windows.Graphics.Imaging.SoftwareBitmap])

        # OCR実行
        $ocrResult = Await ($ocrEngine.RecognizeAsync($softwareBitmap)) `
            ([Windows.Media.Ocr.OcrResult])

        # ストリームクローズ
        $stream.Dispose()

        # 結果返却
        return [PSCustomObject]@{
            Text       = $ocrResult.Text
            Lines      = $ocrResult.Lines | ForEach-Object { $_.Text }
            Words      = $ocrResult.Lines | ForEach-Object {
                $_.Words | ForEach-Object {
                    [PSCustomObject]@{
                        Text       = $_.Text
                        BoundingRect = $_.BoundingRect
                    }
                }
            }
            TextAngle  = $ocrResult.TextAngle
        }
    }
    catch {
        Write-Warning "OCR failed: $_"
        return $null
    }
}
```

### 使用例

```powershell
$result = Invoke-WindowsOcr -ImagePath "C:\temp\screenshot.png" -Language "ja"

if ($result) {
    Write-Host "Full Text:"
    Write-Host $result.Text

    Write-Host "`nLines:"
    $result.Lines | ForEach-Object { Write-Host "- $_" }
}
```

---

## C# 実装（高性能版）

### OCRサービスクラス

```csharp
using System;
using System.Threading.Tasks;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;
using Windows.Storage;
using Windows.Storage.Streams;

public class OcrService
{
    private readonly OcrEngine _ocrEngine;

    public OcrService(string language = "ja")
    {
        var ocrLanguage = new Windows.Globalization.Language(language);
        _ocrEngine = OcrEngine.TryCreateFromLanguage(ocrLanguage);

        if (_ocrEngine == null)
        {
            throw new InvalidOperationException($"OCR engine not available for {language}");
        }
    }

    public async Task<OcrResult> RecognizeAsync(string imagePath)
    {
        var file = await StorageFile.GetFileFromPathAsync(imagePath);

        using (var stream = await file.OpenAsync(FileAccessMode.Read))
        {
            var decoder = await BitmapDecoder.CreateAsync(stream);
            var bitmap = await decoder.GetSoftwareBitmapAsync();

            return await _ocrEngine.RecognizeAsync(bitmap);
        }
    }

    public async Task<string> ExtractTextAsync(string imagePath)
    {
        var result = await RecognizeAsync(imagePath);
        return result?.Text ?? string.Empty;
    }
}
```

### PowerShellから呼び出し

```powershell
# C# DLLをロード
Add-Type -Path ".\OcrService.dll"

$ocr = [OcrService]::new("ja")
$text = $ocr.ExtractTextAsync("C:\temp\screenshot.png").GetAwaiter().GetResult()
```

---

## 特徴量抽出

### キーワード・URL・ファイル抽出

```powershell
function Extract-Features {
    param(
        [string]$Text
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return @{
            keywords = @()
            urls     = @()
            files    = @()
            numbers  = @()
        }
    }

    # URL抽出
    $urlPattern = 'https?://[^\s<>"{}|\\^`\[\]]+'
    $urls = [regex]::Matches($Text, $urlPattern) | ForEach-Object { $_.Value } | Select-Object -Unique

    # ファイルパス抽出
    $filePatterns = @(
        '[A-Za-z]:\\[^\s<>"|?*]+',           # Windowsパス
        '/[^\s<>"|?*]+',                       # Unixパス
        '\b\w+\.(py|js|ts|json|md|txt|csv|xlsx|docx|pdf)\b'  # ファイル名
    )
    $files = @()
    foreach ($pattern in $filePatterns) {
        $files += [regex]::Matches($Text, $pattern) | ForEach-Object { $_.Value }
    }
    $files = $files | Select-Object -Unique

    # 数値抽出
    $numberPatterns = @(
        '\d+(\.\d+)?%',                        # パーセント
        '¥[\d,]+',                             # 日本円
        '\$[\d,.]+',                           # ドル
        '\b\d{3,}\b'                           # 3桁以上の数値
    )
    $numbers = @()
    foreach ($pattern in $numberPatterns) {
        $numbers += [regex]::Matches($Text, $pattern) | ForEach-Object { $_.Value }
    }
    $numbers = $numbers | Select-Object -Unique

    # キーワード抽出（技術用語辞書マッチング）
    $techKeywords = @(
        'Python', 'JavaScript', 'TypeScript', 'React', 'Vue', 'Angular',
        'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP',
        'Git', 'GitHub', 'GitLab', 'Slack', 'Notion', 'Jira',
        'API', 'REST', 'GraphQL', 'SQL', 'NoSQL',
        'Visual Studio', 'VSCode', 'IntelliJ', 'PyCharm'
    )
    $keywords = @()
    foreach ($keyword in $techKeywords) {
        if ($Text -match "\b$keyword\b") {
            $keywords += $keyword
        }
    }

    return @{
        keywords = $keywords
        urls     = $urls
        files    = $files
        numbers  = $numbers
    }
}
```

### 統合使用例

```powershell
# スクリーンショット取得
$screenshotPath = "$env:TEMP\screenshot_$(Get-Date -Format 'yyyyMMdd_HHmmss').png"
Get-Screenshot -OutputPath $screenshotPath

# OCR実行
$ocrResult = Invoke-WindowsOcr -ImagePath $screenshotPath -Language "ja"

# 特徴量抽出
$features = Extract-Features -Text $ocrResult.Text

# レコード作成
$record = @{
    ts           = (Get-Date -Format "o")
    window_title = (Get-ForegroundWindowInfo).Title
    process_name = (Get-ForegroundWindowInfo).ProcessName
    keywords     = $features.keywords
    urls         = $features.urls
    files        = $features.files
    numbers      = $features.numbers
}

# スクリーンショット削除
Remove-Item $screenshotPath -ErrorAction SilentlyContinue

$record
```

---

## 言語パック確認

```powershell
# 利用可能なOCR言語一覧
function Get-AvailableOcrLanguages {
    [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null

    $languages = [Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages

    return $languages | ForEach-Object {
        [PSCustomObject]@{
            LanguageTag = $_.LanguageTag
            DisplayName = $_.DisplayName
            NativeName  = $_.NativeName
        }
    }
}

Get-AvailableOcrLanguages
```

### 言語パック追加（管理者権限）

```powershell
# 日本語OCR言語パック追加
$Capability = Get-WindowsCapability -Online | Where-Object { $_.Name -like "Language.OCR*ja-JP*" }
Add-WindowsCapability -Online -Name $Capability.Name
```

---

## パフォーマンス最適化

### 画像リサイズ（大きすぎる場合）

```powershell
function Resize-Image {
    param(
        [string]$InputPath,
        [string]$OutputPath,
        [int]$MaxWidth = 1920,
        [int]$MaxHeight = 1080
    )

    $image = [System.Drawing.Image]::FromFile($InputPath)

    $ratioX = $MaxWidth / $image.Width
    $ratioY = $MaxHeight / $image.Height
    $ratio = [Math]::Min($ratioX, $ratioY)

    if ($ratio -ge 1) {
        $image.Dispose()
        Copy-Item $InputPath $OutputPath
        return
    }

    $newWidth = [int]($image.Width * $ratio)
    $newHeight = [int]($image.Height * $ratio)

    $bitmap = New-Object System.Drawing.Bitmap($newWidth, $newHeight)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $graphics.DrawImage($image, 0, 0, $newWidth, $newHeight)

    $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)

    $graphics.Dispose()
    $bitmap.Dispose()
    $image.Dispose()
}
```

---

## エラーハンドリング

| エラー | 原因 | 解決策 |
|--------|------|--------|
| OCR engine not available | 言語パック未インストール | 言語パック追加 |
| Access denied | ファイルアクセス権限 | 権限確認 |
| Out of memory | 画像が大きすぎる | リサイズ処理 |
| Invalid image | 破損/非対応形式 | PNG/JPEG確認 |

---

## 設定パラメータ

```json
{
  "ocr": {
    "enabled": true,
    "language": "ja",
    "fallback_language": "en-US",
    "max_image_width": 1920,
    "max_image_height": 1080,
    "timeout_ms": 30000
  }
}
```
