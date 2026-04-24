import json
import tempfile
import unittest
from pathlib import Path

from deduplicator import analyze_playlist_json, write_dry_run_output


class DeduplicatorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_json(self, payload):
        path = self.workdir / "playlist.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_analyzes_duplicates_with_keep_first_rule(self):
        input_path = self._write_json(
            {
                "items": [
                    {"videoId": "A", "playlistItemId": "pi-2", "position": 2},
                    {"videoId": "B", "playlistItemId": "pi-1", "position": 1},
                    {"videoId": "A", "playlistItemId": "pi-0", "position": 0},
                    {"videoId": "A", "playlistItemId": "pi-4", "position": 4},
                ]
            }
        )

        result = analyze_playlist_json(input_path)

        self.assertEqual(result.total_count, 4)
        self.assertEqual(result.unique_count, 2)
        self.assertEqual(result.duplicate_count, 2)
        self.assertIn("pi-0", result.keep_list)
        self.assertEqual(result.delete_list, ["pi-2", "pi-4"])

    def test_supports_current_project_videos_schema(self):
        input_path = self._write_json(
            {
                "videos": [
                    {"video_id": "A", "playlist_item_id": "pi-0", "position": 0},
                    {"video_id": "A", "playlist_item_id": "pi-1", "position": 1},
                ]
            }
        )

        result = analyze_playlist_json(input_path)

        self.assertEqual(result.keep_list, ["pi-0"])
        self.assertEqual(result.delete_list, ["pi-1"])

    def test_fails_when_duplicate_delete_target_has_no_playlist_item_id(self):
        input_path = self._write_json(
            {
                "videos": [
                    {"video_id": "A", "position": 0},
                    {"video_id": "A", "position": 1},
                ]
            }
        )

        with self.assertRaisesRegex(ValueError, "playlistItemId"):
            analyze_playlist_json(input_path)

    def test_writes_dry_run_output(self):
        input_path = self._write_json(
            {
                "videos": [
                    {"video_id": "A", "playlist_item_id": "pi-0", "position": 0},
                    {"video_id": "A", "playlist_item_id": "pi-1", "position": 1},
                ]
            }
        )
        output_path = self.workdir / "target_to_delete.json"

        result = analyze_playlist_json(input_path)
        write_dry_run_output(result, output_path, input_path)

        data = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(data["delete_list"], ["pi-1"])
        self.assertEqual(data["summary"]["duplicate_count"], 1)


if __name__ == "__main__":
    unittest.main()
