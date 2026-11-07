"""Pipeline do YouTube testado com um yt-dlp falso e o ffmpeg de verdade (o YouTube não é acessível nos testes)."""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import youtube as yt

FFMPEG = shutil.which("ffmpeg")
VID = "dQw4w9WgXcQ"

FAKE = r'''#!/usr/bin/env python3
import json, os, shutil, sys
a = sys.argv[1:]
src = os.environ["FAKE_YT_SRC"]
if "-J" in a:
    print(json.dumps({"title": "Vídeo de teste", "uploader": "Canal", "duration": 3, "thumbnail": "",
        "formats": [{"vcodec": "avc1.4d401f", "height": 360}, {"vcodec": "avc1.64001f", "height": 720},
                    {"vcodec": "vp09", "height": 1080}]}))
elif "-g" in a:
    print(src)
else:
    out = a[a.index("-o") + 1].replace("%(id)s", "x").replace("%(ext)s", "mp4")
    for p in (10, 60, 100):
        print("NX|%d|100|100" % p, flush=True)
    shutil.copy(src, out)
'''


def wait(condition, seconds=20):
    end = time.time() + seconds
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.1)
    return False


@unittest.skipUnless(FFMPEG and os.name != "nt", "precisa de ffmpeg e shell POSIX")
class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.src = self.tmp / "src.mp4"
        subprocess.run([FFMPEG, "-v", "error", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=25:duration=3",
                        "-f", "lavfi", "-i", "sine=duration=3", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-shortest", str(self.src)], check=True)
        os.environ["FAKE_YT_SRC"] = str(self.src)
        tools_dir = self.tmp / "tools"
        tools_dir.mkdir()
        fake = tools_dir / "yt-dlp"
        fake.write_text(FAKE)
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        self.settings = {"youtube": {"autoDownload": True, "defaultHeight": 720, "maxFps": 30, "volume": 0.5}}
        self.tools = yt.YouTubeTools(tools_dir)
        self.library = yt.YouTubeLibrary(self.tmp / "data", self.tools, lambda: self.settings)
        self.player = yt.PlayerController(self.library, lambda: self.settings)

    def test_add_downloads_h264_and_player_switches_files(self):
        self.library.add(f"https://youtu.be/{VID}?t=5")
        self.assertTrue(wait(lambda: self.library.items[VID]["info"] == "ok"))
        item = self.library.items[VID]
        self.assertEqual(item["heights"], [360, 720])  # VP9 é ignorado
        self.assertTrue(wait(lambda: self.library.file_for(VID, 720) is not None))
        self.assertEqual(yt.probe_video(FFMPEG, self.library.file_for(VID, 720))["codec"], "h264")

    def test_stream_before_download_then_commands(self):
        self.settings["youtube"]["autoDownload"] = False
        self.library.add(VID)
        self.assertTrue(wait(lambda: self.library.items[VID]["info"] == "ok"))
        self.assertEqual(self.player.command("load", {"id": VID}), "show")
        self.assertEqual(self.player.state["mode"], "stream")
        self.assertEqual(self.player.command("seek", {"t": 2}), "show")
        self.assertEqual(self.player.state["startAt"], 2.0)
        self.assertEqual(self.player.command("quality", {"height": 360}), "show")
        self.assertEqual(self.player.state["height"], 360)
        self.player.command("volume", {"value": 0.3})
        self.assertAlmostEqual(self.player.state["volume"], 0.3)
        self.assertEqual(self.player.command("stop", {}), "hide")

    def test_file_mode_after_download_and_stream_pipe_is_fragmented_mp4(self):
        self.library.add(VID)
        self.assertTrue(wait(lambda: self.library.file_for(VID, 720) is not None))
        self.player.command("load", {"id": VID})
        self.assertEqual(self.player.state["mode"], "file")
        self.player.command("seek", {"t": 1})
        self.assertEqual(self.player.state["seekTo"], 1.0)
        out = subprocess.run(yt.stream_command(FFMPEG, [str(self.src)], 1.0), capture_output=True, timeout=60).stdout
        self.assertGreater(len(out), 1000)
        self.assertIn(b"ftyp", out[:64])

    def test_remove_deletes_files(self):
        self.library.add(VID)
        self.assertTrue(wait(lambda: self.library.file_for(VID, 720) is not None))
        self.library.remove(VID)
        self.assertNotIn(VID, self.library.items)
        self.assertEqual(self.library.files(VID), {})


class ParseTests(unittest.TestCase):
    def test_ids(self):
        for text in (VID, f"https://www.youtube.com/watch?v={VID}&t=3", f"https://youtu.be/{VID}",
                     f"https://www.youtube.com/shorts/{VID}", f"youtube.com/embed/{VID}"):
            self.assertEqual(yt.parse_video_id(text), VID, text)
        for bad in ("", "oi", "https://example.com/x", None):
            self.assertIsNone(yt.parse_video_id(bad))

    def test_selector_prefers_h264(self):
        selector = yt.format_selector(720)
        self.assertIn("avc1", selector)
        self.assertNotIn("vp9", selector.lower())


class TimerTests(unittest.TestCase):
    def test_timer_defaults_and_independent_styles(self):
        import server
        self.assertEqual(server.DEFAULT_STATE["timer"]["mode"], "endTime")
        styles = server.DEFAULT_STYLES["timer"]
        self.assertEqual(set(styles), {"label", "time", "countdown"})
        self.assertNotEqual(styles["time"]["textColor"], styles["countdown"]["textColor"])
        merged = server.deep_merge(server.DEFAULT_STYLES, {"timer": {"countdown": {"fontSize": 99}}})
        self.assertEqual(merged["timer"]["countdown"]["fontSize"], 99)
        self.assertEqual(merged["timer"]["time"]["fontSize"], styles["time"]["fontSize"])

    def test_timer_is_wired_in_ui_and_output(self):
        web = Path(__file__).resolve().parents[1] / "web"
        self.assertIn('data-panel="timer"', (web / "index.html").read_text(encoding="utf-8"))
        self.assertIn('state.mode === "timer"', (web / "output.js").read_text(encoding="utf-8"))
        self.assertIn("timer.countdown", (web / "app.js").read_text(encoding="utf-8"))


class UiContractTests(unittest.TestCase):
    def test_ctrl_click_verse_selection_is_wired(self):
        js = (Path(__file__).resolve().parents[1] / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("event.ctrlKey || event.metaKey", js)
        self.assertIn("toggleBibleVerse", js)
        self.assertIn("bibleComboSlide", js)

    def test_every_yt_id_used_by_the_controller_exists_in_html(self):
        import re
        root = Path(__file__).resolve().parents[1] / "web"
        html = (root / "index.html").read_text(encoding="utf-8")
        js = (root / "app.js").read_text(encoding="utf-8")
        for ident in set(re.findall(r'\$\("#(yt[A-Za-z]+)"\)', js)):
            self.assertIn(f'id="{ident}"', html, ident)
        out = (root / "output.html").read_text(encoding="utf-8")
        self.assertIn('id="ytVideo"', out)
        self.assertIn('id="ytVideo"', (root / "obs.html").read_text(encoding="utf-8"))


@unittest.skipUnless(shutil.which("node"), "precisa do node")
class BibleRefTests(unittest.TestCase):
    def test_jo_is_joao_and_numbered_abbreviations(self):
        script = (
            "const R=require(process.argv[1]);"
            "const b=['I Samuel','I Reis','Jó','João','I João'].map((n,i)=>({name:n,chapterCount:50,pos:i}));"
            "const f=t=>{const r=R.resolve(t,b);return r?b[r.pos].name:null};"
            "console.log(JSON.stringify([f('jo 3:16'),f('jó 1'),f('1 sm 3'),f('1rs 2'),f('1jo 4')]))"
        )
        path = Path(__file__).resolve().parents[1] / "web" / "bible-ref.js"
        out = subprocess.run(["node", "-e", script, str(path)], capture_output=True, encoding="utf-8", check=True).stdout
        self.assertEqual(json.loads(out), ["João", "Jó", "I Samuel", "I Reis", "I João"])


if __name__ == "__main__":
    unittest.main()
