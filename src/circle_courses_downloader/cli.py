from __future__ import annotations

import argparse
from pathlib import Path

from .browser import discover_and_probe_with_browser, probe_standalone_with_browser
from .downloader import download_lessons
from .extractors import infer_login_url_from_origin
from .models import save_csv, save_manifest

DEFAULT_SESSION = Path(".auth/session.json")
DEFAULT_TIMEOUT_MS = 45_000
DEFAULT_VIDEO_TIMEOUT_MS = 20_000
MANIFEST_JSON = "manifest.json"
MANIFEST_CSV = "manifest.csv"


def add_download_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-dir", type=Path, default=Path("downloads"))
    parser.add_argument(
        "--session",
        type=Path,
        default=DEFAULT_SESSION,
        help="Exported session file. The browser profile is stored next to it.",
    )
    parser.add_argument("--force-login", action="store_true", help="Open the browser and create a fresh session.")
    parser.add_argument("--headless", action="store_true", help="Run Chromium without a visible window after login exists.")
    parser.add_argument("--dry-run", action="store_true", help="Discover videos and print yt-dlp commands only.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="circle-course-downloader",
        description="Download Circle course videos using browser-only login.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser("download", help="Download all videos from a Circle course URL.")
    download_parser.add_argument("course_url", help="Full Circle course URL, for example https://community.example.com/c/course-slug.")
    add_download_options(download_parser)

    standalone_parser = subparsers.add_parser(
        "download-standalone",
        help="Download the video from a single Circle community page URL.",
    )
    standalone_parser.add_argument(
        "page_url",
        help="Full Circle page URL, for example https://community.example.com/c/space-slug/post-slug.",
    )
    add_download_options(standalone_parser)

    return parser


def prepare_download_args(args: argparse.Namespace, url: str, invalid_url_message: str) -> None:
    args.login_url = infer_login_url_from_origin(course_url=url)
    if not args.login_url:
        raise SystemExit(invalid_url_message)
    args.timeout_ms = DEFAULT_TIMEOUT_MS
    args.video_timeout_ms = DEFAULT_VIDEO_TIMEOUT_MS


def download_course(args: argparse.Namespace) -> None:
    prepare_download_args(
        args,
        args.course_url,
        "course_url must be a full URL, for example https://community.example.com/c/course-slug",
    )

    lessons = discover_and_probe_with_browser(args, args.course_url)
    save_manifest(args.output_dir / MANIFEST_JSON, lessons)
    save_csv(args.output_dir / MANIFEST_CSV, lessons)

    download_lessons(args, lessons)


def download_standalone(args: argparse.Namespace) -> None:
    prepare_download_args(
        args,
        args.page_url,
        "page_url must be a full URL, for example https://community.example.com/c/space-slug/post-slug",
    )

    lessons = probe_standalone_with_browser(args, args.page_url)
    save_manifest(args.output_dir / MANIFEST_JSON, lessons)
    save_csv(args.output_dir / MANIFEST_CSV, lessons)

    download_lessons(args, lessons)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "download":
        download_course(args)
        return 0

    if args.command == "download-standalone":
        download_standalone(args)
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
