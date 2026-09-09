# video-downloader

A desktop YouTube video/audio downloader built on [yt-dlp](https://github.com/yt-dlp/yt-dlp), with a CustomTkinter UI.

## Structure

```text
core/               # UI-independent download logic - reusable by any front end
  downloader.py      # yt-dlp options, fetch/download, format analysis, error messages
  history.py          # Download history persistence (JSON file)
  logging_config.py   # Shared logging setup
app.py               # Desktop UI (CustomTkinter), imports from core/
requirements.txt
run.bat
```

The `core/` package has no dependency on any UI toolkit. `app.py` is the
desktop front end today; a future web front end (e.g. Flask/FastAPI) can
import the same `core` package instead of reimplementing the download logic.

## Running the desktop app

```sh
pip install -r requirements.txt
python app.py
```

Or on Windows, just run `run.bat`.

## Notes

- `download_history.json` and `logs/` are created at runtime and are gitignored - they contain your personal download history and local file paths.

## Premiere Pro downloads

The desktop app enables **Premiere Pro compatible (H.264 + AAC)** by default.
Choose a quality, leave the checkbox enabled, and download. The result is an
MP4 named `TITLE - Premiere H264.mp4`, separate from earlier downloads.
Restart the app after updating to see the checkbox.

This mode selects YouTube's H.264 video and AAC audio streams without
re-encoding. Quality choices are maximum resolutions; a lower resolution
may be selected if that is what YouTube offers. Best Available selects the
best compatible stream, which may be lower resolution than AV1/VP9 versions.
If no compatible stream is available, the download fails with guidance;
it never silently falls back to an incompatible codec. It does not convert
existing downloads. Turn the checkbox off to use the original download mode.
Audio Only (MP3) is unaffected and disables the checkbox.

FFmpeg must be installed and available on PATH to merge separate streams.
For core API callers, pass `premiere_compatible=True` to `open_client`,
`download`, or `build_ydl_opts` (the API default remains False).

Run the offline format-selection checks with:

```sh
python -m unittest discover -s tests -v
```
