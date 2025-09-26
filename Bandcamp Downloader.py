import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import yt_dlp
import os

class BandcampDownloader:
    def __init__(self, root):
        self.root = root
        root.title("Bandcamp Downloader")

        # Mode toggle
        self.multiple_mode = False
        self.mode_btn = ttk.Button(root, text="Switch to Multiple Albums", command=self.toggle_mode)
        self.mode_btn.grid(row=0, column=2, padx=5, pady=5)

        # URL Entry (will be replaced with Text for multiple)
        self.url_label = ttk.Label(root, text="Album URL:")
        self.url_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.url_entry = ttk.Entry(root, width=50)
        self.url_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.url_text = None  # For multiple mode

        # Path Selection
        ttk.Label(root, text="Download Path:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.path_var = tk.StringVar()
        ttk.Entry(root, textvariable=self.path_var, width=40).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(root, text="Browse", command=self.browse_path).grid(row=2, column=2, padx=5, pady=5)

        # Format Selection
        ttk.Label(root, text="Format:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.format_var = tk.StringVar(value="mp3")
        format_combo = ttk.Combobox(root, textvariable=self.format_var, values=["mp3", "flac", "ogg", "wav"], state="readonly")
        format_combo.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        # Download Button
        self.download_btn = ttk.Button(root, text="Download Album(s)", command=self.start_download_thread)
        self.download_btn.grid(row=4, column=1, padx=5, pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(root, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Configure grid
        root.columnconfigure(1, weight=1)

    def toggle_mode(self):
        self.multiple_mode = not self.multiple_mode
        if self.multiple_mode:
            # Switch to multiple: hide entry, show text
            self.url_entry.grid_remove()
            self.url_text = tk.Text(root, height=5, width=50)
            self.url_text.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
            self.url_label.config(text="Album URLs (one per line):")
            self.mode_btn.config(text="Switch to Single Album")
            self.download_btn.config(text="Download Albums")
        else:
            # Switch to single: hide text, show entry
            if self.url_text:
                self.url_text.grid_remove()
            self.url_entry.grid()
            self.url_label.config(text="Album URL:")
            self.mode_btn.config(text="Switch to Multiple Albums")
            self.download_btn.config(text="Download Album")

    def browse_path(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path_var.set(directory)

    def download_album(self):
        if self.multiple_mode:
            urls_text = self.url_text.get("1.0", tk.END).strip()
            urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        else:
            urls = [self.url_entry.get().strip()]

        path = self.path_var.get().strip()
        dl_format = self.format_var.get()

        if not urls or not any(urls):
            messagebox.showerror("Error", "Please enter at least one Bandcamp album URL.")
            return
        if not path:
            messagebox.showerror("Error", "Please select a download directory.")
            return

        self.download_btn['state'] = 'disabled'
        self.progress.start()

        output_template = os.path.join(path, '%(artist)s - %(album)s', '%(track_number)s - %(title)s.%(ext)s')

        ydl_opts = {
            'format': dl_format,
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [self.progress_hook],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                for url in urls:
                    ydl.download([url])
            messagebox.showinfo("Success", "Download(s) completed successfully.")
        except Exception as e:
            messagebox.showerror("Download Error", f"An error occurred: {str(e)}")
        finally:
            self.progress.stop()
            self.download_btn['state'] = 'normal'

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            print(f"Downloading: {d['_percent_str']} of {d['_total_bytes_str']}")

    def start_download_thread(self):
        thread = threading.Thread(target=self.download_album)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = BandcampDownloader(root)
    root.mainloop()
