import tempfile
import unittest
from pathlib import Path
import sys
import types

if "dotenv" not in sys.modules:
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv_stub

from exporters.base_exporter import BaseExporter
from exporters.json_exporter import JSONExporter
from exporters.markdown_exporter import MarkdownExporter


class _DummyExporter(BaseExporter):
    def export(self, playlist_data):
        return self.get_playlist_dir(playlist_data["title"]) / "dummy.txt"

    def get_file_extension(self) -> str:
        return ".txt"


class MinimumProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        self.sample_playlist = {
            "id": "PL_TEST",
            "title": 'My:Playlist/Name*',
            "description": "테스트 설명",
            "published_at": "2026-01-01T00:00:00Z",
            "videos": [
                {
                    "video_id": "abc123",
                    "title": "테스트 영상",
                    "url": "https://www.youtube.com/watch?v=abc123",
                    "thumbnail": "https://i.ytimg.com/vi/abc123/hqdefault.jpg",
                    "channel_title": "테스트 채널",
                    "added_at": "2026-01-02T00:00:00Z",
                }
            ],
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_exporters_create_output_files(self):
        exporters = [
            JSONExporter(self.output_dir),
            MarkdownExporter(self.output_dir),
        ]

        for exporter in exporters:
            created = exporter.export(self.sample_playlist)
            self.assertTrue(created.exists(), f"{created} 파일이 생성되어야 합니다.")

    def test_filename_sanitization_removes_invalid_chars(self):
        exporter = _DummyExporter(self.output_dir)
        sanitized = exporter.sanitize_filename('A<B>C:"D"/E\\F|G?H*I')
        self.assertNotRegex(sanitized, r'[<>:"/\\|?*]')

    def test_workers_option_removed_from_main_cli(self):
        main_source = Path("main.py").read_text(encoding="utf-8")
        self.assertNotIn("--workers", main_source)


if __name__ == "__main__":
    unittest.main()
