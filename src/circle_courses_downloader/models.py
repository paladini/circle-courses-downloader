from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Lesson:
    index: int
    section_id: str
    lesson_id: str
    url: str
    title: str
    duration: str = ""
    provider: str = ""
    video_urls: list[str] = field(default_factory=list)


def save_manifest(path: Path, lessons: list[Lesson]) -> None:
    payload = {
        "lesson_count": len(lessons),
        "lessons": [asdict(lesson) for lesson in lessons],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_csv(path: Path, lessons: list[Lesson]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["index", "section_id", "lesson_id", "title", "duration", "provider", "url", "video_urls"],
        )
        writer.writeheader()
        for lesson in lessons:
            row = asdict(lesson)
            row["video_urls"] = " | ".join(lesson.video_urls)
            writer.writerow(row)
