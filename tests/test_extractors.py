from circle_courses_downloader.extractors import (
    classify_provider,
    extract_lessons_from_html,
    find_video_urls,
    infer_login_url_from_origin,
)


def test_extract_lessons_from_circle_course_html() -> None:
    html = """
    <a href="/c/course-slug/sections/123/lessons/456">
      <div><p>Lesson title</p><p>12:34</p></div>
    </a>
    <a href="/c/course-slug/sections/123/lessons/456">
      <div><p>Duplicate lesson title</p><p>12:34</p></div>
    </a>
    """

    lessons = extract_lessons_from_html(html, base_url="https://community.example.com/c/course-slug")

    assert len(lessons) == 1
    assert lessons[0].index == 1
    assert lessons[0].section_id == "123"
    assert lessons[0].lesson_id == "456"
    assert lessons[0].title == "Lesson title"
    assert lessons[0].duration == "12:34"
    assert lessons[0].url == "https://community.example.com/c/course-slug/sections/123/lessons/456"


def test_find_video_urls_prioritizes_circle_hls() -> None:
    html = """
    <script>
      window.video = "https:\\/\\/cdn-media.circle.so\\/abc\\/hls\\/playlist.m3u8";
      window.preview = "https://cdn-media.circle.so/abc/cover.jpg";
      window.youtube = "https://www.youtube.com/embed/abcDEF12345";
    </script>
    """

    urls = find_video_urls(html, extra_urls=["https://player.vimeo.com/video/123456"])

    assert urls[0] == "https://cdn-media.circle.so/abc/hls/playlist.m3u8"
    assert "https://www.youtube.com/watch?v=abcDEF12345" in urls
    assert "https://player.vimeo.com/video/123456" in urls
    assert all("cover.jpg" not in url for url in urls)


def test_classify_provider_and_login_url() -> None:
    assert classify_provider("https://cdn-media.circle.so/abc/hls/playlist.m3u8") == "circle-hls"
    assert classify_provider("https://example.com/video.mp4") == "direct-video"
    assert infer_login_url_from_origin("https://community.example.com/c/course-slug") == (
        "https://community.example.com/users/sign_in"
    )
    assert infer_login_url_from_origin("not-a-url") is None
