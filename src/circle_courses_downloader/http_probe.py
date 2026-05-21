from __future__ import annotations

import argparse
import sys
from http.cookiejar import MozillaCookieJar
from urllib.parse import urlparse

import requests

from .extractors import classify_provider, collect_html_files, extract_current_lesson_ids, find_video_urls
from .models import Lesson


def build_session(args: argparse.Namespace) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": args.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    )
    if args.cookie_header:
        session.headers["Cookie"] = args.cookie_header
    if args.cookies_file:
        jar = MozillaCookieJar(str(args.cookies_file))
        jar.load(ignore_discard=True, ignore_expires=True)
        session.cookies.update(jar)
    return session


def fetch_lesson(session: requests.Session, lesson: Lesson, timeout: int) -> str:
    response = session.get(lesson.url, timeout=timeout)
    response.raise_for_status()
    if "/users/sign_in" in urlparse(response.url).path:
        raise RuntimeError("Circle redirected to sign-in. Use browser login or export logged-in cookies.")
    return response.text


def probe_lessons(args: argparse.Namespace, lessons: list[Lesson]) -> list[Lesson]:
    session = build_session(args)
    for lesson in lessons:
        try:
            page = fetch_lesson(session, lesson, args.timeout)
            lesson.video_urls = find_video_urls(page)
            lesson.provider = classify_provider(lesson.video_urls[0]) if lesson.video_urls else "not-found"
            print(f"[{lesson.index:02d}] {lesson.provider:17} {lesson.title}")
        except Exception as exc:  # noqa: BLE001 - CLI should report every lesson and keep going.
            lesson.provider = "error"
            lesson.video_urls = []
            print(f"[{lesson.index:02d}] error             {lesson.title} ({exc})", file=sys.stderr)
    return lessons


def probe_saved_pages(args: argparse.Namespace, lessons: list[Lesson]) -> list[Lesson]:
    by_id = {lesson.lesson_id: lesson for lesson in lessons}
    html_files = collect_html_files(args.html)
    updated = 0

    for html_path in html_files:
        page = html_path.read_text(encoding="utf-8", errors="ignore")
        lesson_ids = extract_current_lesson_ids(page)
        video_urls = find_video_urls(page)
        if not lesson_ids:
            print(f"skip              {html_path} (no current lesson id found)")
            continue
        if not video_urls:
            print(f"skip              {html_path} (no video URL found)")
            continue

        for lesson_id in lesson_ids:
            lesson = by_id.get(lesson_id)
            if not lesson:
                print(f"skip              {html_path} (lesson {lesson_id} is not in manifest)")
                continue
            lesson.video_urls = video_urls
            lesson.provider = classify_provider(video_urls[0])
            updated += 1
            print(f"[{lesson.index:02d}] {lesson.provider:17} {lesson.title} <- {html_path}")

    print(f"Updated {updated} lesson(s) from {len(html_files)} saved HTML file(s).")
    return lessons
