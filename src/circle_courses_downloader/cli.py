from __future__ import annotations

import argparse
import os
from pathlib import Path

from .browser import BrowserAuth, discover_lessons_with_browser, login_and_save_state, probe_lessons_with_browser, resolve_secret
from .downloader import download_lessons
from .extractors import (
    DEFAULT_HTML,
    build_course_url,
    classify_provider,
    extract_current_lesson_ids,
    extract_lessons,
    find_video_urls,
    infer_login_url_from_lessons,
    infer_login_url_from_origin,
)
from .http_probe import probe_lessons, probe_saved_pages
from .models import load_manifest, save_csv, save_manifest


def add_cookie_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cookie-header", help="Raw Circle Cookie header copied from a logged-in browser.")
    parser.add_argument("--cookies-file", type=Path, help="Netscape cookies.txt file for the Circle site.")
    parser.add_argument(
        "--user-agent",
        default=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"
        ),
    )
    parser.add_argument("--timeout", type=int, default=30)


def add_browser_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--email", help="Circle account email. Prefer CIRCLE_EMAIL for local use.")
    parser.add_argument("--password", help="Circle account password. Prefer CIRCLE_PASSWORD for local use.")
    parser.add_argument("--email-env", default="CIRCLE_EMAIL")
    parser.add_argument("--password-env", default="CIRCLE_PASSWORD")
    parser.add_argument("--site-url", help="Circle site origin, for example https://community.example.com.")
    parser.add_argument("--login-url", help="Full login URL. Defaults to <site-url>/users/sign_in or manifest host.")
    parser.add_argument("--storage-state", type=Path, default=Path(".auth/circle-session.json"))
    parser.add_argument("--headless", action="store_true", help="Run Chromium without a visible window.")
    parser.add_argument("--manual-login", action="store_true", help="Open browser and let you complete login manually.")
    parser.add_argument("--force-login", action="store_true", help="Discard/recreate the saved browser session.")
    parser.add_argument("--timeout-ms", type=int, default=45_000)


def add_course_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--html", type=Path, help="Saved Circle course HTML page.")
    parser.add_argument("--course-url", help="Full Circle course URL, for example https://community.example.com/c/course-slug.")
    parser.add_argument("--course-id", help="Course slug/id used after /c/. Requires --site-url unless this is a full URL.")


def add_download_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-dir", type=Path, default=Path("downloads"))
    parser.add_argument("--format", default="bv*+ba/best")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--ytdlp-cookies-file", type=Path)
    parser.add_argument("--ytdlp-cookies-from-browser", help="Example: chrome, edge, firefox")


def resolve_browser_credentials(args: argparse.Namespace, require: bool = False) -> None:
    if args.manual_login:
        args.email = args.email or os.getenv(args.email_env)
        args.password = args.password or os.getenv(args.password_env)
        return
    if not require and args.storage_state.exists() and not args.force_login:
        args.email = args.email or os.getenv(args.email_env)
        args.password = args.password or os.getenv(args.password_env)
        return
    args.email = resolve_secret(args.email, args.email_env, "Circle email: ")
    args.password = resolve_secret(args.password, args.password_env, "Circle password: ", password=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract and download Circle course lesson videos.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest_parser = subparsers.add_parser("manifest", help="Extract lesson links from the saved course HTML.")
    manifest_parser.add_argument("--html", type=Path, default=Path(DEFAULT_HTML))
    manifest_parser.add_argument("--out", type=Path, default=Path("manifest.json"))
    manifest_parser.add_argument("--csv", type=Path, default=Path("manifest.csv"))

    probe_parser = subparsers.add_parser("probe", help="Probe lessons with raw cookies.")
    probe_parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    probe_parser.add_argument("--out", type=Path, default=Path("manifest.probed.json"))
    probe_parser.add_argument("--csv", type=Path, default=Path("manifest.probed.csv"))
    add_cookie_args(probe_parser)

    login_parser = subparsers.add_parser("login", help="Open Chromium, log into Circle, and save a reusable session.")
    login_parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    add_browser_args(login_parser)

    browser_probe_parser = subparsers.add_parser("probe-browser", help="Probe lesson video URLs with Playwright.")
    browser_probe_parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    browser_probe_parser.add_argument("--out", type=Path, default=Path("manifest.probed.json"))
    browser_probe_parser.add_argument("--csv", type=Path, default=Path("manifest.probed.csv"))
    browser_probe_parser.add_argument("--video-timeout-ms", type=int, default=20_000)
    add_browser_args(browser_probe_parser)

    inspect_parser = subparsers.add_parser("inspect-page", help="Detect video URLs in a saved lesson HTML file.")
    inspect_parser.add_argument("--html", type=Path, required=True)

    local_probe_parser = subparsers.add_parser("probe-local", help="Probe using saved lesson HTML files.")
    local_probe_parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    local_probe_parser.add_argument("--html", type=Path, nargs="+", required=True)
    local_probe_parser.add_argument("--out", type=Path, default=Path("manifest.probed.json"))
    local_probe_parser.add_argument("--csv", type=Path, default=Path("manifest.probed.csv"))

    download_parser = subparsers.add_parser("download", help="Download probed lesson videos with yt-dlp.")
    download_parser.add_argument("--manifest", type=Path, default=Path("manifest.probed.json"))
    add_download_args(download_parser)

    run_parser = subparsers.add_parser("run", help="Manifest, browser probe, and download in one command.")
    add_course_source_args(run_parser)
    run_parser.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    run_parser.add_argument("--out", type=Path, default=Path("manifest.probed.json"))
    run_parser.add_argument("--csv", type=Path, default=Path("manifest.probed.csv"))
    run_parser.add_argument("--video-timeout-ms", type=int, default=20_000)
    run_parser.add_argument("--skip-download", action="store_true")
    add_browser_args(run_parser)
    add_download_args(run_parser)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "manifest":
        lessons = extract_lessons(args.html)
        save_manifest(args.out, lessons, args.html)
        save_csv(args.csv, lessons)
        print(f"Found {len(lessons)} lessons.")
        print(f"Wrote {args.out} and {args.csv}.")
        return 0

    if args.command == "probe":
        lessons = probe_lessons(args, load_manifest(args.manifest))
        save_manifest(args.out, lessons)
        save_csv(args.csv, lessons)
        print(f"Wrote {args.out} and {args.csv}.")
        return 0

    if args.command == "login":
        resolve_browser_credentials(args, require=True)
        lessons = load_manifest(args.manifest) if args.manifest.exists() else []
        args.login_url = infer_login_url_from_lessons(lessons, args.site_url, args.login_url)
        auth = BrowserAuth(args.email, args.password, args.login_url, args.storage_state, args.headless, args.timeout_ms)
        login_and_save_state(auth, manual=args.manual_login)
        return 0

    if args.command == "probe-browser":
        resolve_browser_credentials(args)
        manifest_lessons = load_manifest(args.manifest)
        args.login_url = infer_login_url_from_lessons(manifest_lessons, args.site_url, args.login_url)
        lessons = probe_lessons_with_browser(args, manifest_lessons)
        save_manifest(args.out, lessons)
        save_csv(args.csv, lessons)
        print(f"Wrote {args.out} and {args.csv}.")
        return 0

    if args.command == "inspect-page":
        page = args.html.read_text(encoding="utf-8", errors="ignore")
        urls = find_video_urls(page)
        lesson_ids = extract_current_lesson_ids(page)
        if lesson_ids:
            print(f"Lesson id(s): {', '.join(lesson_ids)}")
        print(f"Found {len(urls)} candidate video URLs.")
        for url in urls:
            print(f"{classify_provider(url):17} {url}")
        return 0

    if args.command == "probe-local":
        lessons = probe_saved_pages(args, load_manifest(args.manifest))
        save_manifest(args.out, lessons)
        save_csv(args.csv, lessons)
        print(f"Wrote {args.out} and {args.csv}.")
        return 0

    if args.command == "download":
        download_lessons(args, load_manifest(args.manifest))
        return 0

    if args.command == "run":
        resolve_browser_credentials(args)
        course_url = build_course_url(args.site_url, args.course_url, args.course_id)
        if course_url:
            args.login_url = infer_login_url_from_origin(args.site_url, args.login_url, course_url)
            lessons = discover_lessons_with_browser(args, course_url)
            source_html = None
        else:
            html_path = args.html or Path(DEFAULT_HTML)
            lessons = extract_lessons(html_path)
            args.login_url = infer_login_url_from_lessons(lessons, args.site_url, args.login_url)
            source_html = html_path
        save_manifest(args.manifest, lessons, source_html)
        save_csv(args.manifest.with_suffix(".csv"), lessons)
        lessons = probe_lessons_with_browser(args, lessons)
        save_manifest(args.out, lessons)
        save_csv(args.csv, lessons)
        if not args.skip_download:
            download_lessons(args, lessons)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
