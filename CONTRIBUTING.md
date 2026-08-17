# Contributing

Keep changes focused on the browser-only Circle course and standalone page download
flow. Don't add terminal password prompts, raw cookie input, or alternate
authentication paths.

## Development setup

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install .
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m playwright install chromium
```

## Local checks

```powershell
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m compileall .\src
.\.venv\Scripts\python -m build
.\.venv\Scripts\python -m twine check dist/*
.\.venv\Scripts\circle-course-downloader --help
.\.venv\Scripts\circle-course-downloader download --help
.\.venv\Scripts\circle-course-downloader download-standalone --help
```

## Security

Do not commit browser storage state, downloaded course media, or generated
manifests with signed media URLs.
