@echo off
REM GitHub 仓库初始化脚本 (Windows 版)
REM 用法: init_github_repo.bat [github-username] [repo-name]

set GITHUB_USER=%1
set REPO_NAME=%2

if "%GITHUB_USER%"=="" set GITHUB_USER=yuanxin87-blip
if "%REPO_NAME%"=="" set REPO_NAME=youtube-cloud-downloader

set REPO_URL=https://github.com/%GITHUB_USER%/%REPO_NAME%.git

echo ==========================================
echo YouTube Cloud Downloader - GitHub 初始化
echo ==========================================
echo 用户: %GITHUB_USER%
echo 仓库: %REPO_NAME%
echo URL:  %REPO_URL%
echo.

REM 检查 gh CLI
where gh >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 GitHub CLI (gh)
    echo 请先安装: https://cli.github.com/
    echo 或手动在 GitHub 网页创建仓库
    pause
    exit /b 1
)

REM 检查登录状态
gh auth status >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔐 请先登录 GitHub CLI:
    gh auth login
)

REM 初始化 git
echo 📁 初始化 Git 仓库...
git init
git config user.name "%GITHUB_USER%"
git config user.email "%GITHUB_USER%@users.noreply.github.com"

REM 创建 .gitignore
echo 📝 创建 .gitignore...
(
echo # Python
echo __pycache__/
echo *.pyc
echo *.pyo
echo *.pyd
echo .Python
echo venv/
echo env/
echo .env
echo.
echo # Build
echo dist/
echo build/
echo *.spec
echo *.exe
echo.
echo # Downloads
echo downloads/
echo *.mp4
echo *.m4a
echo *.webm
echo.
echo # IDE
echo .vscode/
echo .idea/
echo *.swp
echo *.swo
echo.
echo # OS
echo .DS_Store
echo Thumbs.db
) > .gitignore

REM 添加文件
echo 📦 添加文件...
git add .

REM 提交
echo 💾 提交初始版本...
git commit -m "feat: 初始化 YouTube Cloud Downloader

- GitHub Actions 工作流下载 YouTube 视频
- 支持多质量选择 (best/1080p/720p/480p/360p/audio)
- 支持代理下载
- 自动上传 MP4 为 Artifact"

REM 创建远程仓库并推送
echo ☁️  创建 GitHub 仓库并推送...
gh repo create "%GITHUB_USER%/%REPO_NAME%" ^
    --public ^
    --description "YouTube 视频云端下载器 - 基于 GitHub Actions + yt-dlp" ^
    --source=. ^
    --remote=origin ^
    --push

echo.
echo ✅ 完成！
echo ==========================================
echo 📋 下一步使用方法：
echo 1. 访问: https://github.com/%GITHUB_USER%/%REPO_NAME%/actions
echo 2. 点击左侧 'YouTube Cloud Downloader'
echo 3. 点击 'Run workflow' -> 填入 YouTube 链接
echo 4. 等待完成 -> 下载 Artifact (右侧 Artifacts 区)
echo ==========================================
pause