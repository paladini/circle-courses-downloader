from __future__ import annotations

import html
import re
from urllib.parse import urljoin, urlparse

from .models import Lesson


LESSON_RE = re.compile(
    r"<a\b(?P<attrs>[^>]*)href=[\"'](?P<url>(?:https?://[^\"']+)?/c/[^\"']+/sections/"
    r"(?P<section_id>\d+)/lessons/(?P<lesson_id>\d+))[\"'][^>]*>(?P<body>.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
SAVED_FROM_RE = re.compile(r"saved from url=\(\d+\)(?P<url>https?://[^\s]+)", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
URL_RE = re.compile(r"https?://[^\s\"'<>\\]+", re.IGNORECASE)
ESCAPED_URL_RE = re.compile(r"https?:\\?/\\?/[^\s\"'<>]+", re.IGNORECASE)
YOUTUBE_ID_RE = re.compile(
    r"(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=|shorts/)|youtu\.be/)"
    r"([A-Za-z0-9_-]{6,})",
    re.IGNORECASE,
)

PROVIDERS = {
    "circle-hls": ("cdn-media.circle.so",),
    "youtube": ("youtube.com", "youtube-nocookie.com", "youtu.be"),
    "vimeo": ("vimeo.com", "player.vimeo.com"),
    "wistia": ("wistia.com", "wistia.net"),
    "loom": ("loom.com",),
    "mux": ("stream.mux.com", "mux.com"),
    "cloudflare-stream": ("videodelivery.net", "cloudflarestream.com"),
    "direct-video": (".mp4", ".m3u8", ".webm", ".mov"),
}
NON_VIDEO_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".css", ".js", ".woff", ".woff2")
PROVIDER_PRIORITY = {
    "circle-hls": 0,
    "direct-video": 1,
    "mux": 2,
    "cloudflare-stream": 3,
    "vimeo": 4,
    "wistia": 5,
    "loom": 6,
    "youtube": 7,
    "unknown": 99,
}


def strip_tags(fragment: str) -> str:
    text = TAG_RE.sub(" ", fragment)
    return " ".join(html.unescape(text).split())


def infer_base_url(page: str) -> str | None:
    saved_from = SAVED_FROM_RE.search(page)
    if saved_from:
        parsed = urlparse(html.unescape(saved_from.group("url")))
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"

    href = re.search(r'href=["\'](?P<url>https?://[^"\']+/c/[^"\']+)["\']', page, flags=re.IGNORECASE)
    if href:
        parsed = urlparse(html.unescape(href.group("url")))
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"

    return None


def extract_lessons_from_html(page: str, base_url: str | None = None) -> list[Lesson]:
    base_url = base_url or infer_base_url(page)
    lessons: list[Lesson] = []
    seen: set[str] = set()

    for match in LESSON_RE.finditer(page):
        lesson_id = match.group("lesson_id")
        if lesson_id in seen:
            continue
        seen.add(lesson_id)

        body = match.group("body")
        paragraphs = [
            strip_tags(part)
            for part in re.findall(r"<p\b[^>]*>(.*?)</p>", body, flags=re.IGNORECASE | re.DOTALL)
        ]
        paragraphs = [part for part in paragraphs if part]
        title = paragraphs[0] if paragraphs else f"lesson-{lesson_id}"
        duration = paragraphs[-1] if len(paragraphs) > 1 else ""

        lessons.append(
            Lesson(
                index=len(lessons) + 1,
                section_id=match.group("section_id"),
                lesson_id=lesson_id,
                url=urljoin(base_url or "", html.unescape(match.group("url"))),
                title=title,
                duration=duration,
            )
        )

    return lessons


def normalize_scraped_url(value: str) -> str:
    value = html.unescape(value)
    value = value.replace("\\/", "/").replace("\\u002F", "/")
    return value.strip(" \t\r\n\"'(),;")


def youtube_watch_url(value: str) -> str | None:
    match = YOUTUBE_ID_RE.search(value)
    if not match:
        return None
    return f"https://www.youtube.com/watch?v={match.group(1)}"


def classify_provider(value: str) -> str:
    lowered = value.lower()
    for provider, needles in PROVIDERS.items():
        if any(needle in lowered for needle in needles):
            return provider
    return "unknown"


def is_video_candidate(value: str, provider: str) -> bool:
    lowered = value.lower()
    if any(ext in lowered.split("?", 1)[0] for ext in NON_VIDEO_EXTENSIONS):
        return False
    if provider == "circle-hls":
        return any(needle in lowered for needle in (".m3u8", "/hls/", ".mp4", ".webm", ".mov"))
    return True


def find_video_urls(page: str, extra_urls: list[str] | None = None) -> list[str]:
    decoded = html.unescape(page).replace("\\/", "/").replace("\\u002F", "/")
    candidates = {normalize_scraped_url(m.group(0)) for m in URL_RE.finditer(decoded)}
    candidates.update(normalize_scraped_url(m.group(0)) for m in ESCAPED_URL_RE.finditer(page))
    candidates.update(normalize_scraped_url(url) for url in extra_urls or [])

    video_urls: list[str] = []
    seen: set[str] = set()
    for candidate in sorted(candidates):
        if "youtube" in candidate.lower() or "youtu.be" in candidate.lower():
            normalized = youtube_watch_url(candidate)
            if not normalized:
                continue
        else:
            normalized = candidate
        provider = classify_provider(normalized)
        if provider == "unknown" or not is_video_candidate(normalized, provider):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        video_urls.append(normalized)

    return sorted(video_urls, key=lambda url: (PROVIDER_PRIORITY.get(classify_provider(url), 99), url))


def infer_login_url_from_origin(
    course_url: str | None = None,
) -> str | None:
    if course_url:
        parsed = urlparse(course_url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}/users/sign_in"
    return None
