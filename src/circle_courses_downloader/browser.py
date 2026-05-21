from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree

from .extractors import classify_provider, extract_lessons_from_html, find_video_urls
from .models import Lesson


VIDEO_WAIT_JS = """() => {
  const text = document.documentElement.innerHTML;
  return text.includes('playlist.m3u8') ||
    text.includes('cdn-media.circle.so') ||
    text.includes('youtube.com/embed') ||
    text.includes('player.vimeo.com') ||
    text.includes('.mp4');
}"""
LESSONS_WAIT_JS = """() => {
  return !!document.querySelector('a[href*="/sections/"][href*="/lessons/"]');
}"""


@dataclass
class BrowserAuth:
    login_url: str
    storage_state: Path
    profile_dir: Path
    headless: bool
    timeout_ms: int


class AuthRequiredError(RuntimeError):
    pass


def resource_urls(page) -> list[str]:
    try:
        return page.evaluate("performance.getEntriesByType('resource').map(entry => entry.name)")
    except Exception:  # noqa: BLE001 - resource timing is best-effort only.
        return []


def save_session(page, auth: BrowserAuth) -> None:
    auth.storage_state.parent.mkdir(parents=True, exist_ok=True)
    page.context.storage_state(path=str(auth.storage_state))
    print(f"Saved browser session to {auth.storage_state}")


def profile_dir_from_session(storage_state: Path) -> Path:
    return storage_state.with_name(f"{storage_state.stem}-browser-profile")


def reset_auth_state(auth: BrowserAuth) -> None:
    if auth.storage_state.exists():
        auth.storage_state.unlink()
    if auth.profile_dir.exists():
        rmtree(auth.profile_dir)


def open_persistent_context(playwright, auth: BrowserAuth, needs_login: bool):
    auth.profile_dir.mkdir(parents=True, exist_ok=True)
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(auth.profile_dir),
        headless=False if needs_login else auth.headless,
    )
    page = context.pages[0] if context.pages else context.new_page()
    return context, page


def wait_for_manual_login(page, auth: BrowserAuth) -> None:
    print("A browser window is open. Log in to Circle there, then return here and press Enter.")
    print("The downloader will keep using this same browser profile after you press Enter.")
    input()
    try:
        page.wait_for_load_state("networkidle", timeout=auth.timeout_ms)
    except Exception:  # noqa: BLE001 - some logged-in pages keep long-polling; the course check below is authoritative.
        pass
    save_session(page, auth)


def open_course_page(page, course_url: str, timeout_ms: int) -> None:
    print(f"Opening course: {course_url}")
    page.goto(course_url, wait_until="domcontentloaded", timeout=timeout_ms)


def is_login_page(page) -> bool:
    return "/users/sign_in" in page.url or "/users/sign_up" in page.url


def discover_and_probe_with_browser(args, course_url: str) -> list[Lesson]:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is not installed. Run: python -m pip install -r requirements.txt") from exc

    auth = BrowserAuth(
        login_url=args.login_url,
        storage_state=args.session,
        profile_dir=profile_dir_from_session(args.session),
        headless=args.headless,
        timeout_ms=args.timeout_ms,
    )

    with sync_playwright() as playwright:
        needs_login = args.force_login or not auth.profile_dir.exists()
        if args.force_login:
            reset_auth_state(auth)
        context, page = open_persistent_context(playwright, auth, needs_login=needs_login)
        try:
            open_course_page(page, course_url, args.timeout_ms)
            if is_login_page(page) and not needs_login:
                print("The saved session is not authenticated for this course. Reopening a visible browser.")
                context.close()
                needs_login = True
                context, page = open_persistent_context(playwright, auth, needs_login=needs_login)
                open_course_page(page, course_url, args.timeout_ms)

            if needs_login or is_login_page(page):
                if is_login_page(page):
                    print("The course opened a login page.")
                wait_for_manual_login(page, auth)
                open_course_page(page, course_url, args.timeout_ms)
                if is_login_page(page):
                    raise AuthRequiredError("Circle still shows the login page after authentication.")

            try:
                page.wait_for_function(LESSONS_WAIT_JS, timeout=args.timeout_ms)
            except PlaywrightTimeoutError:
                pass

            lessons = extract_lessons_from_html(page.content(), base_url=page.url)
            if not lessons:
                raise RuntimeError("No Circle lesson links were found on the course page.")

            for lesson in lessons:
                try:
                    page.goto(lesson.url, wait_until="domcontentloaded", timeout=args.timeout_ms)
                    if is_login_page(page):
                        raise RuntimeError("The saved browser session is not authenticated.")
                    try:
                        page.wait_for_function(VIDEO_WAIT_JS, timeout=args.video_timeout_ms)
                    except PlaywrightTimeoutError:
                        pass
                    urls = find_video_urls(page.content(), extra_urls=resource_urls(page))
                    lesson.video_urls = urls
                    lesson.provider = classify_provider(urls[0]) if urls else "not-found"
                    print(f"[{lesson.index:02d}] {lesson.provider:17} {lesson.title}")
                except Exception as exc:  # noqa: BLE001 - keep probing the rest of the course.
                    lesson.provider = "error"
                    lesson.video_urls = []
                    print(f"[{lesson.index:02d}] error             {lesson.title} ({exc})", file=sys.stderr)

            save_session(page, auth)
            return lessons
        finally:
            context.close()
