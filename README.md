# Circle Course Downloader

Download videos from Circle courses you can access with your own account.
Authentication happens only in the browser: the tool opens a dedicated Chromium
profile, you log in manually, and that browser profile is reused for future
downloads.

This tool doesn't bypass DRM, paywalls, captchas, 2FA, or access controls. Use
it only for content you are authorized to download for personal offline viewing.

## Install from PyPI

```powershell
python -m pip install circle-course-downloader
python -m playwright install chromium
```

## Install from source

Use this path when you cloned the repository locally.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install .
.\.venv\Scripts\python -m playwright install chromium
```

For development and publishing tools, install `requirements.txt` after the
package:

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## Download a course

```powershell
circle-course-downloader download "https://your-circle-site.com/c/course-slug"
```

If you installed from source in a virtual environment, run:

```powershell
.\.venv\Scripts\circle-course-downloader download "https://your-circle-site.com/c/course-slug"
```

## What happens next

On the first run, a Chromium window opens. Log in to Circle in that browser,
then return to the terminal and press `Enter`.

The tool stores the dedicated browser profile and an exported session file
under:

```text
.auth/session-browser-profile/
.auth/session.json
```

Then it opens the course in the same authenticated browser profile, discovers
the lessons, extracts the video URLs, and downloads the videos into
`downloads/`.

The downloader also writes a local manifest beside the downloaded videos:

```text
downloads/manifest.json
downloads/manifest.csv
```

Generated manifests can contain signed media URLs, so don't commit them.

## Download another course

Use the same command with another course URL. The saved session is reused
automatically.

```powershell
circle-course-downloader download "https://your-circle-site.com/c/another-course"
```

## Reset login

Use `--force-login` to open the browser and create a fresh session.

```powershell
circle-course-downloader download "https://your-circle-site.com/c/course-slug" --force-login
```

## Optional flags

```powershell
circle-course-downloader download "https://your-circle-site.com/c/course-slug" --output-dir ".\my-videos"
circle-course-downloader download "https://your-circle-site.com/c/course-slug" --session ".auth/my-site.json"
circle-course-downloader download "https://your-circle-site.com/c/course-slug" --dry-run
circle-course-downloader download "https://your-circle-site.com/c/course-slug" --headless
```

`--headless` only hides Chromium after a saved browser profile already exists.
First login always opens a visible browser window, and the downloader keeps
using that same browser profile after you press `Enter`.

## Build and publish

Install the package and publishing tools:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install .
.\.venv\Scripts\python -m pip install -r requirements.txt
```

Run checks:

```powershell
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m build
.\.venv\Scripts\python -m twine check dist/*
```

Publish to TestPyPI first:

```powershell
.\.venv\Scripts\python -m twine upload --repository testpypi dist/*
```

After validating the TestPyPI package, publish to PyPI:

```powershell
.\.venv\Scripts\python -m twine upload dist/*
```

## Security notes

Never commit `.auth/`, downloaded videos, or generated manifests.

The tool doesn't read tokens or cookies from your default browser. It uses its
own dedicated Chromium profile under `.auth/`.

Circle HLS URLs are usually signed and expire. Download soon after the tool
discovers them.
