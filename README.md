# YouTube 视频云端下载器

基于 **GitHub Actions + yt-dlp** 的 YouTube 视频下载方案，完美解决公司网络无法访问 YouTube 的问题。

> ✅ 无需本地代理 | ✅ 无需本地安装 Python/ffmpeg | ✅ 支持批量下载 | ✅ 结果自动保存为 Artifact

---

## 🚀 快速开始

### 方式一：一键初始化（推荐）

```bash
# 克隆/下载本项目到本地
cd youtube-cloud-downloader

# 运行初始化脚本（自动创建 GitHub 仓库并推送）
bash init_github_repo.sh 你的GitHub用户名 仓库名
# Windows: init_github_repo.bat 你的GitHub用户名 仓库名
```

### 方式二：手动创建

1. 在 GitHub 创建新仓库：`youtube-cloud-downloader` (Public)
2. 上传本项目所有文件到仓库
3. 等待 Actions 自动运行（或手动触发）

---

## 📖 使用方法

### 1. 触发下载

访问仓库的 **Actions** 页面：
```
https://github.com/你的用户名/youtube-cloud-downloader/actions
```

点击左侧 **YouTube Cloud Downloader** → 点击 **Run workflow**

### 2. 填写参数

| 参数 | 说明 | 示例 |
|------|------|------|
| **urls** | YouTube 链接，每行一个或逗号分隔 | 见下方示例 |
| **quality** | 视频质量 | `best` / `1080p` / `720p` / `480p` / `360p` / `audio` |
| **proxy** | 代理地址（可选，GitHub 通常直连） | `socks5://host:port` |
| **template** | 输出文件名模板 | `%(uploader)s/%(title)s.%(ext)s` |

### 3. URL 格式示例

```text
# 单个视频
https://www.youtube.com/watch?v=dQw4w9WgXcQ

# 多个视频（每行一个）
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://youtu.be/jNQXAC9IVRw

# 逗号分隔
https://www.youtube.com/watch?v=abc, https://youtu.be/def

# 播放列表（自动展开所有视频）
https://www.youtube.com/playlist?list=PLxxx

# 频道（下载最新视频）
https://www.youtube.com/@channelname/videos
```

### 4. 获取结果

下载完成后：
- 点击该 workflow run
- 右侧 **Artifacts** 区下载 `youtube-downloads.zip`
- 解压得到按频道/标题组织的 MP4 文件

---

## ⚙️ 高级配置

### 模板变量

| 变量 | 含义 |
|------|------|
| `%(title)s` | 视频标题 |
| `%(uploader)s` | 频道名 |
| `%(upload_date)s` | 上传日期 (YYYYMMDD) |
| `%(id)s` | 视频 ID |
| `%(ext)s` | 扩展名 |
| `%(height)s` | 分辨率高度 |
| `%(resolution)s` | 分辨率 (如 1920x1080) |

### 常用模板

```text
# 按频道分文件夹（默认）
%(uploader)s/%(title)s.%(ext)s

# 简单平铺
%(title)s [%(id)s].%(ext)s

# 含日期
%(upload_date)s - %(uploader)s - %(title)s.%(ext)s

# 含画质
%(title)s [%(height)sp].%(ext)s
```

### 质量选项对照

| 选择 | 实际格式选择器 |
|------|----------------|
| `best` | 最高画质 MP4 (视频+音频合并) |
| `1080p` | ≤1080p 的最佳 MP4 |
| `720p` | ≤720p 的最佳 MP4 |
| `480p` | ≤480p 的最佳 MP4 |
| `360p` | ≤360p 的最佳 MP4 |
| `audio` | 仅音频 M4A |

---

## 🔧 本地测试（可选）

如果想在本地验证脚本逻辑：

```bash
# 安装依赖
pip install yt-dlp

# 运行
python cloud_downloader.py \
  --urls "https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  --quality best \
  --out-dir ./test_downloads
```

---

## 📁 项目结构

```
youtube-cloud-downloader/
├── .github/
│   └── workflows/
│       └── youtube-cloud-downloader.yml   # GitHub Actions 工作流
├── cloud_downloader.py                    # 核心下载脚本
├── init_github_repo.sh                    # Linux/Mac 初始化脚本
├── init_github_repo.bat                   # Windows 初始化脚本
├── .gitignore
└── README.md
```

---

## ❓ 常见问题

### Q: 下载失败 "Sign in to confirm you're not a bot"
**A**: GitHub Actions 运行器 IP 可能被 YouTube 限流。
- 重新运行 workflow（换 IP）
- 或填入 `proxy` 参数使用你的代理

### Q: 视频无声音 / 只有视频
**A**: 选择 `best` 或指定画质时会自动合并音视频。确保选择非 `audio` 选项。

### Q: 私有视频/会员视频无法下载
**A**: 需要提供 cookies。在 workflow 中添加 `COOKIES` secret，脚本中解析（需自行扩展）。

### Q: 单次下载太多视频超时
**A**: 默认超时 120 分钟。大批量建议分批，或修改 workflow 中 `timeout-minutes`。

### Q: Artifact 过期
**A**: 默认保留 7 天（`retention-days: 7`）。及时下载，或改为上传到 Release。

---

## 🔄 进阶：自动化定时下载

编辑 `.github/workflows/youtube-cloud-downloader.yml`，添加 `schedule` 触发器：

```yaml
on:
  workflow_dispatch:  # 手动触发
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨 2 点 (UTC)
```

然后在仓库 Settings → Secrets 添加：
- `SUBSCRIPTION_URLS`: 订阅链接列表（每行一个）
- `DEFAULT_QUALITY`: 默认画质

---

## 📄 许可证

MIT License - 仅供个人学习研究使用，请遵守 YouTube 服务条款。

---

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - 核心下载引擎
- [GitHub Actions](https://github.com/features/actions) - 免费云端计算