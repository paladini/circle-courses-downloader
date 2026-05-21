from __future__ import annotations

import getpass
import os
import sys
from dataclasses import dataclass
from pathlib import Path

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
    email: str | None
    password: str | None
    login_url: str | None
    storage_state: Path
    headless: bool
    timeout_ms: int


def resolve_secret(value: str | None, env_name: str | None, prompt: str, password: bool = False) -> str | None:
    if value:
        return value
    if env_name and os.getenv(env_name):
        return os.getenv(env_name)
    if password:
        entered = getpass.getpass(prompt)
    else:
        entered = input(prompt)
    return entered.strip() or None


def resource_urls(page) -> list[str]:
    try:
        return page.evaluate("performance.getEntriesByType('resource').map(entry => entry.name)")
    except Exception:  # noqa: BLE001 - resource timing is best-effort only.
        return []


def fill_first(page, selectors: list[str], value: str, timeout_ms: int) -> bool:
    selector_timeout = min(timeout_ms, 3_000)
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=selector_timeout)
            locator.fill(value)
            return True
        except Exception:  # noqa: BLE001 - try the next likely Circle selector.
            continue
    return False


def perform_login(page, auth: BrowserAuth, manual: bool = False) -> None:
    page.goto(auth.login_url, wait_until="domcontentloaded", timeout=auth.timeout_ms)

    if manual:
        print("A browser window is open. Finish login there, then press Enter here.")
        input()
    else:
        if not auth.email or not auth.password:
            raise RuntimeError("Email and password are required unless --manual-login is used.")
        email_ok = fill_first(
            page,
            [
                "input[type='email']",
                "input[name='user[email]']",
                "input[name='email']",
                "#user_email",
            ],
            auth.email,
            auth.timeout_ms,
        )
        password_ok = fill_first(
            page,
            [
                "input[type='password']",
                "input[name='user[password]']",
                "input[name='password']",
                "#user_password",
            ],
            auth.password,
            auth.timeout_ms,
        )
        if not email_ok or not password_ok:
            raise RuntimeError("Could not find Circle email/password fields. Try --manual-login.")

        try:
            page.locator("button[type='submit'], input[type='submit']").first.click(timeout=auth.timeout_ms)
        except Exception:
            page.keyboard.press("Enter")

    page.wait_for_load_state("networkidle", timeout=auth.timeout_ms)
    if "/users/sign_in" in page.url:
        raise RuntimeError("Login did not complete. Check credentials, captcha, or 2FA; try --manual-login if needed.")

    auth.storage_state.parent.mkdir(parents=True, exist_ok=True)
    page.context.storage_state(path=str(auth.storage_state))
    print(f"Saved browser session to {auth.storage_state}")


def login_and_save_state(auth: BrowserAuth, manual: bool = False) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is not installed. Run: python -m pip install -r requirements.txt") from exc

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=auth.headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            perform_login(page, auth, manual=manual)
        finally:
            browser.close()


def ensure_storage_state(auth: BrowserAuth, force_login: bool, manual_login: bool) -> None:
    if auth.storage_state.exists() and not force_login:
        return
    login_and_save_state(auth, manual=manual_login)


def probe_lessons_with_browser(args, lessons: list[Lesson]) -> list[Lesson]:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is not installed. Run: python -m pip install -r requirements.txt") from exc

    auth = BrowserAuth(
        email=args.email,
        password=args.password,
        login_url=args.login_url,
        storage_state=args.storage_state,
        headless=args.headless,
        timeout_ms=args.timeout_ms,
    )
    ensure_storage_state(auth, args.force_login, args.manual_login)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=args.headless)
        context = browser.new_context(storage_state=str(args.storage_state))
        page = context.new_page()

        for lesson in lessons:
            try:
                page.goto(lesson.url, wait_until="domcontentloaded", timeout=args.timeout_ms)
                if "/users/sign_in" in page.url:
                    raise RuntimeError("Stored session is not authenticated. Re-run with --force-login.")
                try:
                    page.wait_for_function(VIDEO_WAIT_JS, timeout=args.video_timeout_ms)
                except PlaywrightTimeoutError:
                    pass

                content = page.content()
                urls = find_video_urls(content, extra_urls=resource_urls(page))
                lesson.video_urls = urls
                lesson.provider = classify_provider(urls[0]) if urls else "not-found"
                print(f"[{lesson.index:02d}] {lesson.provider:17} {lesson.title}")
            except Exception as exc:  # noqa: BLE001 - keep probing the rest of the course.
                lesson.provider = "error"
                lesson.video_urls = []
                print(f"[{lesson.index:02d}] error             {lesson.title} ({exc})", file=sys.stderr)

        context.storage_state(path=str(args.storage_state))
        browser.close()

    return lessons


def discover_lessons_with_browser(args, course_url: str) -> list[Lesson]:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is not installed. Run: python -m pip install -r requirements.txt") from exc

    auth = BrowserAuth(
        email=args.email,
        password=args.password,
        login_url=args.login_url,
        storage_state=args.storage_state,
        headless=args.headless,
        timeout_ms=args.timeout_ms,
    )
    ensure_storage_state(auth, args.force_login, args.manual_login)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=args.headless)
        context = browser.new_context(storage_state=str(args.storage_state))
        page = context.new_page()
        try:
            page.goto(course_url, wait_until="domcontentloaded", timeout=args.timeout_ms)
            if "/users/sign_in" in page.url:
                raise RuntimeError("Stored session is not authenticated. Re-run with --force-login.")
            try:
                page.wait_for_function(LESSONS_WAIT_JS, timeout=args.timeout_ms)
            except PlaywrightTimeoutError:
                pass
            lessons = extract_lessons_from_html(page.content(), base_url=page.url)
            if not lessons:
                raise RuntimeError("No Circle lesson links were found on the course page.")
            context.storage_state(path=str(args.storage_state))
            return lessons
        finally:
            browser.close()
