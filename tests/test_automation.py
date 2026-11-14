import datetime as dt
import threading
import time

import automation as A


class FakeHost:
    def __init__(self):
        self.s = {"mode": "song", "live": False, "black": False, "slide": {}, "timer": {"mode": "duration", "durationMin": 5}}

    def state(self):
        return self.s

    def apply(self, changes):
        self.s = {**self.s, **changes}

    def media_url(self, name, kind=""):
        if not name:
            raise A.AutomationError("Escolha um arquivo.")
        return "/media/" + name


def make(tmp_path, steps, trigger=None, conditions=None):
    eng = A.AutomationEngine(FakeHost(), tmp_path / "a.json")
    item = eng.save_item({"name": "t", "trigger": trigger or {"type": "manual"}, "conditions": conditions or [], "steps": steps})
    return eng, item


def wait_idle(eng):
    for _ in range(100):
        if not eng.running:
            return
        time.sleep(0.02)


def test_sanitize_rejects_unknown():
    try:
        A.sanitize_automation({"steps": [{"type": "rm -rf"}]})
        assert False
    except ValueError:
        pass


def test_run_steps_and_persist(tmp_path):
    eng, item = make(tmp_path, [{"type": "blackOn"}, {"type": "background", "params": {"media": "x.jpg"}}])
    assert eng.run_now(item["id"])
    wait_idle(eng)
    assert eng.host.s["black"] is True and eng.host.s["background"] == "/media/x.jpg"
    assert eng.snapshot()["history"][0]["ok"]
    assert len(A.AutomationEngine(eng.host, tmp_path / "a.json").items) == 1


def test_error_logged(tmp_path):
    eng, item = make(tmp_path, [{"type": "background"}])
    eng.run_now(item["id"])
    wait_idle(eng)
    h = eng.snapshot()["history"][0]
    assert not h["ok"] and "Passo 1" in h["message"]


def test_time_trigger_once_per_minute_and_weekday(tmp_path):
    eng, item = make(tmp_path, [{"type": "blackOn"}], {"type": "time", "params": {"at": "08:55", "days": [0]}})
    sunday = dt.datetime(2026, 11, 15, 8, 55, 10)
    monday = dt.datetime(2026, 11, 16, 8, 55, 10)
    assert eng.tick(monday) == []
    assert eng.tick(sunday) == [item["id"]]
    wait_idle(eng)
    assert eng.tick(sunday) == []


def test_pause_and_conditions(tmp_path):
    eng, item = make(tmp_path, [{"type": "blackOn"}], {"type": "time", "params": {"at": "10:00"}},
                     [{"type": "isLive", "params": {"value": "on"}}])
    now = dt.datetime(2026, 11, 15, 10, 0, 1)
    assert eng.tick(now) == []  # não está no ar
    eng.host.s["live"] = True
    eng._fired.clear()
    eng.set_paused(True)
    assert eng.tick(now) == []
    eng.set_paused(False)
    assert eng.tick(now) == [item["id"]]


def test_cancel_wait_and_no_overlap(tmp_path):
    eng, item = make(tmp_path, [{"type": "wait", "params": {"seconds": 30}}, {"type": "blackOn"}])
    assert eng.run_now(item["id"])
    assert not eng.run_now(item["id"])
    time.sleep(0.1)
    assert eng.stop(item["id"]) == 1
    wait_idle(eng)
    assert eng.host.s["black"] is False
    assert "Cancelada" in eng.snapshot()["history"][0]["message"]


def test_message_timed_clear(tmp_path):
    eng, item = make(tmp_path, [{"type": "message", "params": {"text": "Oi", "seconds": 1}}])
    eng.run_now(item["id"])
    time.sleep(0.3)
    assert eng.host.s["live"] is True
    wait_idle(eng)
    assert eng.host.s["live"] is False


def test_stop_step_and_timer(tmp_path):
    eng, item = make(tmp_path, [{"type": "timerStart", "params": {"minutes": 7}}, {"type": "stopAutomation"}, {"type": "blackOn"}])
    eng.run_now(item["id"])
    wait_idle(eng)
    assert eng.host.s["timer"]["durationMin"] == 7 and eng.host.s["timer"]["running"]
    assert eng.host.s["black"] is False
