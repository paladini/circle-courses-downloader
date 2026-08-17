# Circle Course Downloader

[![PyPI](https://img.shields.io/pypi/v/circle-course-downloader?color=2f80ed)](https://pypi.org/project/circle-course-downloader/)
[![Python](https://img.shields.io/pypi/pyversions/circle-course-downloader)](https://pypi.org/project/circle-course-downloader/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A small, practical CLI for saving Circle course and community page videos that you can already access with your own account.

Circle Course Downloader opens a dedicated Chromium profile, lets you sign in normally, discovers videos from course pages or standalone community posts, and downloads the video streams with `yt-dlp`. It is built for personal offline viewing, backups, and unreliable connections.

> This project is unofficial and is not affiliated with Circle. It does not bypass DRM, paywalls, 2FA, captchas, or access controls. Use it only for content you are authorized to view and download.

## Highlights

- Browser-only authentication: no terminal passwords, copied cookies, or pasted tokens.
- Reusable local session stored in a dedicated Playwright Chromium profile.
- Course lesson discovery from real Circle course pages.
- Standalone page downloads for community posts and events with a single embedded video.
- Video URL detection for Circle HLS, direct video links, YouTube, Vimeo, Wistia, Loom, Mux, and Cloudflare Stream.
- `yt-dlp` downloads with resume support and MP4 merge output.
- `manifest.json` and `manifest.csv` exports for auditing what was found.
- Dry-run mode for inspecting generated download commands before saving media.

## Installation

Install the package and the Playwright browser runtime:

```bash
python -m pip install circle-course-downloader
python -m playwright install chromium
```

Python 3.11 or newer is required.

## Quick Start

Run the downloader with a full Circle course URL:

```bash
circle-course-downloader download "https://your-community.example.com/c/course-slug"
```

On the first run, a Chromium window opens. Sign in to Circle in that browser, return to the terminal, and press `Enter`.

After that, the CLI reuses the same dedicated browser profile for future downloads:

```bash
circle-course-downloader download "https://your-community.example.com/c/another-course"
```

Downloaded videos are saved to `downloads/` by default.

For a single community post or event page with one embedded video, use `download-standalone`:

```bash
circle-course-downloader download-standalone "https://your-community.example.com/c/space-slug/post-slug"
```

Use `download` for full course pages that list lessons under `/sections/.../lessons/...`.

## How It Works

1. Opens the requested Circle course page in a persistent Chromium profile.
2. If login is required, waits while you authenticate in the browser.
3. Saves the browser session under `.auth/`.
4. Discovers lesson links from the course page.
5. Visits each lesson, finds candidate video URLs, and classifies the provider.
6. Writes a manifest and downloads each available video with `yt-dlp`.

The default local files are:

```text
.auth/session-browser-profile/
.auth/session.json
downloads/manifest.json
downloads/manifest.csv
downloads/01 - Lesson title.mp4
```

Generated manifests can contain signed media URLs. Do not publish or commit them.

## CLI Usage

### Download a course

```bash
circle-course-downloader download [OPTIONS] COURSE_URL
```

Examples:

```bash
circle-course-downloader download "https://your-community.example.com/c/course-slug" --dry-run
circle-course-downloader download "https://your-community.example.com/c/course-slug" --output-dir "./my-videos"
circle-course-downloader download "https://your-community.example.com/c/course-slug" --force-login
circle-course-downloader download "https://your-community.example.com/c/course-slug" --headless
```

### Download a standalone page

```bash
circle-course-downloader download-standalone [OPTIONS] PAGE_URL
```

Examples:

```bash
circle-course-downloader download-standalone "https://your-community.example.com/c/eventos/my-event" --dry-run
circle-course-downloader download-standalone "https://your-community.example.com/c/eventos/my-event" --output-dir "./my-videos"
```

Both commands share the same options:

| Option | Description |
| --- | --- |
| `--output-dir PATH` | Save videos and manifests somewhere other than `downloads/`. |
| `--session PATH` | Use a different exported session file. The browser profile is stored next to it. |
| `--force-login` | Delete the saved auth state and open a fresh visible login browser. |
| `--headless` | Run Chromium without a visible window after a saved browser profile exists. |
| `--dry-run` | Discover videos and print the `yt-dlp` commands without downloading videos. |

`--headless` is useful only after a saved browser profile already exists. First login always uses a visible browser window.

## Install From Source

Clone the repository, create a virtual environment, install the package, and install Chromium for Playwright:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pip install .
.\.venv\Scripts\python -m playwright install chromium
```

Then run the CLI from the virtual environment:

```powershell
.\.venv\Scripts\circle-course-downloader download "https://your-community.example.com/c/course-slug"
```

For development and publishing tools:

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## Development

Run the local checks before opening a pull request:

```powershell
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m compileall .\src
.\.venv\Scripts\python -m build
.\.venv\Scripts\python -m twine check dist/*
.\.venv\Scripts\circle-course-downloader --help
.\.venv\Scripts\circle-course-downloader download --help
.\.venv\Scripts\circle-course-downloader download-standalone --help
```

The package metadata is defined in `pyproject.toml`, and the CLI entry point is:

```text
circle-course-downloader = circle_courses_downloader.cli:main
```

## Safety And Privacy

Circle Course Downloader uses its own Chromium profile under `.auth/`. It does not read cookies, sessions, or tokens from your default browser.

## Contributing

Contributions are welcome when they keep the project focused on the browser-only Circle course and standalone page download flow.

Good first improvements include:

- Better provider detection for embedded video platforms.
- Clearer error messages for expired sessions or unavailable lessons.
- More fixture-based parser tests.
- Cross-platform documentation polish.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md) before opening a pull request.

## License

MIT. See [LICENSE](LICENSE).
