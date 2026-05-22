@C:\Users\Fernando Paladini\.codex\RTK.md

# Repository Instructions

This project is a public Python CLI for downloading Circle course videos that the user can already access through their own account.

## Guardrails

- Keep the authentication model browser-only. Do not add terminal password prompts, raw cookie input, copied token flows, or code that reads credentials from the user's default browser.
- Do not add behavior that bypasses DRM, paywalls, 2FA, captchas, or Circle access controls.
- Treat `.auth/`, downloaded media, generated manifests, and signed media URLs as private local artifacts.
- Keep public documentation user-facing. Agent instructions belong in this file, not in `README.md`.

## Development

- Use Python 3.11 or newer.
- Install the package locally with `python -m pip install .`.
- Install Playwright Chromium with `python -m playwright install chromium`.
- Install development and publishing tools from `requirements.txt` when needed.

## Checks

Run the relevant checks before handing off changes:

```powershell
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m compileall .\src
.\.venv\Scripts\python -m build
.\.venv\Scripts\python -m twine check dist/*
.\.venv\Scripts\circle-course-downloader --help
.\.venv\Scripts\circle-course-downloader download --help
```
