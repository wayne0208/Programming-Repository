@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "BAT_FILE=%~f0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$c = [System.IO.File]::ReadAllText($env:BAT_FILE, [System.Text.Encoding]::UTF8) -split '(?m)^::___PS_START___\r?$', 2; & ([ScriptBlock]::Create($c[1]))"
set "EXIT_CODE=%errorlevel%"
echo.
pause
exit /b %EXIT_CODE%
::___PS_START___
$ErrorActionPreference = 'Stop'

# 確保終端機輸入與輸出皆使用 UTF-8
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[Console]::InputEncoding  = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding           = $utf8NoBom

$repoRoot = (Get-Location).Path
$tempBase = $null

function Read-InputLine {
    param([string]$Prompt)
    if ([Console]::IsInputRedirected) {
        Write-Host -NoNewline "${Prompt}: "
        $line = [Console]::In.ReadLine()
    } else {
        $line = Read-Host -Prompt $Prompt
    }
    if ($null -eq $line) {
        return ''
    }
    return $line.Trim([char]0xFEFF).Trim()
}

try {
    # 1. 輸入作業編號
    $hwId = Read-InputLine '請輸入作業編號 (例如 hw4)'
    if ([string]::IsNullOrWhiteSpace($hwId)) {
        Write-Host '錯誤：作業編號不可為空。' -ForegroundColor Red
        exit 1
    }

    # 2. 檢查 .\docs\Group\<hwId>\ 是否存在且有檔案
    $groupSrcDir = Join-Path (Join-Path (Join-Path $repoRoot 'docs') 'Group') $hwId
    if (-not (Test-Path -LiteralPath $groupSrcDir -PathType Container)) {
        Write-Host "沒有團體作業$hwId" -ForegroundColor Red
        exit 1
    }

    $groupItems = @(Get-ChildItem -LiteralPath $groupSrcDir -Force)
    $groupHasFiles = @(Get-ChildItem -LiteralPath $groupSrcDir -Recurse -File -Force).Count -gt 0
    if ($groupItems.Count -eq 0 -or -not $groupHasFiles) {
        Write-Host "沒有團體作業$hwId" -ForegroundColor Red
        exit 1
    }

    Write-Host ''
    Write-Host "找到團體作業 $hwId，資料夾內有以下項目：" -ForegroundColor Green
    foreach ($item in $groupItems) {
        if ($item.PSIsContainer) {
            Write-Host "  [資料夾] $($item.Name)"
        } else {
            Write-Host "  [檔案]   $($item.Name)"
        }
    }
    Write-Host ''

    # 3. 輸入學號並檢查個人作業
    $studentId = Read-InputLine '請輸入學號 (例如 112AB0050)'
    if ([string]::IsNullOrWhiteSpace($studentId)) {
        Write-Host '錯誤：學號不可為空。' -ForegroundColor Red
        exit 1
    }

    $personalDir = Join-Path (Join-Path (Join-Path $repoRoot 'docs') 'personal_work') $studentId
    $personalPdf = Join-Path $personalDir "$hwId.pdf"
    if (-not (Test-Path -LiteralPath $personalDir -PathType Container)) {
        Write-Host "${studentId}還沒有寫個人作業" -ForegroundColor Red
        exit 1
    }
    if (-not (Test-Path -LiteralPath $personalPdf -PathType Leaf)) {
        Write-Host "${studentId}還沒有寫個人作業 (找不到 $hwId.pdf)" -ForegroundColor Red
        exit 1
    }

    Write-Host "OK！已找到個人作業：$hwId.pdf" -ForegroundColor Green
    Write-Host ''

    # 4. 輸入姓名
    $studentName = Read-InputLine '請輸入姓名 (例如 王界誠)'
    if ([string]::IsNullOrWhiteSpace($studentName)) {
        Write-Host '錯誤：姓名不可為空。' -ForegroundColor Red
        exit 1
    }

    # 5. 建立暫存打包目錄 13_學號_姓名 (包含 Personal 與 Group)
    $folderName = "13_${studentId}_${studentName}"
    $tempBase   = Join-Path ([System.IO.Path]::GetTempPath()) ("pack_hw_" + [System.Guid]::NewGuid().ToString('N'))
    $stageRoot  = Join-Path $tempBase $folderName
    $dstPersonal = Join-Path $stageRoot 'Personal'
    $dstGroup    = Join-Path $stageRoot 'Group'

    New-Item -ItemType Directory -Path $dstPersonal -Force | Out-Null
    New-Item -ItemType Directory -Path $dstGroup -Force | Out-Null

    # 6. 複製個人作業 PDF 到 Personal (不影響原檔案)
    Copy-Item -LiteralPath $personalPdf -Destination $dstPersonal -Force

    # 7. 處理 Group 資料夾：除了 file.txt 之外全部複製進去
    foreach ($item in $groupItems) {
        if (-not $item.PSIsContainer -and $item.Name.Equals('file.txt', [System.StringComparison]::OrdinalIgnoreCase)) {
            continue
        }
        Copy-Item -LiteralPath $item.FullName -Destination $dstGroup -Recurse -Force
    }

    # 8. 解析 file.txt（若存在）
    $fileTxtPath = Join-Path $groupSrcDir 'file.txt'
    if (Test-Path -LiteralPath $fileTxtPath -PathType Leaf) {
        $lines = [System.IO.File]::ReadAllLines($fileTxtPath, [System.Text.Encoding]::UTF8)
        $lineNum = 0
        foreach ($rawLine in $lines) {
            $lineNum++
            $entry = $rawLine.Trim()
            if ([string]::IsNullOrWhiteSpace($entry)) {
                continue
            }
            # 去除前後成對引號（若有）
            if (($entry.StartsWith('"') -and $entry.EndsWith('"')) -or ($entry.StartsWith("'") -and $entry.EndsWith("'"))) {
                $entry = $entry.Substring(1, $entry.Length - 2).Trim()
            }
            if ([string]::IsNullOrWhiteSpace($entry)) {
                continue
            }

            # 正規化路徑分隔符號並移除尾端斜線，確保資料夾會連同資料夾本身複製進 Group
            $normalized = ($entry -replace '/', '\').TrimEnd('\')
            if ([string]::IsNullOrWhiteSpace($normalized)) {
                continue
            }

            $targetPath = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $normalized))
            if (-not (Test-Path -LiteralPath $targetPath)) {
                Write-Host "錯誤：file.txt 第 $lineNum 行的路徑不存在：$entry" -ForegroundColor Red
                exit 1
            }

            if (Test-Path -LiteralPath $targetPath -PathType Container) {
                Copy-Item -LiteralPath $targetPath -Destination $dstGroup -Recurse -Force
            } else {
                Copy-Item -LiteralPath $targetPath -Destination $dstGroup -Force
            }
        }
    }

    # 9. 壓縮成 zip 放到專案根目錄（最上層包含 13_學號_姓名\）
    $zipPath = Join-Path $repoRoot "$folderName.zip"
    if (Test-Path -LiteralPath $zipPath) {
        Remove-Item -LiteralPath $zipPath -Force
    }

    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory(
        $tempBase,
        $zipPath,
        [System.IO.Compression.CompressionLevel]::Optimal,
        $false,
        [System.Text.Encoding]::UTF8
    )

    Write-Host ''
    Write-Host "打包完成：$zipPath" -ForegroundColor Green
    Write-Host 'zip上傳後記得刪除，不要推到倉庫裡' -ForegroundColor Yellow
}
catch {
    Write-Host "執行發生錯誤：$($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    if ($tempBase -and (Test-Path -LiteralPath $tempBase)) {
        Remove-Item -LiteralPath $tempBase -Recurse -Force -ErrorAction SilentlyContinue
    }
}
