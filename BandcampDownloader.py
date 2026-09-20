import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import json
import os
import sys
import logging
from datetime import datetime
import yt_dlp
from yt_dlp.utils import DownloadError

try:
    from yt_dlp.utils import DownloadCancelled
except ImportError:
    class DownloadCancelled(Exception):
        pass

APP_NAME = "Bandcamp Downloader"
APP_VERSION = "3.0.0"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".bandcamp_downloader")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
LOG_PATH = os.path.join(CONFIG_DIR, "bandcamp_downloader.log")


def setup_logging():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    logger = logging.getLogger("BandcampDownloader")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


class TextHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        message = self.format(record)

        def append():
            self.widget.configure(state="normal")
            self.widget.insert("end", message + "\n")
            self.widget.configure(state="disabled")
            self.widget.see("end")

        try:
            self.widget.after(0, append)
        except Exception:
            pass


class YtdlpLogger:
    def __init__(self, logger):
        self.logger = logger

    def debug(self, msg):
        if msg.startswith("[debug] "):
            self.logger.debug(msg)
        else:
            self.logger.info(msg)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)


class ConfigManager:
    DEFAULTS = {
        "theme": "light",
        "download_path": "",
        "audio_format": "mp3",
        "audio_quality": "320",
        "embed_thumbnail": True,
        "embed_metadata": True,
        "create_subfolder": True,
        "keep_original": False,
        "add_track_number": True,
        "filename_template": "%(title)s",
        "ffmpeg_path": ""
    }

    def __init__(self, path):
        self.path = path
        self.data = dict(self.DEFAULTS)
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                for key in self.DEFAULTS:
                    if key in loaded:
                        self.data[key] = loaded[key]
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except OSError:
            pass

    def get(self, key):
        return self.data.get(key, self.DEFAULTS.get(key))

    def set(self, key, value):
        self.data[key] = value


THEMES = {
    "light": {
        "bg": "#f2f2f2",
        "fg": "#1a1a1a",
        "widget_bg": "#ffffff",
        "select_bg": "#0078d7",
        "select_fg": "#ffffff",
        "accent": "#0078d7",
        "border": "#c0c0c0",
        "disabled_fg": "#a0a0a0",
        "tree_bg": "#ffffff",
        "tree_alt": "#eef2f7",
        "log_bg": "#ffffff",
        "log_fg": "#1a1a1a"
    },
    "dark": {
        "bg": "#1e1e1e",
        "fg": "#e0e0e0",
        "widget_bg": "#2b2b2b",
        "select_bg": "#0e639c",
        "select_fg": "#ffffff",
        "accent": "#3391ff",
        "border": "#3f3f3f",
        "disabled_fg": "#707070",
        "tree_bg": "#252526",
        "tree_alt": "#2d2d30",
        "log_bg": "#121212",
        "log_fg": "#d4d4d4"
    }
}


class ThemeManager:
    def __init__(self, root, style):
        self.root = root
        self.style = style
        self.raw_widgets = []
        self.trees = []
        self.current = "light"

    def register_raw_widget(self, widget):
        self.raw_widgets.append(widget)

    def register_tree(self, tree):
        self.trees.append(tree)

    def apply(self, theme_name):
        colors = THEMES.get(theme_name, THEMES["light"])
        self.current = theme_name
        style = self.style
        style.theme_use("clam")

        style.configure(".", background=colors["bg"], foreground=colors["fg"], fieldbackground=colors["widget_bg"])
        style.configure("TFrame", background=colors["bg"])
        style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
        style.configure("TLabelframe", background=colors["bg"], foreground=colors["fg"], bordercolor=colors["border"])
        style.configure("TLabelframe.Label", background=colors["bg"], foreground=colors["fg"])
        style.configure("TCheckbutton", background=colors["bg"], foreground=colors["fg"])
        style.map("TCheckbutton", background=[("active", colors["bg"])])
        style.configure("TRadiobutton", background=colors["bg"], foreground=colors["fg"])
        style.map("TRadiobutton", background=[("active", colors["bg"])])
        style.configure("TButton", background=colors["widget_bg"], foreground=colors["fg"], bordercolor=colors["border"])
        style.map(
            "TButton",
            background=[("active", colors["accent"]), ("disabled", colors["bg"])],
            foreground=[("active", colors["select_fg"]), ("disabled", colors["disabled_fg"])]
        )
        style.configure("Accent.TButton", background=colors["accent"], foreground=colors["select_fg"])
        style.map("Accent.TButton", background=[("active", colors["accent"]), ("disabled", colors["bg"])])
        style.configure("TEntry", fieldbackground=colors["widget_bg"], foreground=colors["fg"], bordercolor=colors["border"], insertcolor=colors["fg"])
        style.configure("TCombobox", fieldbackground=colors["widget_bg"], background=colors["widget_bg"], foreground=colors["fg"])
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", colors["widget_bg"])],
            foreground=[("readonly", colors["fg"])]
        )
        style.configure("TNotebook", background=colors["bg"], bordercolor=colors["border"])
        style.configure("TNotebook.Tab", background=colors["bg"], foreground=colors["fg"], padding=(12, 6))
        style.map(
            "TNotebook.Tab",
            background=[("selected", colors["accent"])],
            foreground=[("selected", colors["select_fg"])]
        )
        style.configure("TSeparator", background=colors["border"])
        style.configure("TProgressbar", background=colors["accent"], troughcolor=colors["widget_bg"], bordercolor=colors["border"])
        style.configure("Treeview", background=colors["tree_bg"], fieldbackground=colors["tree_bg"], foreground=colors["fg"])
        style.map(
            "Treeview",
            background=[("selected", colors["select_bg"])],
            foreground=[("selected", colors["select_fg"])]
        )
        style.configure("Treeview.Heading", background=colors["widget_bg"], foreground=colors["fg"])
        style.configure("TScrollbar", background=colors["widget_bg"], troughcolor=colors["bg"])
        style.configure("Vertical.TScrollbar", background=colors["widget_bg"], troughcolor=colors["bg"])

        self.root.configure(background=colors["bg"])

        for widget in self.raw_widgets:
            try:
                widget.configure(bg=colors["log_bg"], fg=colors["log_fg"], insertbackground=colors["fg"])
            except tk.TclError:
                pass

        for tree in self.trees:
            tree.tag_configure("evenrow", background=colors["tree_bg"])
            tree.tag_configure("oddrow", background=colors["tree_alt"])


class BandcampDownloaderV3:
    def __init__(self, root):
        self.logger = setup_logging()
        self.logger.info("Application starting, version %s", APP_VERSION)

        self.config = ConfigManager(CONFIG_PATH)

        self.root = root
        root.title(f"{APP_NAME} V3")
        root.geometry("840x1000")
        root.minsize(840, 1000)
        root.resizable(False, False)

        self.style = ttk.Style()
        self.theme_manager = ThemeManager(root, self.style)

        self.queue_items = []
        self.download_history = []
        self.is_downloading = False
        self.cancel_event = threading.Event()

        self.setup_menu()
        self.setup_status_bar()

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self.download_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.history_tab = ttk.Frame(self.notebook)
        self.logs_tab = ttk.Frame(self.notebook)
        self.about_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.download_tab, text="Download")
        self.notebook.add(self.settings_tab, text="Settings")
        self.notebook.add(self.history_tab, text="History")
        self.notebook.add(self.logs_tab, text="Logs")
        self.notebook.add(self.about_tab, text="About")

        self.setup_download_tab()
        self.setup_settings_tab()
        self.setup_history_tab()
        self.setup_logs_tab()
        self.setup_about_tab()

        self.on_format_change()
        self.theme_manager.apply(self.config.get("theme"))

        root.report_callback_exception = self.handle_tk_exception
        threading.excepthook = self.handle_thread_exception
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.logger.info("Application initialized successfully")

    def setup_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Settings", command=self.save_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Light Theme", command=lambda: self.set_theme("light"))
        view_menu.add_command(label="Dark Theme", command=lambda: self.set_theme("dark"))
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: self.notebook.select(self.about_tab))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def setup_status_bar(self):
        bar = ttk.Frame(self.root)
        bar.pack(side="bottom", fill="x")
        self.app_status_var = tk.StringVar(value="Ready")
        ttk.Label(bar, textvariable=self.app_status_var, anchor="w").pack(side="left", padx=8, pady=4)
        ttk.Label(bar, text=f"Version {APP_VERSION}", anchor="e").pack(side="right", padx=8, pady=4)
        ttk.Separator(self.root, orient="horizontal").pack(side="bottom", fill="x")

    def setup_download_tab(self):
        container = ttk.Frame(self.download_tab, padding=10)
        container.pack(fill="both", expand=True)

        input_frame = ttk.LabelFrame(container, text="Add Albums", padding=12)
        input_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(input_frame, text="Bandcamp URLs (one per line):").pack(anchor="w")
        self.url_text = tk.Text(input_frame, height=4, wrap="word")
        self.url_text.pack(fill="x", pady=(5, 8))
        self.theme_manager.register_raw_widget(self.url_text)

        path_row = ttk.Frame(input_frame)
        path_row.pack(fill="x", pady=(0, 8))
        ttk.Label(path_row, text="Download Path:", width=16).pack(side="left")
        self.path_var = tk.StringVar(value=self.config.get("download_path"))
        ttk.Entry(path_row, textvariable=self.path_var).pack(side="left", fill="x", expand=True, padx=(5, 5))
        ttk.Button(path_row, text="Browse", command=self.browse_path, width=10).pack(side="left")

        action_row = ttk.Frame(input_frame)
        action_row.pack(fill="x")
        ttk.Button(action_row, text="Add to Queue", style="Accent.TButton", command=self.add_to_queue).pack(side="left")
        ttk.Button(action_row, text="Clear Input", command=self.clear_input).pack(side="left", padx=(10, 0))

        format_frame = ttk.LabelFrame(container, text="Format and Quality", padding=12)
        format_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(format_frame, text="Audio Format:", width=16).pack(side="left")
        self.format_var = tk.StringVar(value=self.config.get("audio_format"))
        self.format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.format_var,
            values=["mp3", "flac", "wav", "ogg", "opus", "aac", "m4a", "vorbis", "alac", "best"],
            state="readonly",
            width=12
        )
        self.format_combo.pack(side="left", padx=(5, 20))
        self.format_combo.bind("<<ComboboxSelected>>", self.on_format_change)

        ttk.Label(format_frame, text="Quality (kbps):").pack(side="left")
        self.quality_var = tk.StringVar(value=self.config.get("audio_quality"))
        self.quality_combo = ttk.Combobox(
            format_frame,
            textvariable=self.quality_var,
            values=["128", "192", "256", "320", "best"],
            state="readonly",
            width=10
        )
        self.quality_combo.pack(side="left", padx=(5, 0))

        queue_frame = ttk.LabelFrame(container, text="Download Queue", padding=12)
        queue_frame.pack(fill="both", expand=True, pady=(0, 10))

        columns = ("no", "url", "status")
        self.queue_tree = ttk.Treeview(queue_frame, columns=columns, show="headings", height=8)
        self.queue_tree.heading("no", text="#")
        self.queue_tree.heading("url", text="URL")
        self.queue_tree.heading("status", text="Status")
        self.queue_tree.column("no", width=40, anchor="center")
        self.queue_tree.column("url", width=420)
        self.queue_tree.column("status", width=110, anchor="center")

        queue_scroll = ttk.Scrollbar(queue_frame, orient="vertical", command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=queue_scroll.set)
        self.queue_tree.pack(side="left", fill="both", expand=True)
        queue_scroll.pack(side="right", fill="y")
        self.theme_manager.register_tree(self.queue_tree)

        queue_btn_row = ttk.Frame(container)
        queue_btn_row.pack(fill="x", pady=(0, 10))
        self.queue_summary_var = tk.StringVar(value="0 item(s) in queue")
        ttk.Label(queue_btn_row, textvariable=self.queue_summary_var).pack(side="left")
        ttk.Button(queue_btn_row, text="Remove Selected", command=self.remove_selected_from_queue).pack(side="right", padx=(5, 0))
        ttk.Button(queue_btn_row, text="Clear Queue", command=self.clear_queue).pack(side="right")

        progress_frame = ttk.LabelFrame(container, text="Progress", padding=12)
        progress_frame.pack(fill="x", pady=(0, 10))

        self.queue_label_var = tk.StringVar(value="No active download")
        ttk.Label(progress_frame, textvariable=self.queue_label_var).pack(anchor="w")

        ttk.Label(progress_frame, text="Overall Progress:").pack(anchor="w", pady=(8, 0))
        self.overall_progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.overall_progress.pack(fill="x", pady=(2, 8))

        ttk.Label(progress_frame, text="Current Item Progress:").pack(anchor="w")
        self.current_progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.current_progress.pack(fill="x", pady=(2, 8))

        self.info_var = tk.StringVar(value="Ready to download")
        ttk.Label(progress_frame, textvariable=self.info_var).pack(anchor="w")

        self.status_var = tk.StringVar(value="")
        ttk.Label(progress_frame, textvariable=self.status_var, foreground="gray").pack(anchor="w")

        control_row = ttk.Frame(container)
        control_row.pack(pady=5)
        self.download_btn = ttk.Button(control_row, text="Start Queue", style="Accent.TButton", command=self.start_queue_thread, width=18)
        self.download_btn.pack(side="left", padx=10)
        self.cancel_btn = ttk.Button(control_row, text="Cancel", command=self.cancel_download, width=18, state="disabled")
        self.cancel_btn.pack(side="left", padx=10)

    def setup_settings_tab(self):
        container = ttk.Frame(self.settings_tab, padding=10)
        container.pack(fill="both", expand=True)

        appearance_frame = ttk.LabelFrame(container, text="Appearance", padding=12)
        appearance_frame.pack(fill="x", pady=(0, 10))

        self.theme_var = tk.StringVar(value=self.config.get("theme"))
        ttk.Radiobutton(appearance_frame, text="Light Theme", variable=self.theme_var, value="light", command=self.on_theme_change).pack(side="left", padx=(0, 20))
        ttk.Radiobutton(appearance_frame, text="Dark Theme", variable=self.theme_var, value="dark", command=self.on_theme_change).pack(side="left")

        options_frame = ttk.LabelFrame(container, text="Download Options", padding=12)
        options_frame.pack(fill="x", pady=(0, 10))

        self.embed_thumbnail_var = tk.BooleanVar(value=self.config.get("embed_thumbnail"))
        ttk.Checkbutton(options_frame, text="Embed album artwork in audio file", variable=self.embed_thumbnail_var).pack(anchor="w", pady=3)

        self.embed_metadata_var = tk.BooleanVar(value=self.config.get("embed_metadata"))
        ttk.Checkbutton(options_frame, text="Embed metadata (artist, album, track info)", variable=self.embed_metadata_var).pack(anchor="w", pady=3)

        self.create_subfolder_var = tk.BooleanVar(value=self.config.get("create_subfolder"))
        ttk.Checkbutton(options_frame, text="Create subfolder for each album", variable=self.create_subfolder_var).pack(anchor="w", pady=3)

        self.keep_original_var = tk.BooleanVar(value=self.config.get("keep_original"))
        ttk.Checkbutton(options_frame, text="Keep original file after conversion", variable=self.keep_original_var).pack(anchor="w", pady=3)

        self.add_track_number_var = tk.BooleanVar(value=self.config.get("add_track_number"))
        ttk.Checkbutton(options_frame, text="Add track number to filename", variable=self.add_track_number_var).pack(anchor="w", pady=3)

        template_frame = ttk.LabelFrame(container, text="Filename Template", padding=12)
        template_frame.pack(fill="x", pady=(0, 10))

        self.template_var = tk.StringVar(value=self.config.get("filename_template"))
        ttk.Entry(template_frame, textvariable=self.template_var).pack(fill="x", pady=5)
        ttk.Label(template_frame, text="Variables: %(artist)s, %(album)s, %(title)s, %(track_number)s", foreground="gray").pack(anchor="w")

        ffmpeg_frame = ttk.LabelFrame(container, text="FFmpeg Settings", padding=12)
        ffmpeg_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(ffmpeg_frame, text="FFmpeg Path (leave empty for system default):").pack(anchor="w")
        self.ffmpeg_path_var = tk.StringVar(value=self.config.get("ffmpeg_path"))
        ffmpeg_row = ttk.Frame(ffmpeg_frame)
        ffmpeg_row.pack(fill="x", pady=5)
        ttk.Entry(ffmpeg_row, textvariable=self.ffmpeg_path_var).pack(side="left", fill="x", expand=True)
        ttk.Button(ffmpeg_row, text="Browse", command=self.browse_ffmpeg).pack(side="left", padx=(5, 0))
        ttk.Button(ffmpeg_row, text="Test FFmpeg", command=self.test_ffmpeg).pack(side="left", padx=(5, 0))

        action_row = ttk.Frame(container)
        action_row.pack(fill="x", pady=(10, 0))
        ttk.Button(action_row, text="Save Settings", style="Accent.TButton", command=self.save_settings).pack(side="left")
        ttk.Button(action_row, text="Reset to Defaults", command=self.reset_settings).pack(side="left", padx=(10, 0))

    def setup_history_tab(self):
        container = ttk.Frame(self.history_tab, padding=10)
        container.pack(fill="both", expand=True)

        frame = ttk.LabelFrame(container, text="Download History", padding=10)
        frame.pack(fill="both", expand=True)

        columns = ("time", "title", "format", "status")
        self.history_tree = ttk.Treeview(frame, columns=columns, show="headings", height=15)
        self.history_tree.heading("time", text="Time")
        self.history_tree.heading("title", text="Title")
        self.history_tree.heading("format", text="Format")
        self.history_tree.heading("status", text="Status")
        self.history_tree.column("time", width=130)
        self.history_tree.column("title", width=290)
        self.history_tree.column("format", width=80, anchor="center")
        self.history_tree.column("status", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.theme_manager.register_tree(self.history_tree)

        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="Clear History", command=self.clear_history).pack(side="right")

    def setup_logs_tab(self):
        container = ttk.Frame(self.logs_tab, padding=10)
        container.pack(fill="both", expand=True)

        frame = ttk.LabelFrame(container, text="Application Logs", padding=10)
        frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(frame, wrap="word", state="disabled", height=20, borderwidth=1, relief="flat")
        log_scroll = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")
        self.theme_manager.register_raw_widget(self.log_text)

        handler = TextHandler(self.log_text)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S"))
        self.logger.addHandler(handler)

        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_frame, text="Clear Logs", command=self.clear_logs).pack(side="left")
        ttk.Button(btn_frame, text="Open Log File Folder", command=self.open_log_folder).pack(side="left", padx=(10, 0))

    def setup_about_tab(self):
        container = ttk.Frame(self.about_tab, padding=30)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text=APP_NAME, font=("Helvetica", 18, "bold")).pack(pady=10)
        ttk.Label(container, text=f"Version {APP_VERSION}", font=("Helvetica", 11)).pack(pady=5)

        ttk.Separator(container, orient="horizontal").pack(fill="x", pady=20)

        info_frame = ttk.LabelFrame(container, text="Information", padding=15)
        info_frame.pack(fill="x", pady=10)
        ttk.Label(info_frame, text="A tool for downloading music from Bandcamp").pack(pady=3)
        ttk.Label(info_frame, text="Powered by yt-dlp").pack(pady=3)

        format_frame = ttk.LabelFrame(container, text="Supported Formats", padding=15)
        format_frame.pack(fill="x", pady=10)
        ttk.Label(format_frame, text="Lossy: MP3, AAC, OGG, Opus, Vorbis").pack(pady=3)
        ttk.Label(format_frame, text="Lossless: FLAC, WAV, ALAC, M4A").pack(pady=3)

        req_frame = ttk.LabelFrame(container, text="Requirements", padding=15)
        req_frame.pack(fill="x", pady=10)
        ttk.Label(req_frame, text="FFmpeg must be installed for audio conversion").pack(pady=3)
        ttk.Label(req_frame, text="Download FFmpeg from: https://ffmpeg.org", foreground="blue").pack(pady=3)

    def browse_path(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path_var.set(directory)

    def browse_ffmpeg(self):
        filepath = filedialog.askopenfilename(title="Select FFmpeg executable", filetypes=[("All files", "*.*")])
        if filepath:
            self.ffmpeg_path_var.set(filepath)
            self.logger.info("FFmpeg path set to %s", filepath)

    def test_ffmpeg(self):
        ffmpeg_path = self.ffmpeg_path_var.get().strip()
        executable = ffmpeg_path if ffmpeg_path else "ffmpeg"
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
            result = subprocess.run(
                [executable, "-version"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=creationflags
            )
            if result.returncode == 0:
                first_line = result.stdout.splitlines()[0] if result.stdout else "FFmpeg detected"
                self.logger.info("FFmpeg check succeeded: %s", first_line)
                messagebox.showinfo("FFmpeg Check", f"FFmpeg is available.\n\n{first_line}")
            else:
                raise RuntimeError(result.stderr.strip() or "Unknown error")
        except FileNotFoundError:
            self.logger.error("FFmpeg executable not found: %s", executable)
            messagebox.showerror("FFmpeg Check", "FFmpeg executable was not found.\nInstall FFmpeg or set the correct path in Settings.")
        except Exception as e:
            self.logger.error("FFmpeg check failed: %s", e)
            messagebox.showerror("FFmpeg Check", f"FFmpeg check failed:\n{e}")

    def clear_input(self):
        self.url_text.delete("1.0", "end")

    def validate_url(self, url):
        return url.lower().startswith("http") and "bandcamp.com" in url.lower()

    def add_to_queue(self):
        raw_text = self.url_text.get("1.0", "end").strip()
        if not raw_text:
            messagebox.showerror("Error", "Enter at least one Bandcamp URL.")
            return

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        added = 0
        skipped = 0

        for url in lines:
            if not self.validate_url(url):
                skipped += 1
                self.logger.warning("Skipped invalid URL: %s", url)
                continue
            tree_id = self.queue_tree.insert("", "end", values=(len(self.queue_items) + 1, url, "Queued"))
            self.queue_items.append({"tree_id": tree_id, "url": url, "status": "Queued", "title": url})
            added += 1

        self.url_text.delete("1.0", "end")
        self.renumber_queue()
        self.restripe_tree(self.queue_tree)
        self.update_queue_summary()
        self.logger.info("Added %d URL(s) to queue, skipped %d", added, skipped)

        if skipped:
            messagebox.showwarning("Invalid URLs", f"{skipped} URL(s) were skipped because they are not valid Bandcamp links.")

    def remove_selected_from_queue(self):
        if self.is_downloading:
            messagebox.showwarning("Busy", "Cannot modify the queue while downloading.")
            return
        selected = self.queue_tree.selection()
        if not selected:
            return
        self.queue_items = [item for item in self.queue_items if item["tree_id"] not in selected]
        for tree_id in selected:
            self.queue_tree.delete(tree_id)
        self.renumber_queue()
        self.restripe_tree(self.queue_tree)
        self.update_queue_summary()

    def clear_queue(self):
        if self.is_downloading:
            messagebox.showwarning("Busy", "Cannot modify the queue while downloading.")
            return
        for item in self.queue_items:
            self.queue_tree.delete(item["tree_id"])
        self.queue_items.clear()
        self.update_queue_summary()

    def renumber_queue(self):
        for index, item in enumerate(self.queue_items):
            self.queue_tree.set(item["tree_id"], "no", index + 1)

    def restripe_tree(self, tree):
        for index, row_id in enumerate(tree.get_children("")):
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            tree.item(row_id, tags=(tag,))

    def update_queue_summary(self):
        self.queue_summary_var.set(f"{len(self.queue_items)} item(s) in queue")

    def update_queue_row(self, item, status):
        item["status"] = status
        self.queue_tree.set(item["tree_id"], "status", status)

    def on_format_change(self, event=None):
        if self.format_var.get() == "best":
            self.quality_combo.configure(state="disabled")
        else:
            self.quality_combo.configure(state="readonly")

    def build_output_template(self, path):
        template = self.template_var.get().strip() or "%(title)s"
        if self.add_track_number_var.get() and "%(track_number)" not in template:
            template = "%(track_number)02d - " + template
        template += ".%(ext)s"
        if self.create_subfolder_var.get():
            return os.path.join(path, "%(artist)s - %(album)s", template)
        return os.path.join(path, template)

    def get_ydl_options(self, path, audio_format, audio_quality, progress_hook):
        output_template = self.build_output_template(path)

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "progress_hooks": [progress_hook],
            "logger": YtdlpLogger(self.logger)
        }

        ffmpeg_path = self.ffmpeg_path_var.get().strip()
        if ffmpeg_path:
            ydl_opts["ffmpeg_location"] = ffmpeg_path

        if audio_format != "best":
            quality = "0" if audio_quality == "best" else audio_quality
            postprocessors = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
                "preferredquality": quality
            }]
            if self.embed_metadata_var.get():
                postprocessors.append({"key": "FFmpegMetadata"})
            if self.embed_thumbnail_var.get():
                ydl_opts["writethumbnail"] = True
                postprocessors.append({"key": "EmbedThumbnail"})
            ydl_opts["postprocessors"] = postprocessors
            ydl_opts["keepvideo"] = self.keep_original_var.get()

        return ydl_opts

    def make_progress_hook(self, item):
        def hook(d):
            if self.cancel_event.is_set():
                raise DownloadCancelled("Cancelled by user")

            status = d.get("status")
            if status == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate")
                percent = (downloaded / total_bytes * 100) if total_bytes else 0.0
                speed = (d.get("_speed_str") or "N/A").strip()
                eta = (d.get("_eta_str") or "N/A").strip()
                info_dict = d.get("info_dict") or {}
                title = info_dict.get("title", item["url"])
                self.root.after(0, self.update_progress_ui, percent, speed, eta, title)
            elif status == "finished":
                self.root.after(0, self.update_status_ui, "Converting audio, please wait")
            elif status == "error":
                self.logger.warning("Progress hook reported an error for %s", item["url"])

        return hook

    def update_progress_ui(self, percent, speed, eta, title):
        self.current_progress["value"] = min(max(percent, 0), 100)
        display_title = title if len(title) <= 50 else title[:47] + "..."
        self.info_var.set(f"Downloading: {display_title}")
        self.status_var.set(f"Progress: {percent:.1f}% | Speed: {speed} | ETA: {eta}")

    def update_status_ui(self, text):
        self.status_var.set(text)

    def on_item_start(self, item, index, total):
        self.queue_label_var.set(f"Item {index + 1} of {total}")
        self.overall_progress["value"] = (index / total) * 100
        self.current_progress["value"] = 0
        self.info_var.set(f"Starting: {item['url']}")
        self.status_var.set("")
        self.app_status_var.set("Downloading")
        self.update_queue_row(item, "Downloading")

    def process_single_download(self, item, path, audio_format, audio_quality):
        url = item["url"]
        self.logger.info("Starting download: %s", url)
        progress_hook = self.make_progress_hook(item)
        ydl_opts = self.get_ydl_options(path, audio_format, audio_quality, progress_hook)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            title = url
            if info:
                title = info.get("title") or info.get("album") or url
            item["title"] = title
            self.logger.info("Completed download: %s", title)
            return "complete", title
        except DownloadCancelled:
            self.logger.info("Download cancelled: %s", url)
            return "cancelled", item.get("title", url)
        except DownloadError as e:
            self.logger.error("Download error for %s: %s", url, e)
            return "error", item.get("title", url)
        except Exception:
            self.logger.exception("Unexpected error while downloading %s", url)
            return "error", item.get("title", url)

    def download_worker(self):
        total = len(self.queue_items)
        completed = 0
        errors = 0
        cancelled = 0

        path = self.path_var.get().strip()
        audio_format = self.format_var.get()
        audio_quality = self.quality_var.get()

        for index, item in enumerate(self.queue_items):
            if self.cancel_event.is_set():
                self.root.after(0, self.update_queue_row, item, "Cancelled")
                cancelled += 1
                continue

            self.root.after(0, self.on_item_start, item, index, total)
            result_status, title = self.process_single_download(item, path, audio_format, audio_quality)

            if result_status == "complete":
                completed += 1
            elif result_status == "cancelled":
                cancelled += 1
            else:
                errors += 1

            self.root.after(0, self.add_to_history, title, audio_format, result_status.capitalize())
            self.root.after(0, self.update_queue_row, item, result_status.capitalize())

        self.root.after(0, self.on_queue_finished, completed, errors, cancelled, total)

    def on_queue_finished(self, completed, errors, cancelled, total):
        self.is_downloading = False
        self.cancel_event.clear()
        self.download_btn["state"] = "normal"
        self.cancel_btn["state"] = "disabled"
        self.overall_progress["value"] = 100
        self.current_progress["value"] = 0
        self.info_var.set("Queue finished")
        self.status_var.set(f"Completed: {completed} | Errors: {errors} | Cancelled: {cancelled} | Total: {total}")
        self.app_status_var.set("Ready")

        self.logger.info(
            "Queue finished. Completed=%d Errors=%d Cancelled=%d Total=%d",
            completed, errors, cancelled, total
        )

        if errors > 0:
            messagebox.showwarning("Queue Finished", f"Finished with {errors} error(s).\nCheck the Logs tab for details.")
        elif cancelled > 0:
            messagebox.showinfo("Queue Finished", "Queue finished. Some items were cancelled.")
        else:
            messagebox.showinfo("Queue Finished", "All downloads finished successfully.")

    def start_queue_thread(self):
        if self.is_downloading:
            return
        if not self.queue_items:
            messagebox.showerror("Error", "The queue is empty. Add at least one Bandcamp URL.")
            return

        path = self.path_var.get().strip()
        if not path:
            messagebox.showerror("Error", "Please select a download directory.")
            return
        if not os.path.isdir(path):
            messagebox.showerror("Error", "The selected download path does not exist.")
            return

        self.is_downloading = True
        self.cancel_event.clear()
        self.download_btn["state"] = "disabled"
        self.cancel_btn["state"] = "normal"
        self.overall_progress["value"] = 0
        self.current_progress["value"] = 0
        self.app_status_var.set("Downloading")

        self.logger.info("Queue started with %d item(s)", len(self.queue_items))

        thread = threading.Thread(target=self.download_worker, daemon=True)
        thread.start()

    def cancel_download(self):
        if not self.is_downloading:
            return
        self.cancel_event.set()
        self.info_var.set("Cancelling, please wait...")
        self.app_status_var.set("Cancelling")
        self.logger.info("Cancel requested by user")

    def add_to_history(self, title, format_type, status):
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        display_title = (title or "Unknown")[:60]
        self.history_tree.insert("", 0, values=(time_str, display_title, format_type.upper(), status))
        self.download_history.append((time_str, display_title, format_type, status))
        self.restripe_tree(self.history_tree)

    def clear_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        self.download_history.clear()
        self.logger.info("Download history cleared")

    def clear_logs(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def open_log_folder(self):
        folder = os.path.dirname(LOG_PATH)
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])
        except Exception as e:
            self.logger.error("Failed to open log folder: %s", e)
            messagebox.showerror("Error", f"Could not open log folder:\n{e}")

    def set_theme(self, theme_name):
        self.theme_var.set(theme_name)
        self.on_theme_change()

    def on_theme_change(self):
        theme = self.theme_var.get()
        self.theme_manager.apply(theme)
        self.config.set("theme", theme)
        self.logger.info("Theme changed to %s", theme)

    def save_settings(self, silent=False):
        self.config.set("theme", self.theme_var.get())
        self.config.set("download_path", self.path_var.get())
        self.config.set("audio_format", self.format_var.get())
        self.config.set("audio_quality", self.quality_var.get())
        self.config.set("embed_thumbnail", self.embed_thumbnail_var.get())
        self.config.set("embed_metadata", self.embed_metadata_var.get())
        self.config.set("create_subfolder", self.create_subfolder_var.get())
        self.config.set("keep_original", self.keep_original_var.get())
        self.config.set("add_track_number", self.add_track_number_var.get())
        self.config.set("filename_template", self.template_var.get())
        self.config.set("ffmpeg_path", self.ffmpeg_path_var.get())
        self.config.save()
        self.logger.info("Settings saved")
        if not silent:
            messagebox.showinfo("Settings", "Settings have been saved.")

    def reset_settings(self):
        defaults = ConfigManager.DEFAULTS
        self.theme_var.set(defaults["theme"])
        self.path_var.set(defaults["download_path"])
        self.format_var.set(defaults["audio_format"])
        self.quality_var.set(defaults["audio_quality"])
        self.embed_thumbnail_var.set(defaults["embed_thumbnail"])
        self.embed_metadata_var.set(defaults["embed_metadata"])
        self.create_subfolder_var.set(defaults["create_subfolder"])
        self.keep_original_var.set(defaults["keep_original"])
        self.add_track_number_var.set(defaults["add_track_number"])
        self.template_var.set(defaults["filename_template"])
        self.ffmpeg_path_var.set(defaults["ffmpeg_path"])
        self.theme_manager.apply(defaults["theme"])
        self.on_format_change()
        self.logger.info("Settings reset to defaults")

    def handle_tk_exception(self, exc_type, exc_value, exc_traceback):
        self.logger.error("Unhandled UI exception", exc_info=(exc_type, exc_value, exc_traceback))
        messagebox.showerror("Unexpected Error", f"{exc_type.__name__}: {exc_value}")

    def handle_thread_exception(self, args):
        self.logger.error("Unhandled thread exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
        self.root.after(
            0,
            lambda: messagebox.showerror("Unexpected Error", f"{args.exc_type.__name__}: {args.exc_value}")
        )

    def on_close(self):
        if self.is_downloading:
            if not messagebox.askyesno("Exit", "A download is in progress. Do you want to cancel it and exit?"):
                return
            self.cancel_event.set()
        self.save_settings(silent=True)
        self.logger.info("Application closed")
        self.root.destroy()


def main():
    root = tk.Tk()
    app = BandcampDownloaderV3(root)
    root.mainloop()


if __name__ == "__main__":
    main()
