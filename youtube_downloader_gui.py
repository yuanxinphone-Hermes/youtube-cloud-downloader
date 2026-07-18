#!/usr/bin/env python3
"""
YouTube MP4 Downloader with OPML Subscription Import
- Single video download
- Batch download from OPML (YouTube subscriptions)
- Proxy support
- Quality selection
"""
import os
import sys
import threading
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Try to import yt_dlp
try:
    import yt_dlp
except ImportError:
    yt_dlp = None


class MyLogger:
    def __init__(self, app):
        self.app = app

    def debug(self, msg):
        if msg.strip():
            self.app.log(msg)

    def info(self, msg):
        if msg.strip():
            self.app.log(msg)

    def warning(self, msg):
        if msg.strip():
            self.app.log(f"WARNING: {msg}")

    def error(self, msg):
        if msg.strip():
            self.app.log(f"ERROR: {msg}")


class YoutubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube MP4 Downloader")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Configure Grid weight
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Style
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Variables
        self.url_var = tk.StringVar()
        self.quality_var = tk.StringVar(value="best")
        self.save_dir_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.filename_var = tk.StringVar()
        self.proxy_var = tk.StringVar()
        self.downloading = False
        self.single_stop = False
        
        # Batch download variables
        self.batch_urls = []  # List of (channel, title, url) tuples
        self.batch_stop = False

        # Main Container with Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # ==================== TAB 1: Single Video Download ====================
        self.tab_single = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.tab_single, text=" 单个视频下载 ")
        self.tab_single.columnconfigure(1, weight=1)
        self._build_single_tab()

        # ==================== TAB 2: Batch Download from OPML ====================
        self.tab_batch = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(self.tab_batch, text=" 批量下载 (OPML订阅) ")
        self.tab_batch.columnconfigure(1, weight=1)
        self.tab_batch.rowconfigure(4, weight=1)
        self._build_batch_tab()

        # Status Bar (shared)
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        self.status_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        # Custom button style
        self.style.configure("Accent.TButton", foreground="black", background="#d1e7dd", font=("Segoe UI", 10, "bold"))
        self.style.configure("Danger.TButton", foreground="white", background="#dc3545", font=("Segoe UI", 10, "bold"))

        # Check dependencies
        self.check_or_install_dependencies()

    # ==================== UI BUILDERS ====================
    def _build_single_tab(self):
        f = self.tab_single
        # URL
        ttk.Label(f, text="YouTube 链接:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.url_entry = ttk.Entry(f, textvariable=self.url_var, font=("Segoe UI", 10))
        self.url_entry.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        self.url_entry.focus()

        # Options Frame
        opt = ttk.LabelFrame(f, text=" 设置 ", padding="10")
        opt.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        opt.columnconfigure(1, weight=1)

        # Quality
        ttk.Label(opt, text="视频质量:").grid(row=0, column=0, sticky="w", pady=5)
        self.quality_combo = ttk.Combobox(
            opt, textvariable=self.quality_var,
            values=["best", "1080p", "720p", "480p", "360p", "audio"],
            state="readonly", width=15
        )
        self.quality_combo.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        # Custom Filename
        ttk.Label(opt, text="自定义文件名 (可选):").grid(row=1, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(opt, textvariable=self.filename_var)
        self.name_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=5)

        # Save Directory
        ttk.Label(opt, text="保存目录:").grid(row=2, column=0, sticky="w", pady=5)
        self.dir_entry = ttk.Entry(opt, textvariable=self.save_dir_var)
        self.dir_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        ttk.Button(opt, text="浏览...", command=self.browse_directory).grid(row=2, column=2, sticky="e", pady=5)

        # Proxy
        ttk.Label(opt, text="代理 (可选):").grid(row=3, column=0, sticky="w", pady=5)
        self.proxy_entry = ttk.Entry(opt, textvariable=self.proxy_var)
        self.proxy_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        ttk.Label(opt, text="例: socks5://127.0.0.1:7890 或 http://127.0.0.1:7890", font=("Segoe UI", 8), foreground="gray").grid(row=4, column=1, columnspan=2, sticky="w", padx=10, pady=(0, 5))

        # Download Button
        btn_frame = ttk.Frame(f)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=(5, 15), sticky="ew")
        self.download_btn = ttk.Button(btn_frame, text="下载视频", style="Accent.TButton", command=self.start_download)
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.single_stop_btn = ttk.Button(btn_frame, text="停止下载", style="Danger.TButton", command=self.stop_single_download, state="disabled")
        self.single_stop_btn.pack(side="left", fill="x", expand=True)

        # Log Area
        ttk.Label(f, text="下载日志 / 进度:", font=("Segoe UI", 9, "bold")).grid(row=4, column=0, sticky="w", pady=(0, 5))
        log_frame = ttk.Frame(f)
        log_frame.grid(row=5, column=0, columnspan=3, sticky="nsew", pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        f.rowconfigure(5, weight=1)

        self.log_text = tk.Text(log_frame, height=12, wrap="word", font=("Consolas", 9), background="#f8f9fa")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _build_batch_tab(self):
        f = self.tab_batch
        # OPML Import Section
        ttk.Label(f, text="导入 YouTube 订阅 (OPML):", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        opml_frame = ttk.Frame(f)
        opml_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        opml_frame.columnconfigure(0, weight=1)
        
        self.opml_path_var = tk.StringVar()
        ttk.Entry(opml_frame, textvariable=self.opml_path_var, font=("Segoe UI", 9)).grid(row=0, column=0, sticky="ew", padx=(0, 10))
        ttk.Button(opml_frame, text="选择 OPML 文件", command=self.browse_opml).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(opml_frame, text="解析订阅并获取最新视频", command=self.parse_opml_and_fetch).grid(row=0, column=2)

        # Settings for batch (shared quality, dir, proxy)
        opt = ttk.LabelFrame(f, text=" 批量下载设置 ", padding="10")
        opt.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 15))
        opt.columnconfigure(1, weight=1)

        ttk.Label(opt, text="视频质量:").grid(row=0, column=0, sticky="w", pady=5)
        self.batch_quality_var = tk.StringVar(value="best")
        ttk.Combobox(opt, textvariable=self.batch_quality_var,
            values=["best", "1080p", "720p", "480p", "360p", "audio"],
            state="readonly", width=15).grid(row=0, column=1, sticky="w", padx=10, pady=5)

        ttk.Label(opt, text="保存目录:").grid(row=1, column=0, sticky="w", pady=5)
        self.batch_dir_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        ttk.Entry(opt, textvariable=self.batch_dir_var).grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        ttk.Button(opt, text="浏览...", command=lambda: self.browse_directory_var(self.batch_dir_var)).grid(row=1, column=2, sticky="e", pady=5)

        ttk.Label(opt, text="代理 (可选):").grid(row=2, column=0, sticky="w", pady=5)
        self.batch_proxy_var = tk.StringVar()
        ttk.Entry(opt, textvariable=self.batch_proxy_var).grid(row=2, column=1, columnspan=2, sticky="ew", padx=10, pady=5)

        # Video List (Treeview)
        ttk.Label(f, text="待下载视频列表 (双击→单个下载，Delete/Backspace→删除，Shift/Ctrl+点击多选):", font=("Segoe UI", 9, "bold")).grid(row=3, column=0, sticky="w", pady=(0, 5))
        
        list_frame = ttk.Frame(f)
        list_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(0, 15))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        f.rowconfigure(4, weight=1)

        cols = ("channel", "title", "url")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=10, selectmode="extended")
        self.tree.heading("channel", text="频道/来源")
        self.tree.heading("title", text="视频标题")
        self.tree.heading("url", text="链接")
        self.tree.column("channel", width=200, anchor="w")
        self.tree.column("title", width=400, anchor="w")
        self.tree.column("url", width=200, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        # Double-click: send to single download tab
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        # Delete key: remove selected items
        self.tree.bind("<Delete>", self.on_tree_delete)
        # Also bind Backspace for convenience
        self.tree.bind("<BackSpace>", self.on_tree_delete)
        
        tree_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=tree_scroll.set)

        # Batch Action Buttons
        btn_frame = ttk.Frame(f)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=(0, 10))
        self.batch_download_btn = ttk.Button(btn_frame, text="开始批量下载", style="Accent.TButton", command=self.start_batch_download)
        self.batch_download_btn.pack(side="left", padx=5)
        self.batch_stop_btn = ttk.Button(btn_frame, text="停止下载", style="Danger.TButton", command=self.stop_batch_download, state="disabled")
        self.batch_stop_btn.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="清空列表", command=self.clear_batch_list).pack(side="left", padx=5)

        # Batch Log
        ttk.Label(f, text="批量下载日志:", font=("Segoe UI", 9, "bold")).grid(row=6, column=0, sticky="w", pady=(0, 5))
        log_frame = ttk.Frame(f)
        log_frame.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        f.rowconfigure(7, weight=1)

        self.batch_log_text = tk.Text(log_frame, height=8, wrap="word", font=("Consolas", 9), background="#f8f9fa")
        self.batch_log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.batch_log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.batch_log_text.configure(yscrollcommand=scrollbar.set)

    # ==================== HELPERS ====================
    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.save_dir_var.get())
        if directory:
            self.save_dir_var.set(directory)

    def browse_directory_var(self, var: tk.StringVar):
        directory = filedialog.askdirectory(initialdir=var.get())
        if directory:
            var.set(directory)

    def browse_opml(self):
        path = filedialog.askopenfilename(
            title="选择 YouTube 订阅 OPML 文件",
            filetypes=[("OPML files", "*.opml"), ("XML files", "*.xml"), ("All files", "*.*")]
        )
        if path:
            self.opml_path_var.set(path)

    def log(self, message: str, clear: bool = False, batch: bool = False):
        target = self.batch_log_text if batch else self.log_text
        target.config(state="normal")
        if clear:
            target.delete("1.0", tk.END)
        target.insert(tk.END, message + "\n")
        target.see(tk.END)
        target.config(state="disabled")

    def check_or_install_dependencies(self):
        global yt_dlp
        if yt_dlp is not None:
            self.log("✓ yt-dlp 已可用")
            return

        def task():
            global yt_dlp
            self.status_var.set("检查依赖...")
            self.log("yt-dlp 未安装，正在通过 pip 安装...")
            try:
                import subprocess
                subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp", "-q"], check=True)
                import yt_dlp
                self.log("✓ yt-dlp 安装并加载成功!")
                self.status_var.set("就绪")
            except Exception as e:
                self.log(f"✗ 安装 yt-dlp 失败: {e}")
                self.status_var.set("错误: 缺少 yt-dlp")
                messagebox.showerror("依赖错误", f"无法加载或安装 yt-dlp: {e}")
        threading.Thread(target=task, daemon=True).start()

    # ==================== OPML PARSING ====================
    def parse_opml_and_fetch(self):
        opml_path = self.opml_path_var.get().strip()
        if not opml_path:
            messagebox.showwarning("提示", "请先选择 OPML 文件")
            return
        if not os.path.exists(opml_path):
            messagebox.showerror("错误", "OPML 文件不存在")
            return

        self.log("正在解析 OPML 文件...", batch=True)
        self.status_var.set("解析 OPML 中...")
        
        def worker():
            try:
                channels = self._parse_opml(opml_path)
                self.log(f"找到 {len(channels)} 个订阅频道", batch=True)
                
                # Fetch latest video for each channel
                videos = []
                for i, (channel_title, channel_url) in enumerate(channels):
                    self.log(f"[{i+1}/{len(channels)}] 获取: {channel_title} ...", batch=True)
                    latest = self._get_latest_video(channel_url, channel_title)
                    if latest:
                        videos.append(latest)
                        self.log(f"  → 找到: {latest[1]}", batch=True)
                    else:
                        self.log(f"  → 未找到视频或获取失败", batch=True)
                
                # Update UI on main thread
                self.root.after(0, lambda: self._populate_batch_list(videos))
                self.root.after(0, lambda: self.status_var.set(f"就绪 - 找到 {len(videos)} 个视频"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log(f"✗ 解析失败: {e}", batch=True))
                self.root.after(0, lambda: self.status_var.set("解析失败"))
                self.root.after(0, lambda: messagebox.showerror("错误", f"解析 OPML 失败:\n{e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _parse_opml(self, opml_path: str):
        """Parse OPML and return list of (channel_title, channel_url)"""
        tree = ET.parse(opml_path)
        root = tree.getroot()
        
        channels = []
        # OPML structure: <opml><body><outline ...><outline .../></outline></body></opml>
        for outline in root.iter("outline"):
            # YouTube OPML typically has: text="Channel Name", xmlUrl="https://www.youtube.com/feeds/videos.xml?channel_id=UC..."
            xml_url = outline.get("xmlUrl") or outline.get("xml_url")
            title = outline.get("text") or outline.get("title") or "Unknown"
            
            if xml_url and "youtube.com" in xml_url:
                # Extract channel_id from xmlUrl
                # Format: https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxxxx
                parsed = urlparse(xml_url)
                qs = parse_qs(parsed.query)
                channel_id = qs.get("channel_id", [None])[0]
                if channel_id:
                    # Use the channel URL format that yt-dlp can handle
                    channel_url = f"https://www.youtube.com/channel/{channel_id}"
                    channels.append((title, channel_url))
        
        return channels

    def _get_latest_video(self, channel_url: str, channel_title: str):
        """Use yt-dlp to extract the latest video from a channel"""
        global yt_dlp
        if yt_dlp is None:
            try:
                import yt_dlp
            except ImportError:
                return None
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'playlistend': 1,  # Only get first (latest) video
        }
        
        # Add proxy if configured
        proxy = self.batch_proxy_var.get().strip()
        if proxy:
            ydl_opts['proxy'] = proxy
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(channel_url, download=False)
                if result and 'entries' in result and result['entries']:
                    entry = result['entries'][0]
                    video_url = entry.get('url') or entry.get('webpage_url')
                    video_title = entry.get('title', 'Unknown Title')
                    if video_url:
                        return (channel_title, video_title, video_url)
        except Exception as e:
            self.log(f"  获取失败: {e}", batch=True)
        return None

    def _populate_batch_list(self, videos):
        """Populate the treeview with fetched videos"""
        self.batch_urls = videos
        self.tree.delete(*self.tree.get_children())
        for channel, title, url in videos:
            self.tree.insert("", "end", values=(channel, title, url))
        self.log(f"列表已更新，共 {len(videos)} 个视频待下载", batch=True)

    def on_tree_double_click(self, event):
        """Double-click: send selected video URL to single download tab"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            values = self.tree.item(item, "values")
            if values and len(values) >= 3:
                url = values[2]
                self.url_var.set(url)
                self.notebook.select(self.tab_single)
                self.url_entry.focus()
                self.log(f"已发送到单个下载: {values[1]}")

    def on_tree_delete(self, event):
        """Delete/Backspace key: remove all selected items (supports multi-select with Shift/Ctrl)"""
        selection = self.tree.selection()
        if not selection:
            return
        # Get all children in order, then filter selected ones
        all_children = self.tree.get_children()
        # Get indices of selected items
        selected_indices = [all_children.index(item) for item in selection]
        # Sort in reverse order for correct deletion
        for idx in sorted(selected_indices, reverse=True):
            self.tree.delete(all_children[idx])
            if 0 <= idx < len(self.batch_urls):
                self.batch_urls.pop(idx)
        self.log(f"已移除 {len(selected_indices)} 个视频", batch=True)

    def clear_batch_list(self):
        self.tree.delete(*self.tree.get_children())
        self.batch_urls.clear()
        self.log("列表已清空", batch=True)

    # ==================== DOWNLOAD LOGIC ====================
    def _build_ydl_opts(self, quality: str, out_dir: Path, custom_name: str = "", proxy: str = ""):
        quality_formats = {
            "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]",
            "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]",
            "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]",
            "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]",
            "audio": "bestaudio[ext=m4a]/bestaudio",
        }
        format_selector = quality_formats.get(quality, quality_formats["best"])
        
        if custom_name:
            out_template = str(out_dir / f"{custom_name}.%(ext)s")
        else:
            out_template = str(out_dir / "%(title)s.%(ext)s")
        
        opts = {
            'format': format_selector,
            'merge_output_format': 'mp4',
            'outtmpl': out_template,
            'nocheckcertificate': True,
            'logger': MyLogger(self),
            'progress_hooks': [self.download_progress_hook],
            'no_warnings': True,
            'quiet': False
        }
        if proxy:
            opts['proxy'] = proxy
        return opts

    def download_progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '').strip().replace('\x1b[0;33m', '').replace('\x1b[0m', '')
            if percent:
                self.status_var.set(f"下载中... {percent}")
        elif d['status'] == 'finished':
            self.status_var.set("后处理 (合并中)...")

    # ==================== SINGLE DOWNLOAD ====================
    def start_download(self):
        global yt_dlp
        if yt_dlp is None:
            try:
                import yt_dlp
            except ImportError:
                messagebox.showerror("错误", "yt-dlp 尚未加载，请稍等或重启")
                return

        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("输入错误", "请粘贴 YouTube 链接!")
            return
        if "youtube.com" not in url and "youtu.be" not in url:
            messagebox.showwarning("输入错误", "请提供有效的 YouTube 链接!")
            return
        if self.downloading:
            messagebox.showinfo("等待", "已有下载任务在进行中")
            return

        self.downloading = True
        self.single_stop = False
        self.download_btn.config(state="disabled")
        self.single_stop_btn.config(state="normal")
        self.status_var.set("下载中...")
        self.log("开始下载...", clear=True)
        threading.Thread(target=self.download_worker, args=(url,), daemon=True).start()

    def stop_single_download(self):
        self.single_stop = True
        self.log("正在停止下载... (当前片段完成后停止)")
        self.single_stop_btn.config(state="disabled")

    def download_worker(self, url: str):
        global yt_dlp
        quality = self.quality_var.get()
        out_dir = Path(self.save_dir_var.get())
        custom_name = self.filename_var.get().strip()
        proxy = self.proxy_var.get().strip()

        ydl_opts = self._build_ydl_opts(quality, out_dir, custom_name, proxy)
        
        # Add progress hook to check for stop signal
        original_hooks = ydl_opts.get('progress_hooks', [])
        def stop_check_hook(d):
            if self.single_stop:
                raise Exception("用户取消下载")
            # Call original hooks
            for hook in original_hooks:
                hook(d)
            # Also call the existing progress hook
            self.download_progress_hook(d)
        ydl_opts['progress_hooks'] = [stop_check_hook]

        self.log(f"目标: {url}")
        self.log(f"质量: {quality}")
        self.log(f"输出: {out_dir}\n")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            if not self.single_stop:
                self.log("\n✓ 下载完成!")
                self.status_var.set("下载成功!")
                messagebox.showinfo("成功", "视频下载成功!")
            else:
                self.log("\n⏹ 下载已停止")
                self.status_var.set("下载已停止")
        except Exception as e:
            if "用户取消下载" in str(e):
                self.log("\n⏹ 下载已停止")
                self.status_var.set("下载已停止")
            else:
                self.log(f"\n✗ 下载出错: {e}")
                self.status_var.set("下载失败")
                messagebox.showerror("错误", f"下载失败:\n{e}")
        finally:
            self.downloading = False
            self.download_btn.config(state="normal")
            self.single_stop_btn.config(state="disabled")

    # ==================== BATCH DOWNLOAD ====================
    def start_batch_download(self):
        global yt_dlp
        if yt_dlp is None:
            try:
                import yt_dlp
            except ImportError:
                messagebox.showerror("错误", "yt-dlp 尚未加载")
                return

        if not self.batch_urls:
            messagebox.showwarning("提示", "列表为空，请先解析 OPML 获取视频")
            return
        if self.downloading:
            messagebox.showinfo("等待", "已有下载任务在进行")
            return

        self.downloading = True
        self.batch_stop = False
        self.batch_download_btn.config(state="disabled")
        self.batch_stop_btn.config(state="normal")
        self.status_var.set("批量下载进行中...")
        self.log("=== 开始批量下载 ===\n", batch=True)
        
        threading.Thread(target=self.batch_download_worker, daemon=True).start()

    def stop_batch_download(self):
        self.batch_stop = True
        self.log("正在停止... (当前视频下载完成后停止)", batch=True)
        self.batch_stop_btn.config(state="disabled")

    def batch_download_worker(self):
        global yt_dlp
        quality = self.batch_quality_var.get()
        out_dir = Path(self.batch_dir_var.get())
        proxy = self.batch_proxy_var.get().strip()
        
        total = len(self.batch_urls)
        success = 0
        failed = 0
        
        for idx, (channel, title, url) in enumerate(self.batch_urls):
            if self.batch_stop:
                self.log(f"\n用户停止下载 (已完成 {success}/{total})", batch=True)
                break
            
            self.log(f"\n[{idx+1}/{total}] {channel} - {title}", batch=True)
            self.log(f"URL: {url}", batch=True)
            
            # Use channel name as prefix for filename to avoid conflicts
            safe_channel = "".join(c for c in channel if c.isalnum() or c in " _-").strip()[:50]
            safe_title = "".join(c for c in title if c.isalnum() or c in " _-").strip()[:100]
            custom_name = f"[{safe_channel}] {safe_title}"
            
            ydl_opts = self._build_ydl_opts(quality, out_dir, custom_name, proxy)
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                self.log("  ✓ 完成", batch=True)
                success += 1
            except Exception as e:
                self.log(f"  ✗ 失败: {e}", batch=True)
                failed += 1
            
            self.status_var.set(f"批量下载: {idx+1}/{total} (成功:{success} 失败:{failed})")
        
        # Final summary
        self.log(f"\n=== 批量下载结束: 成功 {success}, 失败 {failed}, 总计 {total} ===", batch=True)
        self.status_var.set(f"批量下载完成: 成功 {success}, 失败 {failed}")
        self.downloading = False
        self.batch_download_btn.config(state="normal")
        self.batch_stop_btn.config(state="disabled")
        
        if not self.batch_stop:
            messagebox.showinfo("完成", f"批量下载结束\n成功: {success}\n失败: {failed}")


def main():
    root = tk.Tk()
    app = YoutubeDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()