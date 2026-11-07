"""YouTube support for NexStage.

Goals (church PC with a GT 730 graphics card):

* Always H.264 + AAC in MP4, capped at 30 fps and at most 1080p, because that
  is what old graphics cards decode in hardware. VP9/AV1 are never used.
* Hybrid playback. When a video is added it is downloaded in the background.
  If the operator projects it before the download finishes, the video starts
  right away as a direct stream (the H.264 and AAC tracks are copied, not
  re-encoded, by ffmpeg). Once the file exists it is played from disk.
* The operator never decodes video: the controller only sends commands
  (play, position, volume, resolution) and the projection page plays.

The tools are external programs (yt-dlp, ffmpeg, a JavaScript runtime that
yt-dlp needs for YouTube). ffmpeg ships inside the app; yt-dlp and the
JavaScript runtime are downloaded from GitHub on first use so they can be
updated without a new NexStage release.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Callable

HEIGHTS = (360, 480, 720, 1080)
DEFAULT_HEIGHT = 720
DEFAULT_MAX_FPS = 30
MAX_HEIGHT = 1080
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)  # never flash a console window on Windows
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
YTDLP_RELEASES = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/"
DENO_RELEASES = "https://github.com/denoland/deno/releases/latest/download/"
URL_CACHE_SECONDS = 15 * 60


class YouTubeError(Exception):
    """An error whose message is safe and useful to show to the operator."""


# ----------------------------------------------------------------- parsing


def parse_video_id(text: Any) -> str | None:
    """Accept a full link, a short link, a Shorts/embed link or the 11 character code."""
    tokens = str(text or "").strip().split()
    if not tokens:
        return None
    token = tokens[0].strip("<>\"'()[]")
    if VIDEO_ID.fullmatch(token):
        return token
    try:
        parsed = urllib.parse.urlparse(token if "://" in token else "https://" + token)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    for prefix in ("www.", "m.", "music."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    parts = [part for part in parsed.path.split("/") if part]
    candidate = ""
    if host in {"youtube.com", "youtube-nocookie.com"}:
        if parts and parts[0] == "watch":
            candidate = urllib.parse.parse_qs(parsed.query).get("v", [""])[0]
        elif len(parts) >= 2 and parts[0] in {"shorts", "embed", "live", "v"}:
            candidate = parts[1]
    elif host == "youtu.be" and parts:
        candidate = parts[0]
    return candidate if VIDEO_ID.fullmatch(candidate) else None


def format_selector(height: int, max_fps: int = DEFAULT_MAX_FPS, strict: bool = False) -> str:
    """yt-dlp format selector that prefers H.264 video and AAC audio.

    ``strict`` is used for direct streaming, where nothing is re-encoded, so
    only H.264 is acceptable. For downloads the last options accept any codec
    and the file is converted to H.264 afterwards.
    """
    h = max(144, min(int(height), MAX_HEIGHT))
    f = max(10, int(max_fps))
    video = f"bv*[vcodec^=avc1][height<={h}]"
    audio = "ba[acodec^=mp4a]/ba"
    options = [f"{video}[fps<={f}]+{audio}", f"{video}+{audio}", f"b[vcodec^=avc1][height<={h}]"]
    if not strict:
        options += [f"bv*[height<={h}]+ba", f"b[height<={h}]", "b"]
    return "/".join(options)


def friendly_error(output: str) -> str:
    text = output or ""
    lowered = text.lower()
    rules = (
        ("sign in to confirm", "O YouTube pediu confirmação de que não é um robô. Tente de novo mais tarde ou atualize os componentes."),
        ("private video", "Este vídeo é privado."),
        ("video unavailable", "Vídeo indisponível."),
        ("this video is not available", "Vídeo indisponível neste país ou removido."),
        ("members-only", "Vídeo exclusivo para membros do canal."),
        ("confirm your age", "Vídeo com restrição de idade: não dá para baixar sem login."),
        ("live event will begin", "Esta transmissão ao vivo ainda não começou."),
        ("is a live", "Transmissões ao vivo não são suportadas; use um vídeo gravado."),
        ("unable to download", "Não foi possível acessar o YouTube. Confira a internet."),
        ("getaddrinfo", "Sem internet para acessar o YouTube."),
        ("timed out", "O YouTube demorou demais para responder. Confira a internet."),
        ("http error 403", "O YouTube recusou o download (erro 403). Atualize os componentes do YouTube."),
        ("no such option", "Os componentes do YouTube estão desatualizados. Atualize-os."),
    )
    for needle, message in rules:
        if needle in lowered and message:
            return message
    lines = [line.strip() for line in text.splitlines() if "error" in line.lower()]
    detail = (lines[-1] if lines else text.strip().splitlines()[-1] if text.strip() else "erro desconhecido")
    detail = re.sub(r"^\s*ERROR:\s*(\[[^\]]+\]\s*)?", "", detail)[:220]
    return f"Falha ao consultar o YouTube: {detail}"


# ------------------------------------------------------------------- tools


def _machine() -> str:
    machine = platform.machine().lower()
    return "arm64" if machine in {"arm64", "aarch64"} else "x64"


def ytdlp_asset() -> str:
    if os.name == "nt":
        return "yt-dlp.exe"
    if sys.platform == "darwin":
        return "yt-dlp_macos"
    return "yt-dlp_linux_aarch64" if _machine() == "arm64" else "yt-dlp_linux"


def deno_asset() -> str:
    arm = _machine() == "arm64"
    if os.name == "nt":
        return "deno-x86_64-pc-windows-msvc.zip"
    if sys.platform == "darwin":
        return "deno-aarch64-apple-darwin.zip" if arm else "deno-x86_64-apple-darwin.zip"
    return "deno-aarch64-unknown-linux-gnu.zip" if arm else "deno-x86_64-unknown-linux-gnu.zip"


def download_file(url: str, destination: Path, progress: Callable[[float], None] | None = None) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response, temporary.open("wb") as output:
            total = int(response.headers.get("Content-Length") or 0)
            done = 0
            while True:
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                output.write(chunk)
                done += len(chunk)
                if progress and total:
                    progress(min(1.0, done / total))
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def run_capture(command: list[str], timeout: float = 90) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command, capture_output=True, timeout=timeout, creationflags=NO_WINDOW,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired as exc:
        return 124, "", "timed out"
    except OSError as exc:
        return 127, "", str(exc)
    return (
        completed.returncode,
        completed.stdout.decode("utf-8", "replace"),
        completed.stderr.decode("utf-8", "replace"),
    )


class YouTubeTools:
    """Locates (and downloads) yt-dlp, ffmpeg and a JavaScript runtime."""

    def __init__(self, tools_dir: Path) -> None:
        self.tools_dir = tools_dir
        self.lock = threading.RLock()
        self.progress: dict[str, Any] = {"state": "idle", "step": "", "percent": 0, "message": ""}
        self.on_ready: Callable[[], None] | None = None
        self._no_js_flag = False

    # -- locating
    def _local(self, name: str) -> Path | None:
        candidate = self.tools_dir / (name + (".exe" if os.name == "nt" else ""))
        return candidate if candidate.is_file() else None

    def ytdlp_path(self) -> str | None:
        local = self._local("yt-dlp")
        if local:
            return str(local)
        return shutil.which("yt-dlp")

    def ffmpeg_path(self) -> str | None:
        try:
            import imageio_ffmpeg  # type: ignore[import-not-found]

            exe = imageio_ffmpeg.get_ffmpeg_exe()
            if exe and Path(exe).is_file():
                return str(exe)
        except Exception:  # noqa: BLE001 - optional bundled copy
            pass
        local = self._local("ffmpeg")
        if local:
            return str(local)
        return shutil.which("ffmpeg")

    def js_runtime(self) -> tuple[str, str] | None:
        """(name, path) of a JavaScript runtime that yt-dlp understands."""
        local = self._local("deno")
        if local:
            return "deno", str(local)
        for name in ("deno", "node", "bun"):
            found = shutil.which(name)
            if found:
                return name, found
        return None

    def ready(self) -> bool:
        return bool(self.ytdlp_path() and self.ffmpeg_path())

    def status(self) -> dict[str, Any]:
        runtime = self.js_runtime()
        with self.lock:
            progress = dict(self.progress)
        return {
            "ytdlp": bool(self.ytdlp_path()),
            "ffmpeg": bool(self.ffmpeg_path()),
            "jsRuntime": runtime[0] if runtime else "",
            "ready": self.ready(),
            "install": progress,
        }

    # -- running yt-dlp
    def ytdlp_command(self, args: list[str]) -> list[str]:
        ytdlp = self.ytdlp_path()
        if not ytdlp:
            raise YouTubeError("Os componentes do YouTube ainda não foram instalados.")
        command = [
            ytdlp, "--ignore-config", "--no-playlist", "--no-colors", "--no-cache-dir",
            "--socket-timeout", "20", "--retries", "5", "--fragment-retries", "5",
        ]
        ffmpeg = self.ffmpeg_path()
        if ffmpeg:
            command += ["--ffmpeg-location", ffmpeg]
        runtime = self.js_runtime()
        if runtime and not self._no_js_flag:
            command += ["--js-runtimes", f"{runtime[0]}:{runtime[1]}"]
        return command + args

    def query(self, args: list[str], timeout: float = 120) -> str:
        """Run yt-dlp and return stdout; raises YouTubeError with a readable message."""
        for attempt in (1, 2):
            code, out, err = run_capture(self.ytdlp_command(args), timeout)
            if code != 0 and "no such option: --js-runtimes" in err and not self._no_js_flag:
                self._no_js_flag = True  # an older yt-dlp: retry without the flag
                continue
            break
        if code != 0:
            raise YouTubeError(friendly_error(err or out))
        return out

    # -- installing
    def _set(self, **values: Any) -> None:
        with self.lock:
            self.progress.update(values)

    def install_async(self, update: bool = False) -> bool:
        with self.lock:
            if self.progress.get("state") == "running":
                return False
            self.progress = {"state": "running", "step": "yt-dlp", "percent": 0, "message": "Preparando…"}
        threading.Thread(target=self._install, args=(update,), name="NexStageYouTubeTools", daemon=True).start()
        return True

    def _install(self, update: bool) -> None:
        try:
            self.tools_dir.mkdir(parents=True, exist_ok=True)
            target = self.tools_dir / ("yt-dlp.exe" if os.name == "nt" else "yt-dlp")
            if update and target.is_file():
                self._set(step="yt-dlp", percent=5, message="Atualizando o yt-dlp…")
                code, out, err = run_capture([str(target), "-U"], 180)
                if code != 0:
                    self._set(message="Baixando o yt-dlp novamente…")
                    download_file(YTDLP_RELEASES + ytdlp_asset(), target, lambda p: self._set(percent=int(5 + p * 55)))
            else:
                self._set(step="yt-dlp", percent=1, message="Baixando o yt-dlp…")
                download_file(YTDLP_RELEASES + ytdlp_asset(), target, lambda p: self._set(percent=int(1 + p * 59)))
            if os.name != "nt":
                target.chmod(0o755)
            code, out, err = run_capture([str(target), "--version"], 60)
            if code != 0:
                target.unlink(missing_ok=True)
                raise YouTubeError("O yt-dlp baixado não abriu neste computador.")

            if not self._local("deno") and not any(shutil.which(n) for n in ("deno", "node", "bun")):
                self._set(step="Runtime JavaScript", percent=62, message="Baixando o componente JavaScript…")
                archive = self.tools_dir / "deno.zip"
                try:
                    download_file(DENO_RELEASES + deno_asset(), archive, lambda p: self._set(percent=int(62 + p * 33)))
                    with zipfile.ZipFile(archive) as bundle:
                        name = "deno.exe" if os.name == "nt" else "deno"
                        bundle.extract(name, self.tools_dir)
                    if os.name != "nt":
                        (self.tools_dir / "deno").chmod(0o755)
                    code, out, err = run_capture([str(self.tools_dir / ("deno.exe" if os.name == "nt" else "deno")), "--version"], 60)
                    if code != 0:
                        (self._local("deno") or Path(os.devnull)).unlink(missing_ok=True)
                except (OSError, urllib.error.URLError, zipfile.BadZipFile, KeyError):
                    # Optional: some videos still work without it.
                    pass
                finally:
                    archive.unlink(missing_ok=True)
            if not self.ffmpeg_path():
                raise YouTubeError("O ffmpeg não foi encontrado. Reinstale o NexStage ou instale o ffmpeg no sistema.")
            self._set(state="done", step="", percent=100, message="Componentes do YouTube prontos.")
            if self.on_ready:
                self.on_ready()
        except (YouTubeError, OSError, urllib.error.URLError) as exc:
            message = str(exc) if isinstance(exc, YouTubeError) else (
                "Não foi possível baixar os componentes. Confira a internet e tente de novo."
            )
            self._set(state="error", message=message)


# ----------------------------------------------------------------- library


def probe_video(ffmpeg: str, path: Path) -> dict[str, Any]:
    """Codec and frame rate of the first video stream, read from `ffmpeg -i`."""
    code, out, err = run_capture([ffmpeg, "-hide_banner", "-i", str(path)], 60)
    text = err + out
    match = re.search(r"Video:\s*([A-Za-z0-9_]+)", text)
    fps = re.search(r"(\d+(?:\.\d+)?)\s*fps", text)
    return {"codec": match.group(1).lower() if match else "", "fps": float(fps.group(1)) if fps else 0.0}


LOCAL_SUFFIXES = {".mp4", ".m4v", ".mov", ".webm", ".mkv", ".avi", ".wmv", ".flv", ".mpg", ".mpeg", ".ts", ".m2ts", ".3gp"}
BROWSER_AUDIO = {"aac", "mp3"}


def probe_media(ffmpeg: str, path: Path) -> dict[str, Any]:
    """Duration, resolution, frame rate and codecs of a local file, read from `ffmpeg -i`."""
    code, out, err = run_capture([ffmpeg, "-hide_banner", "-i", str(path)], 90)
    text = err + out
    video = re.search(r"Video:\s*([A-Za-z0-9_]+)", text)
    audio = re.search(r"Audio:\s*([A-Za-z0-9_]+)", text)
    size = re.search(r",\s*(\d{2,5})x(\d{2,5})[\s,\[]", text)
    fps = re.search(r"(\d+(?:\.\d+)?)\s*fps", text)
    duration = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    seconds = 0.0
    if duration:
        seconds = int(duration.group(1)) * 3600 + int(duration.group(2)) * 60 + float(duration.group(3))
    return {
        "vcodec": video.group(1).lower() if video else "", "acodec": audio.group(1).lower() if audio else "",
        "width": int(size.group(1)) if size else 0, "height": int(size.group(2)) if size else 0,
        "fps": float(fps.group(1)) if fps else 0.0, "duration": seconds,
    }


class YouTubeLibrary:
    """Videos added by the operator, their files and the background downloads."""

    def __init__(
        self,
        root: Path,
        tools: YouTubeTools,
        get_settings: Callable[[], dict[str, Any]],
    ) -> None:
        self.root = root
        self.files_dir = root / "youtube"
        self.index_path = root / "youtube.json"
        self.tools = tools
        self.get_settings = get_settings
        self.lock = threading.RLock()
        self.wake = threading.Condition(self.lock)
        self.items: dict[str, dict[str, Any]] = {}
        self.jobs: dict[tuple[str, int], dict[str, Any]] = {}
        self.queue: list[tuple[str, int]] = []
        self.url_cache: dict[tuple[str, int], tuple[float, list[str]]] = {}
        self.url_locks: dict[tuple[str, int], threading.Lock] = {}
        self.worker: threading.Thread | None = None
        self._load()
        tools.on_ready = self.resume_pending

    # -- persistence
    def _load(self) -> None:
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
            for item in data.get("items", []):
                if VIDEO_ID.fullmatch(str(item.get("id", ""))):
                    if item.get("kind") == "local" and item.get("info") == "pending":
                        item.update({"info": "error", "error": "O programa foi fechado durante a preparação. Adicione o vídeo de novo."})
                    self.items[item["id"]] = item
        except (FileNotFoundError, OSError, ValueError, AttributeError):
            self.items = {}

    def _save(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.index_path.with_suffix(".json.tmp")
        with self.lock:
            payload = {"items": list(self.items.values())}
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, self.index_path)

    # -- files
    def files(self, video_id: str) -> dict[int, Path]:
        found: dict[int, Path] = {}
        try:
            for path in self.files_dir.glob(f"{video_id}-*.mp4"):
                match = re.fullmatch(re.escape(video_id) + r"-(\d+)\.mp4", path.name)
                if match and path.is_file():
                    found[int(match.group(1))] = path
        except OSError:
            pass
        return found

    def file_for(self, video_id: str, height: int) -> Path | None:
        return self.files(video_id).get(int(height))

    def available_heights(self, video_id: str) -> list[int]:
        item = self.items.get(video_id, {})
        heights = sorted({int(h) for h in item.get("heights", []) if 144 <= int(h) <= MAX_HEIGHT})
        return heights or list(HEIGHTS)

    def pick_height(self, video_id: str, wanted: int) -> int:
        """Largest available height that does not exceed ``wanted`` (or the smallest one)."""
        heights = self.available_heights(video_id)
        below = [h for h in heights if h <= int(wanted)]
        return max(below) if below else min(heights)

    # -- adding
    def add(self, text: str) -> dict[str, Any]:
        video_id = parse_video_id(text)
        if not video_id:
            raise YouTubeError("Não entendi o link. Cole o endereço do vídeo ou só o código de 11 letras.")
        with self.lock:
            existing = self.items.get(video_id)
            if existing:
                if existing.get("info") != "ok":
                    self._start_info(video_id)
                elif self.tools.ready():
                    self.queue_download(video_id, self.pick_height(video_id, self._default_height()))
                return existing
            self.items[video_id] = {
                "id": video_id, "title": video_id, "channel": "", "duration": 0, "heights": [],
                "thumbnail": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
                "addedAt": int(time.time()), "info": "pending", "error": "",
            }
            self._save()
        self._start_info(video_id)
        return self.items[video_id]

    def _default_height(self) -> int:
        try:
            return int(self.get_settings().get("youtube", {}).get("defaultHeight", DEFAULT_HEIGHT))
        except (TypeError, ValueError):
            return DEFAULT_HEIGHT

    def _max_fps(self) -> int:
        try:
            return int(self.get_settings().get("youtube", {}).get("maxFps", DEFAULT_MAX_FPS))
        except (TypeError, ValueError):
            return DEFAULT_MAX_FPS

    def _auto_download(self) -> bool:
        return bool(self.get_settings().get("youtube", {}).get("autoDownload", True))

    def _start_info(self, video_id: str) -> None:
        if not self.tools.ready():
            with self.lock:
                self.items[video_id]["info"] = "needs-tools"
            return
        with self.lock:
            self.items[video_id]["info"] = "pending"
            self.items[video_id]["error"] = ""
        threading.Thread(target=self._fetch_info, args=(video_id,), name="NexStageYouTubeInfo", daemon=True).start()

    def resume_pending(self) -> None:
        """Called when the tools become ready: look up videos that were waiting."""
        for video_id, item in list(self.items.items()):
            if item.get("info") in {"needs-tools", "pending", "error"} and item.get("info") != "ok":
                self._start_info(video_id)

    def _fetch_info(self, video_id: str) -> None:
        try:
            raw = self.tools.query(["-J", "--skip-download", f"https://www.youtube.com/watch?v={video_id}"], 150)
            data = json.loads(raw)
            heights = sorted({
                int(f["height"]) for f in data.get("formats", [])
                if str(f.get("vcodec", "")).startswith("avc1") and f.get("height")
                and 144 <= int(f["height"]) <= MAX_HEIGHT
            })
            with self.lock:
                item = self.items.get(video_id)
                if not item:
                    return
                item.update({
                    "title": str(data.get("title") or video_id)[:200],
                    "channel": str(data.get("uploader") or data.get("channel") or "")[:120],
                    "duration": int(data.get("duration") or 0),
                    "heights": heights,
                    "thumbnail": str(data.get("thumbnail") or item.get("thumbnail", "")),
                    "info": "ok", "error": "",
                })
                if data.get("is_live"):
                    item.update({"info": "error", "error": "Transmissões ao vivo não são suportadas; use um vídeo gravado."})
            self._save()
            if self.items.get(video_id, {}).get("info") == "ok" and self._auto_download():
                self.queue_download(video_id, self.pick_height(video_id, self._default_height()))
        except (YouTubeError, ValueError, KeyError) as exc:
            with self.lock:
                if video_id in self.items:
                    self.items[video_id].update({"info": "error", "error": str(exc)})

    # -- local videos (files already on the computer)
    def add_local(self, source: Path, original_name: str) -> dict[str, Any]:
        """Register a copied file and prepare it (H.264/AAC mp4 + thumbnail) in the background."""
        video_id = "L" + uuid.uuid4().hex[:10]
        stem = Path(original_name).stem.replace("_", " ").strip() or "Vídeo"
        item = {
            "id": video_id, "kind": "local", "title": stem[:200], "channel": "", "duration": 0, "heights": [],
            "thumbnail": "", "addedAt": int(time.time()), "info": "pending", "error": "", "note": "Preparando…",
        }
        with self.lock:
            self.items[video_id] = item
        self._save()
        threading.Thread(target=self._process_local, args=(video_id, source), name="NexStageLocalVideo", daemon=True).start()
        return item

    def _fail_local(self, video_id: str, message: str) -> None:
        with self.lock:
            if video_id in self.items:
                self.items[video_id].update({"info": "error", "error": message})
        self._save()

    def _process_local(self, video_id: str, source: Path) -> None:
        workdir = source.parent
        job: dict[str, Any] | None = None
        try:
            ffmpeg = self.tools.ffmpeg_path()
            if not ffmpeg:
                raise YouTubeError("O ffmpeg não foi encontrado. Reinstale o NexStage.")
            info = probe_media(ffmpeg, source)
            if not info["vcodec"] or not info["height"]:
                raise YouTubeError("Este arquivo não parece ser um vídeo válido.")
            target_height = max(144, min(MAX_HEIGHT, info["height"]))
            self.files_dir.mkdir(parents=True, exist_ok=True)
            final = self.files_dir / f"{video_id}-{target_height}.mp4"
            audio_ok = info["acodec"] in BROWSER_AUDIO or not info["acodec"]
            codecs_ok = info["vcodec"] == "h264" and audio_ok and info["height"] <= MAX_HEIGHT
            job = {"state": "running", "percent": 0, "error": "", "cancel": threading.Event()}
            with self.lock:
                self.jobs[(video_id, target_height)] = job
            if codecs_ok and source.suffix.lower() == ".mp4":
                os.replace(source, final)
                note = "H.264 pronto (sem converter)"
            elif codecs_ok:
                self._run_ffmpeg([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-map", "0:v:0", "-map", "0:a:0?",
                                  "-c", "copy", "-movflags", "+faststart", str(workdir / "out.mp4")], info["duration"], job)
                os.replace(workdir / "out.mp4", final)
                note = "H.264 pronto (só reempacotado)"
            else:
                with self.lock:
                    self.items[video_id]["note"] = "Convertendo para H.264…"
                self._run_ffmpeg([
                    ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-map", "0:v:0", "-map", "0:a:0?",
                    "-vf", f"scale=-2:'min(ih,{MAX_HEIGHT})',format=yuv420p",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-profile:v", "high", "-level", "4.1",
                    "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-movflags", "+faststart", str(workdir / "out.mp4"),
                ], info["duration"], job)
                os.replace(workdir / "out.mp4", final)
                note = "Convertido para H.264"
            thumb = self.files_dir / f"{video_id}-thumb.jpg"
            at = max(0.0, min(5.0, info["duration"] / 3))
            run_capture([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{at:.2f}", "-i", str(final), "-frames:v", "1", "-vf", "scale=320:-2", str(thumb)], 60)
            with self.lock:
                if video_id not in self.items:  # removed while preparing
                    final.unlink(missing_ok=True)
                    thumb.unlink(missing_ok=True)
                    return
                self.items[video_id].update({
                    "duration": int(info["duration"]), "heights": [target_height], "info": "ok", "error": "", "note": note,
                    "thumbnail": f"/youtube/file/{thumb.name}" if thumb.is_file() else "",
                })
                job["state"], job["percent"] = "done", 100
            self._save()
        except YouTubeError as exc:
            self._fail_local(video_id, str(exc))
            if job:
                job["state"], job["error"] = "error", str(exc)
        except Exception as exc:  # noqa: BLE001 - never leave the item pending forever
            self._fail_local(video_id, f"Falha ao preparar o vídeo: {exc}")
            if job:
                job["state"], job["error"] = "error", str(exc)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    @staticmethod
    def _run_ffmpeg(command: list[str], duration: float, job: dict[str, Any]) -> None:
        """Run ffmpeg and map its progress to job['percent'] (0-98)."""
        command = command[:-1] + ["-progress", "pipe:1", "-nostats", command[-1]]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=NO_WINDOW)
        assert process.stdout is not None
        tail: list[str] = []
        for raw in iter(process.stdout.readline, b""):
            line = raw.decode("utf-8", "replace").strip()
            if job["cancel"].is_set():
                process.kill()
                process.wait()
                raise YouTubeError("Cancelado.")
            if line.startswith("out_time_us=") and duration:
                try:
                    job["percent"] = int(max(0, min(98, int(line.split("=")[1]) / 1_000_000 / duration * 98)))
                except ValueError:
                    pass
            elif line and "=" not in line:
                tail.append(line)
                tail = tail[-6:]
        process.wait()
        if process.returncode != 0:
            raise YouTubeError("Não foi possível preparar este vídeo: " + (" ".join(tail)[-160:] or "erro no ffmpeg"))

    # -- downloads
    def queue_download(self, video_id: str, height: int) -> None:
        height = int(height)
        with self.lock:
            if video_id not in self.items or self.file_for(video_id, height):
                return
            key = (video_id, height)
            job = self.jobs.get(key)
            if job and job["state"] in {"queued", "running"}:
                return
            self.jobs[key] = {"state": "queued", "percent": 0, "error": "", "cancel": threading.Event()}
            self.queue.append(key)
            if not self.worker or not self.worker.is_alive():
                self.worker = threading.Thread(target=self._worker, name="NexStageYouTubeDownloads", daemon=True)
                self.worker.start()
            self.wake.notify_all()

    def _worker(self) -> None:
        while True:
            with self.lock:
                while not self.queue:
                    if not self.wake.wait(timeout=60) and not self.queue:
                        self.worker = None
                        return
                key = self.queue.pop(0)
                job = self.jobs.get(key)
                if not job or job["cancel"].is_set():
                    continue
                job["state"] = "running"
            try:
                self._download(key, job)
                job["state"], job["percent"] = "done", 100
            except YouTubeError as exc:
                job["state"], job["error"] = "error", str(exc)
            except Exception as exc:  # noqa: BLE001 - never kill the worker
                job["state"], job["error"] = "error", f"Falha inesperada: {exc}"

    def _download(self, key: tuple[str, int], job: dict[str, Any]) -> None:
        video_id, height = key
        ffmpeg = self.tools.ffmpeg_path()
        if not ffmpeg:
            raise YouTubeError("O ffmpeg não foi encontrado.")
        self.files_dir.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix=f".tmp-{video_id}-", dir=self.files_dir))
        try:
            command = self.tools.ytdlp_command([
                "-f", format_selector(height, self._max_fps()),
                "--merge-output-format", "mp4",
                "--newline", "--progress-template",
                "download:NX|%(progress.downloaded_bytes)s|%(progress.total_bytes)s|%(progress.total_bytes_estimate)s",
                "-o", str(work / "%(id)s.%(ext)s"),
                f"https://www.youtube.com/watch?v={video_id}",
            ])
            tail: list[str] = []
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                creationflags=NO_WINDOW,
            )
            streams_done, last_pct = 0, 0.0
            assert process.stdout is not None
            for raw in iter(process.stdout.readline, b""):
                line = raw.decode("utf-8", "replace").strip()
                if job["cancel"].is_set():
                    process.kill()
                    process.wait()
                    raise YouTubeError("Download cancelado.")
                if line.startswith("NX|"):
                    parts = line.split("|")
                    try:
                        done = float(parts[1])
                        total = float(parts[2]) if parts[2] not in {"NA", "None", ""} else float(parts[3])
                        pct = max(0.0, min(1.0, done / total)) if total else 0.0
                    except (ValueError, IndexError):
                        continue
                    if pct < last_pct - 0.5:
                        streams_done += 1  # a second stream (audio) started
                    last_pct = pct
                    job["percent"] = int(min(95, (min(streams_done, 1) + pct) / 2 * 95))
                elif line:
                    tail.append(line)
                    tail = tail[-12:]
            process.wait()
            if process.returncode != 0:
                if "no such option: --js-runtimes" in "\n".join(tail):
                    self.tools._no_js_flag = True
                raise YouTubeError(friendly_error("\n".join(tail)))
            job["percent"] = 96
            produced = [p for p in work.iterdir() if p.is_file() and p.suffix.lower() not in {".part", ".ytdl", ".temp"}]
            if not produced:
                raise YouTubeError("O download terminou, mas nenhum arquivo foi criado.")
            source = max(produced, key=lambda p: p.stat().st_size)
            final = self.files_dir / f"{video_id}-{height}.mp4"
            info = probe_video(ffmpeg, source)
            if info["codec"] != "h264" or source.suffix.lower() != ".mp4":
                converted = work / "h264.mp4"
                self._to_h264(ffmpeg, source, converted, height, info, job)
                source = converted
            os.replace(source, final)
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def _to_h264(self, ffmpeg: str, source: Path, target: Path, height: int, info: dict[str, Any], job: dict[str, Any]) -> None:
        """Last resort: the video had no H.264 version, so convert it (uses the CPU for a while)."""
        job["percent"] = 97
        filters = [f"scale=-2:'min(ih,{int(height)})'"]
        if info.get("fps", 0) > 30.5:
            filters.append("fps=30")  # a CPU conversion is only needed when there was no H.264 at all
        code, out, err = run_capture([
            ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
            "-vf", ",".join(filters),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-profile:v", "high", "-level", "4.1",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(target),
        ], 3600)
        if code != 0 or not target.is_file():
            raise YouTubeError("Não foi possível converter o vídeo para H.264.")

    # -- streaming
    def stream_urls(self, video_id: str, height: int) -> list[str]:
        key = (video_id, int(height))
        with self.lock:
            lock = self.url_locks.setdefault(key, threading.Lock())
        with lock:
            now = time.time()
            cached = self.url_cache.get(key)
            if cached and now - cached[0] < URL_CACHE_SECONDS:
                return cached[1]
            out = self.tools.query([
                "-g", "-f", format_selector(height, self._max_fps(), strict=True),
                f"https://www.youtube.com/watch?v={video_id}",
            ], 150)
            urls = [line.strip() for line in out.splitlines() if line.strip()]
            if not urls:
                raise YouTubeError("Não há versão H.264 deste vídeo para transmitir direto.")
            self.url_cache[key] = (time.time(), urls)
            return urls

    def prefetch_stream(self, video_id: str, height: int) -> None:
        def run() -> None:
            try:
                self.stream_urls(video_id, height)
            except YouTubeError:
                pass

        threading.Thread(target=run, name="NexStageYouTubePrefetch", daemon=True).start()

    # -- removing / listing
    def remove(self, video_id: str) -> None:
        with self.lock:
            self.items.pop(video_id, None)
            for key, job in list(self.jobs.items()):
                if key[0] == video_id:
                    job["cancel"].set()
                    self.jobs.pop(key, None)
            self.queue = [key for key in self.queue if key[0] != video_id]
        for path in self.files(video_id).values():
            path.unlink(missing_ok=True)
        (self.files_dir / f"{video_id}-thumb.jpg").unlink(missing_ok=True)
        self._save()

    def snapshot(self) -> list[dict[str, Any]]:
        result = []
        with self.lock:
            items = sorted(self.items.values(), key=lambda item: item.get("addedAt", 0), reverse=True)
            for item in items:
                video_id = item["id"]
                files = {str(h): path.stat().st_size for h, path in self.files(video_id).items()}
                jobs = {
                    str(key[1]): {"state": job["state"], "percent": job["percent"], "error": job["error"]}
                    for key, job in self.jobs.items() if key[0] == video_id
                }
                result.append({
                    **{k: item.get(k) for k in ("id", "title", "channel", "duration", "thumbnail", "info", "error")},
                    "kind": item.get("kind", "youtube"), "note": item.get("note", ""),
                    "heights": self.available_heights(video_id),
                    "files": files, "jobs": jobs,
                })
        return result


# ------------------------------------------------------------------ player


def stream_command(ffmpeg: str, urls: list[str], start: float, fast_seek: bool = True) -> list[str]:
    """ffmpeg command that copies H.264/AAC into a fragmented MP4 on stdout (no re-encoding).

    ``fast_seek`` jumps straight to ``start`` using the stream's index. If that fails the
    caller retries with ``fast_seek=False``, which reads from the beginning (slower, always works).
    """
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin"]
    for url in urls[:2]:
        if url.startswith("http"):
            command += ["-user_agent", USER_AGENT, "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "5"]
        if start > 0.5 and fast_seek:
            command += ["-ss", f"{start:.2f}"]
        command += ["-i", url]
    if start > 0.5 and not fast_seek:
        command += ["-ss", f"{start:.2f}"]
    if len(urls) >= 2:
        command += ["-map", "0:v:0", "-map", "1:a:0?"]
    else:
        command += ["-map", "0:v:0", "-map", "0:a:0?"]
    command += [
        "-c", "copy", "-avoid_negative_ts", "make_zero",
        "-movflags", "frag_keyframe+empty_moov+default_base_moof", "-f", "mp4", "pipe:1",
    ]
    return command


class PlayerController:
    """State of the video playing on the projection. Commands come from the operator."""

    def __init__(self, library: YouTubeLibrary, get_settings: Callable[[], dict[str, Any]]) -> None:
        self.library = library
        self.get_settings = get_settings
        self.lock = threading.RLock()
        volume = 0.8
        try:
            volume = float(get_settings().get("youtube", {}).get("volume", 0.8))
        except (TypeError, ValueError):
            pass
        self.state: dict[str, Any] = {
            "item": "", "title": "", "duration": 0, "mode": "", "src": "", "srcToken": 0, "startAt": 0.0,
            "playing": False, "volume": max(0.0, min(1.0, volume)), "muted": False, "height": 0,
            "seekToken": 0, "seekTo": 0.0, "message": "",
        }
        self.status: dict[str, Any] = self._empty_status()

    @staticmethod
    def _empty_status() -> dict[str, Any]:
        return {
            "srcToken": 0, "t": 0.0, "duration": 0.0, "playing": False, "buffering": False,
            "ended": False, "error": "", "needsGesture": False, "updatedAt": 0.0,
        }

    # -- reading
    def public(self) -> dict[str, Any]:
        with self.lock:
            return {**self.state, "resumeAt": float(self.status.get("t", 0.0)) if self.status.get("srcToken") == self.state["srcToken"] else 0.0}

    def report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Status posted by the projection about 2 times per second."""
        with self.lock:
            self.status = {
                "srcToken": int(payload.get("srcToken", 0)),
                "t": max(0.0, float(payload.get("t", 0) or 0)),
                "duration": max(0.0, float(payload.get("duration", 0) or 0)),
                "playing": bool(payload.get("playing", False)),
                "buffering": bool(payload.get("buffering", False)),
                "ended": bool(payload.get("ended", False)),
                "error": str(payload.get("error", ""))[:200],
                "needsGesture": bool(payload.get("needsGesture", False)),
                "updatedAt": time.time(),
            }
            return self.status

    def current_status(self) -> dict[str, Any]:
        with self.lock:
            fresh = time.time() - float(self.status.get("updatedAt", 0)) < 3.0
            return {
                **self.status, "connected": fresh, "item": self.state["item"],
                "title": self.state["title"], "mode": self.state["mode"], "height": self.state["height"],
                "volume": self.state["volume"], "muted": self.state["muted"],
                "wantPlaying": self.state["playing"], "message": self.state["message"],
                "duration": self.status.get("duration") or self.state["duration"],
            }

    # -- source choice
    def _choose(self, video_id: str, height: int, position: float) -> dict[str, Any]:
        """Local file if it exists, otherwise a direct stream (and start the download)."""
        library = self.library
        height = library.pick_height(video_id, height)
        path = library.file_for(video_id, height)
        if library.items.get(video_id, {}).get("kind") == "local" and not path:
            raise YouTubeError("O arquivo deste vídeo não foi encontrado. Adicione-o de novo.")
        if path:
            return {"mode": "file", "src": f"/youtube/file/{path.name}", "height": height, "message": ""}
        if library.tools.ready():
            library.queue_download(video_id, height)
            library.prefetch_stream(video_id, height)
            src = f"/youtube/stream?id={video_id}&h={height}&t={position:.2f}"
            return {"mode": "stream", "src": src, "height": height, "message": "Transmissão direta (baixando em segundo plano)"}
        others = library.files(video_id)
        if others:
            nearest = min(others, key=lambda h: abs(h - height))
            return {"mode": "file", "src": f"/youtube/file/{others[nearest].name}", "height": nearest, "message": ""}
        raise YouTubeError("Instale os componentes do YouTube para reproduzir este vídeo.")

    def _clamp(self, position: float) -> float:
        duration = float(self.state.get("duration") or 0)
        position = max(0.0, position)
        return min(position, max(0.0, duration - 0.5)) if duration else position

    # -- commands
    def command(self, action: str, payload: dict[str, Any]) -> str:
        """Apply a command. Returns 'show', 'hide' or '' so the caller can update live/blackout."""
        with self.lock:
            state = self.state
            if action == "load":
                video_id = str(payload.get("id", ""))
                item = self.library.items.get(video_id)
                if not item:
                    raise YouTubeError("Vídeo não encontrado na lista.")
                wanted = int(payload.get("height") or self.get_settings().get("youtube", {}).get("defaultHeight", DEFAULT_HEIGHT))
                start = float(payload.get("start") or 0)
                choice = self._choose(video_id, wanted, start)
                state.update({
                    "item": video_id, "title": item.get("title", ""), "duration": item.get("duration", 0),
                    "srcToken": state["srcToken"] + 1, "startAt": start, "playing": True, **choice,
                })
                self.status = self._empty_status()
                return "show"
            if not state["item"] and action not in {"volume", "mute"}:
                raise YouTubeError("Nenhum vídeo carregado.")
            if action in {"play", "pause", "toggle"}:
                state["playing"] = (not state["playing"]) if action == "toggle" else action == "play"
                if self.status.get("ended") and state["playing"]:
                    return self._reload(0.0) or "show"
                return "show" if state["playing"] else ""
            if action == "seek":
                if "delta" in payload:
                    base = float(self.status.get("t", 0.0)) if self.status.get("srcToken") == state["srcToken"] else state["startAt"]
                    target = base + float(payload["delta"])
                else:
                    target = float(payload.get("t", 0))
                target = self._clamp(target)
                if state["mode"] == "stream":
                    return self._reload(target) or "show"
                state["seekToken"] += 1
                state["seekTo"] = target
                self.status["ended"] = False
                return ""
            if action == "volume":
                state["volume"] = max(0.0, min(1.0, float(payload.get("value", 0))))
                state["muted"] = False
                return ""
            if action == "mute":
                state["muted"] = bool(payload.get("value", not state["muted"]))
                return ""
            if action == "quality":
                position = float(self.status.get("t", 0.0)) if self.status.get("srcToken") == state["srcToken"] else state["startAt"]
                return self._reload(position, height=int(payload.get("height", 0))) or ""
            if action == "stop":
                state.update({"item": "", "title": "", "src": "", "mode": "", "playing": False, "message": "", "duration": 0})
                state["srcToken"] += 1
                self.status = self._empty_status()
                return "hide"
        raise YouTubeError("Comando desconhecido.")

    def _reload(self, position: float, height: int = 0) -> str:
        """Re-choose the source (file now ready, new quality, or a stream seek) at ``position``."""
        state = self.state
        choice = self._choose(state["item"], height or state["height"], position)
        state.update({"srcToken": state["srcToken"] + 1, "startAt": position, **choice})
        self.status = self._empty_status()
        return "show" if state["playing"] else ""
