import json
import hashlib
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server


class SongParserTests(unittest.TestCase):
    def test_sections_and_chunks(self):
        song = server.parse_song_text(
            "teste.txt",
            "Title: Minha Música\n\n[Verso 1]\nA\nB\nC\nD\nE\n\n[Refrão]\nR1\nR2",
        )
        self.assertEqual(song["title"], "Minha Música")
        self.assertEqual(len(song["slides"]), 3)
        self.assertEqual(song["slides"][0]["text"], "A\nB\nC\nD")
        self.assertEqual(song["slides"][1]["text"], "E")
        self.assertEqual(song["slides"][2]["label"], "Refrão")

    def test_blank_lines_create_slides(self):
        song = server.parse_song_text("Louvor_Novo.txt", "Linha 1\nLinha 2\n\nLinha 3")
        self.assertEqual(song["title"], "Louvor Novo")
        self.assertEqual([slide["text"] for slide in song["slides"]], ["Linha 1\nLinha 2", "Linha 3"])


class BibleParserTests(unittest.TestCase):
    def test_zefania(self):
        xml = """<?xml version='1.0'?><XMLBIBLE biblename='Teste'><BIBLEBOOK bname='Livro'><CHAPTER cnumber='3'><VERS vnumber='4'>Texto <STYLE>completo</STYLE>.</VERS></CHAPTER></BIBLEBOOK></XMLBIBLE>"""
        bible = server.parse_zefania_xml("teste.xml", xml)
        self.assertEqual(bible["name"], "Teste")
        self.assertEqual(bible["books"][0]["name"], "Livro")
        self.assertEqual(bible["books"][0]["chapters"][0]["verses"][0]["text"], "Texto completo.")

    def test_rejects_entities(self):
        with self.assertRaises(ValueError):
            server.parse_zefania_xml("bad.xml", "<!DOCTYPE x [<!ENTITY a 'x'>]><XMLBIBLE />")

    def test_rejects_unknown_shape(self):
        with self.assertRaises(ValueError):
            server.parse_zefania_xml("bad.xml", "<root><item>texto</item></root>")


class StateTests(unittest.TestCase):
    def test_revision_and_wait_notification(self):
        with tempfile.TemporaryDirectory() as temporary:
            original_paths = (server.DATA_DIR, server.MEDIA_DIR, server.BIBLE_DIR, server.FONT_DIR, server.LIBRARY_FILE, server.SETTINGS_FILE)
            root = Path(temporary)
            server.DATA_DIR = root / "data"
            server.MEDIA_DIR = root / "media"
            server.BIBLE_DIR = server.DATA_DIR / "bibles"
            server.FONT_DIR = server.DATA_DIR / "fonts"
            server.LIBRARY_FILE = server.DATA_DIR / "library.json"
            server.SETTINGS_FILE = server.DATA_DIR / "settings.json"
            try:
                store = server.AppStore()
                initial = store.state["revision"]
                received = []
                waiter = threading.Thread(target=lambda: received.append(store.wait_state(initial, 1)))
                waiter.start(); time.sleep(0.03)
                updated = dict(store.state); updated["live"] = True
                store.update_state(updated); waiter.join(1)
                self.assertTrue(received[0]["live"])
                self.assertEqual(received[0]["revision"], initial + 1)
            finally:
                (server.DATA_DIR, server.MEDIA_DIR, server.BIBLE_DIR, server.FONT_DIR, server.LIBRARY_FILE, server.SETTINGS_FILE) = original_paths


class LouvorJATests(unittest.TestCase):
    def test_local_catalog_search_and_import_are_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "database.db"
            with closing(sqlite3.connect(database)) as connection:
                connection.executescript(
                    """
                    CREATE TABLE MUSICAS (ID INTEGER, NOME TEXT, ALBUM TEXT, LETRA TEXT);
                    CREATE TABLE MUSICAS_SLIDE (MUSICA_ID INTEGER, TIPO TEXT, LETRA TEXT, ORDEM INTEGER);
                    INSERT INTO MUSICAS VALUES (7, 'Coração Fiel', 'CD Jovem', 'Letra agregada');
                    INSERT INTO MUSICAS_SLIDE VALUES (7, 'LETRA', 'Primeiro slide', 1);
                    INSERT INTO MUSICAS_SLIDE VALUES (7, 'LETRA', 'Segundo slide', 2);
                    """
                )
            before = hashlib.sha256(database.read_bytes()).hexdigest()
            catalog = server.LouvorJACatalog()
            connections = []
            actual_open = server.open_sqlite_read_only

            def tracked_open(path):
                opened = actual_open(path)
                connections.append(opened)
                return opened

            with mock.patch("server.open_sqlite_read_only", side_effect=tracked_open):
                status = catalog.status(str(database))
                self.assertTrue(status["available"])
                self.assertEqual(status["count"], 1)
                self.assertEqual(catalog.search("coracao", str(database))[0]["id"], 7)
                song = catalog.song(7, str(database))
            self.assertEqual(song["source"], "Louvor JA")
            self.assertEqual([slide["text"] for slide in song["slides"]], ["Primeiro slide", "Segundo slide"])
            self.assertEqual(before, hashlib.sha256(database.read_bytes()).hexdigest())
            self.assertGreaterEqual(len(connections), 2)
            for opened in connections:
                with self.assertRaises(sqlite3.ProgrammingError):
                    opened.execute("SELECT 1")

    def test_bible_versions_and_chapter_are_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "database.db"
            with closing(sqlite3.connect(database)) as connection:
                connection.executescript(
                    """
                    CREATE TABLE bible_version (
                        id_bible_version INTEGER PRIMARY KEY,
                        name TEXT, abbreviation TEXT, id_language TEXT
                    );
                    CREATE TABLE bible_book (
                        id_bible_book INTEGER PRIMARY KEY,
                        book_number INTEGER, name TEXT, chapters INTEGER,
                        abbreviation TEXT, id_language TEXT
                    );
                    CREATE TABLE bible_verse (
                        id_bible_verse INTEGER PRIMARY KEY,
                        id_bible_version INTEGER, id_bible_book INTEGER,
                        chapter INTEGER, verse INTEGER, text TEXT, id_language TEXT
                    );
                    INSERT INTO bible_version VALUES (5, 'Nova Versão Internacional', 'NVI', 'pt');
                    INSERT INTO bible_book VALUES (43, 43, 'João', 21, 'Jo', 'pt');
                    INSERT INTO bible_verse VALUES (1, 5, 43, 3, 16, 'Porque Deus amou o mundo.', 'pt');
                    INSERT INTO bible_verse VALUES (2, 5, 43, 3, 17, '', 'pt');
                    """
                )
            before = hashlib.sha256(database.read_bytes()).hexdigest()
            catalog = server.LouvorJABibleCatalog()
            connections = []
            actual_open = server.open_sqlite_read_only

            def tracked_open(path):
                opened = actual_open(path)
                connections.append(opened)
                return opened

            with mock.patch("server.open_sqlite_read_only", side_effect=tracked_open):
                status = catalog.status(str(database))
                self.assertTrue(status["available"])
                self.assertEqual(status["versions"][0]["abbreviation"], "NVI")
                self.assertEqual(catalog.books(5, str(database))[0]["name"], "João")
                chapter = catalog.chapter(5, 43, 3, str(database))
            self.assertEqual(chapter["bible"], "NVI")
            self.assertEqual(chapter["bookAbbreviation"], "Jo")
            self.assertEqual(chapter["verses"], [{"number": "16", "text": "Porque Deus amou o mundo."}])
            self.assertEqual(before, hashlib.sha256(database.read_bytes()).hexdigest())
            self.assertGreaterEqual(len(connections), 2)
            for opened in connections:
                with self.assertRaises(sqlite3.ProgrammingError):
                    opened.execute("SELECT 1")


class SettingsMigrationTests(unittest.TestCase):
    def test_nested_visual_defaults_survive_partial_settings(self):
        merged = server.deep_merge(server.DEFAULT_SETTINGS, {"styles": {"bible": {"text": {"fontSize": 77}}}})
        self.assertEqual(merged["styles"]["bible"]["text"]["fontSize"], 77)
        self.assertIn("reference", merged["styles"]["bible"])
        self.assertIn("clock", merged["styles"])
        self.assertIn("song", merged)

    def test_custom_font_size_has_no_upper_limit(self):
        settings = server.AppStore._validated_settings(
            {"styles": {"clock": {"time": {"fontSize": 4096}}}}
        )
        self.assertEqual(settings["styles"]["clock"]["time"]["fontSize"], 4096)

    def test_settings_export_is_portable(self):
        with tempfile.TemporaryDirectory() as temporary:
            original_paths = (server.DATA_DIR, server.MEDIA_DIR, server.BIBLE_DIR, server.FONT_DIR, server.LIBRARY_FILE, server.SETTINGS_FILE)
            root = Path(temporary)
            server.DATA_DIR = root / "data"
            server.MEDIA_DIR = root / "media"
            server.BIBLE_DIR = server.DATA_DIR / "bibles"
            server.FONT_DIR = server.DATA_DIR / "fonts"
            server.LIBRARY_FILE = server.DATA_DIR / "library.json"
            server.SETTINGS_FILE = server.DATA_DIR / "settings.json"
            try:
                store = server.AppStore()
                store.save_settings({"louvorJaDb": "C:/local/database.db", "output": {"preferredScreen": "Tela|1920|1080"}})
                bundle = store.export_settings()
                self.assertEqual(bundle["kind"], "NexStageSettings")
                self.assertEqual(bundle["settings"]["louvorJaDb"], "")
                self.assertEqual(bundle["settings"]["output"]["preferredScreen"], "")
                revision = store.state["revision"]
                imported = store.import_settings({"kind": "NexStageSettings", "schemaVersion": 1, "settings": {"styles": {"bible": {"text": {"fontSize": 777}}}}})
                self.assertEqual(imported["styles"]["bible"]["text"]["fontSize"], 777)
                self.assertEqual(imported["louvorJaDb"], "C:/local/database.db")
                self.assertEqual(imported["output"]["preferredScreen"], "Tela|1920|1080")
                self.assertEqual(store.state["revision"], revision + 1)
            finally:
                (server.DATA_DIR, server.MEDIA_DIR, server.BIBLE_DIR, server.FONT_DIR, server.LIBRARY_FILE, server.SETTINGS_FILE) = original_paths


class UpdateTests(unittest.TestCase):
    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload
            self.headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, _size=-1):
            return self.payload

    def test_version_parser(self):
        self.assertEqual(server.version_numbers("v0.4.12"), (0, 4, 12))
        self.assertGreater(server.version_numbers("0.5.0"), server.version_numbers("0.4.9"))

    def test_official_release_asset_is_detected(self):
        release = {
            "tag_name": "v0.4.3",
            "name": "NexStage 0.4.3",
            "html_url": "https://github.com/Natan-Tec/NexStage/releases/tag/v0.4.3",
            "assets": [{
                "name": "NexStage-Setup.exe",
                "size": 123456,
                "browser_download_url": "https://github.com/Natan-Tec/NexStage/releases/download/v0.4.3/NexStage-Setup.exe",
            }],
        }
        response = self.FakeResponse(json.dumps(release).encode("utf-8"))
        service = server.UpdateService(current_version="0.4.2", supported=True)
        with mock.patch("server.urllib.request.urlopen", return_value=response):
            info = service.check()
        self.assertTrue(info["available"])
        self.assertTrue(info["downloadReady"])
        self.assertTrue(info["updateSupported"])
        self.assertEqual(info["latestVersion"], "0.4.3")

    def test_update_download_rejects_untrusted_hosts(self):
        self.assertTrue(server.UpdateService._trusted_download_url(
            "https://github.com/Natan-Tec/NexStage/releases/download/v1/NexStage-Setup.exe"
        ))
        self.assertFalse(server.UpdateService._trusted_download_url(
            "https://example.com/NexStage-Setup.exe"
        ))

    def test_about_has_correct_author_and_paths(self):
        info = server.about_info("http://127.0.0.1:4317")
        self.assertEqual(info["author"], "Natan Gabriel")
        self.assertEqual(info["controllerUrl"], "http://127.0.0.1:4317/")
        self.assertEqual(info["obsUrl"], "http://127.0.0.1:4317/obs")


if __name__ == "__main__":
    unittest.main()
