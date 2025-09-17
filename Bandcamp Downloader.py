import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import yt_dlp
import os

class BandcampDownloader:
    def __init__(self, root):
        self.root = root
        root.title("Bandcamp Downloader")

        # URL Entry
        ttk.Label(root, text="Album URL:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.url_entry = ttk.Entry(root, width=50)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Path Selection
        ttk.Label(root, text="Download Path:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.path_var = tk.StringVar()
        ttk.Entry(root, textvariable=self.path_var, width=40).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(root, text="Browse", command=self.browse_path).grid(row=1, column=2, padx=5, pady=5)

        # Format Selection
        ttk.Label(root, text="Format:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.format_var = tk.StringVar(value="mp3")
        format_combo = ttk.Combobox(root, textvariable=self.format_var, values=["mp3", "flac", "ogg", "wav"], state="readonly")
        format_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        # Download Button
        self.download_btn = ttk.Button(root, text="Download Album", command=self.start_download_thread)
        self.download_btn.grid(row=3, column=1, padx=5, pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(root, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Configure grid
        root.columnconfigure(1, weight=1)

    def browse_path(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path_var.set(directory)

    def download_album(self):
        url = self.url_entry.get().strip()
        path = self.path_var.get().strip()
        dl_format = self.format_var.get()

        if not url:
            messagebox.showerror("Error", "Please enter a Bandcamp album URL.")
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
                ydl.download([url])
            messagebox.showinfo("Success", "Download completed successfully.")
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