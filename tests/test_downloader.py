from argparse import Namespace
from pathlib import Path

from circle_courses_downloader.downloader import build_ytdlp_command, iter_download_targets, safe_filename
from circle_courses_downloader.models import Lesson


def lesson(index: int, title: str, video_urls: list[str] | None = None) -> Lesson:
    return Lesson(
        index=index,
        section_id="10",
        lesson_id=str(index),
        url=f"https://community.example.com/c/course/sections/10/lessons/{index}",
        title=title,
        duration="",
        provider="circle-hls" if video_urls else "",
        video_urls=video_urls or [],
    )


def test_safe_filename_removes_invalid_characters() -> None:
    assert safe_filename('A <bad> "filename" / lesson?') == "A bad filename lesson"
    assert safe_filename("   ") == "lesson"


def test_iter_download_targets_skips_lessons_without_video_urls() -> None:
    lessons = [
        lesson(1, "No video"),
        lesson(2, "With video", ["https://cdn-media.circle.so/abc/hls/playlist.m3u8"]),
    ]

    targets = list(iter_download_targets(lessons))

    assert targets == [(lessons[1], "https://cdn-media.circle.so/abc/hls/playlist.m3u8")]


def test_build_ytdlp_command_uses_python_module() -> None:
    args = Namespace(output_dir=Path("downloads"))
    target = lesson(3, "Intro: setup", ["https://cdn-media.circle.so/abc/hls/playlist.m3u8"])

    command = build_ytdlp_command(args, target, target.video_urls[0])

    assert command[1:3] == ["-m", "yt_dlp"]
    assert "--merge-output-format" in command
    assert "downloads" in command[-2]
    assert command[-1] == "https://cdn-media.circle.so/abc/hls/playlist.m3u8"
