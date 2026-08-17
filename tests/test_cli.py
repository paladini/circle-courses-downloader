from argparse import Namespace
from pathlib import Path

import pytest

from circle_courses_downloader.cli import build_parser, main
from circle_courses_downloader.downloader import build_ytdlp_command, iter_download_targets
from circle_courses_downloader.extractors import standalone_lesson_from_page


def test_parser_accepts_download_standalone() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "download-standalone",
            "https://community.example.com/c/eventos/my-event",
            "--dry-run",
            "--output-dir",
            "out",
        ]
    )

    assert args.command == "download-standalone"
    assert args.page_url == "https://community.example.com/c/eventos/my-event"
    assert args.dry_run is True
    assert args.output_dir == Path("out")


def test_parser_requires_page_url_for_download_standalone() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["download-standalone"])


def test_parser_download_standalone_shares_session_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "download-standalone",
            "https://community.example.com/c/eventos/my-event",
            "--session",
            ".auth/custom.json",
            "--force-login",
            "--headless",
        ]
    )

    assert args.session == Path(".auth/custom.json")
    assert args.force_login is True
    assert args.headless is True


def test_main_rejects_unknown_command() -> None:
    with pytest.raises(SystemExit):
        main(["unknown-command"])


def test_standalone_lesson_flows_through_downloader_helpers() -> None:
    page_url = "https://community.example.com/c/eventos/my-event"
    html = '<meta property="og:title" content="My Event | Community" />'
    lesson = standalone_lesson_from_page(page_url, html)
    lesson.video_urls = ["https://cdn-media.circle.so/abc/hls/playlist.m3u8"]
    lesson.provider = "circle-hls"

    targets = list(iter_download_targets([lesson]))
    assert targets == [(lesson, lesson.video_urls[0])]

    command = build_ytdlp_command(Namespace(output_dir=Path("downloads")), lesson, lesson.video_urls[0])
    assert command[-1] == "https://cdn-media.circle.so/abc/hls/playlist.m3u8"
