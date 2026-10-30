import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.images = {}

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.ids.add(element_id)
            if tag == "img":
                self.images[element_id] = attributes


class ControllerPreviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (WEB / "index.html").read_text(encoding="utf-8")
        cls.javascript = (WEB / "app.js").read_text(encoding="utf-8")
        cls.parser = IdCollector()
        cls.parser.feed(cls.html)

    def test_dual_preview_structure(self):
        required = {
            "previewFrame",
            "stagePreviewFrame",
            "monitorStatus",
            "stagePreviewBlackout",
            "stagePreviewText",
        }
        self.assertTrue(required.issubset(self.parser.ids))

    def test_watermark_exists_in_both_previews(self):
        self.assertIn("previewOverlay", self.parser.images)
        self.assertIn("stagePreviewOverlay", self.parser.images)

    def test_monitor_has_output_and_prepared_modes(self):
        self.assertRegex(self.html, r'data-monitor-view="output"')
        self.assertRegex(self.html, r'data-monitor-view="draft"')

    def test_video_preview_uses_a_frozen_canvas_frame(self):
        self.assertIn("function captureVideoFrame", self.javascript)
        self.assertIn('canvas.toDataURL("image/jpeg"', self.javascript)
        self.assertNotRegex(self.html, r"<video\b")

    def test_every_direct_id_reference_exists(self):
        referenced = set(re.findall(r'\$\("#([A-Za-z][\w-]*)"\)', self.javascript))
        missing = referenced - self.parser.ids
        self.assertEqual(missing, set())

    def test_030_controls_and_favicon_exist(self):
        required = {
            "openLouvorJA", "ljaDialog", "styleTarget", "fontInput",
            "screenSelect", "editBibleVisual", "editClockVisual", "slideDialog",
        }
        self.assertTrue(required.issubset(self.parser.ids))
        self.assertIn('rel="icon" href="/favicon.ico"', self.html)
        self.assertTrue((WEB / "favicon.ico").is_file())
        self.assertRegex(self.html, r'<img class="brand-mark" src="/favicon\.ico"')

    def test_independent_visual_models_are_used(self):
        for target in ("song.text", "bible.text", "bible.reference", "clock.time", "clock.date"):
            self.assertIn(target, self.javascript)
        self.assertIn("function applyBlockStyle", (WEB / "output.js").read_text(encoding="utf-8"))

    def test_040_louvorja_bible_unlimited_size_and_settings_transfer(self):
        required = {
            "refreshLjaBibles", "ljaBibleQuickStatus", "fontSizeNumber",
            "exportSettings", "importSettings", "settingsInput",
        }
        self.assertTrue(required.issubset(self.parser.ids))
        self.assertIn("/api/louvorja/bible/chapter", self.javascript)
        self.assertIn("function exportSettingsFile", self.javascript)
        self.assertRegex(self.html, r'id="fontSizeNumber"[^>]*min="1"')
        self.assertNotRegex(self.html, r'id="fontSizeNumber"[^>]*max=')

    def test_042_about_and_updater_controls_exist(self):
        required = {
            "aboutVersion", "aboutSystem", "aboutController", "aboutObs",
            "aboutDataPath", "aboutGithub", "updateStatus", "checkUpdates",
            "installUpdate", "openDataFolder",
        }
        self.assertTrue(required.issubset(self.parser.ids))
        self.assertIn("function checkForUpdates", self.javascript)
        self.assertIn("/api/update/apply", self.javascript)

    def test_043_bible_quick_reference_verse_navigation_and_release_workflow(self):
        required = {
            "bibleQuick", "bibleQuickGo", "bibleQuickHint", "verseSelect", "verseToSelect",
            "bibleJoin", "biblePrevChapter", "bibleNextChapter",
        }
        self.assertTrue(required.issubset(self.parser.ids))
        self.assertTrue((WEB / "bible-ref.js").is_file())
        self.assertLess(self.html.index('/bible-ref.js'), self.html.index('/app.js'))
        for name in ("function openChapter", "function stepSlide", "function restoreBibleOnce",
                     "function captureBibleContext", "function bibleQuickGo", "function applyBibleSelection"):
            self.assertIn(name, self.javascript)
        reference = (WEB / "bible-ref.js").read_text(encoding="utf-8")
        for name in ("function parse", "function findBook", "function resolve"):
            self.assertIn(name, reference)
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        for fragment in ("windows-latest", "NexStage-Setup.exe", "NexStage.iss", "unittest discover", "--windowed"):
            self.assertIn(fragment, workflow)

    def test_042_windows_installer_contract(self):
        installer = (ROOT / "packaging" / "windows" / "NexStage.iss").read_text(encoding="utf-8")
        launcher = (ROOT / "windows_launcher.py").read_text(encoding="utf-8")
        build = (ROOT / "build-windows.bat").read_text(encoding="utf-8")
        self.assertIn(r"DefaultDirName=C:\NexStage", installer)
        self.assertIn("MyAppPublisher \"Natan Gabriel\"", installer)
        self.assertIn("NexStage-Setup", installer)
        self.assertIn("uninsneveruninstall", installer)
        for label in (
            "Abrir controlador", "Abrir telão", "Copiar endereço do OBS",
            "Abrir pasta dos dados", "Encerrar NexStage",
        ):
            self.assertIn(label, launcher)
        self.assertIn("--windowed", build)
        self.assertIn("--contents-directory app", build)
        self.assertIn(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe", build)
        self.assertFalse((ROOT / "instalar.bat").exists())


if __name__ == "__main__":
    unittest.main()
