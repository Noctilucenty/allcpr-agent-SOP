"""Local SOP image extraction and deterministic media matching.

The indexer copies image files and extracts images embedded in .docx/.pptx files
into ``app/web/static/sop_media``. Metadata is derived only from source paths and
document names. It does not OCR, inspect, or visually describe image contents.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

from .schemas import SopMediaItem

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SOP_ROOT = PROJECT_ROOT / "SOP"
PACKAGE_ROOT = Path(__file__).resolve().parent
INDEX_PATH = PACKAGE_ROOT / "sop_media_index.json"
MEDIA_ROOT = PROJECT_ROOT / "app" / "web" / "static" / "sop_media"
MEDIA_URL_PREFIX = "/static/sop_media"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
DOC_EXTENSIONS = {".docx", ".pptx"}

SCENARIO_TAGS: Dict[str, set[str]] = {
    "smart_manikin_site_inspection": {
        "smart",
        "manikin",
        "site",
        "inspection",
        "equipment",
        "placement",
        "diagram",
        "supplies",
        "consumables",
        "aed",
        "pad",
        "bvm",
        "pocket",
        "mask",
        "ipad",
        "tablet",
        "巡检",
        "器材",
        "摆放",
        "耗材",
        "设备",
    },
    "smart_manikin_troubleshooting": {
        "smart",
        "manikin",
        "instruction",
        "quick",
        "guide",
        "learning",
        "station",
        "completion",
        "photo",
        "pass",
        "bluetooth",
        "pad",
        "tablet",
        "假人",
        "平板",
        "蓝牙",
        "完成",
    },
    "venue_access_issue": {
        "instruction",
        "santa",
        "clara",
        "newark",
        "door",
        "gate",
        "lock",
        "box",
        "passcode",
        "room",
        "floor",
        "门",
        "门禁",
        "大门",
        "钥匙",
        "楼梯",
        "电梯",
        "房间",
    },
    "completion_or_certificate_issue": {
        "completion",
        "photo",
        "pass",
        "session",
        "certificate",
        "support",
        "完成",
        "证书",
        "截图",
    },
}


def _sha(text: str, n: int = 12) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:n]


def _rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _tokenize_path(path: Path) -> set[str]:
    # Tokenize the *repo-relative* path only — never the absolute path — so the
    # index never leaks local machine paths / usernames (e.g. /Users/<name>/...)
    # into the committed tags. Meaningful tokens (SOP folder + document name)
    # are preserved, so deterministic matching is unchanged.
    text = _rel(path).replace("_", " ").replace("-", " ").replace("/", " ").lower()
    tokens = {t.strip(" .()[]{}:,;\"'") for t in text.split() if t.strip()}
    compact = text.replace(" ", "")
    for phrase in ("smart manikin", "santa clara", "black screen", "quick start"):
        if phrase in text:
            tokens.update(phrase.split())
    for zh in ("门禁", "大门", "楼梯", "电梯", "房间", "假人", "平板", "蓝牙", "完成", "证书", "截图"):
        if zh in compact:
            tokens.add(zh)
    return tokens


def _related_scenarios(path: Path, tags: set[str]) -> List[str]:
    related = []
    path_text = path.as_posix().lower()
    is_inspection = "inspection" in path_text or "巡检" in tags
    if is_inspection:
        # Inspection media (e.g. the page-3 equipment placement diagram) belongs to
        # the inspection scenario, not generic device troubleshooting.
        related.append("smart_manikin_site_inspection")
    elif {"smart", "manikin"} <= tags or "smart manikin" in path_text:
        related.append("smart_manikin_troubleshooting")
    if tags & SCENARIO_TAGS["venue_access_issue"]:
        related.append("venue_access_issue")
    if tags & SCENARIO_TAGS["completion_or_certificate_issue"]:
        related.append("completion_or_certificate_issue")
    return list(dict.fromkeys(related))


def _safe_description(source: Path, embedded: bool) -> str:
    name = source.name
    if embedded:
        return f"Image extracted from {name}. Metadata is based on source document name only; no image analysis was performed."
    if "instruction" in source.as_posix().lower():
        return f"Source image from instruction materials near {name}. No image analysis was performed."
    return f"Source image copied from SOP folder: {name}. No image analysis was performed."


def _title(source: Path, related: Sequence[str], embedded: bool) -> str:
    if "smart_manikin_site_inspection" in related:
        return "Smart Manikin 专员分点巡检 SOP — equipment placement diagram"
    if "smart_manikin_troubleshooting" in related:
        return "Smart Manikin source image"
    if "venue_access_issue" in related:
        return "Venue/access source image"
    if "completion_or_certificate_issue" in related:
        return "Completion/certificate source image"
    return "SOP source image" if not embedded else "Extracted SOP image"


def _make_item(source: Path, out_path: Path, tags: set[str], embedded: bool) -> SopMediaItem:
    related = _related_scenarios(source, tags)
    return SopMediaItem(
        id=_sha(f"{_rel(source)}::{out_path.name}"),
        source_file=_rel(source),
        extracted_path=_rel(out_path),
        url=f"{MEDIA_URL_PREFIX}/{out_path.name}",
        media_type="image",
        title=_title(source, related, embedded),
        description=_safe_description(source, embedded),
        tags=sorted(tags),
        related_scenarios=related,
    )


def _copy_image(source: Path) -> SopMediaItem | None:
    tags = _tokenize_path(source)
    ext = source.suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        return None
    out_name = f"{_sha(_rel(source))}{ext}"
    out_path = MEDIA_ROOT / out_name
    if not out_path.exists():
        shutil.copy2(source, out_path)
    return _make_item(source, out_path, tags, embedded=False)


def _extract_doc_images(source: Path) -> Iterable[SopMediaItem]:
    ext = source.suffix.lower()
    if ext not in DOC_EXTENSIONS:
        return []
    media_prefix = "word/media/" if ext == ".docx" else "ppt/media/"
    items: List[SopMediaItem] = []
    tags = _tokenize_path(source)
    try:
        with zipfile.ZipFile(source) as zf:
            for name in sorted(zf.namelist()):
                media_ext = Path(name).suffix.lower()
                if not name.startswith(media_prefix) or media_ext not in IMAGE_EXTENSIONS:
                    continue
                out_name = f"{_sha(_rel(source) + '::' + name)}{media_ext}"
                out_path = MEDIA_ROOT / out_name
                if not out_path.exists():
                    out_path.write_bytes(zf.read(name))
                items.append(_make_item(source, out_path, tags, embedded=True))
    except (OSError, zipfile.BadZipFile):
        return []
    return items


def build_media_index(force: bool = False) -> List[SopMediaItem]:
    """Build or load the local SOP image index."""
    if INDEX_PATH.exists() and not force:
        try:
            payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
            return [SopMediaItem(**item) for item in payload]
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass

    if not SOP_ROOT.exists():
        return []

    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    items: List[SopMediaItem] = []
    for source in sorted(SOP_ROOT.rglob("*")):
        if not source.is_file():
            continue
        if source.suffix.lower() in IMAGE_EXTENSIONS:
            item = _copy_image(source)
            if item:
                items.append(item)
        elif source.suffix.lower() in DOC_EXTENSIONS:
            items.extend(_extract_doc_images(source))

    INDEX_PATH.write_text(
        json.dumps([item.dict() for item in items], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return items


def _query_tags(question: str, scenario: str) -> set[str]:
    tags = set(SCENARIO_TAGS.get(scenario, set()))
    q = (question or "").lower()
    for token in (
        "smart",
        "manikin",
        "black",
        "screen",
        "bluetooth",
        "completion",
        "certificate",
        "door",
        "gate",
        "locked",
        "santa",
        "clara",
        "newark",
        "黑屏",
        "蓝牙",
        "证书",
        "完成",
        "门",
        "门禁",
        "大门",
        "equipment",
        "placement",
        "supplies",
        "consumables",
        "aed",
        "bvm",
        "pocket",
        "巡检",
        "器材",
        "摆放",
        "耗材",
    ):
        if token in q:
            tags.add(token)
    return tags


def find_relevant_sop_media(question: str, scenario: str, top_k: int = 3) -> List[SopMediaItem]:
    """Return high-confidence SOP images for a question/scenario.

    Only scenarios with clear source-media relationships are matched. General
    incidents such as power or internet outage intentionally return no media
    unless explicit scenario tags exist in the index.
    """
    if scenario not in SCENARIO_TAGS:
        return []

    query_tags = _query_tags(question, scenario)
    matches = []
    for item in build_media_index():
        item_tags = set(item.tags)
        if scenario not in item.related_scenarios:
            continue
        score = 4 + len(query_tags & item_tags)
        if "instruction" in item_tags:
            score += 2
        if "smart_manikin_troubleshooting" == scenario and "smart" in item_tags and "manikin" in item_tags:
            score += 3
        if "venue_access_issue" == scenario and {"santa", "clara"} & item_tags:
            score += 2
        matches.append((score, item))

    matches.sort(key=lambda pair: (-pair[0], pair[1].source_file, pair[1].id))
    return [item for score, item in matches[:top_k] if score >= 4]

