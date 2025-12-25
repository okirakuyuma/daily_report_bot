# スクリーンショット リファレンス

## 基本取得

```powershell
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Get-Screenshot {
    param([string]$OutputPath)

    $screen = [System.Windows.Forms.Screen]::PrimaryScreen
    $bounds = $screen.Bounds

    $bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)

    $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)

    $graphics.Dispose()
    $bitmap.Dispose()
}
```

## マルチモニター対応

```powershell
function Get-AllScreensScreenshot {
    param([string]$OutputPath)

    $screens = [System.Windows.Forms.Screen]::AllScreens
    $minX = ($screens | Measure-Object -Property { $_.Bounds.X } -Minimum).Minimum
    $minY = ($screens | Measure-Object -Property { $_.Bounds.Y } -Minimum).Minimum
    $maxX = ($screens | Measure-Object -Property { $_.Bounds.X + $_.Bounds.Width } -Maximum).Maximum
    $maxY = ($screens | Measure-Object -Property { $_.Bounds.Y + $_.Bounds.Height } -Maximum).Maximum

    $width = $maxX - $minX
    $height = $maxY - $minY

    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($minX, $minY, 0, 0, [System.Drawing.Size]::new($width, $height))

    $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}
```

## 注意事項

- 高DPI環境では実際のピクセル数が異なる場合あり
- ハードウェアアクセラレーションで黒画面の場合はGDI+で再取得
