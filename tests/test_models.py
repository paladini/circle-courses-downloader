import json

from circle_courses_downloader.models import Lesson, save_manifest


def test_save_manifest_writes_course_lessons(tmp_path) -> None:
    manifest_path = tmp_path / "manifest.json"
    lessons = [
        Lesson(
            index=1,
            section_id="10",
            lesson_id="20",
            url="https://community.example.com/c/course/sections/10/lessons/20",
            title="Lesson title",
            provider="circle-hls",
            video_urls=["https://cdn-media.circle.so/abc/hls/playlist.m3u8"],
        )
    ]

    save_manifest(manifest_path, lessons)

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["lesson_count"] == 1
    assert payload["lessons"][0]["title"] == "Lesson title"
    assert "source_html" not in payload
