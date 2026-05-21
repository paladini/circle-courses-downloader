# Contributing

This is a small personal-use downloader. Keep changes focused, readable, and respectful of platform access controls.

## Development

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e .
.\.venv\Scripts\python -m playwright install chromium
```

Run a quick local check:

```powershell
.\.venv\Scripts\python -m py_compile .\download_course.py .\src\circle_courses_downloader\*.py
.\.venv\Scripts\python .\download_course.py manifest
.\.venv\Scripts\python .\download_course.py inspect-page --html .\exemplo-pagina-video.html
```

## Security

Do not commit credentials, cookies, browser storage state, or downloaded course media.
