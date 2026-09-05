"""
YouTube Video Downloader
A modern, easy-to-use application for downloading YouTube videos
With comprehensive logging and diagnostics
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
from datetime import datetime
from pathlib import Path

from core.logging_config import setup_logging, LOG_DIR
from core.history import DownloadHistory
from core import downloader

logger = setup_logging()

# App configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        logger.info("=" * 60)
        logger.info("Application started")

        self.title("YouTube Downloader")
        self.geometry("900x750")
        self.minsize(800, 650)

        self.history = DownloadHistory()
        self.download_path = downloader.DEFAULT_DOWNLOAD_PATH
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.is_downloading = False
        self.current_formats = []

        self.setup_ui()
        logger.info(f"Download path: {self.download_path}")

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.create_header()
        self.create_download_section()
        self.create_tabs()
        self.create_status_bar()

    def create_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            title_frame,
            text="YouTube Downloader",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(side="left", padx=(0, 10))

        subtitle = ctk.CTkLabel(
            title_frame,
            text="Download videos in highest quality",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle.pack(side="left", pady=(8, 0))

        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")

        # Open logs button
        logs_btn = ctk.CTkButton(
            btn_frame,
            text="View Logs",
            width=80,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self.open_logs
        )
        logs_btn.pack(side="left", padx=(0, 10))

        self.theme_btn = ctk.CTkButton(
            btn_frame,
            text="Light Mode",
            width=100,
            command=self.toggle_theme
        )
        self.theme_btn.pack(side="left")

    def create_download_section(self):
        download_frame = ctk.CTkFrame(self)
        download_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        download_frame.grid_columnconfigure(1, weight=1)

        # URL input
        url_label = ctk.CTkLabel(download_frame, text="Video URL:", font=ctk.CTkFont(size=14))
        url_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        self.url_entry = ctk.CTkEntry(
            download_frame,
            placeholder_text="Paste YouTube URL here...",
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.url_entry.grid(row=0, column=1, padx=(0, 15), pady=(15, 5), sticky="ew")

        # Options row 1
        options_frame = ctk.CTkFrame(download_frame, fg_color="transparent")
        options_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=10, sticky="ew")
        options_frame.grid_columnconfigure(4, weight=1)

        # Quality selector
        quality_label = ctk.CTkLabel(options_frame, text="Quality:")
        quality_label.grid(row=0, column=0, padx=(0, 10))

        self.quality_var = ctk.StringVar(value="Best Available")
        self.quality_dropdown = ctk.CTkOptionMenu(
            options_frame,
            values=downloader.QUALITY_OPTIONS,
            variable=self.quality_var,
            width=150
        )
        self.quality_dropdown.grid(row=0, column=1, padx=(0, 20))

        # Fetch info button
        self.fetch_btn = ctk.CTkButton(
            options_frame,
            text="Check Video",
            width=100,
            fg_color="#17a2b8",
            hover_color="#138496",
            command=self.fetch_video_info
        )
        self.fetch_btn.grid(row=0, column=2, padx=(0, 20))

        # Options row 2
        options_frame2 = ctk.CTkFrame(download_frame, fg_color="transparent")
        options_frame2.grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="ew")
        options_frame2.grid_columnconfigure(1, weight=1)

        location_label = ctk.CTkLabel(options_frame2, text="Save to:")
        location_label.grid(row=0, column=0, padx=(0, 10))

        self.location_entry = ctk.CTkEntry(options_frame2, width=400)
        self.location_entry.insert(0, str(self.download_path))
        self.location_entry.grid(row=0, column=1, padx=(0, 10), sticky="ew")

        browse_btn = ctk.CTkButton(
            options_frame2,
            text="Browse",
            width=80,
            command=self.browse_location
        )
        browse_btn.grid(row=0, column=2, padx=(0, 10))

        open_folder_btn = ctk.CTkButton(
            options_frame2,
            text="Open Folder",
            width=100,
            fg_color="#28a745",
            hover_color="#218838",
            command=self.open_downloads_folder
        )
        open_folder_btn.grid(row=0, column=3)

        # Download button
        self.download_btn = ctk.CTkButton(
            download_frame,
            text="Download",
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_download
        )
        self.download_btn.grid(row=3, column=0, columnspan=2, padx=15, pady=15, sticky="ew")

    def create_tabs(self):
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        # Progress tab
        self.progress_tab = self.tabview.add("Download Progress")
        self.progress_tab.grid_columnconfigure(0, weight=1)
        self.progress_tab.grid_rowconfigure(2, weight=1)

        # Video info frame
        self.info_frame = ctk.CTkFrame(self.progress_tab)
        self.info_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.info_frame.grid_columnconfigure(0, weight=1)

        self.video_title_label = ctk.CTkLabel(
            self.info_frame,
            text="No video selected",
            font=ctk.CTkFont(size=16, weight="bold"),
            wraplength=700
        )
        self.video_title_label.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        self.video_info_label = ctk.CTkLabel(
            self.info_frame,
            text="Paste a URL and click 'Check Video' or 'Download'",
            text_color="gray"
        )
        self.video_info_label.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        # Available formats display
        self.formats_label = ctk.CTkLabel(
            self.info_frame,
            text="",
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        self.formats_label.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="w")

        # Progress frame
        progress_container = ctk.CTkFrame(self.progress_tab)
        progress_container.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        progress_container.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(progress_container, height=20)
        self.progress_bar.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            progress_container,
            text="Ready to download",
            font=ctk.CTkFont(size=14)
        )
        self.progress_label.grid(row=1, column=0, padx=20, pady=(0, 10))

        self.detail_label = ctk.CTkLabel(
            progress_container,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.detail_label.grid(row=2, column=0, padx=20, pady=(0, 20))

        # Diagnostics textbox
        diag_label = ctk.CTkLabel(self.progress_tab, text="Diagnostics Log:", anchor="w")
        diag_label.grid(row=2, column=0, padx=10, pady=(10, 0), sticky="w")

        self.diag_text = ctk.CTkTextbox(self.progress_tab, height=150, font=ctk.CTkFont(size=11))
        self.diag_text.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="nsew")

        # History tab
        self.history_tab = self.tabview.add("Download History")
        self.history_tab.grid_columnconfigure(0, weight=1)
        self.history_tab.grid_rowconfigure(0, weight=1)

        self.create_history_view()

    def create_history_view(self):
        self.history_scroll = ctk.CTkScrollableFrame(self.history_tab)
        self.history_scroll.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.history_scroll.grid_columnconfigure(0, weight=1)

        clear_btn = ctk.CTkButton(
            self.history_tab,
            text="Clear History",
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self.clear_history
        )
        clear_btn.grid(row=1, column=0, padx=10, pady=10, sticky="e")

        self.refresh_history()

    def refresh_history(self):
        for widget in self.history_scroll.winfo_children():
            widget.destroy()

        history_data = self.history.get_all()

        if not history_data:
            empty_label = ctk.CTkLabel(
                self.history_scroll,
                text="No downloads yet. Your download history will appear here.",
                text_color="gray",
                font=ctk.CTkFont(size=14)
            )
            empty_label.grid(row=0, column=0, pady=50)
            return

        for idx, item in enumerate(history_data[:50]):  # Show last 50
            self.create_history_item(idx, item)

    def create_history_item(self, idx, item):
        item_frame = ctk.CTkFrame(self.history_scroll)
        item_frame.grid(row=idx, column=0, padx=5, pady=5, sticky="ew")
        item_frame.grid_columnconfigure(1, weight=1)

        title = item.get("title", "Unknown")
        if len(title) > 60:
            title = title[:60] + "..."

        title_label = ctk.CTkLabel(
            item_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 2), sticky="w")

        date_str = item.get("downloaded_at", "")
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str)
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass

        resolution = item.get("resolution", "")
        info_text = f"{item.get('quality', 'Unknown')}"
        if resolution:
            info_text += f" | {resolution}"
        info_text += f" | {date_str}"

        info_label = ctk.CTkLabel(
            item_frame,
            text=info_text,
            text_color="gray",
            font=ctk.CTkFont(size=12)
        )
        info_label.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        open_btn = ctk.CTkButton(
            item_frame,
            text="Open Folder",
            width=100,
            height=28,
            command=lambda p=item.get("file_path", ""): self.open_file_location(p)
        )
        open_btn.grid(row=0, column=2, rowspan=2, padx=15, pady=10)

    def create_status_bar(self):
        self.status_bar = ctk.CTkLabel(
            self,
            text="Ready",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.status_bar.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="w")

    def log_diag(self, message):
        """Log to diagnostics panel and file"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        self.diag_text.insert("end", log_line)
        self.diag_text.see("end")
        logger.info(message)

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        if current == "Dark":
            ctk.set_appearance_mode("light")
            self.theme_btn.configure(text="Dark Mode")
        else:
            ctk.set_appearance_mode("dark")
            self.theme_btn.configure(text="Light Mode")

    def browse_location(self):
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.download_path = Path(folder)
            self.location_entry.delete(0, "end")
            self.location_entry.insert(0, str(self.download_path))
            logger.info(f"Download path changed to: {folder}")

    def open_downloads_folder(self):
        folder = Path(self.location_entry.get())
        folder.mkdir(parents=True, exist_ok=True)
        if folder.exists():
            os.startfile(folder)

    def open_logs(self):
        if LOG_DIR.exists():
            os.startfile(LOG_DIR)

    def open_file_location(self, file_path):
        if not file_path:
            return
        folder = Path(file_path).parent
        if folder.exists():
            os.startfile(folder)

    def clear_history(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all download history?"):
            self.history.clear()
            self.refresh_history()

    def fetch_video_info(self):
        """Fetch and display video information without downloading"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return

        self.fetch_btn.configure(state="disabled", text="Checking...")
        self.diag_text.delete("1.0", "end")
        self.log_diag(f"Fetching info for: {url}")

        thread = threading.Thread(target=self._fetch_info_thread, args=(url,), daemon=True)
        thread.start()

    def _fetch_info_thread(self, url):
        try:
            self.log_diag("Connecting to YouTube...")

            info = downloader.fetch_info(url)
            self.current_formats = info.get('formats', [])

            self.log_diag(f"Video found: {info.get('title', 'Unknown')}")

            analysis = downloader.analyze_formats(info)
            resolutions = analysis['resolutions']
            best_video = analysis['best_video']
            best_audio = analysis['best_audio']

            self.log_diag(f"Available resolutions: {resolutions}")
            if best_video:
                self.log_diag(f"Best video: {best_video.get('height')}p, codec: {best_video.get('vcodec')}, bitrate: {best_video.get('tbr')}kbps")
            if best_audio:
                self.log_diag(f"Best audio: {best_audio.get('acodec')}, bitrate: {best_audio.get('abr')}kbps")

            # Update UI
            title = info.get('title', 'Unknown')
            duration_str = downloader.format_duration(info.get('duration', 0))

            best_height = best_video.get('height', 0) if best_video else 0
            resolution_str = f"{best_height}p" if best_height else "Unknown"

            if best_height >= 2160:
                resolution_str += " (4K)"
            elif best_height >= 1440:
                resolution_str += " (2K)"
            elif best_height >= 1080:
                resolution_str += " (Full HD)"

            info_text = f"Duration: {duration_str} | Best resolution: {resolution_str}"

            formats_text = f"Available: {', '.join([f'{r}p' for r in resolutions[:6]])}"
            if len(resolutions) > 6:
                formats_text += f" (+{len(resolutions)-6} more)"

            self.update_ui(lambda: self.video_title_label.configure(text=title))
            self.update_ui(lambda: self.video_info_label.configure(text=info_text))
            self.update_ui(lambda: self.formats_label.configure(text=formats_text))
            self.update_ui(lambda: self.fetch_btn.configure(state="normal", text="Check Video"))
            self.update_ui(lambda: self.status_bar.configure(text="Video info loaded"))

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error fetching info: {error_msg}", exc_info=True)
            self.log_diag(f"ERROR: {error_msg}")

            user_msg = downloader.get_user_friendly_error(error_msg)
            self.update_ui(lambda: messagebox.showerror("Error", user_msg))
            self.update_ui(lambda: self.fetch_btn.configure(state="normal", text="Check Video"))

    def start_download(self):
        if self.is_downloading:
            messagebox.showwarning("Download in Progress", "Please wait for the current download to finish.")
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return

        if not downloader.is_youtube_url(url):
            messagebox.showerror("Error", "Please enter a valid YouTube URL")
            return

        self.is_downloading = True
        self.download_btn.configure(state="disabled", text="Downloading...")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting download...")
        self.detail_label.configure(text="")
        self.status_bar.configure(text="Downloading...")
        self.diag_text.delete("1.0", "end")

        self.log_diag(f"Starting download: {url}")
        self.log_diag(f"Quality setting: {self.quality_var.get()}")

        thread = threading.Thread(target=self.download_video, args=(url,), daemon=True)
        thread.start()

    def download_video(self, url):
        quality = self.quality_var.get()
        download_path = Path(self.location_entry.get())
        download_path.mkdir(parents=True, exist_ok=True)

        try:
            with downloader.open_client(quality, download_path, progress_hook=self.progress_hook) as ydl:
                self.log_diag(f"Format string: {ydl.params.get('format')}")
                self.log_diag("Fetching video information...")
                self.update_ui(lambda: self.progress_label.configure(text="Fetching video information..."))

                info = ydl.extract_info(url, download=False)

                title = info.get('title', 'Unknown')
                duration_str = downloader.format_duration(info.get('duration', 0))

                # Get selected format info
                requested_format = info.get('requested_formats', [])
                if requested_format:
                    video_fmt = next((f for f in requested_format if f.get('vcodec', 'none') != 'none'), None)
                    audio_fmt = next((f for f in requested_format if f.get('acodec', 'none') != 'none'), None)

                    if video_fmt:
                        height = video_fmt.get('height', 0)
                        vcodec = video_fmt.get('vcodec', 'unknown')
                        vbr = video_fmt.get('tbr', 0) or video_fmt.get('vbr', 0)
                        self.log_diag(f"Selected video: {height}p, {vcodec}, ~{vbr:.0f}kbps")

                    if audio_fmt:
                        acodec = audio_fmt.get('acodec', 'unknown')
                        abr = audio_fmt.get('abr', 0)
                        self.log_diag(f"Selected audio: {acodec}, ~{abr:.0f}kbps")

                width = info.get('width', 0)
                height = info.get('height', 0)
                resolution = f"{width}x{height}" if width and height else "Unknown"
                fps = info.get('fps', 0)
                filesize_str = downloader.format_filesize(info.get('filesize') or info.get('filesize_approx', 0))

                quality_info = f"Duration: {duration_str} | Resolution: {resolution}"
                if fps:
                    quality_info += f" @ {fps}fps"
                quality_info += f" | Size: ~{filesize_str}"

                self.update_ui(lambda: self.video_title_label.configure(text=title))
                self.update_ui(lambda: self.video_info_label.configure(text=quality_info))

                # Download
                self.log_diag("Starting download...")
                self.update_ui(lambda: self.progress_label.configure(text="Downloading..."))

                ydl.download([url])

                self.log_diag("Download completed!")

                # Determine file extension
                ext = "mp4"
                if quality == "Audio Only (MP3)":
                    ext = "mp3"

                # Record in history
                self.history.add({
                    "title": title,
                    "url": url,
                    "quality": quality,
                    "resolution": resolution,
                    "file_path": str(download_path / f"{title}.{ext}"),
                    "downloaded_at": datetime.now().isoformat(),
                })

                self.update_ui(self.on_download_complete)

        except downloader.DownloadError as e:
            error_msg = str(e)
            logger.error(f"Download error: {error_msg}", exc_info=True)
            self.log_diag(f"DOWNLOAD ERROR: {error_msg}")

            user_msg = downloader.get_user_friendly_error(error_msg)
            self.update_ui(lambda: self.on_download_error(user_msg))

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error: {error_msg}", exc_info=True)
            self.log_diag(f"UNEXPECTED ERROR: {error_msg}")

            self.update_ui(lambda: self.on_download_error(f"An unexpected error occurred. Check the logs for details."))

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)

                if total > 0:
                    progress = downloaded / total
                    speed = d.get('speed', 0)
                    speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed else "..."
                    eta = d.get('eta', 0)
                    eta_str = f"{eta // 60}:{eta % 60:02d}" if eta else "..."

                    downloaded_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024

                    self.update_ui(lambda p=progress: self.progress_bar.set(p))
                    self.update_ui(lambda: self.progress_label.configure(
                        text=f"Downloading: {progress * 100:.1f}%"
                    ))
                    self.update_ui(lambda: self.detail_label.configure(
                        text=f"{downloaded_mb:.1f} / {total_mb:.1f} MB | Speed: {speed_str} | ETA: {eta_str}"
                    ))
            except Exception as e:
                logger.debug(f"Progress hook error: {e}")

        elif d['status'] == 'finished':
            self.log_diag(f"Download finished, processing...")
            self.update_ui(lambda: self.progress_label.configure(text="Processing video..."))
            self.update_ui(lambda: self.progress_bar.set(0.95))

    def update_ui(self, func):
        self.after(0, func)

    def on_download_complete(self):
        self.is_downloading = False
        self.download_btn.configure(state="normal", text="Download")
        self.progress_bar.set(1)
        self.progress_label.configure(text="Download complete!")
        self.detail_label.configure(text="")
        self.status_bar.configure(text="Download complete!")
        self.url_entry.delete(0, "end")
        self.refresh_history()
        messagebox.showinfo("Success", "Video downloaded successfully!")

    def on_download_error(self, error_msg):
        self.is_downloading = False
        self.download_btn.configure(state="normal", text="Download")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Download failed")
        self.detail_label.configure(text="Check diagnostics log for details")
        self.status_bar.configure(text="Error occurred")
        messagebox.showerror("Download Error", error_msg)


def main():
    logger.info("Starting YouTube Downloader application")
    app = YouTubeDownloaderApp()
    app.mainloop()
    logger.info("Application closed")


if __name__ == "__main__":
    main()
