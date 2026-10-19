# GitHub Pages に公開するスクリプト（初回も2回目以降もこれ1本）
# 使い方:  .\deploy.ps1 https://github.com/<ユーザー名>/<リポジトリ名>.git
param([string]$RepoUrl)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Copy-Item "波風.html" "docs\index.html" -Force
if (-not (Test-Path ".git")) {
  git init -b main | Out-Null
  if (-not $RepoUrl) { Write-Host "初回はリポジトリURLを引数に渡してください"; exit 1 }
  git remote add origin $RepoUrl
}
git add docs/index.html README.md src deploy.ps1 .gitignore
git commit -m "update 波風 $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>$null
git push -u origin main
Write-Host "公開先: GitHub → Settings → Pages で Branch: main / Folder: /docs を選ぶと https://<ユーザー名>.github.io/<リポジトリ名>/ で見られます"
