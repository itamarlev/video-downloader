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
