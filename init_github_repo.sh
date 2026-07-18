#!/bin/bash
# GitHub 仓库初始化脚本
# 用法: bash init_github_repo.sh [github-username] [repo-name]

set -e

GITHUB_USER="${1:-yuanxin87-blip}"
REPO_NAME="${2:-youtube-cloud-downloader}"
REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

echo "=========================================="
echo "YouTube Cloud Downloader - GitHub 初始化"
echo "=========================================="
echo "用户: ${GITHUB_USER}"
echo "仓库: ${REPO_NAME}"
echo "URL:  ${REPO_URL}"
echo ""

# 检查 gh CLI
if ! command -v gh &> /dev/null; then
    echo "❌ 未找到 GitHub CLI (gh)"
    echo "请先安装: https://cli.github.com/"
    echo "或手动在 GitHub 网页创建仓库"
    exit 1
fi

# 检查是否已登录
if ! gh auth status &> /dev/null; then
    echo "🔐 请先登录 GitHub CLI:"
    gh auth login
fi

# 初始化 git
echo "📁 初始化 Git 仓库..."
git init
git config user.name "${GITHUB_USER}"
git config user.email "${GITHUB_USER}@users.noreply.github.com"

# 创建 .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
.env

# Build
dist/
build/
*.spec
*.exe

# Downloads
downloads/
*.mp4
*.m4a
*.webm

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF

# 添加文件
echo "📦 添加文件..."
git add .

# 提交
echo "💾 提交初始版本..."
git commit -m "feat: 初始化 YouTube Cloud Downloader

- GitHub Actions 工作流下载 YouTube 视频
- 支持多质量选择 (best/1080p/720p/480p/360p/audio)
- 支持代理下载
- 自动上传 MP4 为 Artifact"

# 创建远程仓库
echo "☁️  创建 GitHub 仓库..."
gh repo create "${GITHUB_USER}/${REPO_NAME}" \
    --public \
    --description "YouTube 视频云端下载器 - 基于 GitHub Actions + yt-dlp" \
    --source=. \
    --remote=origin \
    --push

echo ""
echo "✅ 完成！"
echo "=========================================="
echo "📋 下一步使用方法："
echo "1. 访问: https://github.com/${GITHUB_USER}/${REPO_NAME}/actions"
echo "2. 点击左侧 'YouTube Cloud Downloader'"
echo "3. 点击 'Run workflow' -> 填入 YouTube 链接"
echo "4. 等待完成 -> 下载 Artifact (右侧 Artifacts 区)"
echo "=========================================="