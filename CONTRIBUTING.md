# Contributing

This is a small personal-use downloader. Keep changes focused, readable, and respectful of platform access controls.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m playwright install chromium
```

Run a quick local check:

```powershell
.\.venv\Scripts\python -m compileall .\src .\download_course.py
.\.venv\Scripts\circle-course-downloader --help
.\.venv\Scripts\circle-course-downloader download --help
```

## Security

Do not commit browser storage state or downloaded course media.
