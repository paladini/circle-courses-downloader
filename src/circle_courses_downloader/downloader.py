from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from .models import Lesson


def safe_filename(value: str, max_length: int = 120) -> str:
    value = re.sub(r"[<>:\"/\\|?*\x00-\x1F]", " ", value)
    value = " ".join(value.split()).strip(". ")
    return value[:max_length].rstrip() or "lesson"


def iter_download_targets(lessons: Iterable[Lesson]) -> Iterable[tuple[Lesson, str]]:
    for lesson in lessons:
        if lesson.video_urls:
            yield lesson, lesson.video_urls[0]


def build_ytdlp_command(args: argparse.Namespace, lesson: Lesson, video_url: str) -> list[str]:
    output_dir: Path = args.output_dir
    filename = f"{lesson.index:02d} - {safe_filename(lesson.title)}.%(ext)s"
    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "--continue",
        "--merge-output-format",
        "mp4",
        "-f",
        args.format,
        "-o",
        str(output_dir / filename),
        video_url,
    ]
    if args.ytdlp_cookies_file:
        command[-1:-1] = ["--cookies", str(args.ytdlp_cookies_file)]
    if args.ytdlp_cookies_from_browser:
        command[-1:-1] = ["--cookies-from-browser", args.ytdlp_cookies_from_browser]
    return command


def download_lessons(args: argparse.Namespace, lessons: list[Lesson]) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)

    found_any = False
    for lesson, video_url in iter_download_targets(lessons):
        found_any = True
        command = build_ytdlp_command(args, lesson, video_url)
        print(f"Downloading [{lesson.index:02d}] {lesson.title}")
        if args.dry_run:
            print(" ".join(command))
            continue
        subprocess.run(command, check=True)

    if not found_any:
        print("No downloadable video URLs found in the manifest. Run probe-browser, probe, or probe-local first.")
