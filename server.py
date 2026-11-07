#!/usr/bin/env python3
"""NexStage local presentation server.

The server intentionally uses only Python's standard library.  The browser does
the rendering and video decoding, while this process persists the library and
keeps every output synchronized through a tiny polling API.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import mimetypes
import os
import platform
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
import xml.etree.ElementTree as ET
from contextlib import closing
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import youtube as yt


APP_NAME = "NexStage"
APP_VERSION = "0.8.0"
APP_AUTHOR = "Natan Gabriel"
APP_REPOSITORY = "https://github.com/Natan-Tec/NexStage"
GITHUB_LATEST_RELEASE_API = (
    "https://api.github.com/repos/Natan-Tec/NexStage/releases/latest"
)
IS_FROZEN = bool(getattr(sys, "frozen", False))
SOURCE_ROOT = Path(__file__).resolve().parent
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT)).resolve()
INSTALL_ROOT = Path(sys.executable).resolve().parent if IS_FROZEN else SOURCE_ROOT
_configured_data_root = os.environ.get("NEXSTAGE_HOME", "").strip()
RUNTIME_ROOT = (
    Path(_configured_data_root).expanduser().resolve()
    if _configured_data_root
    else INSTALL_ROOT
)
ROOT = SOURCE_ROOT
WEB_DIR = RESOURCE_ROOT / "web"
DATA_DIR = RUNTIME_ROOT / "data"
MEDIA_DIR = RUNTIME_ROOT / "media"
BIBLE_DIR = DATA_DIR / "bibles"
FONT_DIR = DATA_DIR / "fonts"
LIBRARY_FILE = DATA_DIR / "library.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
MAX_JSON_BYTES = 24 * 1024 * 1024
MAX_MEDIA_BYTES = 8 * 1024 * 1024 * 1024
MAX_FONT_BYTES = 32 * 1024 * 1024
SETTINGS_EXPORT_KIND = "NexStageSettings"
SETTINGS_EXPORT_SCHEMA = 1
MAX_UPDATE_BYTES = 512 * 1024 * 1024
UPDATE_CACHE_SECONDS = 15 * 60

DEFAULT_THEME = {
    "fontFamily": "Arial, Helvetica, sans-serif",
    "fontSize": 64,
    "fontWeight": 800,
    "textColor": "#ffffff",
    "accentColor": "#1687ff",
    "align": "center",
    "vertical": "center",
    "shadow": True,
    "uppercase": False,
    "maxWidth": 86,
    "overlayOpacity": 1,
}


def block_style(
    *,
    size: int,
    weight: int,
    color: str,
    x: float,
    y: float,
    width: int,
    align: str = "center",
    uppercase: bool = False,
    line_height: float = 1.13,
    letter_spacing: float = 0,
    shadow: bool = True,
    auto_fit: bool = False,
) -> dict[str, Any]:
    return {
        "fontFamily": "Arial, Helvetica, sans-serif",
        "fontSize": size,
        "fontWeight": weight,
        "textColor": color,
        "align": align,
        "x": x,
        "y": y,
        "maxWidth": width,
        "lineHeight": line_height,
        "letterSpacing": letter_spacing,
        "shadow": shadow,
        "uppercase": uppercase,
        "italic": False,
        "outline": False,
        "background": False,
        "backgroundColor": "#000000",
        "backgroundOpacity": 0.35,
        "autoFit": auto_fit,
        "minFontSize": 26,
    }


DEFAULT_STYLES = {
    "song": {
        "label": block_style(
            size=24, weight=800, color="#66b7ff", x=50, y=24,
            width=80, uppercase=True, letter_spacing=2.5,
        ),
        "text": block_style(
            size=64, weight=800, color="#ffffff", x=50, y=52,
            width=86, auto_fit=True,
        ),
        "reference": block_style(
            size=24, weight=600, color="#e7edf5", x=50, y=80, width=80,
        ),
    },
    "bible": {
        "version": block_style(
            size=22, weight=800, color="#66b7ff", x=50, y=20,
            width=80, uppercase=True, letter_spacing=2.2,
        ),
        "text": block_style(
            size=58, weight=750, color="#ffffff", x=50, y=48,
            width=86, line_height=1.18, auto_fit=True,
        ),
        "reference": block_style(
            size=28, weight=700, color="#e7edf5", x=50, y=79, width=80,
        ),
    },
    "clock": {
        "label": block_style(
            size=26, weight=700, color="#66b7ff", x=50, y=27, width=82,
        ),
        "time": block_style(
            size=112, weight=300, color="#ffffff", x=50, y=50,
            width=88, letter_spacing=2.5,
        ),
        "date": block_style(
            size=28, weight=600, color="#e7edf5", x=50, y=72, width=82,
        ),
    },
}

DEFAULT_STYLES["timer"] = {
    "label": block_style(size=26, weight=700, color="#66b7ff", x=50, y=16, width=82),
    "time": block_style(size=130, weight=300, color="#ffffff", x=50, y=36, width=88, letter_spacing=2),
    "countdown": block_style(size=150, weight=300, color="#ff6b81", x=50, y=68, width=88, letter_spacing=2),
}

DEFAULT_TIMER = {
    "mode": "endTime",      # endTime = termina num horário; duration = duração fixa a partir do "Ligar"
    "endTime": "10:00",
    "durationMin": 40,
    "running": False,
    "startedAt": 0,
    "showSeconds": True,
    "format24": True,
    "hideAtZero": False,
    "label": "",
}

DEFAULT_STATE: dict[str, Any] = {
    "revision": 1,
    "updatedAt": 0,
    "live": False,
    "black": False,
    "mode": "blank",
    "slide": {"text": "", "label": "", "reference": ""},
    "background": "",
    "overlay": "",
    "theme": DEFAULT_THEME,
    "styles": DEFAULT_STYLES,
    "fonts": [],
    "youtube": {},
    "timer": DEFAULT_TIMER,
    "clock": {
        "format24": True,
        "showSeconds": False,
        "showDate": True,
        "dateFormat": "long",
        "label": "",
    },
}

DEFAULT_SETTINGS = {
    "videoCrossfadeMs": 450,
    "defaultBackground": "",
    "defaultOverlay": "",
    "theme": DEFAULT_THEME,
    "styles": DEFAULT_STYLES,
    "clock": DEFAULT_STATE["clock"],
    "timer": DEFAULT_TIMER,
    "bible": {"showVersion": True, "referenceFormat": "full"},
    "fonts": {"autoImport": True, "prefix": "CMG"},
    "youtube": {"autoDownload": True, "defaultHeight": 720, "maxFps": 30, "volume": 0.8, "autoSwitchToFile": True},
    "song": {
        "showSectionLabels": True,
        "showCredits": False,
        "creditsFormat": "artist",
        "linesPerSlide": 4,
    },
    "ui": {
        "accentColor": "#1687ff",
        "scale": 100,
        "density": "comfortable",
        "confirmDelete": True,
        "confirmClear": False,
    },
    "output": {
        "preferredScreen": "",
        "openFullscreenSize": True,
    },
    "performance": {
        "previewMode": "frame",
        "preloadMode": "balanced",
    },
    "louvorJaDb": "",
}


def ensure_directories() -> None:
    for directory in (DATA_DIR, MEDIA_DIR, BIBLE_DIR, FONT_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def deep_merge(base: Any, incoming: Any) -> Any:
    """Merge nested settings without sharing mutable defaults."""
    if isinstance(base, dict) and isinstance(incoming, dict):
        merged = {key: deep_merge(value, {}) for key, value in base.items()}
        for key, value in incoming.items():
            if key in merged:
                merged[key] = deep_merge(merged[key], value)
            else:
                merged[key] = json.loads(json.dumps(value))
        return merged
    if incoming == {} and not isinstance(base, dict):
        return json.loads(json.dumps(base))
    return json.loads(json.dumps(incoming))


def atomic_write_json(path: Path, payload: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    temporary.replace(path)


def read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return fallback


def clean_text(value: str) -> str:
    value = value.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    value = "\n".join(line.rstrip() for line in value.split("\n"))
    return value.strip()


def safe_name(filename: str, fallback: str = "arquivo") -> str:
    name = Path(filename).name
    stem = unicodedata.normalize("NFKD", Path(name).stem)
    stem = "".join(c for c in stem if not unicodedata.combining(c))
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip(".-") or fallback
    suffix = re.sub(r"[^A-Za-z0-9.]", "", Path(name).suffix.lower())[:12]
    return f"{stem[:90]}{suffix}"


def unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / safe_name(filename)
    if not candidate.exists():
        return candidate
    stem, suffix = candidate.stem, candidate.suffix
    counter = 2
    while True:
        alternate = directory / f"{stem}-{counter}{suffix}"
        if not alternate.exists():
            return alternate
        counter += 1


def version_numbers(value: str) -> tuple[int, int, int]:
    """Return a comparable release version from values such as ``v0.4.2``."""
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", str(value))
    if not match:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())


def update_supported() -> bool:
    return IS_FROZEN and sys.platform == "win32"


class UpdateService:
    """Check and download only the official Windows installer from GitHub."""

    def __init__(
        self,
        api_url: str = GITHUB_LATEST_RELEASE_API,
        current_version: str = APP_VERSION,
        supported: bool | None = None,
    ) -> None:
        self.api_url = api_url
        self.current_version = current_version
        self._supported = supported
        self._cache: dict[str, Any] | None = None
        self._cached_at = 0.0
        self._lock = threading.Lock()

    @property
    def supported(self) -> bool:
        return update_supported() if self._supported is None else self._supported

    @staticmethod
    def _request(url: str) -> urllib.request.Request:
        return urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"{APP_NAME}/{APP_VERSION}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

    @staticmethod
    def _asset_from_release(release: dict[str, Any]) -> dict[str, Any] | None:
        for asset in release.get("assets", []):
            if str(asset.get("name", "")).lower() == "nexstage-setup.exe":
                return asset
        return None

    def _fetch_latest(self) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(self._request(self.api_url), timeout=6) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
        except urllib.error.HTTPError as exc:
            if exc.code == HTTPStatus.NOT_FOUND:
                raise ValueError("Ainda não há uma release publicada no GitHub.") from exc
            raise ValueError("O GitHub não respondeu à consulta de atualização.") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise ValueError(
                "Não foi possível verificar atualizações. Confira a internet e tente novamente."
            ) from exc
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("A resposta de atualização recebida é grande demais.")
        try:
            release = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("O GitHub devolveu uma resposta de atualização inválida.") from exc

        latest = str(release.get("tag_name", "")).lstrip("vV")
        if version_numbers(latest) == (0, 0, 0):
            raise ValueError("A release publicada não possui uma versão válida.")
        asset = self._asset_from_release(release)
        available = version_numbers(latest) > version_numbers(self.current_version)
        result = {
            "available": available,
            "currentVersion": self.current_version,
            "latestVersion": latest,
            "releaseName": str(release.get("name") or f"NexStage {latest}"),
            "releaseUrl": str(release.get("html_url") or APP_REPOSITORY + "/releases"),
            "publishedAt": str(release.get("published_at") or ""),
            "downloadReady": bool(asset),
            "downloadName": str(asset.get("name", "")) if asset else "",
            "downloadSize": int(asset.get("size", 0) or 0) if asset else 0,
            "downloadUrl": str(asset.get("browser_download_url", "")) if asset else "",
            "updateSupported": self.supported,
        }
        if available and not asset:
            result["message"] = (
                "Há uma versão nova, mas o instalador NexStage-Setup.exe não foi anexado."
            )
        elif available:
            result["message"] = f"NexStage {latest} está disponível."
        else:
            result["message"] = "Você já está usando a versão mais recente."
        return result

    def check(self, force: bool = False) -> dict[str, Any]:
        with self._lock:
            fresh = time.monotonic() - self._cached_at < UPDATE_CACHE_SECONDS
            if not force and fresh and self._cache is not None:
                return dict(self._cache)
            result = self._fetch_latest()
            self._cache = result
            self._cached_at = time.monotonic()
            return dict(result)

    @staticmethod
    def _trusted_download_url(url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower()
        return parsed.scheme == "https" and (
            host == "github.com"
            or host.endswith(".github.com")
            or host.endswith(".githubusercontent.com")
        )

    def download_installer(self) -> Path:
        if not self.supported:
            raise ValueError(
                "A instalação automática está disponível somente no NexStage instalado no Windows."
            )
        info = self.check()
        if not info.get("available"):
            raise ValueError("Você já está usando a versão mais recente.")
        url = str(info.get("downloadUrl", ""))
        if not info.get("downloadReady") or not self._trusted_download_url(url):
            raise ValueError("A release não possui um instalador oficial válido.")
        expected_size = int(info.get("downloadSize", 0) or 0)
        if expected_size > MAX_UPDATE_BYTES:
            raise ValueError("O instalador publicado excede o tamanho permitido.")

        destination_dir = Path(tempfile.gettempdir()) / "NexStage"
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / "NexStage-Setup.exe"
        partial = destination.with_suffix(".exe.part")
        try:
            with urllib.request.urlopen(self._request(url), timeout=30) as response:
                header_size = int(response.headers.get("Content-Length", "0") or 0)
                if header_size > MAX_UPDATE_BYTES:
                    raise ValueError("O instalador publicado excede o tamanho permitido.")
                total = 0
                with partial.open("wb") as target:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_UPDATE_BYTES:
                            raise ValueError("O instalador publicado excede o tamanho permitido.")
                        target.write(chunk)
            if expected_size and total != expected_size:
                raise ValueError("O download do instalador ficou incompleto.")
            with partial.open("rb") as downloaded:
                if downloaded.read(2) != b"MZ":
                    raise ValueError("O arquivo baixado não é um instalador válido do Windows.")
            partial.replace(destination)
            return destination
        except ValueError:
            partial.unlink(missing_ok=True)
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            partial.unlink(missing_ok=True)
            raise ValueError(
                "Não foi possível baixar a atualização. Confira a internet e tente novamente."
            ) from exc


UPDATE_SERVICE = UpdateService()
_UPDATE_INSTALL_CALLBACK: Any = None


def set_update_install_callback(callback: Any) -> None:
    global _UPDATE_INSTALL_CALLBACK
    _UPDATE_INSTALL_CALLBACK = callback


def open_data_folder() -> None:
    opener = getattr(os, "startfile", None)
    if sys.platform != "win32" or opener is None:
        raise ValueError("Este botão está disponível no aplicativo instalado no Windows.")
    try:
        opener(str(DATA_DIR))
    except OSError as exc:
        raise ValueError("O Windows não conseguiu abrir a pasta dos dados.") from exc


def about_info(base_url: str) -> dict[str, Any]:
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "author": APP_AUTHOR,
        "system": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "controllerUrl": base_url.rstrip("/") + "/",
        "obsUrl": base_url.rstrip("/") + "/obs",
        "dataPath": str(DATA_DIR),
        "installPath": str(INSTALL_ROOT),
        "repository": APP_REPOSITORY,
        "installedBuild": IS_FROZEN,
        "updateSupported": update_supported(),
    }


def parse_song_text(filename: str, content: str, title: str = "", lines_per_slide: int = 4) -> dict[str, Any]:
    """Parse common worship TXT conventions into compact slides."""
    content = clean_text(content)
    lines = content.split("\n") if content else []
    detected_title = title.strip()

    if lines and not detected_title:
        first = lines[0].strip()
        if first.lower().startswith("title:"):
            detected_title = first.split(":", 1)[1].strip()
            lines = lines[1:]
        elif first.startswith("# "):
            detected_title = first[2:].strip()
            lines = lines[1:]
    if not detected_title:
        detected_title = Path(filename).stem.replace("_", " ").strip() or "Sem título"

    section_re = re.compile(r"^\s*\[([^\]]+)]\s*$|^\s*(verso|estrofe|refr[aã]o|ponte|coro|intro|final)\s*\d*\s*:?\s*$", re.I)
    sections: list[tuple[str, list[str]]] = []
    current_label = ""
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_lines
        trimmed = [line.strip() for line in current_lines]
        while trimmed and not trimmed[0]:
            trimmed.pop(0)
        while trimmed and not trimmed[-1]:
            trimmed.pop()
        if trimmed:
            sections.append((current_label, trimmed))
        current_lines = []

    for line in lines:
        match = section_re.match(line)
        if match:
            flush()
            current_label = (match.group(1) or match.group(2) or "").strip().title()
            continue
        if not line.strip():
            flush()
            current_label = ""
            continue
        current_lines.append(line)
    flush()

    slides: list[dict[str, str]] = []
    per_slide = max(1, min(12, int(lines_per_slide or 4)))
    for label, section_lines in sections:
        # Keep slides readable even when a TXT file has no blank lines.
        for index in range(0, len(section_lines), per_slide):
            chunk = section_lines[index : index + per_slide]
            slides.append({"label": label, "text": "\n".join(chunk)})

    if not slides and content:
        slides = [{"label": "", "text": content}]

    return {
        "id": f"song-{uuid.uuid4().hex[:12]}",
        "title": detected_title,
        "source": "txt",
        "filename": Path(filename).name,
        "slides": slides,
        "createdAt": int(time.time()),
    }


def strip_xml_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].upper()


def element_text(node: ET.Element) -> str:
    return re.sub(r"\s+", " ", "".join(node.itertext())).strip()


def first_attr(node: ET.Element, names: tuple[str, ...], default: str = "") -> str:
    lowered = {key.lower(): value for key, value in node.attrib.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value is not None:
            return str(value)
    return default


def parse_zefania_xml(filename: str, content: str) -> dict[str, Any]:
    """Read Zefania XML and a conservative generic BOOK/CHAPTER/VERSE subset."""
    if "<!DOCTYPE" in content.upper() or "<!ENTITY" in content.upper():
        raise ValueError("XML com DTD/ENTITY não é aceito por segurança.")
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise ValueError(f"XML inválido: {exc}") from exc

    bible_name = first_attr(root, ("biblename", "name", "title"))
    if not bible_name:
        bible_name = Path(filename).stem.replace("_", " ") or "Bíblia"

    books: list[dict[str, Any]] = []
    book_tags = {"BIBLEBOOK", "BOOK", "B"}
    chapter_tags = {"CHAPTER", "CHAP", "C"}
    verse_tags = {"VERS", "VERSE", "V"}

    for book_index, book_node in enumerate(root.iter(), start=1):
        if strip_xml_namespace(book_node.tag) not in book_tags:
            continue
        book_name = first_attr(
            book_node,
            ("bname", "bsname", "name", "bookname", "n", "osisid"),
            f"Livro {len(books) + 1}",
        )
        chapters: list[dict[str, Any]] = []
        for chapter_node in list(book_node):
            if strip_xml_namespace(chapter_node.tag) not in chapter_tags:
                continue
            chapter_number = first_attr(
                chapter_node, ("cnumber", "number", "n", "id"), str(len(chapters) + 1)
            )
            verses: list[dict[str, str]] = []
            for verse_node in chapter_node.iter():
                if strip_xml_namespace(verse_node.tag) not in verse_tags:
                    continue
                verse_number = first_attr(
                    verse_node, ("vnumber", "number", "n", "id"), str(len(verses) + 1)
                )
                text = element_text(verse_node)
                if text:
                    verses.append({"number": verse_number, "text": text})
            if verses:
                chapters.append({"number": chapter_number, "verses": verses})
        if chapters:
            books.append({"name": book_name, "chapters": chapters})

    if not books:
        raise ValueError(
            "Nenhum livro foi encontrado. Use XML Zefania (BIBLEBOOK/CHAPTER/VERS)."
        )

    return {
        "id": f"bible-{uuid.uuid4().hex[:12]}",
        "name": bible_name,
        "filename": Path(filename).name,
        "format": "Zefania XML",
        "books": books,
        "createdAt": int(time.time()),
    }


def strip_lrc_timestamps(text: str) -> str:
    lines = []
    for line in clean_text(text).split("\n"):
        line = re.sub(r"^(?:\[[0-9:.]+])+", "", line).strip()
        if line and not re.match(r"^\[(ar|ti|al|by|offset):", line, re.I):
            lines.append(line)
    return "\n".join(lines)


def search_key(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or "").casefold())
    without_marks = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return " ".join(without_marks.split())


def font_family_for(filename: str) -> str:
    digest = hashlib.sha1(filename.encode("utf-8")).hexdigest()[:10]
    return f"NexStageFont-{digest}"


def font_format(suffix: str) -> str:
    return {
        ".ttf": "truetype",
        ".otf": "opentype",
        ".woff": "woff",
        ".woff2": "woff2",
    }.get(suffix.lower(), "truetype")


def list_fonts() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    try:
        paths = sorted(FONT_DIR.iterdir(), key=lambda item: item.name.casefold())
    except FileNotFoundError:
        return results
    for path in paths:
        if not path.is_file() or path.suffix.lower() not in {".ttf", ".otf", ".woff", ".woff2"}:
            continue
        results.append(
            {
                "name": path.stem.replace("_", " ").replace("-", " "),
                "filename": path.name,
                "family": font_family_for(path.name),
                "format": font_format(path.suffix),
                "url": "/fonts/" + urllib.parse.quote(path.name),
                "size": path.stat().st_size,
            }
        )
    return results


FONT_SUFFIXES = {".ttf", ".otf", ".woff", ".woff2"}
DEFAULT_SYSTEM_FONT_PREFIX = "CMG"


def system_font_directories() -> list[Path]:
    """Folders where the operating system keeps installed fonts."""
    home = Path.home()
    if os.name == "nt":
        windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot") or r"C:\Windows"
        folders = [Path(windir) / "Fonts"]
        local = os.environ.get("LOCALAPPDATA", "").strip()
        if local:
            folders.append(Path(local) / "Microsoft" / "Windows" / "Fonts")
        return folders
    if sys.platform == "darwin":
        return [Path("/System/Library/Fonts"), Path("/Library/Fonts"), home / "Library" / "Fonts"]
    return [
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        home / ".fonts",
        home / ".local" / "share" / "fonts",
    ]


def font_name_key(value: Any) -> str:
    """Compare font names ignoring case, accents, spaces, dashes and underscores."""
    return re.sub(r"[^a-z0-9]", "", search_key(value))


def registry_system_fonts(prefix_key: str) -> list[Path]:
    """Windows lists each installed font's display name in the registry.

    This finds fonts whose *display name* starts with the prefix even when the
    file name does not (for example, ``CMG Sans (TrueType)`` -> ``cmgs.ttf``).
    """
    if os.name != "nt":
        return []
    try:
        import winreg  # type: ignore[import-not-found]
    except ImportError:  # pragma: no cover - only on Windows
        return []
    windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot") or r"C:\Windows"
    found: list[Path] = []
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):  # pragma: no cover
        try:
            with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts") as key:
                index = 0
                while True:
                    try:
                        display, value, _kind = winreg.EnumValue(key, index)
                    except OSError:
                        break
                    index += 1
                    if not isinstance(value, str):
                        continue
                    if not font_name_key(re.sub(r"\s*\([^)]*\)\s*$", "", display)).startswith(prefix_key):
                        continue
                    path = Path(value)
                    if not path.is_absolute():
                        path = Path(windir) / "Fonts" / value
                    found.append(path)
        except OSError:
            continue
    return found


def find_system_fonts(
    prefix: str = DEFAULT_SYSTEM_FONT_PREFIX, directories: list[Path] | None = None
) -> list[Path]:
    """Installed fonts whose file or display name starts with ``prefix``."""
    prefix_key = font_name_key(prefix)
    if not prefix_key:
        return []
    candidates: list[Path] = []
    for folder in directories if directories is not None else system_font_directories():
        try:
            if not folder.is_dir():
                continue
            for path in folder.rglob("*"):
                if path.suffix.lower() in FONT_SUFFIXES and font_name_key(path.stem).startswith(prefix_key):
                    candidates.append(path)
        except OSError:
            continue
    if directories is None:
        candidates.extend(registry_system_fonts(prefix_key))
    unique: dict[str, Path] = {}
    for path in candidates:
        try:
            if path.suffix.lower() not in FONT_SUFFIXES or not path.is_file():
                continue
        except OSError:
            continue
        unique.setdefault(safe_name(path.name).casefold(), path)
    return sorted(unique.values(), key=lambda item: item.name.casefold())


def file_digest(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def system_fonts_manifest() -> Path:
    return DATA_DIR / "system-fonts.json"


def sync_system_fonts(
    prefix: str = DEFAULT_SYSTEM_FONT_PREFIX, directories: list[Path] | None = None
) -> dict[str, Any]:
    """Copy the system's CMG fonts into NexStage and drop manual duplicates.

    * New system fonts are copied (keeping the same file name a manual import
      would have, so styles that already use the font keep working).
    * Fonts copied by this function are refreshed when the system file changes.
    * Manually imported fonts that match a system font (same name or same
      bytes) are deleted. Manual fonts without a system match are kept.
    The result lists what happened; ``remap`` maps old font families to the
    family that replaced them, so saved styles can be updated.
    """
    result: dict[str, Any] = {
        "found": 0, "imported": [], "updated": [], "removedManual": [], "keptManual": [], "remap": {},
    }
    ensure_directories()
    prefix_key = font_name_key(prefix)
    sources = find_system_fonts(prefix, directories)
    result["found"] = len(sources)
    manifest_path = system_fonts_manifest()
    manifest = read_json(manifest_path, {})
    managed: dict[str, Any] = manifest.get("files", {}) if isinstance(manifest, dict) else {}
    changed = False

    def copy_in(source: Path, target: Path) -> None:
        temporary = target.with_name(target.name + ".part")
        try:
            shutil.copyfile(source, temporary)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

    copied: dict[str, Path] = {}  # target file name -> system source
    for source in sources:
        target_name = safe_name(source.name)
        target = FONT_DIR / target_name
        try:
            stat = source.stat()
            meta = {"source": str(source), "size": stat.st_size, "mtime": int(stat.st_mtime)}
            known = managed.get(target_name)
            if known and target.is_file():
                if known.get("size") != meta["size"] or known.get("mtime") != meta["mtime"]:
                    copy_in(source, target)
                    result["updated"].append(target_name)
                    managed[target_name] = meta
                    changed = True
            else:
                if target.exists():  # same name, imported by hand: replaced by the system copy
                    result["removedManual"].append(target_name)
                else:
                    result["imported"].append(target_name)
                copy_in(source, target)
                managed[target_name] = meta
                changed = True
            copied[target_name] = source
        except OSError:
            continue

    # Manual copies stored under another name (e.g. "CMG-Sans-2.ttf") or in another case.
    try:
        existing = [item for item in FONT_DIR.iterdir() if item.is_file() and item.suffix.lower() in FONT_SUFFIXES]
    except OSError:
        existing = []
    for path in existing:
        if path.name in managed or path.name in result["removedManual"]:
            continue
        if not font_name_key(path.stem).startswith(prefix_key):
            continue
        match: str | None = None
        for name, source in copied.items():
            if font_name_key(Path(name).stem) == font_name_key(path.stem):
                match = name
                break
        if match is None:
            try:
                size = path.stat().st_size
                digest = None
                for name, source in copied.items():
                    if source.stat().st_size != size:
                        continue
                    digest = digest or file_digest(path)
                    if file_digest(source) == digest:
                        match = name
                        break
            except OSError:
                match = None
        if match is None:
            result["keptManual"].append(path.name)
            continue
        try:
            path.unlink()
        except OSError:
            result["keptManual"].append(path.name)
            continue
        result["removedManual"].append(path.name)
        if path.name != match:
            result["remap"][font_family_for(path.name)] = font_family_for(match)
    if changed:
        atomic_write_json(manifest_path, {"files": managed})
    return result


def louvorja_candidates(configured: str = "") -> list[Path]:
    candidates: list[Path] = []
    if configured.strip():
        chosen = Path(configured.strip().strip('"'))
        candidates.append(chosen / "database.db" if chosen.is_dir() else chosen)
    for variable in ("ProgramFiles(x86)", "ProgramFiles"):
        root = os.environ.get(variable, "").strip()
        if root:
            candidates.append(Path(root) / "Louvor JA" / "config" / "database.db")
    candidates.extend(
        [
            Path(r"C:\Program Files (x86)\Louvor JA\config\database.db"),
            Path(r"C:\Program Files\Louvor JA\config\database.db"),
        ]
    )
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).casefold()
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def find_louvorja_database(configured: str = "") -> Path | None:
    return next((path for path in louvorja_candidates(configured) if path.is_file()), None)


def open_sqlite_read_only(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=4.0)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
    except Exception:
        connection.close()
        raise
    return connection


class LouvorJACatalog:
    """Small metadata cache; lyrics remain in the user's database until selected."""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.signature: tuple[str, int, int] | None = None
        self.items: list[dict[str, Any]] = []

    def database(self, configured: str = "") -> Path:
        path = find_louvorja_database(configured)
        if not path:
            raise ValueError(
                "Louvor JA não encontrado. Confira o caminho do database.db nos Ajustes."
            )
        return path

    @staticmethod
    def _has_object(connection: sqlite3.Connection, name: str) -> bool:
        return connection.execute(
            "SELECT 1 FROM sqlite_master WHERE lower(name)=lower(?) "
            "AND type IN ('table','view') LIMIT 1",
            (name,),
        ).fetchone() is not None

    def load(self, configured: str = "") -> tuple[Path, list[dict[str, Any]]]:
        path = self.database(configured)
        stat = path.stat()
        signature = (str(path.resolve()), int(stat.st_mtime_ns), int(stat.st_size))
        with self.lock:
            if self.signature == signature:
                return path, self.items
            try:
                with closing(open_sqlite_read_only(path)) as connection:
                    if not self._has_object(connection, "MUSICAS"):
                        raise ValueError("O banco não contém a estrutura MUSICAS esperada.")
                    try:
                        rows = connection.execute(
                            """
                            SELECT DISTINCT M.ID, M.NOME,
                                   COALESCE(A.NOME, M.ALBUM, '') AS ALBUM
                              FROM MUSICAS M
                         LEFT JOIN ALBUM_MUSICAS AM ON AM.ID_MUSICA = M.ID
                         LEFT JOIN ALBUM A ON A.ID = AM.ID_ALBUM
                             WHERE M.NOME IS NOT NULL
                          ORDER BY M.NOME COLLATE NOCASE, M.ID
                            """
                        ).fetchall()
                    except sqlite3.DatabaseError:
                        rows = connection.execute(
                            """
                            SELECT ID, NOME, COALESCE(ALBUM, '') AS ALBUM
                              FROM MUSICAS
                             WHERE NOME IS NOT NULL
                          ORDER BY NOME COLLATE NOCASE, ID
                            """
                        ).fetchall()
            except sqlite3.DatabaseError as exc:
                raise ValueError(
                    "Não foi possível ler o database.db do Louvor JA como SQLite."
                ) from exc

            grouped: dict[int, dict[str, Any]] = {}
            for row in rows:
                song_id = int(row["ID"])
                item = grouped.setdefault(
                    song_id,
                    {"id": song_id, "title": str(row["NOME"] or "").strip(), "albums": []},
                )
                album = str(row["ALBUM"] or "").strip()
                if album and album not in item["albums"]:
                    item["albums"].append(album)
            self.items = list(grouped.values())
            self.signature = signature
            return path, self.items

    def status(self, configured: str = "") -> dict[str, Any]:
        path = find_louvorja_database(configured)
        if not path:
            return {
                "available": False,
                "path": configured,
                "count": 0,
                "message": "Louvor JA não foi encontrado automaticamente.",
            }
        try:
            resolved, items = self.load(configured)
            return {
                "available": True,
                "path": str(resolved),
                "count": len(items),
                "message": "Catálogo disponível offline.",
            }
        except (OSError, ValueError) as exc:
            return {
                "available": False,
                "path": str(path),
                "count": 0,
                "message": str(exc),
            }

    def search(self, query: str, configured: str = "") -> list[dict[str, Any]]:
        query = clean_text(query)[:180]
        if len(query) < 2:
            raise ValueError("Digite pelo menos dois caracteres.")
        _, items = self.load(configured)
        words = search_key(query).split()
        matches = [
            item for item in items
            if all(word in search_key(f"{item['title']} {' '.join(item['albums'])}") for word in words)
        ]
        normalized_query = search_key(query)
        matches.sort(
            key=lambda item: (
                not search_key(item["title"]).startswith(normalized_query),
                search_key(item["title"]),
                item["id"],
            )
        )
        return matches[:80]

    def song(self, song_id: int, configured: str = "") -> dict[str, Any]:
        path, items = self.load(configured)
        metadata = next((item for item in items if item["id"] == song_id), None)
        if not metadata:
            raise ValueError("Música não encontrada no Louvor JA.")
        try:
            with closing(open_sqlite_read_only(path)) as connection:
                slides: list[sqlite3.Row] = []
                if self._has_object(connection, "MUSICAS_SLIDE"):
                    slides = connection.execute(
                        """
                        SELECT LETRA, ORDEM
                          FROM MUSICAS_SLIDE
                         WHERE MUSICA_ID = ?
                           AND upper(COALESCE(TIPO, '')) = 'LETRA'
                           AND trim(COALESCE(LETRA, '')) <> ''
                      ORDER BY ORDEM
                        """,
                        (song_id,),
                    ).fetchall()
                if not slides and self._has_object(connection, "MUSICAS_LETRA"):
                    slides = connection.execute(
                        """
                        SELECT LETRA, ORDEM
                          FROM MUSICAS_LETRA
                         WHERE MUSICA = ?
                           AND COALESCE(EXIBE_SLIDE, 1) = 1
                           AND trim(COALESCE(LETRA, '')) <> ''
                      ORDER BY ORDEM
                        """,
                        (song_id,),
                    ).fetchall()
                texts = [str(row["LETRA"] or "").strip() for row in slides if row["LETRA"]]
                if not texts:
                    row = connection.execute(
                        "SELECT LETRA FROM MUSICAS WHERE ID = ? LIMIT 1", (song_id,)
                    ).fetchone()
                    if row and row["LETRA"]:
                        texts = [str(row["LETRA"]).strip()]
        except sqlite3.DatabaseError as exc:
            raise ValueError("Não foi possível ler a letra escolhida no banco.") from exc
        if not texts:
            raise ValueError("Essa música não possui letra disponível no banco.")
        fingerprint = hashlib.sha256("\n\n".join(texts).encode("utf-8")).hexdigest()[:20]
        return {
            "id": f"song-{uuid.uuid4().hex[:12]}",
            "title": metadata["title"],
            "artist": "",
            "album": " / ".join(metadata["albums"]),
            "source": "Louvor JA",
            "sourceId": str(song_id),
            "sourceFingerprint": fingerprint,
            "slides": [{"label": "", "text": text} for text in texts],
            "createdAt": int(time.time()),
        }


LOUVOR_JA = LouvorJACatalog()


class LouvorJABibleCatalog:
    """Reads Bible metadata and one selected chapter from Louvor JA on demand."""

    REQUIRED_OBJECTS = ("bible_version", "bible_book", "bible_verse")

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.signature: tuple[str, int, int] | None = None
        self.versions_cache: list[dict[str, Any]] = []
        self.books_cache: list[dict[str, Any]] = []

    def database(self, configured: str = "") -> Path:
        path = find_louvorja_database(configured)
        if not path:
            raise ValueError(
                "Bíblia do Louvor JA não encontrada. Confira o database.db nos Ajustes."
            )
        return path

    @staticmethod
    def _has_object(connection: sqlite3.Connection, name: str) -> bool:
        return connection.execute(
            "SELECT 1 FROM sqlite_master WHERE lower(name)=lower(?) "
            "AND type IN ('table','view') LIMIT 1",
            (name,),
        ).fetchone() is not None

    def load(self, configured: str = "") -> tuple[Path, list[dict[str, Any]], list[dict[str, Any]]]:
        path = self.database(configured)
        stat = path.stat()
        signature = (str(path.resolve()), int(stat.st_mtime_ns), int(stat.st_size))
        with self.lock:
            if self.signature == signature:
                return path, self.versions_cache, self.books_cache
            try:
                with closing(open_sqlite_read_only(path)) as connection:
                    missing = [
                        name for name in self.REQUIRED_OBJECTS
                        if not self._has_object(connection, name)
                    ]
                    if missing:
                        raise ValueError(
                            "Este database.db não contém a Bíblia esperada do Louvor JA."
                        )
                    version_rows = connection.execute(
                        """
                        SELECT id_bible_version, name, abbreviation
                          FROM bible_version
                         WHERE lower(id_language) = 'pt'
                      ORDER BY id_bible_version
                        """
                    ).fetchall()
                    book_rows = connection.execute(
                        """
                        SELECT id_bible_book, book_number, name, chapters, abbreviation
                          FROM bible_book
                         WHERE lower(id_language) = 'pt'
                      ORDER BY book_number, id_bible_book
                        """
                    ).fetchall()
            except sqlite3.DatabaseError as exc:
                raise ValueError(
                    "Não foi possível ler as versões bíblicas do database.db."
                ) from exc

            self.versions_cache = [
                {
                    "id": int(row["id_bible_version"]),
                    "name": str(row["name"] or "").strip(),
                    "abbreviation": str(row["abbreviation"] or "").strip(),
                    "bookCount": len(book_rows),
                }
                for row in version_rows
            ]
            self.books_cache = [
                {
                    "index": int(row["id_bible_book"]),
                    "number": int(row["book_number"]),
                    "name": str(row["name"] or "").strip(),
                    "abbreviation": str(row["abbreviation"] or "").strip(),
                    "chapterCount": int(row["chapters"]),
                }
                for row in book_rows
            ]
            self.signature = signature
            return path, self.versions_cache, self.books_cache

    def status(self, configured: str = "") -> dict[str, Any]:
        path = find_louvorja_database(configured)
        if not path:
            return {
                "available": False,
                "path": configured,
                "count": 0,
                "versions": [],
                "message": "Louvor JA não foi encontrado automaticamente.",
            }
        try:
            resolved, versions, books = self.load(configured)
            return {
                "available": bool(versions and books),
                "path": str(resolved),
                "count": len(versions),
                "bookCount": len(books),
                "versions": versions,
                "message": "Versões bíblicas disponíveis offline.",
            }
        except (OSError, ValueError) as exc:
            return {
                "available": False,
                "path": str(path),
                "count": 0,
                "versions": [],
                "message": str(exc),
            }

    def books(self, version_id: int, configured: str = "") -> list[dict[str, Any]]:
        _, versions, books = self.load(configured)
        if not any(item["id"] == version_id for item in versions):
            raise ValueError("Versão bíblica não encontrada no Louvor JA.")
        return books

    def chapter(
        self,
        version_id: int,
        book_id: int,
        chapter_number: int,
        configured: str = "",
    ) -> dict[str, Any]:
        if version_id <= 0 or book_id <= 0 or chapter_number <= 0:
            raise ValueError("Versão, livro ou capítulo inválido.")
        path, versions, books = self.load(configured)
        version = next((item for item in versions if item["id"] == version_id), None)
        book = next((item for item in books if item["index"] == book_id), None)
        if not version or not book or chapter_number > int(book["chapterCount"]):
            raise ValueError("Passagem bíblica não encontrada no Louvor JA.")
        try:
            with closing(open_sqlite_read_only(path)) as connection:
                rows = connection.execute(
                    """
                    SELECT verse, text
                      FROM bible_verse
                     WHERE id_bible_version = ?
                       AND id_bible_book = ?
                       AND chapter = ?
                       AND trim(COALESCE(text, '')) <> ''
                  ORDER BY verse, id_bible_verse
                    """,
                    (version_id, book_id, chapter_number),
                ).fetchall()
        except sqlite3.DatabaseError as exc:
            raise ValueError("Não foi possível ler o capítulo escolhido.") from exc
        verses = [
            {"number": str(row["verse"]), "text": clean_text(str(row["text"] or ""))}
            for row in rows
            if clean_text(str(row["text"] or ""))
        ]
        if not verses:
            raise ValueError("Esse capítulo não possui texto disponível nesta versão.")
        return {
            "bible": version["abbreviation"] or version["name"],
            "bibleName": version["name"],
            "book": book["name"],
            "bookAbbreviation": book["abbreviation"],
            "chapter": str(chapter_number),
            "verses": verses,
            "source": "Louvor JA",
        }


LOUVOR_JA_BIBLE = LouvorJABibleCatalog()


class AppStore:
    def __init__(self) -> None:
        ensure_directories()
        self.lock = threading.RLock()
        self.changed = threading.Condition(self.lock)
        self.library = read_json(LIBRARY_FILE, {"songs": [], "bibles": []})
        self.library.setdefault("songs", [])
        self.library.setdefault("bibles", [])
        loaded_settings = read_json(SETTINGS_FILE, {})
        self.settings = deep_merge(DEFAULT_SETTINGS, loaded_settings)

        # Migrate the single 0.2 theme into the new independent component styles.
        if "styles" not in loaded_settings and loaded_settings.get("theme"):
            old_theme = deep_merge(DEFAULT_THEME, loaded_settings["theme"])
            for section in self.settings["styles"].values():
                for component in section.values():
                    component.update(
                        {
                            "fontFamily": old_theme["fontFamily"],
                            "textColor": old_theme["textColor"],
                            "shadow": old_theme["shadow"],
                            "uppercase": old_theme["uppercase"],
                            "align": old_theme["align"],
                        }
                    )
            self.settings["styles"]["song"]["text"]["fontSize"] = old_theme["fontSize"]
            self.settings["styles"]["song"]["text"]["fontWeight"] = old_theme["fontWeight"]
            self.settings["styles"]["song"]["text"]["maxWidth"] = old_theme["maxWidth"]

        self.last_font_sync: dict[str, Any] = {}
        self.font_sync_announced = False
        if self.settings.get("fonts", {}).get("autoImport", True):
            try:
                self.last_font_sync = self._sync_fonts_locked()
            except Exception:  # fonts are optional; never block startup
                self.last_font_sync = {}

        self.yt_tools = yt.YouTubeTools(DATA_DIR / "tools")
        self.yt_library = yt.YouTubeLibrary(DATA_DIR, self.yt_tools, lambda: self.settings)
        self.player = yt.PlayerController(self.yt_library, lambda: self.settings)
        self._volume_saved = (0.0, float(self.settings.get("youtube", {}).get("volume", 0.8)))
        for leftover in (DATA_DIR / "youtube").glob(".tmp-*") if (DATA_DIR / "youtube").is_dir() else []:
            shutil.rmtree(leftover, ignore_errors=True)  # unfinished downloads from a previous run

        self.state = deep_merge(DEFAULT_STATE, {})
        self.state["youtube"] = self.player.public()
        self.state["theme"] = {**DEFAULT_THEME, **self.settings.get("theme", {})}
        self.state["styles"] = deep_merge(DEFAULT_STYLES, self.settings.get("styles", {}))
        self.state["clock"] = deep_merge(DEFAULT_STATE["clock"], self.settings.get("clock", {}))
        self.state["timer"] = deep_merge(DEFAULT_TIMER, self.settings.get("timer", {}))
        self.state["fonts"] = list_fonts()
        self.state["background"] = self.settings.get("defaultBackground", "")
        self.state["overlay"] = self.settings.get("defaultOverlay", "")

    def _sync_fonts_locked(self) -> dict[str, Any]:
        prefix = str(self.settings.get("fonts", {}).get("prefix") or DEFAULT_SYSTEM_FONT_PREFIX)
        result = sync_system_fonts(prefix)
        remap = result.pop("remap", {})
        if remap:
            # Styles that used a deleted manual copy now point to the system copy.
            def replace(value: Any) -> Any:
                text = json.dumps(value, ensure_ascii=False)
                for old, new in remap.items():
                    text = text.replace(old, new)
                return json.loads(text)

            self.settings["styles"] = replace(self.settings.get("styles", {}))
            state = getattr(self, "state", None)
            if isinstance(state, dict) and "styles" in state:
                state["styles"] = replace(state["styles"])
            atomic_write_json(SETTINGS_FILE, self.settings)
        return result

    def _font_sync_for_bootstrap(self) -> dict[str, Any]:
        """The startup result is announced once, not on every page reload."""
        announce = not self.font_sync_announced
        self.font_sync_announced = True
        return {**self.last_font_sync, "announce": announce} if self.last_font_sync else {}

    def sync_fonts(self) -> dict[str, Any]:
        """Search the system again (button in the settings) and refresh the state."""
        with self.changed:
            result = self._sync_fonts_locked()
            self.last_font_sync = result
            self.state["fonts"] = list_fonts()
            self.state["revision"] = int(self.state.get("revision", 0)) + 1
            self.state["updatedAt"] = int(time.time() * 1000)
            self.changed.notify_all()
            return {**result, "fonts": self.state["fonts"], "styles": self.settings.get("styles", {})}

    def bootstrap(self) -> dict[str, Any]:
        with self.lock:
            bibles = [
                {
                    "id": bible["id"],
                    "name": bible["name"],
                    "filename": bible.get("filename", ""),
                    "format": bible.get("format", "XML"),
                    "bookCount": len(bible.get("books", [])),
                }
                for bible in self.library["bibles"]
            ]
            return {
                "app": {
                    "name": APP_NAME,
                    "version": APP_VERSION,
                    "author": APP_AUTHOR,
                    "repository": APP_REPOSITORY,
                    "updateSupported": update_supported(),
                },
                "songs": self.library["songs"],
                "bibles": bibles,
                "media": list_media(),
                "fonts": list_fonts(),
                "fontSync": self._font_sync_for_bootstrap(),
                "settings": self.settings,
                "state": self.state,
                "defaults": {"styles": DEFAULT_STYLES, "settings": DEFAULT_SETTINGS},
            }

    def update_state(self, incoming: dict[str, Any]) -> dict[str, Any]:
        with self.changed:
            safe = json.loads(json.dumps(incoming))
            safe["revision"] = int(self.state.get("revision", 0)) + 1
            safe["updatedAt"] = int(time.time() * 1000)
            safe["theme"] = {**DEFAULT_THEME, **safe.get("theme", {})}
            safe["styles"] = deep_merge(DEFAULT_STYLES, safe.get("styles", {}))
            safe["clock"] = deep_merge(DEFAULT_STATE["clock"], safe.get("clock", {}))
            safe["timer"] = deep_merge(DEFAULT_TIMER, safe.get("timer", {}))
            safe["fonts"] = safe.get("fonts") or list_fonts()
            # Showing a slide or the clock dismisses the video; flags such as blackout do not.
            if self.player.state["item"] and safe.get("mode") != "youtube":
                self.player.command("stop", {})
            safe["youtube"] = self.player.public()
            self.state = safe
            self.changed.notify_all()
            return self.state

    # ---- YouTube -------------------------------------------------------
    def _publish_youtube(self) -> None:
        self.state["youtube"] = self.player.public()
        self.state["revision"] = int(self.state.get("revision", 0)) + 1
        self.state["updatedAt"] = int(time.time() * 1000)
        self.changed.notify_all()

    def youtube_overview(self) -> dict[str, Any]:
        self.youtube_tick()
        return {
            "tools": self.yt_tools.status(),
            "items": self.yt_library.snapshot(),
            "status": self.player.current_status(),
            "settings": self.settings.get("youtube", {}),
        }

    def youtube_add(self, text: str) -> dict[str, Any]:
        item = self.yt_library.add(text)
        if not self.yt_tools.ready() and self.yt_tools.progress.get("state") != "running":
            self.yt_tools.install_async()  # first use: fetch yt-dlp in the background
        return item

    def youtube_command(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self.changed:
            effect = self.player.command(action, payload)
            if effect == "show":
                self.state.update({"live": True, "black": False, "mode": "youtube"})
            elif effect == "hide" and self.state.get("mode") == "youtube":
                self.state["mode"] = "blank"
            self._publish_youtube()
            if action == "volume":
                self._remember_volume()
            return {"status": self.player.current_status(), "state": self.state}

    def _remember_volume(self) -> None:
        last_time, last_value = self._volume_saved
        value = self.player.state["volume"]
        if abs(value - last_value) >= 0.02 and time.time() - last_time > 1.5:
            self._volume_saved = (time.time(), value)
            self.settings.setdefault("youtube", {})["volume"] = round(value, 3)
            atomic_write_json(SETTINGS_FILE, self.settings)

    def youtube_report(self, payload: dict[str, Any]) -> None:
        self.player.report(payload)

    def youtube_tick(self) -> None:
        """When the background download finishes, move a direct stream to the local file."""
        with self.changed:
            state = self.player.state
            if state["mode"] != "stream" or not state["item"]:
                return
            if not self.settings.get("youtube", {}).get("autoSwitchToFile", True):
                return
            status = self.player.status
            if status.get("srcToken") != state["srcToken"] or status.get("buffering"):
                return
            if self.yt_library.file_for(state["item"], state["height"]):
                with self.player.lock:
                    self.player._reload(float(status.get("t", 0.0)))
                self._publish_youtube()

    def wait_state(self, revision: int, timeout: float = 20.0) -> dict[str, Any]:
        """Long-poll state updates so idle outputs use virtually no network/CPU."""
        with self.changed:
            if int(self.state.get("revision", 0)) <= revision:
                self.changed.wait(timeout=timeout)
            return self.state

    def save_song(self, song: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            self.library["songs"].append(song)
            atomic_write_json(LIBRARY_FILE, self.library)
            return song

    def import_external_song(self, song: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        with self.lock:
            source = str(song.get("source", ""))
            source_id = str(song.get("sourceId", ""))
            existing = next(
                (
                    item for item in self.library["songs"]
                    if str(item.get("source", "")) == source
                    and str(item.get("sourceId", "")) == source_id
                ),
                None,
            )
            if existing:
                return existing, True
            self.library["songs"].append(song)
            atomic_write_json(LIBRARY_FILE, self.library)
            return song, False

    def lines_per_slide(self, requested: Any = None) -> int:
        try:
            value = int(requested) if requested not in (None, "") else int(self.settings.get("song", {}).get("linesPerSlide", 4))
        except (TypeError, ValueError):
            value = 4
        return max(1, min(12, value))

    def update_song(self, incoming: dict[str, Any]) -> dict[str, Any]:
        song_id = str(incoming.get("id", ""))
        if not song_id:
            raise ValueError("ID da música não informado.")
        slides = incoming.get("slides")
        if not isinstance(slides, list) or not slides:
            raise ValueError("A música precisa ter pelo menos um slide.")
        normalized_slides = []
        for slide in slides[:500]:
            if not isinstance(slide, dict):
                continue
            text = clean_text(str(slide.get("text", "")))
            label = clean_text(str(slide.get("label", "")))[:100]
            if text:
                normalized_slides.append({"text": text[:12000], "label": label})
        if not normalized_slides:
            raise ValueError("Nenhum slide com texto foi informado.")
        with self.lock:
            song = next((item for item in self.library["songs"] if item["id"] == song_id), None)
            if not song:
                raise KeyError("Música não encontrada")
            song["title"] = clean_text(str(incoming.get("title", song.get("title", ""))))[:200]
            song["artist"] = clean_text(str(incoming.get("artist", song.get("artist", ""))))[:200]
            song["album"] = clean_text(str(incoming.get("album", song.get("album", ""))))[:200]
            song["slides"] = normalized_slides
            song["favorite"] = bool(incoming.get("favorite", song.get("favorite", False)))
            song["updatedAt"] = int(time.time())
            atomic_write_json(LIBRARY_FILE, self.library)
            return song

    def delete_song(self, song_id: str) -> bool:
        with self.lock:
            before = len(self.library["songs"])
            self.library["songs"] = [s for s in self.library["songs"] if s["id"] != song_id]
            if len(self.library["songs"]) == before:
                return False
            atomic_write_json(LIBRARY_FILE, self.library)
            return True

    def save_bible(self, bible: dict[str, Any], raw_xml: str) -> dict[str, Any]:
        with self.lock:
            raw_path = BIBLE_DIR / f"{bible['id']}.xml"
            raw_path.write_text(raw_xml, encoding="utf-8")
            self.library["bibles"].append(bible)
            atomic_write_json(LIBRARY_FILE, self.library)
            return {
                "id": bible["id"],
                "name": bible["name"],
                "filename": bible["filename"],
                "format": bible["format"],
                "bookCount": len(bible["books"]),
            }

    def bible_books(self, bible_id: str) -> list[dict[str, Any]]:
        with self.lock:
            bible = next((b for b in self.library["bibles"] if b["id"] == bible_id), None)
            if not bible:
                raise KeyError("Bíblia não encontrada")
            return [
                {"index": index, "name": book["name"], "chapterCount": len(book["chapters"])}
                for index, book in enumerate(bible["books"])
            ]

    def bible_chapter(self, bible_id: str, book_index: int, chapter_index: int) -> dict[str, Any]:
        with self.lock:
            bible = next((b for b in self.library["bibles"] if b["id"] == bible_id), None)
            if not bible:
                raise KeyError("Bíblia não encontrada")
            book = bible["books"][book_index]
            chapter = book["chapters"][chapter_index]
            return {
                "bible": bible["name"],
                "book": book["name"],
                "chapter": chapter["number"],
                "verses": chapter["verses"],
            }

    def save_settings(self, incoming: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            self.settings = deep_merge(self.settings, incoming)
            self.settings = deep_merge(DEFAULT_SETTINGS, self.settings)
            atomic_write_json(SETTINGS_FILE, self.settings)
            return self.settings

    def export_settings(self) -> dict[str, Any]:
        """Build a portable settings file without machine-specific paths."""
        with self.lock:
            settings = json.loads(json.dumps(self.settings))
            settings["louvorJaDb"] = ""
            settings.setdefault("output", {})["preferredScreen"] = ""
            return {
                "kind": SETTINGS_EXPORT_KIND,
                "schemaVersion": SETTINGS_EXPORT_SCHEMA,
                "appVersion": APP_VERSION,
                "exportedAt": int(time.time()),
                "settings": settings,
                "notIncluded": [
                    "biblioteca de músicas",
                    "arquivos de mídia",
                    "arquivos de fontes",
                    "caminho do Louvor JA",
                    "monitor preferido",
                ],
            }

    @staticmethod
    def _validated_settings(incoming: Any) -> dict[str, Any]:
        if not isinstance(incoming, dict):
            raise ValueError("O arquivo de configurações não contém um objeto válido.")
        if "kind" in incoming:
            if incoming.get("kind") != SETTINGS_EXPORT_KIND:
                raise ValueError("Este arquivo não é uma configuração do NexStage.")
            if int(incoming.get("schemaVersion", 0)) > SETTINGS_EXPORT_SCHEMA:
                raise ValueError("A configuração foi criada por uma versão mais nova do NexStage.")
            incoming = incoming.get("settings")
            if not isinstance(incoming, dict):
                raise ValueError("O arquivo não contém a seção de configurações.")

        allowed = set(DEFAULT_SETTINGS)
        filtered = {key: value for key, value in incoming.items() if key in allowed}
        settings = deep_merge(DEFAULT_SETTINGS, filtered)

        # Text sizes intentionally have no maximum. Only invalid, infinite or
        # non-positive values fall back to the component default.
        for section, components in settings.get("styles", {}).items():
            if not isinstance(components, dict):
                continue
            for component, style in components.items():
                if not isinstance(style, dict):
                    continue
                default_style = DEFAULT_STYLES.get(section, {}).get(component, {})
                for key in ("fontSize", "minFontSize"):
                    value = style.get(key, default_style.get(key, 26))
                    try:
                        number = float(value)
                    except (TypeError, ValueError):
                        number = float(default_style.get(key, 26))
                    if not math.isfinite(number) or number <= 0:
                        number = float(default_style.get(key, 26))
                    style[key] = int(number) if number.is_integer() else number
        return settings

    def import_settings(self, bundle: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            imported = self._validated_settings(bundle)
            # These identify hardware and a local installation, so importing a
            # visual preset must not unexpectedly replace them.
            imported["louvorJaDb"] = self.settings.get("louvorJaDb", "")
            imported.setdefault("output", {})["preferredScreen"] = (
                self.settings.get("output", {}).get("preferredScreen", "")
            )
            self.settings = imported
            atomic_write_json(SETTINGS_FILE, self.settings)
            self.state["theme"] = deep_merge(DEFAULT_THEME, self.settings.get("theme", {}))
            self.state["styles"] = deep_merge(DEFAULT_STYLES, self.settings.get("styles", {}))
            self.state["clock"] = deep_merge(DEFAULT_STATE["clock"], self.settings.get("clock", {}))
            self.state["timer"] = deep_merge(DEFAULT_TIMER, self.settings.get("timer", {}))
            self.state["background"] = self.settings.get("defaultBackground", "")
            self.state["overlay"] = self.settings.get("defaultOverlay", "")
            self.state["revision"] = int(self.state.get("revision", 0)) + 1
            self.state["updatedAt"] = int(time.time() * 1000)
            self.changed.notify_all()
            return self.settings


def list_media() -> list[dict[str, Any]]:
    results = []
    allowed = {".mp4", ".webm", ".mov", ".m4v", ".jpg", ".jpeg", ".png", ".webp", ".gif"}
    try:
        paths = sorted(MEDIA_DIR.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True)
    except FileNotFoundError:
        return []
    for path in paths:
        if path.is_file() and path.suffix.lower() in allowed:
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            results.append(
                {
                    "name": path.name,
                    "url": "/media/" + urllib.parse.quote(path.name),
                    "type": "video" if mime.startswith("video/") else "image",
                    "size": path.stat().st_size,
                }
            )
    return results


STORE = AppStore()


class NexStageHandler(BaseHTTPRequestHandler):
    server_version = f"{APP_NAME}/{APP_VERSION}"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        if getattr(self.server, "quiet", False):
            return
        sys.stdout.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Allow", "GET, POST, DELETE, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        try:
            if path == "/api/bootstrap":
                self.send_json(STORE.bootstrap(), cache=False)
            elif path == "/api/about":
                self.send_json(
                    about_info(getattr(self.server, "base_url", "http://127.0.0.1:4310")),
                    cache=False,
                )
            elif path == "/api/update/check":
                force = query.get("force", ["0"])[0] == "1"
                self.send_json(UPDATE_SERVICE.check(force=force), cache=False)
            elif path == "/api/state":
                revision = int(query.get("since", ["0"])[0])
                self.send_json(STORE.wait_state(revision), cache=False)
            elif path == "/api/media":
                self.send_json(list_media(), cache=False)
            elif path == "/api/fonts":
                self.send_json(list_fonts(), cache=False)
            elif path == "/api/lyrics/search":
                self.handle_lyrics_search(query.get("q", [""])[0])
            elif path == "/api/louvorja/status":
                self.send_json(
                    LOUVOR_JA.status(str(STORE.settings.get("louvorJaDb", ""))),
                    cache=False,
                )
            elif path == "/api/louvorja/search":
                self.send_json(
                    LOUVOR_JA.search(
                        query.get("q", [""])[0],
                        str(STORE.settings.get("louvorJaDb", "")),
                    ),
                    cache=False,
                )
            elif path == "/api/louvorja/bible/status":
                self.send_json(
                    LOUVOR_JA_BIBLE.status(
                        str(STORE.settings.get("louvorJaDb", ""))
                    ),
                    cache=False,
                )
            elif path == "/api/louvorja/bible/books":
                self.send_json(
                    LOUVOR_JA_BIBLE.books(
                        int(query.get("version", ["0"])[0]),
                        str(STORE.settings.get("louvorJaDb", "")),
                    ),
                    cache=False,
                )
            elif path == "/api/louvorja/bible/chapter":
                self.send_json(
                    LOUVOR_JA_BIBLE.chapter(
                        int(query.get("version", ["0"])[0]),
                        int(query.get("book", ["0"])[0]),
                        int(query.get("chapter", ["0"])[0]),
                        str(STORE.settings.get("louvorJaDb", "")),
                    ),
                    cache=False,
                )
            elif path == "/api/settings/export":
                self.send_json(STORE.export_settings(), cache=False)
            elif path.startswith("/api/bible/") and path.endswith("/books"):
                bible_id = path.split("/")[3]
                self.send_json(STORE.bible_books(bible_id), cache=False)
            elif path.startswith("/api/bible/") and path.endswith("/chapter"):
                bible_id = path.split("/")[3]
                book = int(query.get("book", ["0"])[0])
                chapter = int(query.get("chapter", ["0"])[0])
                self.send_json(STORE.bible_chapter(bible_id, book, chapter), cache=False)
            elif path == "/api/youtube":
                self.send_json(STORE.youtube_overview(), cache=False)
            elif path.startswith("/youtube/file/"):
                self.serve_youtube_file(path[len("/youtube/file/") :])
            elif path == "/youtube/stream":
                self.handle_youtube_stream(query)
            elif path.startswith("/media/"):
                self.serve_media(path[len("/media/") :])
            elif path.startswith("/fonts/"):
                self.serve_font(path[len("/fonts/") :])
            else:
                self.serve_web(path)
        except (KeyError, IndexError, ValueError, yt.YouTubeError) as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except BrokenPipeError:
            pass
        except Exception as exc:  # pragma: no cover - final safety boundary
            self.send_json({"error": f"Erro interno: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            if path == "/api/media/upload":
                self.handle_media_upload()
                return
            if path == "/api/font/upload":
                self.handle_font_upload()
                return
            if path == "/api/video-local/upload":
                self.handle_local_video_upload()
                return
            payload = self.read_json_body()
            if path == "/api/state":
                self.send_json(STORE.update_state(payload), cache=False)
            elif path == "/api/fonts/sync":
                self.send_json(STORE.sync_fonts(), cache=False)
            elif path == "/api/youtube/add":
                self.send_json(STORE.youtube_add(str(payload.get("text", ""))), status=HTTPStatus.CREATED)
            elif path == "/api/youtube/remove":
                video_id = str(payload.get("id", ""))
                if STORE.player.state["item"] == video_id:
                    STORE.youtube_command("stop", {})
                STORE.yt_library.remove(video_id)
                self.send_json({"ok": True}, cache=False)
            elif path == "/api/youtube/install":
                started = STORE.yt_tools.install_async(update=bool(payload.get("update", False)))
                self.send_json({"started": started, "tools": STORE.yt_tools.status()}, cache=False)
            elif path == "/api/youtube/download":
                video_id = str(payload.get("id", ""))
                if video_id not in STORE.yt_library.items:
                    raise KeyError("Vídeo não encontrado.")
                height = STORE.yt_library.pick_height(video_id, int(payload.get("height", yt.DEFAULT_HEIGHT)))
                STORE.yt_library.queue_download(video_id, height)
                self.send_json({"ok": True, "height": height}, cache=False)
            elif path == "/api/youtube/command":
                self.send_json(
                    STORE.youtube_command(str(payload.get("action", "")), payload), cache=False
                )
            elif path == "/api/youtube/report":
                STORE.youtube_report(payload)
                self.send_json({"ok": True}, cache=False)
            elif path == "/api/song/import":
                song = parse_song_text(
                    str(payload.get("filename", "musica.txt")),
                    str(payload.get("content", "")),
                    str(payload.get("title", "")),
                    STORE.lines_per_slide(payload.get("linesPerSlide")),
                )
                if payload.get("artist"):
                    song["artist"] = clean_text(str(payload["artist"]))[:200]
                if payload.get("manual"):
                    song["source"] = "manual"
                self.send_json(STORE.save_song(song), status=HTTPStatus.CREATED)
            elif path == "/api/lyrics/import":
                lyrics = str(payload.get("lyrics", ""))
                song = parse_song_text(
                    str(payload.get("filename", "letra-online.txt")),
                    lyrics,
                    str(payload.get("title", "")),
                    STORE.lines_per_slide(payload.get("linesPerSlide")),
                )
                song["source"] = "LRCLIB"
                song["artist"] = str(payload.get("artist", ""))
                self.send_json(STORE.save_song(song), status=HTTPStatus.CREATED)
            elif path == "/api/louvorja/import":
                song = LOUVOR_JA.song(
                    int(payload.get("id", 0)),
                    str(STORE.settings.get("louvorJaDb", "")),
                )
                imported, already_imported = STORE.import_external_song(song)
                self.send_json(
                    {"song": imported, "alreadyImported": already_imported},
                    status=HTTPStatus.OK if already_imported else HTTPStatus.CREATED,
                )
            elif path == "/api/song/update":
                self.send_json(STORE.update_song(payload))
            elif path == "/api/bible/import":
                content = str(payload.get("content", ""))
                bible = parse_zefania_xml(str(payload.get("filename", "biblia.xml")), content)
                self.send_json(STORE.save_bible(bible, content), status=HTTPStatus.CREATED)
            elif path == "/api/settings/import":
                self.send_json(STORE.import_settings(payload), cache=False)
            elif path == "/api/settings":
                self.send_json(STORE.save_settings(payload))
            elif path == "/api/system/open-data":
                open_data_folder()
                self.send_json({"ok": True}, cache=False)
            elif path == "/api/update/apply":
                if _UPDATE_INSTALL_CALLBACK is None:
                    raise ValueError(
                        "O instalador automático só funciona no NexStage instalado no Windows."
                    )
                installer = UPDATE_SERVICE.download_installer()
                self.send_json(
                    {
                        "ok": True,
                        "message": "Atualização baixada. O instalador será aberto agora.",
                    },
                    cache=False,
                )
                threading.Timer(0.7, _UPDATE_INSTALL_CALLBACK, args=(installer,)).start()
            else:
                self.send_error(HTTPStatus.NOT_FOUND)
        except (KeyError, IndexError, ValueError, json.JSONDecodeError, yt.YouTubeError) as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as exc:  # pragma: no cover
            self.send_json({"error": f"Erro interno: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/song/"):
            song_id = path.rsplit("/", 1)[-1]
            if STORE.delete_song(song_id):
                self.send_json({"ok": True})
            else:
                self.send_json({"error": "Música não encontrada"}, status=HTTPStatus.NOT_FOUND)
            return
        if path.startswith("/api/media/"):
            name = urllib.parse.unquote(path[len("/api/media/") :])
            target = (MEDIA_DIR / Path(name).name).resolve()
            if target.parent != MEDIA_DIR.resolve() or not target.exists():
                self.send_json({"error": "Mídia não encontrada"}, status=HTTPStatus.NOT_FOUND)
                return
            target.unlink()
            self.send_json({"ok": True})
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_JSON_BYTES:
            raise ValueError("Tamanho de requisição inválido")
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def handle_media_upload(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        filename = urllib.parse.unquote(self.headers.get("X-Filename", "midia"))
        suffix = Path(filename).suffix.lower()
        allowed = {".mp4", ".webm", ".mov", ".m4v", ".jpg", ".jpeg", ".png", ".webp", ".gif"}
        if suffix not in allowed:
            raise ValueError("Formato não aceito. Use MP4, WebM, MOV, JPG, PNG, WebP ou GIF.")
        if length <= 0 or length > MAX_MEDIA_BYTES:
            raise ValueError("Arquivo vazio ou maior que 8 GB")
        target = unique_path(MEDIA_DIR, filename)
        remaining = length
        try:
            with target.open("wb") as output:
                while remaining:
                    chunk = self.rfile.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ConnectionError("Upload interrompido")
                    output.write(chunk)
                    remaining -= len(chunk)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        item = next(item for item in list_media() if item["name"] == target.name)
        self.send_json(item, status=HTTPStatus.CREATED)

    def handle_local_video_upload(self) -> None:
        """Copy a video from the computer into the app (streamed), then prepare it in the background."""
        length = int(self.headers.get("Content-Length", "0"))
        filename = urllib.parse.unquote(self.headers.get("X-Filename", "video.mp4"))
        suffix = Path(filename).suffix.lower()
        if suffix not in yt.LOCAL_SUFFIXES:
            raise ValueError("Formato de vídeo não aceito. Use MP4, MOV, MKV, WebM, AVI, WMV, MPG ou TS.")
        if length <= 0 or length > 24 * 1024 * 1024 * 1024:
            raise ValueError("Arquivo vazio ou maior que 24 GB.")
        library = STORE.yt_library
        library.files_dir.mkdir(parents=True, exist_ok=True)
        workdir = Path(tempfile.mkdtemp(prefix=".tmp-up-", dir=library.files_dir))
        source = workdir / f"original{suffix}"
        remaining = length
        try:
            with source.open("wb") as output:
                while remaining:
                    chunk = self.rfile.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ConnectionError("Upload interrompido")
                    output.write(chunk)
                    remaining -= len(chunk)
        except Exception:
            shutil.rmtree(workdir, ignore_errors=True)
            raise
        self.send_json(library.add_local(source, filename), status=HTTPStatus.CREATED)

    def handle_font_upload(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        filename = urllib.parse.unquote(self.headers.get("X-Filename", "fonte"))
        suffix = Path(filename).suffix.lower()
        if suffix not in {".ttf", ".otf", ".woff", ".woff2"}:
            raise ValueError("Formato não aceito. Use TTF, OTF, WOFF ou WOFF2.")
        if length <= 0 or length > MAX_FONT_BYTES:
            raise ValueError("Fonte vazia ou maior que 32 MB.")
        target = unique_path(FONT_DIR, filename)
        remaining = length
        try:
            with target.open("wb") as output:
                while remaining:
                    chunk = self.rfile.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ConnectionError("Upload interrompido")
                    output.write(chunk)
                    remaining -= len(chunk)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        item = next(item for item in list_fonts() if item["filename"] == target.name)
        self.send_json(item, status=HTTPStatus.CREATED)

    def handle_lyrics_search(self, query: str) -> None:
        query = clean_text(query)[:180]
        if len(query) < 2:
            raise ValueError("Digite o nome da música e, se possível, o artista.")
        url = "https://lrclib.net/api/search?" + urllib.parse.urlencode({"q": query})
        request = urllib.request.Request(
            url,
            headers={"User-Agent": f"{APP_NAME}/{APP_VERSION} (local church presenter)"},
        )
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                raw_results = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ValueError("Não foi possível consultar letras online agora.") from exc
        results = []
        for item in raw_results[:12]:
            lyrics = item.get("plainLyrics") or strip_lrc_timestamps(item.get("syncedLyrics") or "")
            if not lyrics:
                continue
            results.append(
                {
                    "id": item.get("id"),
                    "title": item.get("trackName") or "Sem título",
                    "artist": item.get("artistName") or "",
                    "album": item.get("albumName") or "",
                    "duration": item.get("duration"),
                    "lyrics": lyrics,
                }
            )
        self.send_json(results, cache=False)

    def serve_web(self, url_path: str) -> None:
        aliases = {
            "/": "index.html",
            "/output": "output.html",
            "/obs": "obs.html",
        }
        relative = aliases.get(url_path, url_path.lstrip("/"))
        target = (WEB_DIR / relative).resolve()
        if WEB_DIR.resolve() not in target.parents and target != WEB_DIR.resolve():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        self.serve_file(target, cache_seconds=0)  # html/css/js sempre revalidados: após atualizar, nada fica com visual antigo

    def serve_media(self, encoded_name: str) -> None:
        name = Path(urllib.parse.unquote(encoded_name)).name
        target = (MEDIA_DIR / name).resolve()
        if target.parent != MEDIA_DIR.resolve():
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        self.serve_file(target, cache_seconds=31536000, allow_range=True)

    def serve_youtube_file(self, encoded_name: str) -> None:
        name = Path(urllib.parse.unquote(encoded_name)).name
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}-(\d{2,4}\.mp4|thumb\.jpg)", name):
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        # The file name never changes for the same video and height, so the browser must not cache it forever.
        self.serve_file(STORE.yt_library.files_dir / name, cache_seconds=0, allow_range=True)

    def handle_youtube_stream(self, query: dict[str, list[str]]) -> None:
        """Direct H.264 stream while the download is not finished (audio and video are copied, not converted)."""
        video_id = query.get("id", [""])[0]
        if not yt.VIDEO_ID.fullmatch(video_id):
            raise ValueError("Código de vídeo inválido.")
        height = int(query.get("h", ["720"])[0])
        start = max(0.0, float(query.get("t", ["0"])[0]))
        library = STORE.yt_library
        ffmpeg = library.tools.ffmpeg_path()
        if not ffmpeg:
            raise yt.YouTubeError("O ffmpeg não foi encontrado.")
        urls = library.stream_urls(video_id, height)
        process = None
        first = b""
        for fast in (True, False) if start > 0.5 else (True,):
            process = subprocess.Popen(
                yt.stream_command(ffmpeg, urls, start, fast_seek=fast),
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                creationflags=yt.NO_WINDOW,
            )
            assert process.stdout is not None
            first = process.stdout.read1(65536)
            if first:
                break
            process.kill()
            process.wait()
        try:
            if not first or process is None or process.stdout is None:
                self.send_json({"error": "O YouTube não entregou o vídeo."}, status=HTTPStatus.BAD_GATEWAY)
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.close_connection = True
            self.wfile.write(first)
            while True:
                chunk = process.stdout.read1(262144)
                if not chunk:
                    break
                self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        finally:
            if process is not None:
                process.kill()
                process.wait()

    def serve_font(self, encoded_name: str) -> None:
        name = Path(urllib.parse.unquote(encoded_name)).name
        target = (FONT_DIR / name).resolve()
        if target.parent != FONT_DIR.resolve() or target.suffix.lower() not in {
            ".ttf", ".otf", ".woff", ".woff2"
        }:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        self.serve_file(target, cache_seconds=31536000)

    def serve_file(self, target: Path, cache_seconds: int, allow_range: bool = False) -> None:
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        file_size = target.stat().st_size
        mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        start, end = 0, file_size - 1
        status = HTTPStatus.OK
        range_header = self.headers.get("Range") if allow_range else None
        if range_header:
            match = re.match(r"bytes=(\d*)-(\d*)", range_header)
            if match:
                if not match.group(1) and match.group(2):
                    suffix_length = min(int(match.group(2)), file_size)
                    start = file_size - suffix_length
                    end = file_size - 1
                elif match.group(1):
                    start = int(match.group(1))
                    if match.group(2):
                        end = min(int(match.group(2)), file_size - 1)
                if start > end or start >= file_size:
                    self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                    self.send_header("Content-Range", f"bytes */{file_size}")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                status = HTTPStatus.PARTIAL_CONTENT

        length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", f"public, max-age={cache_seconds}" if cache_seconds else "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        if allow_range:
            self.send_header("Accept-Ranges", "bytes")
        if status == HTTPStatus.PARTIAL_CONTENT:
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.end_headers()
        with target.open("rb") as source:
            source.seek(start)
            remaining = length
            while remaining:
                chunk = source.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def send_json(
        self, payload: Any, status: HTTPStatus = HTTPStatus.OK, cache: bool = True
    ) -> None:
        raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "private, max-age=0" if cache else "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)


class NexStageServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def create_server(
    host: str = "127.0.0.1", start_port: int = 4310, quiet: bool = False
) -> tuple[NexStageServer, int]:
    port = start_port
    while port < start_port + 10 and not port_available(host, port):
        port += 1
    if port >= start_port + 10:
        raise OSError(
            f"Nenhuma porta livre encontrada entre {start_port} e {start_port + 9}."
        )
    instance = NexStageServer((host, port), NexStageHandler)
    instance.quiet = quiet
    public_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    instance.base_url = f"http://{public_host}:{port}"
    return instance, port


def main() -> None:
    parser = argparse.ArgumentParser(description="NexStage local church presenter")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4310)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    try:
        server, port = create_server(args.host, args.port, args.quiet)
    except OSError as exc:
        raise SystemExit(str(exc)) from exc
    url = server.base_url + "/"
    print(f"\n{APP_NAME} {APP_VERSION} aberto em {url}")
    print(f"Saída OBS: {url}obs")
    print("Pressione Ctrl+C para encerrar.\n")

    if not args.no_browser:
        threading.Timer(0.55, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\nNexStage encerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
