from circle_courses_downloader.extractors import (
    classify_provider,
    extract_lessons_from_html,
    extract_page_title,
    find_video_urls,
    infer_login_url_from_origin,
    standalone_lesson_from_page,
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


def test_extract_page_title_prefers_og_title() -> None:
    html = """
    <head>
      <meta property="og:title" content="Harness Engineering na Prática | Tech Leads club" />
      <title>Fallback title</title>
    </head>
    """

    assert extract_page_title(html) == "Harness Engineering na Prática"


def test_extract_page_title_falls_back_to_title_tag() -> None:
    html = "<html><head><title>Event replay | Community</title></head></html>"

    assert extract_page_title(html) == "Event replay"


def test_extract_page_title_falls_back_to_url_slug() -> None:
    page_url = "https://community.example.com/c/eventos/my-event-slug"

    assert extract_page_title("<html></html>", page_url=page_url) == "my event slug"


def test_standalone_lesson_from_page() -> None:
    page_url = "https://community.example.com/c/eventos-da-comunidade/my-event-slug"
    html = '<meta property="og:title" content="My Event | Community" />'

    lesson = standalone_lesson_from_page(page_url, html)

    assert lesson.index == 1
    assert lesson.section_id == "standalone"
    assert lesson.lesson_id == "my-event-slug"
    assert lesson.url == page_url
    assert lesson.title == "My Event"


def test_find_video_urls_on_post_like_html() -> None:
    html = """
    <script>
      window.stream = "https:\\/\\/stream.mux.com\\/abc123.m3u8";
    </script>
    """

    urls = find_video_urls(html)

    assert urls[0] == "https://stream.mux.com/abc123.m3u8"
    assert classify_provider(urls[0]) == "mux"
