# Circle Course Downloader

Download videos from Circle courses you can access with your own account. Authentication happens only in the browser: the tool opens a dedicated Chromium profile, you log in manually, and that browser profile is reused for future downloads.

This tool does not bypass DRM, paywalls, captchas, 2FA, or access controls. Use it only for content you are authorized to download for personal offline viewing.

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m playwright install chromium
```

## Download a Course

```powershell
.\.venv\Scripts\circle-course-downloader download "https://your-circle-site.com/c/course-slug"
```

## What Happens Next

On the first run, a Chromium window opens. Log in to Circle in that browser, then return to the terminal and press `Enter`.

The tool stores the dedicated browser profile and an exported session file under:

```text
.auth/session-browser-profile/
.auth/session.json
```

Then it opens the course in the same authenticated browser profile, discovers the lessons, extracts the video URLs, and downloads the videos into:

```text
downloads/
```

## Download Another Course

Use the same command with another course URL. The saved session is reused automatically.

```powershell
.\.venv\Scripts\circle-course-downloader download "https://your-circle-site.com/c/another-course"
```

## Reset Login

Use `--force-login` to open the browser and create a fresh session.

```powershell
.\.venv\Scripts\circle-course-downloader download "https://your-circle-site.com/c/course-slug" --force-login
```

## Optional Flags

```powershell
.\.venv\Scripts\circle-course-downloader download "https://your-circle-site.com/c/course-slug" --output-dir ".\my-videos"
.\.venv\Scripts\circle-course-downloader download "https://your-circle-site.com/c/course-slug" --session ".auth/my-site.json"
.\.venv\Scripts\circle-course-downloader download "https://your-circle-site.com/c/course-slug" --dry-run
.\.venv\Scripts\circle-course-downloader download "https://your-circle-site.com/c/course-slug" --headless
```

`--headless` only hides Chromium after a saved browser profile already exists. First login always opens a visible browser window, and the downloader keeps using that same browser profile after you press `Enter`.

## Security Notes

Never commit `.auth/` or downloaded videos.

The tool does not read tokens or cookies from your default browser. It uses its own dedicated Chromium profile under `.auth/`.

Circle HLS URLs are usually signed and expire. Download soon after the tool discovers them.
