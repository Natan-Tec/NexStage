#!/usr/bin/env python3
"""NexStage launcher for macOS and Linux (compiled app, no terminal window).

* One instance only: opening it again just reopens the controller.
* Tray icon (Linux) / menu bar icon (macOS) when the system supports it.
  Without one, NexStage keeps running in the background; stop it with
  ``NexStage --stop``.
* Data lives outside the app folder, so updating or moving the app keeps it:
  macOS  ~/Library/Application Support/NexStage
  Linux  ~/.local/share/NexStage   (or $XDG_DATA_HOME/NexStage)
  Set NEXSTAGE_HOME to choose another folder.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Any

try:  # POSIX only; the module stays importable on Windows for the test suite.
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

APP_NAME = "NexStage"


def data_home() -> Path:
    configured = os.environ.get("NEXSTAGE_HOME", "").strip()
    if configured:
        return Path(configured).expanduser()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_DATA_HOME", "").strip() or str(Path.home() / ".local" / "share")
    return Path(base) / APP_NAME


def bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)).resolve()


def runtime_file() -> Path:
    return data_home() / "data" / "runtime.json"


def stop_file() -> Path:
    return data_home() / "data" / "stop.request"


def lock_file() -> Path:
    return data_home() / "data" / "instance.lock"


def show_message(title: str, message: str, error: bool = False) -> None:
    """Small native dialog; falls back to stderr when nothing is available."""
    try:
        if sys.platform == "darwin" and shutil.which("osascript"):
            script = [
                "on run argv",
                "display dialog (item 1 of argv) with title (item 2 of argv) "
                f'buttons {{"OK"}} default button "OK" with icon {"stop" if error else "note"}',
                "end run",
            ]
            args = ["osascript"] + [part for line in script for part in ("-e", line)]
            subprocess.run(args + [message, title], check=False, timeout=120)
            return
        for tool, command in (
            ("zenity", ["zenity", "--error" if error else "--info", "--title", title, "--text", message]),
            ("kdialog", ["kdialog", "--title", title, "--error" if error else "--msgbox", message]),
        ):
            if shutil.which(tool) and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
                subprocess.run(command, check=False, timeout=120)
                return
    except (OSError, subprocess.SubprocessError):
        pass
    print(f"{title}: {message}", file=sys.stderr if error else sys.stdout)


class SingleInstance:
    def __init__(self, path: Path) -> None:
        self.file: Any = None
        self.already_running = False
        if fcntl is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        self.file = open(path, "a+")  # noqa: SIM115 - kept open for the whole run
        try:
            fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.already_running = True

    def close(self) -> None:
        if self.file is not None:
            try:
                if not self.already_running and fcntl is not None:
                    fcntl.flock(self.file, fcntl.LOCK_UN)
            finally:
                self.file.close()
                self.file = None


def read_runtime() -> dict[str, Any]:
    try:
        data = json.loads(runtime_file().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, OSError, ValueError):
        return {}


def probe_existing_controller() -> str:
    """Find the controller written by the first instance, with a safe fallback."""
    for _ in range(20):
        try:
            port = int(read_runtime().get("port", 0))
            if 4310 <= port <= 4319:
                return f"http://127.0.0.1:{port}/"
        except (TypeError, ValueError):
            pass
        time.sleep(0.15)
    return "http://127.0.0.1:4310/"


def open_url(url: str) -> None:
    try:
        opened = webbrowser.open(url, new=2)
    except webbrowser.Error:
        opened = False
    if not opened:
        show_message(
            APP_NAME,
            f"Não foi possível abrir o navegador. Abra este endereço manualmente:\n\n{url}",
            error=True,
        )


def copy_text(text: str) -> bool:
    commands = (
        [["pbcopy"]]
        if sys.platform == "darwin"
        else [["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]
    )
    for command in commands:
        if shutil.which(command[0]):
            try:
                subprocess.run(command, input=text.encode("utf-8"), check=True, timeout=5)
                return True
            except (OSError, subprocess.SubprocessError):
                continue
    return False


def open_folder(path: Path) -> None:
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    try:
        subprocess.Popen([opener, str(path)], close_fds=True)
    except OSError:
        show_message(APP_NAME, f"Não foi possível abrir a pasta:\n\n{path}", error=True)


def write_runtime(path: Path, port: int, version: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(
            {"name": APP_NAME, "version": version, "port": port, "pid": os.getpid()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary.replace(path)


def stop_running_instance() -> int:
    """`NexStage --stop`: ask the running instance to quit."""
    runtime = read_runtime()
    pid = runtime.get("pid")
    if not pid:
        print("O NexStage não está em execução.")
        return 0
    stop_file().parent.mkdir(parents=True, exist_ok=True)
    stop_file().write_text("stop", encoding="utf-8")
    try:
        os.kill(int(pid), signal.SIGTERM)
    except (OSError, ValueError, AttributeError):
        pass
    for _ in range(40):
        if not runtime_file().exists():
            print("NexStage encerrado.")
            return 0
        time.sleep(0.15)
    print("O NexStage não respondeu ao pedido para encerrar.", file=sys.stderr)
    return 1


def check_tray() -> int:
    """`NexStage --check-tray`: confirm the tray components are inside the app (used when building)."""
    try:
        import pystray
        from PIL import Image

        icon_path = bundle_root() / "web" / "favicon.ico"
        Image.open(icon_path).load()
        print(f"tray: ok ({pystray.Icon.__module__})")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"tray: indisponível ({type(exc).__name__}: {exc})")
        return 1


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=APP_NAME, description="NexStage para macOS e Linux")
    parser.add_argument("--no-browser", action="store_true", help="não abrir o navegador ao iniciar")
    parser.add_argument("--stop", action="store_true", help="encerrar o NexStage que está em execução")
    parser.add_argument("--version", action="store_true", help="mostrar a versão")
    parser.add_argument("--check-tray", action="store_true", help="verificar os componentes da bandeja")
    args, _unknown = parser.parse_known_args(argv)  # macOS may add -psn_* arguments

    # Data must be configured before the server module reads it.
    os.environ["NEXSTAGE_HOME"] = str(data_home())

    if args.check_tray:
        return check_tray()
    if args.stop:
        return stop_running_instance()
    if args.version:
        import server as nexstage_server

        print(f"{APP_NAME} {nexstage_server.APP_VERSION}")
        return 0

    try:
        instance = SingleInstance(lock_file())
    except OSError as exc:
        show_message(APP_NAME, f"Não foi possível acessar a pasta de dados:\n{data_home()}\n\n{exc}", error=True)
        return 1

    if instance.already_running:
        if not args.no_browser:
            open_url(probe_existing_controller())
        instance.close()
        return 0

    server_instance = None
    server_thread = None
    tray_icon: Any = None
    stop_event = threading.Event()
    runtime = runtime_file()
    try:
        try:
            import server as nexstage_server
        except (OSError, PermissionError) as exc:
            raise RuntimeError(f"O NexStage não conseguiu acessar a pasta de dados:\n{data_home()}") from exc
        if not (nexstage_server.WEB_DIR / "index.html").is_file():
            raise RuntimeError("Os arquivos da interface não foram encontrados. Baixe o NexStage novamente.")
        try:
            server_instance, port = nexstage_server.create_server(quiet=True)
        except OSError as exc:
            raise RuntimeError(
                "As portas 4310 a 4319 estão ocupadas. "
                "Feche o outro programa que está usando essas portas e tente novamente."
            ) from exc

        base_url = f"http://127.0.0.1:{port}"
        stop_file().unlink(missing_ok=True)
        write_runtime(runtime, port, nexstage_server.APP_VERSION)
        server_thread = threading.Thread(
            target=server_instance.serve_forever,
            kwargs={"poll_interval": 0.25},
            name="NexStageServer",
            daemon=True,
        )
        server_thread.start()

        def request_stop(*_args: Any) -> None:
            stop_event.set()
            if tray_icon is not None:
                try:
                    tray_icon.stop()
                except Exception:  # noqa: BLE001 - leaving anyway
                    pass

        for name in ("SIGTERM", "SIGINT", "SIGHUP"):
            if hasattr(signal, name):
                try:
                    signal.signal(getattr(signal, name), request_stop)
                except (ValueError, OSError):
                    pass

        def watch_stop_request() -> None:  # a native event loop may not run Python signal handlers
            while not stop_event.wait(0.4):
                if stop_file().exists():
                    request_stop()
                    return

        threading.Thread(target=watch_stop_request, name="NexStageStopWatch", daemon=True).start()

        def open_controller(_icon: Any = None, _item: Any = None) -> None:
            open_url(base_url + "/")

        def open_output(_icon: Any = None, _item: Any = None) -> None:
            open_url(base_url + "/output")

        def copy_obs(icon: Any = None, _item: Any = None) -> None:
            if copy_text(base_url + "/obs"):
                try:
                    if icon:
                        icon.notify("Endereço do OBS copiado.", APP_NAME)
                except Exception:  # noqa: BLE001 - notifications are optional
                    pass
            else:
                show_message(APP_NAME, f"Endereço do OBS:\n\n{base_url}/obs")

        def open_data(_icon: Any = None, _item: Any = None) -> None:
            open_folder(nexstage_server.DATA_DIR)

        def quit_app(_icon: Any = None, _item: Any = None) -> None:
            request_stop()

        try:
            import pystray
            from PIL import Image

            icon_path = bundle_root() / "web" / "favicon.ico"
            menu = pystray.Menu(
                pystray.MenuItem("Abrir controlador", open_controller, default=True),
                pystray.MenuItem("Abrir telão", open_output),
                pystray.MenuItem("Copiar endereço do OBS", copy_obs),
                pystray.MenuItem("Abrir pasta dos dados", open_data),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Encerrar NexStage", quit_app),
            )
            tray_icon = pystray.Icon(APP_NAME, Image.open(icon_path), f"{APP_NAME} {nexstage_server.APP_VERSION}", menu)
        except Exception:  # noqa: BLE001 - no tray support: keep running without it
            tray_icon = None

        if not args.no_browser:
            opener = threading.Timer(0.65, open_controller)
            opener.daemon = True
            opener.start()

        if tray_icon is not None:
            try:
                tray_icon.run()  # blocks until "Encerrar NexStage" or --stop
            except Exception:  # noqa: BLE001 - tray failed at runtime: continue without it
                tray_icon = None
        while not stop_event.wait(0.5):
            pass
    except Exception as exc:  # last user-facing startup boundary
        show_message(f"{APP_NAME} não iniciou", str(exc), error=True)
        return 1
    finally:
        if server_instance is not None and server_thread is not None:
            server_instance.shutdown()
            server_instance.server_close()
        elif server_instance is not None:
            server_instance.server_close()
        if server_thread is not None:
            server_thread.join(timeout=3)
        runtime.unlink(missing_ok=True)
        stop_file().unlink(missing_ok=True)
        instance.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
