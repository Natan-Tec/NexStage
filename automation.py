"""Automações do NexStage: QUANDO (gatilho) -> SE (condições) -> ENTÃO (passos).

Só dados, nunca código livre. Tudo o que o editor mostra vem do CATÁLOGO abaixo: para criar um bloco
novo basta registrá-lo no catálogo e escrever a função da ação (``@action("tipo")``).
O motor roda numa thread do servidor, então as automações funcionam mesmo com o controlador fechado.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import threading
import time
import urllib.parse
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Callable

MAX_AUTOMATIONS = 100
MAX_STEPS = 60
MAX_NAME = 80
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".m4v"}
DAY_NAMES = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]


class AutomationError(Exception):
    """Erro com mensagem útil para mostrar ao operador (vai para o histórico)."""


class StopRun(Exception):
    """O bloco "Parar automação" foi executado."""


class Cancelled(Exception):
    """O operador cancelou a execução em andamento."""


# ------------------------------------------------------------------ catálogo


def param(key: str, label: str, kind: str, **extra: Any) -> dict[str, Any]:
    return {"key": key, "label": label, "kind": kind, **extra}


DAYS = param("days", "Dias da semana (vazio = todos)", "days", default=[])

TRIGGERS: dict[str, dict[str, Any]] = {
    "time": {"label": "Quando chegar o horário", "params": [param("at", "Horário", "time", default="08:55"), DAYS]},
    "every": {"label": "A cada tantos minutos", "params": [param("minutes", "Minutos", "number", default=30, min=1, max=1440)]},
    "appStart": {"label": "Quando o NexStage abrir", "params": []},
    "manual": {"label": "Só quando eu mandar executar", "params": []},
}

CONDITIONS: dict[str, dict[str, Any]] = {
    "weekday": {"label": "Se o dia da semana for", "params": [param("days", "Dias", "days", default=[1])]},
    "timeBetween": {
        "label": "Se o horário estiver entre",
        "params": [param("start", "De", "time", default="08:00"), param("end", "Até", "time", default="12:00")],
    },
    "isLive": {
        "label": "Se o telão estiver",
        "params": [param("value", "Estado", "select", default="on", options=[["on", "no ar"], ["off", "fora do ar"]])],
    },
}

ACTIONS: dict[str, dict[str, Any]] = {
    # Aparência e fundo
    "background": {"label": "Colocar fundo", "group": "Aparência", "params": [param("media", "Fundo", "media", media="background", default="")]},
    "removeBackground": {"label": "Remover fundo", "group": "Aparência", "params": []},
    "logo": {"label": "Ativar logo", "group": "Aparência", "params": [param("media", "Imagem da logo", "media", media="image", default="")]},
    "removeLogo": {"label": "Desativar logo", "group": "Aparência", "params": []},
    # Conteúdo
    "showClock": {"label": "Exibir relógio", "group": "Conteúdo", "params": []},
    "hideClock": {"label": "Ocultar relógio", "group": "Conteúdo", "params": []},
    "message": {
        "label": "Exibir mensagem", "group": "Conteúdo",
        "params": [
            param("text", "Texto", "text", default="Bem-vindos!"),
            param("seconds", "Por quantos segundos (0 = até limpar)", "number", default=0, min=0, max=3600),
        ],
    },
    # Sistema
    "timerStart": {
        "label": "Iniciar cronômetro", "group": "Sistema",
        "params": [
            param("minutes", "Duração em minutos (0 = usar o que está na aba Cronômetro)", "number", default=0, min=0, max=600),
            param("endTime", "…ou hora de término (vazio = não usar)", "time", default="", optional=True),
        ],
    },
    "timerRestart": {"label": "Reiniciar cronômetro", "group": "Sistema", "params": []},
    "blackOn": {"label": "Tela preta (ligar)", "group": "Sistema", "params": []},
    "blackOff": {"label": "Tela preta (desligar)", "group": "Sistema", "params": []},
    "clearScreen": {"label": "Limpar a tela", "group": "Sistema", "params": []},
    # Controle
    "wait": {"label": "Esperar", "group": "Controle", "params": [param("seconds", "Segundos", "number", default=5, min=0, max=86400)]},
    "stopAutomation": {"label": "Parar esta automação", "group": "Controle", "params": []},
}


def catalog() -> dict[str, Any]:
    def listing(source: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        return [{"type": key, **value} for key, value in source.items()]

    return {"triggers": listing(TRIGGERS), "conditions": listing(CONDITIONS), "actions": listing(ACTIONS), "dayNames": DAY_NAMES}


# --------------------------------------------------------------- validação


def clean_params(specs: list[dict[str, Any]], raw: Any) -> dict[str, Any]:
    raw = raw if isinstance(raw, dict) else {}
    clean: dict[str, Any] = {}
    for spec in specs:
        key, kind = spec["key"], spec["kind"]
        value = raw.get(key, spec.get("default"))
        if kind == "text":
            value = str(value if value is not None else "")[:500]
        elif kind == "number":
            try:
                number = float(value)
            except (TypeError, ValueError):
                number = float(spec.get("default", 0))
            number = max(float(spec.get("min", 0)), min(float(spec.get("max", 1_000_000)), number))
            value = int(number) if number == int(number) else round(number, 2)
        elif kind == "time":
            value = str(value or "")
            if not TIME_RE.match(value):
                value = "" if spec.get("optional") else str(spec.get("default", "00:00"))
        elif kind == "days":
            try:
                value = sorted({int(day) for day in (value or []) if 0 <= int(day) <= 6})
            except (TypeError, ValueError):
                value = []
        elif kind == "media":
            value = Path(str(value or "")).name[:200]
        elif kind == "select":
            allowed = {option[0] for option in spec.get("options", [])}
            value = value if value in allowed else spec.get("default")
        elif kind == "toggle":
            value = bool(value)
        clean[key] = value
    return clean


def _clean_block(raw: Any, registry: dict[str, dict[str, Any]], what: str) -> dict[str, Any]:
    if not isinstance(raw, dict) or raw.get("type") not in registry:
        raise ValueError(f"{what} desconhecido.")
    kind = raw["type"]
    return {"type": kind, "params": clean_params(registry[kind]["params"], raw.get("params"))}


def sanitize_automation(raw: Any, existing_id: str = "") -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Automação inválida.")
    steps = raw.get("steps") or []
    conditions = raw.get("conditions") or []
    if not isinstance(steps, list) or not isinstance(conditions, list):
        raise ValueError("Automação inválida.")
    if len(steps) > MAX_STEPS or len(conditions) > 20:
        raise ValueError(f"Limite de {MAX_STEPS} passos por automação.")
    name = re.sub(r"\s+", " ", str(raw.get("name") or "")).strip()[:MAX_NAME] or "Nova automação"
    return {
        "id": existing_id or str(raw.get("id") or "") or "a" + uuid.uuid4().hex[:10],
        "name": name,
        "enabled": bool(raw.get("enabled", True)),
        "trigger": _clean_block(raw.get("trigger") or {"type": "manual"}, TRIGGERS, "Gatilho"),
        "conditions": [_clean_block(item, CONDITIONS, "Condição") for item in conditions],
        "steps": [_clean_block(item, ACTIONS, "Ação") for item in steps],
    }


# ------------------------------------------------------------------- ações


class Context:
    """O que uma ação pode usar: o "host" (NexStage) e a espera cancelável."""

    def __init__(self, host: Any, cancel: threading.Event) -> None:
        self.host = host
        self.cancel = cancel

    def sleep(self, seconds: float) -> None:
        if self.cancel.wait(max(0.0, float(seconds))):
            raise Cancelled()


Handler = Callable[[Context, dict[str, Any]], None]
HANDLERS: dict[str, Handler] = {}


def action(name: str) -> Callable[[Handler], Handler]:
    def register(function: Handler) -> Handler:
        HANDLERS[name] = function
        return function

    return register


def _now_ms() -> int:
    return int(time.time() * 1000)


@action("background")
def _background(ctx: Context, params: dict[str, Any]) -> None:
    ctx.host.apply({"background": ctx.host.media_url(params.get("media", ""), "background")})


@action("removeBackground")
def _remove_background(ctx: Context, params: dict[str, Any]) -> None:
    ctx.host.apply({"background": ""})


@action("logo")
def _logo(ctx: Context, params: dict[str, Any]) -> None:
    ctx.host.apply({"overlay": ctx.host.media_url(params.get("media", ""), "image")})


@action("removeLogo")
def _remove_logo(ctx: Context, params: dict[str, Any]) -> None:
    ctx.host.apply({"overlay": ""})


@action("showClock")
def _show_clock(ctx: Context, params: dict[str, Any]) -> None:
    ctx.host.apply({"mode": "clock", "live": True, "black": False})


@action("hideClock")
def _hide_clock(ctx: Context, params: dict[str, Any]) -> None:
    if ctx.host.state().get("mode") == "clock":
        ctx.host.apply({"live": False})


@action("message")
def _message(ctx: Context, params: dict[str, Any]) -> None:
    text = str(params.get("text", "")).strip()
    if not text:
        raise AutomationError("A mensagem está vazia.")
    ctx.host.apply({"mode": "song", "live": True, "black": False, "slide": {"text": text, "label": "", "reference": ""}})
    seconds = float(params.get("seconds") or 0)
    if seconds > 0:
        ctx.sleep(seconds)
        state = ctx.host.state()
        if state.get("mode") == "song" and state.get("slide", {}).get("text") == text:
            ctx.host.apply({"live": False})  # só limpa se ninguém trocou o conteúdo nesse meio tempo


def _show_timer(ctx: Context, timer: dict[str, Any]) -> None:
    ctx.host.apply({"mode": "timer", "live": True, "black": False, "timer": timer, "slide": {"text": "", "label": "", "reference": ""}})


@action("timerStart")
def _timer_start(ctx: Context, params: dict[str, Any]) -> None:
    timer = dict(ctx.host.state().get("timer") or {})
    minutes, end_time = int(params.get("minutes") or 0), str(params.get("endTime") or "")
    if end_time:
        timer.update({"mode": "endTime", "endTime": end_time, "running": False, "startedAt": 0})
    elif minutes > 0:
        timer.update({"mode": "duration", "durationMin": minutes, "running": True, "startedAt": _now_ms()})
    elif timer.get("mode") == "duration":
        timer.update({"running": True, "startedAt": _now_ms()})
    _show_timer(ctx, timer)


@action("timerRestart")
def _timer_restart(ctx: Context, params: dict[str, Any]) -> None:
    timer = dict(ctx.host.state().get("timer") or {})
    if timer.get("mode") == "duration":
        timer.update({"running": True, "startedAt": _now_ms()})
    _show_timer(ctx, timer)


@action("blackOn")
def _black_on(ctx: Context, params: dict[str, Any]) -> None:
    ctx.host.apply({"black": True})


@action("blackOff")
def _black_off(ctx: Context, params: dict[str, Any]) -> None:
    ctx.host.apply({"black": False})


@action("clearScreen")
def _clear_screen(ctx: Context, params: dict[str, Any]) -> None:
    ctx.host.apply({"live": False, "black": False})


@action("wait")
def _wait(ctx: Context, params: dict[str, Any]) -> None:
    ctx.sleep(float(params.get("seconds") or 0))


@action("stopAutomation")
def _stop(ctx: Context, params: dict[str, Any]) -> None:
    raise StopRun()


# ------------------------------------------------------------------- motor


def _js_weekday(moment: dt.datetime) -> int:
    return (moment.weekday() + 1) % 7  # 0 = domingo, como no editor


def _minutes(text: str) -> int:
    hours, minutes = text.split(":")
    return int(hours) * 60 + int(minutes)


def conditions_ok(conditions: list[dict[str, Any]], now: dt.datetime, host: Any) -> bool:
    for condition in conditions:
        kind, params = condition["type"], condition["params"]
        if kind == "weekday":
            ok = _js_weekday(now) in params.get("days", [])
        elif kind == "timeBetween":
            current, start, end = now.hour * 60 + now.minute, _minutes(params["start"]), _minutes(params["end"])
            ok = start <= current <= end if start <= end else (current >= start or current <= end)
        elif kind == "isLive":
            state = host.state()
            live = bool(state.get("live") and not state.get("black"))
            ok = live if params.get("value") == "on" else not live
        else:
            ok = False
        if not ok:
            return False
    return True


class AutomationEngine:
    def __init__(self, host: Any, path: Path) -> None:
        self.host = host
        self.path = path
        self.lock = threading.RLock()
        self.items: list[dict[str, Any]] = []
        self.paused = False
        self.history: deque[dict[str, Any]] = deque(maxlen=200)
        self.running: dict[str, threading.Event] = {}
        self._fired: dict[str, str] = {}
        self._next_every: dict[str, float] = {}
        self._started_at = 0.0
        self._boot_done = False
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._load()

    # -- persistência
    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.paused = bool(data.get("paused", False))
            for raw in data.get("items", [])[:MAX_AUTOMATIONS]:
                try:
                    self.items.append(sanitize_automation(raw, str(raw.get("id", ""))))
                except ValueError:
                    continue  # uma automação quebrada não derruba as outras
        except (FileNotFoundError, OSError, ValueError, AttributeError):
            self.items = []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".json.tmp")
        with self.lock:
            payload = {"paused": self.paused, "items": self.items}
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, self.path)

    # -- API usada pelo servidor
    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "paused": self.paused, "items": json.loads(json.dumps(self.items)),
                "history": list(self.history)[::-1][:60], "running": sorted(self.running),
            }

    def save_item(self, raw: Any) -> dict[str, Any]:
        with self.lock:
            existing_id = str(raw.get("id", "")) if isinstance(raw, dict) else ""
            known = any(item["id"] == existing_id for item in self.items)
            if not known and len(self.items) >= MAX_AUTOMATIONS:
                raise ValueError(f"Limite de {MAX_AUTOMATIONS} automações.")
            item = sanitize_automation(raw, existing_id if known else "")
            if known:
                self.items = [item if current["id"] == item["id"] else current for current in self.items]
            else:
                self.items.append(item)
            self._next_every.pop(item["id"], None)
        self._save()
        return item

    def delete(self, automation_id: str) -> bool:
        self.stop(automation_id)
        with self.lock:
            before = len(self.items)
            self.items = [item for item in self.items if item["id"] != automation_id]
            removed = len(self.items) != before
        if removed:
            self._save()
        return removed

    def set_paused(self, paused: bool) -> None:
        with self.lock:
            self.paused = bool(paused)
        self._save()

    def stop(self, automation_id: str = "") -> int:
        """Cancela uma execução (ou todas, se o id for vazio)."""
        with self.lock:
            targets = [self.running[automation_id]] if automation_id in self.running else ([] if automation_id else list(self.running.values()))
        for event in targets:
            event.set()
        return len(targets)

    def run_now(self, automation_id: str, reason: str = "manual") -> bool:
        with self.lock:
            item = next((entry for entry in self.items if entry["id"] == automation_id), None)
        if not item:
            raise KeyError("Automação não encontrada.")
        return self._launch(item, reason)

    # -- execução
    def _log(self, item: dict[str, Any], ok: bool, message: str, reason: str) -> None:
        with self.lock:
            self.history.append({
                "at": int(time.time() * 1000), "id": item["id"], "name": item["name"],
                "ok": ok, "message": message, "reason": reason,
            })

    def _launch(self, item: dict[str, Any], reason: str) -> bool:
        with self.lock:
            if item["id"] in self.running:
                return False
            cancel = threading.Event()
            self.running[item["id"]] = cancel
        threading.Thread(target=self.execute, args=(item, cancel, reason), name="NexStageAutomation", daemon=True).start()
        return True

    def execute(self, item: dict[str, Any], cancel: threading.Event, reason: str = "manual") -> None:
        """Roda os passos em sequência (síncrono; ``_launch`` chama isto numa thread)."""
        context = Context(self.host, cancel)
        done = 0
        try:
            for number, step in enumerate(item["steps"], start=1):
                if cancel.is_set():
                    raise Cancelled()
                handler = HANDLERS.get(step["type"])
                if not handler:
                    raise AutomationError(f"Passo {number}: ação desconhecida.")
                try:
                    handler(context, step["params"])
                except AutomationError as exc:
                    raise AutomationError(f"Passo {number} ({ACTIONS[step['type']]['label']}): {exc}") from exc
                done += 1
            self._log(item, True, f"Executada ({done} passo{'s' if done != 1 else ''})", reason)
        except StopRun:
            self._log(item, True, f"Parada pela própria automação no passo {done + 1}", reason)
        except Cancelled:
            self._log(item, True, f"Cancelada pelo operador após {done} passo{'s' if done != 1 else ''}", reason)
        except AutomationError as exc:
            self._log(item, False, str(exc), reason)
        except Exception as exc:  # noqa: BLE001 - uma falha nunca derruba o servidor
            self._log(item, False, f"Falha inesperada: {exc}", reason)
        finally:
            with self.lock:
                self.running.pop(item["id"], None)

    # -- agendamento
    def tick(self, now: dt.datetime | None = None, monotonic: float | None = None) -> list[str]:
        """Chamado a cada segundo. Devolve os ids disparados (útil nos testes)."""
        now = now or dt.datetime.now()
        monotonic = time.monotonic() if monotonic is None else monotonic
        fired: list[str] = []
        with self.lock:
            if self.paused:
                return fired
            items = [item for item in self.items if item["enabled"]]
            boot = not self._boot_done and monotonic - self._started_at >= 3
            if boot:
                self._boot_done = True
        for item in items:
            trigger, params = item["trigger"]["type"], item["trigger"]["params"]
            due, reason = False, trigger
            if trigger == "time":
                stamp = f"{now:%Y-%m-%d} {params['at']}"
                if now.strftime("%H:%M") == params["at"] and self._fired.get(item["id"]) != stamp:
                    days = params.get("days") or []
                    if not days or _js_weekday(now) in days:
                        self._fired[item["id"]] = stamp
                        due = True
            elif trigger == "every":
                period = max(1, int(params["minutes"])) * 60
                next_due = self._next_every.setdefault(item["id"], monotonic + period)
                if monotonic >= next_due:
                    self._next_every[item["id"]] = monotonic + period
                    due = True
            elif trigger == "appStart":
                due = boot
            if due and conditions_ok(item["conditions"], now, self.host):
                if self._launch(item, reason):
                    fired.append(item["id"])
        return fired

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._started_at = time.monotonic()
        self._stop.clear()

        def loop() -> None:
            while not self._stop.wait(1.0):
                try:
                    self.tick()
                except Exception:  # noqa: BLE001
                    pass

        self._thread = threading.Thread(target=loop, name="NexStageAutomationClock", daemon=True)
        self._thread.start()

    def shutdown(self) -> None:
        self._stop.set()
        self.stop()
