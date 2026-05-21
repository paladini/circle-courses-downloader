# Circle Courses Downloader

Personal downloader for Circle course lessons that your own logged-in account can access.

It can:

- Extract a lesson manifest from a saved Circle course HTML page.
- Open Chromium with Playwright, log into a Circle site, and save a reusable local browser session.
- Visit every lesson page from that session and detect the real video URL.
- Download detected media with `yt-dlp`.
- Probe saved lesson HTML files when you already have them locally.

This tool does not bypass DRM, paywalls, captchas, 2FA, or access controls. Use it only for content you are authorized to download for personal offline viewing.

## Quick Start

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m playwright install chromium
```

Create a manifest from a saved Circle course page:

```powershell
.\.venv\Scripts\python .\download_course.py manifest --html ".\course-page.html"
```

Set credentials through environment variables:

```powershell
$env:CIRCLE_EMAIL = "you@example.com"
$env:CIRCLE_PASSWORD = "your-password"
```

Probe lesson pages with Playwright:

```powershell
.\.venv\Scripts\python .\download_course.py probe-browser
```

Download videos:

```powershell
.\.venv\Scripts\python .\download_course.py download
```

## One Command With a Course Link

This is the easiest flow for someone who just cloned the project:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m playwright install chromium

$env:CIRCLE_EMAIL = "you@example.com"
$env:CIRCLE_PASSWORD = "your-password"

.\.venv\Scripts\python .\download_course.py run `
  --course-url "https://community.example.com/c/course-slug"
```

You can also pass the Circle site and the course slug/id separately:

```powershell
.\.venv\Scripts\python .\download_course.py run `
  --site-url "https://community.example.com" `
  --course-id "course-slug"
```

In Circle URLs, the course id this tool needs is usually the value after `/c/`.

For example:

```text
https://community.example.com/c/my-course-name
                                ^^^^^^^^^^^^^^
                                course id/slug
```

## One Command With a Saved HTML Page

If your saved course page contains absolute Circle lesson links, the tool can infer the site login URL:

```powershell
.\.venv\Scripts\python .\download_course.py run --html ".\course-page.html"
```

If the tool cannot infer the site, pass the Circle site origin:

```powershell
.\.venv\Scripts\python .\download_course.py run `
  --html ".\course-page.html" `
  --site-url "https://community.example.com"
```

You can also pass the exact login URL:

```powershell
.\.venv\Scripts\python .\download_course.py run `
  --html ".\course-page.html" `
  --login-url "https://community.example.com/users/sign_in"
```

What `run` does:

1. Logs into the Circle site if `.auth/circle-session.json` does not exist.
2. Opens the course link or reads the saved course HTML.
3. Discovers lesson URLs and writes `manifest.json` and `manifest.csv`.
4. Visits every lesson URL from the manifest.
5. Detects the primary media URL, usually Circle HLS `playlist.m3u8`.
6. Writes `manifest.probed.json` and `manifest.probed.csv`.
7. Downloads videos into `downloads/`.

Use `--skip-download` to only probe:

```powershell
.\.venv\Scripts\python .\download_course.py run --course-url "https://community.example.com/c/course-slug" --skip-download
```

Use `--headless` to hide Chromium:

```powershell
.\.venv\Scripts\python .\download_course.py run --html ".\course-page.html" --headless
```

## Manual Login

If the site uses captcha, SSO, or 2FA, do a manual login once:

```powershell
.\.venv\Scripts\python .\download_course.py login --site-url "https://community.example.com" --manual-login
.\.venv\Scripts\python .\download_course.py probe-browser
.\.venv\Scripts\python .\download_course.py download
```

The browser session is saved to `.auth/circle-session.json` and ignored by Git.

Force a new login:

```powershell
.\.venv\Scripts\python .\download_course.py login --site-url "https://community.example.com" --force-login
```

## Saved HTML Flow

Inspect one saved lesson page:

```powershell
.\.venv\Scripts\python .\download_course.py inspect-page --html ".\lesson-page.html"
```

Update the manifest from one or more saved lesson pages:

```powershell
.\.venv\Scripts\python .\download_course.py probe-local --html ".\lesson-page.html"
```

You can pass a directory:

```powershell
.\.venv\Scripts\python .\download_course.py probe-local --html ".\saved-lessons"
```

## Cookie Fallback

If you prefer to copy cookies manually:

```powershell
$env:CIRCLE_COOKIE = "paste-cookie-header-here"
.\.venv\Scripts\python .\download_course.py probe --cookie-header $env:CIRCLE_COOKIE
.\.venv\Scripts\python .\download_course.py download
```

## Generic Site Support

The parser looks for Circle-style lesson URLs:

```text
https://any-circle-site.example/c/<course-slug>/sections/<section-id>/lessons/<lesson-id>
```

Relative links like `/c/<course>/sections/.../lessons/...` are supported when the saved HTML includes a source URL or other absolute course links that reveal the site origin.

Use these options when inference is not enough:

- `--site-url`: Circle site origin, such as `https://community.example.com`.
- `--login-url`: exact login URL.
- `--storage-state`: where to store the authenticated browser session.
- `--email-env` and `--password-env`: custom environment variable names for credentials.

## Project Layout

```text
src/circle_courses_downloader/
  browser.py       Playwright login and browser probing
  cli.py           command-line interface
  downloader.py    yt-dlp command builder and downloads
  extractors.py    HTML parsing and video URL detection
  http_probe.py    cookie-header probing fallback
  models.py        manifest model, JSON and CSV helpers
download_course.py backward-compatible script entrypoint
pyproject.toml     package metadata and console script
requirements.txt   runtime dependencies
```

## Editable Install

```powershell
.\.venv\Scripts\python -m pip install -e .
circle-courses-downloader --help
```

You can also run:

```powershell
.\.venv\Scripts\python -m circle_courses_downloader --help
```

## Security Notes

Never commit `.auth/`, `.env`, `cookies.txt`, or downloaded videos.

Circle HLS URLs are usually signed and expire. Probe and download in the same session when possible.
