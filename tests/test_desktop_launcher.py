import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import desktop_launcher  # noqa: E402


class DesktopLauncherTests(unittest.TestCase):
    def test_data_home_follows_each_platform(self):
        with mock.patch.dict(os.environ, {"NEXSTAGE_HOME": ""}, clear=False):
            with mock.patch.object(sys, "platform", "darwin"):
                self.assertEqual(
                    desktop_launcher.data_home(),
                    Path.home() / "Library" / "Application Support" / "NexStage",
                )
            with mock.patch.object(sys, "platform", "linux"):
                with mock.patch.dict(os.environ, {"XDG_DATA_HOME": ""}):
                    self.assertEqual(desktop_launcher.data_home(), Path.home() / ".local" / "share" / "NexStage")
                with mock.patch.dict(os.environ, {"XDG_DATA_HOME": "/tmp/xdg"}):
                    self.assertEqual(desktop_launcher.data_home(), Path("/tmp/xdg/NexStage"))

    def test_nexstage_home_overrides_everything(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.dict(os.environ, {"NEXSTAGE_HOME": temporary}):
                self.assertEqual(desktop_launcher.data_home(), Path(temporary))
                self.assertEqual(desktop_launcher.runtime_file(), Path(temporary) / "data" / "runtime.json")

    @unittest.skipIf(desktop_launcher.fcntl is None, "bloqueio de arquivo só existe em macOS e Linux")
    def test_only_one_instance_can_hold_the_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            lock = Path(temporary) / "data" / "instance.lock"
            first = desktop_launcher.SingleInstance(lock)
            second = desktop_launcher.SingleInstance(lock)
            try:
                self.assertFalse(first.already_running)
                self.assertTrue(second.already_running)
            finally:
                second.close()
                first.close()
            third = desktop_launcher.SingleInstance(lock)
            try:
                self.assertFalse(third.already_running)
            finally:
                third.close()

    def test_runtime_file_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.dict(os.environ, {"NEXSTAGE_HOME": temporary}):
                desktop_launcher.write_runtime(desktop_launcher.runtime_file(), 4312, "9.9.9")
                data = desktop_launcher.read_runtime()
                self.assertEqual((data["port"], data["version"], data["pid"]), (4312, "9.9.9", os.getpid()))
                self.assertEqual(desktop_launcher.probe_existing_controller(), "http://127.0.0.1:4312/")

    def test_release_workflow_builds_every_platform(self):
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        for fragment in (
            "windows-latest", "ubuntu-22.04", "macos-latest", "macos-15-intel",
            "NexStage-Setup.exe", "NexStage-Linux-x64.tar.gz",
            "NexStage-macOS-AppleSilicon.dmg", "NexStage-macOS-Intel.dmg",
            "desktop_launcher.py", "--check-tray", "--stop",
        ):
            self.assertIn(fragment, workflow)
        for name in ("instalar.sh", "desinstalar.sh", "LEIA-ME.txt"):
            self.assertTrue((ROOT / "packaging" / "linux" / name).is_file())
        self.assertTrue((ROOT / "packaging" / "macos" / "LEIA-ME.txt").is_file())


if __name__ == "__main__":
    unittest.main()
