# WinRT OCR リファレンス

## セットアップ

```powershell
Add-Type -AssemblyName System.Runtime.WindowsRuntime

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

[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
```

## OCR実行

```powershell
function Invoke-WindowsOcr {
    param([string]$ImagePath, [string]$Language = "ja")

    $ocrLanguage = [Windows.Globalization.Language]::new($Language)
    $ocrEngine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($ocrLanguage)
    if ($null -eq $ocrEngine) { return $null }

    $storageFile = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)) ([Windows.Storage.StorageFile])
    $stream = Await ($storageFile.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $softwareBitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    $ocrResult = Await ($ocrEngine.RecognizeAsync($softwareBitmap)) ([Windows.Media.Ocr.OcrResult])

    $stream.Dispose()
    return $ocrResult.Text
}
```

## 特徴量抽出

```powershell
function Extract-Features {
    param([string]$Text)

    $urls = [regex]::Matches($Text, 'https?://[^\s<>"{}|\\^`\[\]]+') | ForEach-Object { $_.Value }
    $files = [regex]::Matches($Text, '\b\w+\.(py|js|ts|json|md|txt)\b') | ForEach-Object { $_.Value }

    return @{ urls = $urls; files = $files }
}
```

## トラブルシューティング

| エラー | 解決策 |
|--------|--------|
| OCR engine not available | 言語パック追加: `Add-WindowsCapability -Online -Name Language.OCR*ja-JP*` |
| Out of memory | 画像をリサイズ（1920x1080以下） |
