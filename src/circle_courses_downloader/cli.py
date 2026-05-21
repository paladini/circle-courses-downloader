from __future__ import annotations

import argparse
from pathlib import Path

from .browser import discover_and_probe_with_browser
from .downloader import download_lessons
from .extractors import infer_login_url_from_origin
from .models import save_csv, save_manifest

DEFAULT_SESSION = Path(".auth/session.json")
DEFAULT_TIMEOUT_MS = 45_000
DEFAULT_VIDEO_TIMEOUT_MS = 20_000


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="circle-course-downloader",
        description="Download Circle course videos using browser-only login.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser("download", help="Download all videos from a Circle course URL.")
    download_parser.add_argument("course_url", help="Full Circle course URL, for example https://community.example.com/c/course-slug.")
    download_parser.add_argument("--output-dir", type=Path, default=Path("downloads"))
    download_parser.add_argument(
        "--session",
        type=Path,
        default=DEFAULT_SESSION,
        help="Exported session file. The browser profile is stored next to it.",
    )
    download_parser.add_argument("--force-login", action="store_true", help="Open the browser and create a fresh session.")
    download_parser.add_argument("--headless", action="store_true", help="Run Chromium without a visible window after login exists.")
    download_parser.add_argument("--dry-run", action="store_true", help="Discover lessons and print yt-dlp commands only.")

    return parser


def download_course(args: argparse.Namespace) -> None:
    args.login_url = infer_login_url_from_origin(course_url=args.course_url)
    if not args.login_url:
        raise SystemExit("course_url must be a full URL, for example https://community.example.com/c/course-slug")
    args.timeout_ms = DEFAULT_TIMEOUT_MS
    args.video_timeout_ms = DEFAULT_VIDEO_TIMEOUT_MS

    lessons = discover_and_probe_with_browser(args, args.course_url)
    save_manifest(Path("manifest.json"), lessons)
    save_csv(Path("manifest.csv"), lessons)
    save_manifest(Path("manifest.probed.json"), lessons)
    save_csv(Path("manifest.probed.csv"), lessons)

    download_lessons(args, lessons)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "download":
        download_course(args)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
