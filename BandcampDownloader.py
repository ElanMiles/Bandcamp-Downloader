import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import yt_dlp
import os
from datetime import datetime, timedelta


class BandcampDownloaderV2:
    def __init__(self, root):
        self.root = root
        root.title("Bandcamp Downloader V2")
        root.geometry("650x500")
        root.minsize(600, 450)
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.download_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.history_tab = ttk.Frame(self.notebook)
        self.about_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.download_tab, text='Download')
        self.notebook.add(self.settings_tab, text='Settings')
        self.notebook.add(self.history_tab, text='History')
        self.notebook.add(self.about_tab, text='About')
        
        self.setup_download_tab()
        self.setup_settings_tab()
        self.setup_history_tab()
        self.setup_about_tab()
        
        self.start_time = None
        self.is_downloading = False
        self.download_history = []

    def setup_download_tab(self):
        main_frame = ttk.LabelFrame(self.download_tab, text="Download Music", padding=15)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill='x', pady=5)
        ttk.Label(url_frame, text="Bandcamp URL:", width=15).pack(side='left')
        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.pack(side='left', fill='x', expand=True, padx=(5, 0))
        
        path_frame = ttk.Frame(main_frame)
        path_frame.pack(fill='x', pady=5)
        ttk.Label(path_frame, text="Download Path:", width=15).pack(side='left')
        self.path_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.path_var).pack(side='left', fill='x', expand=True, padx=(5, 5))
        ttk.Button(path_frame, text="Browse", command=self.browse_path, width=10).pack(side='left')
        
        format_frame = ttk.Frame(main_frame)
        format_frame.pack(fill='x', pady=10)
        
        ttk.Label(format_frame, text="Audio Format:", width=15).pack(side='left')
        self.format_var = tk.StringVar(value="mp3")
        self.format_combo = ttk.Combobox(
            format_frame, 
            textvariable=self.format_var, 
            values=["mp3", "flac", "wav", "ogg", "opus", "aac", "m4a", "vorbis", "alac", "best"],
            state="readonly",
            width=12
        )
        self.format_combo.pack(side='left', padx=(5, 20))
        
        ttk.Label(format_frame, text="Quality (kbps):").pack(side='left')
        self.quality_var = tk.StringVar(value="320")
        self.quality_combo = ttk.Combobox(
            format_frame,
            textvariable=self.quality_var,
            values=["128", "192", "256", "320", "best"],
            state="readonly",
            width=10
        )
        self.quality_combo.pack(side='left', padx=(5, 0))
        
        self.progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=10)
        self.progress_frame.pack(fill='x', pady=15)
        
        self.progress = ttk.Progressbar(self.progress_frame, mode='determinate', length=400)
        self.progress.pack(fill='x', pady=(0, 10))
        
        self.info_var = tk.StringVar(value="Ready to download")
        self.info_label = ttk.Label(self.progress_frame, textvariable=self.info_var)
        self.info_label.pack()
        
        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(self.progress_frame, textvariable=self.status_var, foreground='gray')
        self.status_label.pack()
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)
        
        self.download_btn = ttk.Button(btn_frame, text="Start Download", command=self.start_download_thread, width=18)
        self.download_btn.pack(side='left', padx=10)
        
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.cancel_download, width=18, state='disabled')
        self.cancel_btn.pack(side='left', padx=10)
        
        ttk.Button(btn_frame, text="Clear", command=self.clear_fields, width=18).pack(side='left', padx=10)

    def setup_settings_tab(self):
        settings_frame = ttk.LabelFrame(self.settings_tab, text="Download Settings", padding=15)
        settings_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.embed_thumbnail_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Embed album artwork in audio file", variable=self.embed_thumbnail_var).pack(anchor='w', pady=5)
        
        self.embed_metadata_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Embed metadata (artist, album, track info)", variable=self.embed_metadata_var).pack(anchor='w', pady=5)
        
        self.create_subfolder_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Create subfolder for each album", variable=self.create_subfolder_var).pack(anchor='w', pady=5)
        
        self.keep_original_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Keep original file after conversion", variable=self.keep_original_var).pack(anchor='w', pady=5)
        
        self.add_track_number_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Add track number to filename", variable=self.add_track_number_var).pack(anchor='w', pady=5)
        
        ttk.Separator(settings_frame, orient='horizontal').pack(fill='x', pady=15)
        
        template_frame = ttk.LabelFrame(settings_frame, text="Filename Template", padding=10)
        template_frame.pack(fill='x', pady=10)
        
        self.template_var = tk.StringVar(value="%(track_number)02d - %(title)s")
        ttk.Entry(template_frame, textvariable=self.template_var, width=50).pack(fill='x', pady=5)
        ttk.Label(template_frame, text="Variables: %(artist)s, %(album)s, %(title)s, %(track_number)s, %(track_number)02d", foreground='gray').pack(anchor='w')
        
        ttk.Separator(settings_frame, orient='horizontal').pack(fill='x', pady=15)
        
        ffmpeg_frame = ttk.LabelFrame(settings_frame, text="FFmpeg Settings", padding=10)
        ffmpeg_frame.pack(fill='x', pady=10)
        
        ttk.Label(ffmpeg_frame, text="FFmpeg Path (leave empty for system default):").pack(anchor='w')
        self.ffmpeg_path_var = tk.StringVar(value="")
        ffmpeg_entry_frame = ttk.Frame(ffmpeg_frame)
        ffmpeg_entry_frame.pack(fill='x', pady=5)
        ttk.Entry(ffmpeg_entry_frame, textvariable=self.ffmpeg_path_var).pack(side='left', fill='x', expand=True)
        ttk.Button(ffmpeg_entry_frame, text="Browse", command=self.browse_ffmpeg).pack(side='left', padx=(5, 0))

    def setup_history_tab(self):
        history_frame = ttk.LabelFrame(self.history_tab, text="Download History", padding=10)
        history_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('time', 'title', 'format', 'status')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=15)
        
        self.history_tree.heading('time', text='Time')
        self.history_tree.heading('title', text='Title')
        self.history_tree.heading('format', text='Format')
        self.history_tree.heading('status', text='Status')
        
        self.history_tree.column('time', width=120)
        self.history_tree.column('title', width=250)
        self.history_tree.column('format', width=80)
        self.history_tree.column('status', width=100)
        
        scrollbar = ttk.Scrollbar(history_frame, orient='vertical', command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        btn_frame = ttk.Frame(self.history_tab)
        btn_frame.pack(fill='x', padx=10, pady=5)
        ttk.Button(btn_frame, text="Clear History", command=self.clear_history).pack(side='right')

    def setup_about_tab(self):
        about_frame = ttk.Frame(self.about_tab, padding=30)
        about_frame.pack(fill='both', expand=True)
        
        ttk.Label(about_frame, text="Bandcamp Downloader", font=('Helvetica', 18, 'bold')).pack(pady=10)
        ttk.Label(about_frame, text="Version 2.0.0", font=('Helvetica', 11)).pack(pady=5)
        
        ttk.Separator(about_frame, orient='horizontal').pack(fill='x', pady=20)
        
        info_frame = ttk.LabelFrame(about_frame, text="Information", padding=15)
        info_frame.pack(fill='x', pady=10)
        
        ttk.Label(info_frame, text="A tool for downloading music from Bandcamp").pack(pady=3)
        ttk.Label(info_frame, text="Powered by yt-dlp").pack(pady=3)
        
        format_frame = ttk.LabelFrame(about_frame, text="Supported Formats", padding=15)
        format_frame.pack(fill='x', pady=10)
        
        ttk.Label(format_frame, text="Lossy: MP3, AAC, OGG, Opus, Vorbis").pack(pady=3)
        ttk.Label(format_frame, text="Lossless: FLAC, WAV, ALAC, M4A").pack(pady=3)
        
        req_frame = ttk.LabelFrame(about_frame, text="Requirements", padding=15)
        req_frame.pack(fill='x', pady=10)
        
        ttk.Label(req_frame, text="FFmpeg must be installed for audio conversion").pack(pady=3)
        ttk.Label(req_frame, text="Download FFmpeg from: https://ffmpeg.org", foreground='blue').pack(pady=3)

    def browse_path(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path_var.set(directory)

    def browse_ffmpeg(self):
        filepath = filedialog.askopenfilename(filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if filepath:
            self.ffmpeg_path_var.set(filepath)

    def clear_fields(self):
        self.url_entry.delete(0, tk.END)
        self.progress['value'] = 0
        self.info_var.set("Ready to download")
        self.status_var.set("")

    def clear_history(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        self.download_history.clear()

    def add_to_history(self, title, format_type, status):
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.history_tree.insert('', 0, values=(time_str, title[:40], format_type.upper(), status))

    def cancel_download(self):
        self.is_downloading = False
        self.info_var.set("Cancelling download...")

    def get_output_template(self, path):
        template = self.template_var.get() + ".%(ext)s"
        if self.create_subfolder_var.get():
            return os.path.join(path, '%(artist)s - %(album)s', template)
        return os.path.join(path, template)

    def get_ydl_options(self, path, audio_format, audio_quality):
        output_template = self.get_output_template(path)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self.progress_hook],
            'ignoreerrors': True,
        }
        
        if self.ffmpeg_path_var.get():
            ydl_opts['ffmpeg_location'] = self.ffmpeg_path_var.get()
        
        if audio_format != 'best':
            postprocessors = []
            
            quality = '0' if audio_quality == 'best' else audio_quality
            
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': quality,
            })
            
            if self.embed_metadata_var.get():
                postprocessors.append({'key': 'FFmpegMetadata'})
            
            if self.embed_thumbnail_var.get():
                ydl_opts['writethumbnail'] = True
                postprocessors.append({'key': 'EmbedThumbnail'})
            
            ydl_opts['postprocessors'] = postprocessors
            ydl_opts['keepvideo'] = self.keep_original_var.get()
        
        return ydl_opts

    def download_album(self):
        url = self.url_entry.get().strip()
        path = self.path_var.get().strip()
        audio_format = self.format_var.get()
        audio_quality = self.quality_var.get()

        if not url:
            messagebox.showerror("Error", "Please enter a Bandcamp URL.")
            return
        if not path:
            messagebox.showerror("Error", "Please select a download directory.")
            return

        self.start_time = datetime.now()
        self.is_downloading = True
        self.info_var.set("Initializing download...")
        self.status_var.set("")
        self.download_btn['state'] = 'disabled'
        self.cancel_btn['state'] = 'normal'
        self.progress['value'] = 0

        ydl_opts = self.get_ydl_options(path, audio_format, audio_quality)
        
        album_title = "Unknown"
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    album_title = info.get('title', info.get('album', 'Unknown'))
                
                if self.is_downloading:
                    ydl.download([url])
            
            if self.is_downloading:
                messagebox.showinfo("Success", "Download completed successfully!")
                self.info_var.set("Download complete")
                self.progress['value'] = 100
                self.add_to_history(album_title, audio_format, "Complete")
            else:
                self.info_var.set("Download cancelled")
                self.add_to_history(album_title, audio_format, "Cancelled")
                
        except Exception as e:
            error_msg = str(e)
            if self.is_downloading:
                if "ffmpeg" in error_msg.lower() or "ffprobe" in error_msg.lower():
                    messagebox.showerror("FFmpeg Error", "FFmpeg is not installed or not found.\nPlease install FFmpeg to convert audio formats.")
                else:
                    messagebox.showerror("Download Error", f"An error occurred:\n{error_msg}")
                self.info_var.set("Error occurred")
                self.add_to_history(album_title, audio_format, "Error")
        finally:
            self.download_btn['state'] = 'normal'
            self.cancel_btn['state'] = 'disabled'
            self.is_downloading = False

    def progress_hook(self, d):
        if not self.is_downloading:
            return
            
        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0%').strip().replace('%', '')
            try:
                percent = float(percent_str)
            except ValueError:
                percent = 0
            
            self.progress['value'] = min(percent, 100)
            
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            
            if total and self.start_time:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                if elapsed > 0 and downloaded > 0:
                    speed = downloaded / elapsed
                    remaining = total - downloaded
                    eta_seconds = remaining / speed if speed > 0 else 0
                    eta = str(timedelta(seconds=int(eta_seconds)))
                else:
                    eta = "Calculating..."
            else:
                eta = "Unknown"

            title = d.get('info_dict', {}).get('title', 'Unknown track')
            speed_str = d.get('_speed_str', 'N/A')
            
            display_title = title[:45] + "..." if len(title) > 45 else title
            self.info_var.set(f"Downloading: {display_title}")
            self.status_var.set(f"Progress: {percent:.1f}% | Speed: {speed_str} | ETA: {eta}")
            
        elif d['status'] == 'finished':
            self.info_var.set("Converting audio format...")
            self.status_var.set("Please wait...")
            self.progress['value'] = 100
            
        elif d['status'] == 'error':
            self.info_var.set("Error during download")

    def start_download_thread(self):
        thread = threading.Thread(target=self.download_album, daemon=True)
        thread.start()


if __name__ == "__main__":
    root = tk.Tk()
    app = BandcampDownloaderV2(root)
    root.mainloop()