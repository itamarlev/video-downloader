"""Core video download logic built on yt-dlp.

Deliberately has no dependency on any UI toolkit, so it can be reused by
the desktop app (customtkinter) and, in the future, a web front end.
"""

import logging
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("youtube_downloader")

try:
    import yt_dlp
except ImportError:
    logger.info("Installing yt-dlp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp

logger.info(f"yt-dlp version: {yt_dlp.version.__version__}")

DownloadError = yt_dlp.utils.DownloadError

QUALITY_OPTIONS = ["Best Available", "1080p", "720p", "480p", "360p", "Audio Only (MP3)"]

DEFAULT_DOWNLOAD_PATH = Path.home() / "Downloads" / "YouTube Downloads"

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
)

_QUALITY_FORMATS = {
    "Best Available": (
        'bestvideo[ext=mp4]+bestaudio[ext=m4a]/'
        'bestvideo[ext=mp4]+bestaudio/'
        'bestvideo+bestaudio[ext=m4a]/'
        'bestvideo+bestaudio/'
        'best'
    ),
    "1080p": (
        'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/'
        'bestvideo[height<=1080]+bestaudio[ext=m4a]/'
        'bestvideo[height<=1080]+bestaudio/'
        'best[height<=1080]/best'
    ),
    "720p": (
        'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/'
        'bestvideo[height<=720]+bestaudio[ext=m4a]/'
        'bestvideo[height<=720]+bestaudio/'
        'best[height<=720]/best'
    ),
    "480p": (
        'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/'
        'bestvideo[height<=480]+bestaudio/'
        'best[height<=480]/best'
    ),
    "360p": (
        'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/'
        'bestvideo[height<=360]+bestaudio/'
        'best[height<=360]/best'
    ),
}


def premiere_format(quality):
    """Only select YouTube H.264 video and AAC audio; never fall back to AV1."""
    cap = f"[height<={quality[:-1]}]" if quality in QUALITY_OPTIONS[1:5] else ""
    return (
        f"bestvideo{cap}[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a][acodec^=mp4a]/"
        f"best{cap}[ext=mp4][vcodec^=avc1][acodec^=mp4a]"
    )


def build_ydl_opts(quality, download_path, for_info_only=False, progress_hook=None,
                   premiere_compatible=False):
    """Build yt-dlp options for the given quality setting and destination folder."""
    opts = {
        'outtmpl': str(Path(download_path) / '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'socket_timeout': 30,
        'retries': 5,
        'fragment_retries': 5,
        'ignoreerrors': False,
        'restrictfilenames': False,
        'windowsfilenames': True,
        'geo_bypass': True,
        'noplaylist': True,
        'http_headers': {
            'User-Agent': USER_AGENT,
        },
    }

    if not for_info_only and progress_hook is not None:
        opts['progress_hooks'] = [progress_hook]

    if quality == "Audio Only (MP3)":
        opts['format'] = 'bestaudio/best'
        opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }]
    elif premiere_compatible and not for_info_only:
        opts['format'] = premiere_format(quality)
        # A separate name prevents yt-dlp reusing a previous AV1 download.
        opts['outtmpl'] = str(Path(download_path) / '%(title)s - Premiere H264.%(ext)s')
    else:
        opts['format'] = _QUALITY_FORMATS.get(quality, _QUALITY_FORMATS["Best Available"])

    return opts


def get_user_friendly_error(error_msg, premiere_compatible=False):
    """Convert a technical yt-dlp error into a user-friendly message."""
    error_lower = error_msg.lower()

    if "ffmpeg" in error_lower and ("not found" in error_lower or "not installed" in error_lower):
        return "FFmpeg is required to merge video and audio. Install FFmpeg, add it to PATH, then restart the app."
    if premiere_compatible and "format" in error_lower and "not available" in error_lower:
        return ("YouTube has no H.264 + AAC download at this quality or below. "
                "Try another quality, or turn off Premiere compatibility and convert the downloaded video to H.264 before importing it.")
    if "private video" in error_lower:
        return "This video is private and cannot be downloaded."
    elif "video unavailable" in error_lower:
        return "This video is unavailable. It may have been removed or is not accessible in your region."
    elif "age" in error_lower and "verif" in error_lower:
        return "This video requires age verification. Try logging into YouTube in your browser first."
    elif "copyright" in error_lower:
        return "This video cannot be downloaded due to copyright restrictions."
    elif "live" in error_lower and "stream" in error_lower:
        return "Live streams cannot be downloaded while they are still live."
    elif "format" in error_lower and "not available" in error_lower:
        return "The requested quality is not available. Try selecting a different quality option."
    elif "403" in error_lower and "forbidden" in error_lower:
        return "YouTube rejected the request (403 Forbidden). This is usually caused by an outdated yt-dlp. Run: pip install --upgrade yt-dlp"
    elif "transport error" in error_lower:
        return "Network error. Please check your internet connection and try again."
    elif "unable to download" in error_lower:
        return "Download failed while fetching video data. This can be a temporary YouTube issue, or an outdated yt-dlp. Try again, or run: pip install --upgrade yt-dlp"
    elif "geo" in error_lower or "country" in error_lower:
        return "This video is not available in your country."
    elif "sign in" in error_lower or "login" in error_lower:
        return "This video requires you to be signed in to YouTube."
    else:
        return f"Download failed: {error_msg[:200]}..." if len(error_msg) > 200 else f"Download failed: {error_msg}"


def is_youtube_url(url):
    return "youtube.com" in url or "youtu.be" in url


def open_client(quality, download_path, progress_hook=None, for_info_only=False,
                premiere_compatible=False):
    """Return a yt-dlp client configured for the given quality/destination.

    Use as a context manager: `with open_client(...) as ydl:` so callers
    (desktop UI, future web UI) never need to import yt_dlp directly.
    """
    if premiere_compatible and quality != "Audio Only (MP3)" and not for_info_only:
        if not shutil.which("ffmpeg"):
            raise DownloadError("FFmpeg not found on PATH")
    opts = build_ydl_opts(quality, download_path, for_info_only=for_info_only,
                          progress_hook=progress_hook, premiere_compatible=premiere_compatible)
    return yt_dlp.YoutubeDL(opts)


def fetch_info(url):
    """Fetch video metadata for a URL without downloading it."""
    opts = build_ydl_opts(quality="Best Available", download_path=Path.cwd(), for_info_only=True)
    opts['skip_download'] = True
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def analyze_formats(info):
    """Summarize the formats available on an info dict returned by fetch_info/download."""
    formats = info.get('formats', [])
    video_formats = [f for f in formats if f.get('vcodec', 'none') != 'none']
    audio_formats = [f for f in formats if f.get('acodec', 'none') != 'none' and f.get('vcodec', 'none') == 'none']

    resolutions = sorted({f['height'] for f in video_formats if f.get('height')}, reverse=True)

    best_video = max(video_formats, key=lambda f: (f.get('height', 0), f.get('tbr', 0)), default=None)
    best_audio = max(audio_formats, key=lambda f: f.get('abr', 0), default=None)

    return {
        'resolutions': resolutions,
        'best_video': best_video,
        'best_audio': best_audio,
    }


def download(url, quality, download_path, progress_hook=None, premiere_compatible=False):
    """Download a video and return its metadata info dict."""
    download_path = Path(download_path)
    download_path.mkdir(parents=True, exist_ok=True)

    with open_client(quality, download_path, progress_hook=progress_hook,
                     premiere_compatible=premiere_compatible) as ydl:
        info = ydl.extract_info(url, download=True)
    return info


def format_duration(seconds):
    if not seconds:
        return "Unknown"
    seconds = int(seconds)
    return f"{seconds // 60}:{seconds % 60:02d}"


def format_filesize(num_bytes):
    if not num_bytes:
        return "Unknown"
    return f"{num_bytes / 1024 / 1024:.1f} MB"
