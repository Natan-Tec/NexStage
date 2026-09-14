#!/usr/bin/env python3
"""Native Windows launcher for the installed NexStage application."""

from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any


APP_NAME = "NexStage"
APP_VERSION = "0.4.2"
MUTEX_NAME = "Local\\NexStage_NatanGabriel"
ERROR_ALREADY_EXISTS = 183
WM_ICON_INFORMATION = 0x40


def install_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)).resolve()


def runtime_file() -> Path:
    return install_root() / "data" / "runtime.json"


def show_message(title: str, message: str, error: bool = False) -> None:
    if sys.platform == "win32":
        flags = 0x10 if error else WM_ICON_INFORMATION
        ctypes.windll.user32.MessageBoxW(None, message, title, flags)
    else:  # Useful when validating the source tree outside Windows.
        print(f"{title}: {message}", file=sys.stderr if error else sys.stdout)


class SingleInstance:
    def __init__(self, name: str) -> None:
        self.handle: Any = None
        self.already_running = False
        if sys.platform != "win32":
            return
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.SetLastError(0)
        self.handle = kernel32.CreateMutexW(None, False, name)
        if not self.handle:
            raise OSError("O Windows não conseguiu criar o controle de instância única.")
        self.already_running = kernel32.GetLastError() == ERROR_ALREADY_EXISTS

    def close(self) -> None:
        if self.handle and sys.platform == "win32":
            ctypes.windll.kernel32.CloseHandle(self.handle)
            self.handle = None


def probe_existing_controller() -> str:
    """Find the controller written by the first instance, with a safe fallback."""
    for _ in range(20):
        try:
            data = json.loads(runtime_file().read_text(encoding="utf-8"))
            port = int(data.get("port", 0))
            if 4310 <= port <= 4319:
                return f"http://127.0.0.1:{port}/"
        except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
            pass
        time.sleep(0.1)
    for port in range(4310, 4320):
        url = f"http://127.0.0.1:{port}/api/about"
        try:
            with urllib.request.urlopen(url, timeout=0.2) as response:
                data = json.loads(response.read(64 * 1024).decode("utf-8"))
            if data.get("name") == APP_NAME:
                return f"http://127.0.0.1:{port}/"
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            continue
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


def copy_windows_text(text: str) -> None:
    """Copy Unicode text with the Windows API, without an extra dependency."""
    if sys.platform != "win32":
        raise OSError("Área de transferência indisponível.")
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    if not user32.OpenClipboard(None):
        raise OSError("A área de transferência está ocupada.")
    handle = None
    try:
        user32.EmptyClipboard()
        encoded = text.encode("utf-16-le") + b"\x00\x00"
        handle = kernel32.GlobalAlloc(0x0002, len(encoded))
        if not handle:
            raise OSError("Não foi possível reservar a área de transferência.")
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            raise OSError("Não foi possível acessar a área de transferência.")
        ctypes.memmove(pointer, encoded, len(encoded))
        kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(13, handle):
            raise OSError("Não foi possível copiar o endereço.")
        handle = None  # Ownership belongs to Windows after SetClipboardData.
    finally:
        user32.CloseClipboard()
        if handle:
            kernel32.GlobalFree(handle)


def write_runtime(path: Path, port: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(
            {"name": APP_NAME, "version": APP_VERSION, "port": port, "pid": os.getpid()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary.replace(path)


def launch_installer(path: Path) -> None:
    try:
        subprocess.Popen(
            [str(path), "/SP-", "/CLOSEAPPLICATIONS"],
            cwd=str(path.parent),
            close_fds=True,
        )
    except OSError as exc:
        show_message(
            "Atualização do NexStage",
            f"O instalador foi baixado, mas o Windows não conseguiu abri-lo.\n\n{path}\n\n{exc}",
            error=True,
        )


def run() -> int:
    if sys.platform != "win32":
        show_message(APP_NAME, "Este launcher compilado é exclusivo para Windows.", error=True)
        return 1

    try:
        instance = SingleInstance(MUTEX_NAME)
    except OSError as exc:
        show_message(APP_NAME, str(exc), error=True)
        return 1

    if instance.already_running:
        open_url(probe_existing_controller())
        instance.close()
        return 0

    server_instance = None
    server_thread = None
    tray_icon = None
    pending_installer: dict[str, Path | None] = {"path": None}
    runtime = runtime_file()
    try:
        try:
            import server as nexstage_server
        except (OSError, PermissionError) as exc:
            raise RuntimeError(
                "O NexStage não conseguiu acessar a pasta de dados. "
                "Verifique as permissões de C:\\NexStage."
            ) from exc

        required = nexstage_server.WEB_DIR / "index.html"
        if not required.is_file():
            raise RuntimeError(
                "Os arquivos da interface não foram encontrados. Reinstale o NexStage."
            )

        try:
            server_instance, port = nexstage_server.create_server(quiet=True)
        except OSError as exc:
            raise RuntimeError(
                "As portas 4310 a 4319 estão ocupadas. "
                "Feche o outro programa que está usando essas portas e tente novamente."
            ) from exc

        base_url = f"http://127.0.0.1:{port}"
        write_runtime(runtime, port)
        server_thread = threading.Thread(
            target=server_instance.serve_forever,
            kwargs={"poll_interval": 0.25},
            name="NexStageServer",
            daemon=True,
        )
        server_thread.start()

        try:
            import pystray
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "Os componentes da bandeja não foram encontrados. Reinstale o NexStage."
            ) from exc

        icon_path = bundle_root() / "web" / "favicon.ico"
        if not icon_path.is_file():
            raise RuntimeError("O ícone oficial do NexStage não foi encontrado.")
        image = Image.open(icon_path)

        def open_controller(_icon: Any = None, _item: Any = None) -> None:
            open_url(base_url + "/")

        def open_output(_icon: Any = None, _item: Any = None) -> None:
            open_url(base_url + "/output")

        def copy_obs(icon: Any = None, _item: Any = None) -> None:
            try:
                copy_windows_text(base_url + "/obs")
                if icon:
                    icon.notify("Endereço do OBS copiado.", APP_NAME)
            except OSError as exc:
                show_message(APP_NAME, str(exc), error=True)

        def open_data(_icon: Any = None, _item: Any = None) -> None:
            try:
                os.startfile(str(nexstage_server.DATA_DIR))
            except OSError:
                show_message(APP_NAME, "O Windows não conseguiu abrir a pasta dos dados.", True)

        def stop_app(icon: Any = None, _item: Any = None) -> None:
            if icon:
                icon.stop()

        menu = pystray.Menu(
            pystray.MenuItem("Abrir controlador", open_controller, default=True),
            pystray.MenuItem("Abrir telão", open_output),
            pystray.MenuItem("Copiar endereço do OBS", copy_obs),
            pystray.MenuItem("Abrir pasta dos dados", open_data),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Encerrar NexStage", stop_app),
        )
        tray_icon = pystray.Icon(APP_NAME, image, f"{APP_NAME} {APP_VERSION}", menu)

        def request_update(installer: Path) -> None:
            pending_installer["path"] = installer
            tray_icon.stop()

        nexstage_server.set_update_install_callback(request_update)
        opener = threading.Timer(0.65, open_controller)
        opener.daemon = True
        opener.start()
        tray_icon.run()
    except Exception as exc:  # This is the last user-facing startup boundary.
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
        instance.close()

    if pending_installer["path"] is not None:
        launch_installer(pending_installer["path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
