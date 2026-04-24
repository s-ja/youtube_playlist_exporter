import json
import tempfile
import unittest
from pathlib import Path

from deleter import (
    backup_target_file,
    delete_playlist_items,
    limited_targets,
    load_successful_playlist_item_ids,
    load_target_file,
    pending_targets,
    write_log,
)


class _FakeDeleteRequest:
    def __init__(self, playlist_item_id, failures):
        self.playlist_item_id = playlist_item_id
        self.failures = failures

    def execute(self):
        if self.playlist_item_id in self.failures:
            raise RuntimeError("simulated failure")
        return None


class _FakePlaylistItems:
    def __init__(self, calls, failures):
        self.calls = calls
        self.failures = failures

    def delete(self, id):
        self.calls.append(id)
        return _FakeDeleteRequest(id, self.failures)


class _FakeService:
    def __init__(self, failures=None):
        self.calls = []
        self.failures = set(failures or [])

    def playlistItems(self):
        return _FakePlaylistItems(self.calls, self.failures)


class DeleterTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workdir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_target(self):
        path = self.workdir / "target_to_delete.json"
        path.write_text(
            json.dumps(
                {
                    "source_file": "output/Music 03/Music 03.json",
                    "summary": {"duplicate_count": 3},
                    "delete_list": ["pi-1", "pi-2", "pi-3"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return path

    def test_load_target_file_requires_delete_list(self):
        path = self._write_target()
        data = load_target_file(path)
        self.assertEqual(data["delete_list"], ["pi-1", "pi-2", "pi-3"])

    def test_limited_targets_applies_limit(self):
        self.assertEqual(limited_targets(["a", "b", "c"], 2), ["a", "b"])

    def test_limited_targets_rejects_invalid_limit(self):
        with self.assertRaisesRegex(ValueError, "1 이상"):
            limited_targets(["a"], 0)

    def test_backup_and_write_log(self):
        target_path = self._write_target()
        backup_path = backup_target_file(target_path, self.workdir, "20260424_120000")
        log_path = self.workdir / "deletion_success_20260424_120000.json"
        write_log(log_path, [{"playlistItemId": "pi-1"}])

        self.assertTrue(backup_path.exists())
        self.assertTrue(log_path.exists())

    def test_load_successful_playlist_item_ids_from_logs(self):
        write_log(
            self.workdir / "deletion_success_20260424_120000.json",
            [{"playlistItemId": "pi-1"}, {"playlistItemId": "pi-3"}],
        )
        write_log(
            self.workdir / "deletion_failed_20260424_120000.json",
            [{"playlistItemId": "pi-2"}],
        )

        successful_ids = load_successful_playlist_item_ids(self.workdir)

        self.assertEqual(successful_ids, {"pi-1", "pi-3"})

    def test_pending_targets_excludes_successful_ids_by_default(self):
        targets = pending_targets(["pi-1", "pi-2", "pi-3"], {"pi-1", "pi-3"}, False)

        self.assertEqual(targets, ["pi-2"])

    def test_pending_targets_can_ignore_success_logs(self):
        targets = pending_targets(["pi-1", "pi-2", "pi-3"], {"pi-1", "pi-3"}, True)

        self.assertEqual(targets, ["pi-1", "pi-2", "pi-3"])

    def test_delete_playlist_items_continues_after_failure(self):
        service = _FakeService(failures={"pi-2"})

        successes, failures = delete_playlist_items(service, ["pi-1", "pi-2", "pi-3"], delay=0)

        self.assertEqual(service.calls, ["pi-1", "pi-2", "pi-3"])
        self.assertEqual([item["playlistItemId"] for item in successes], ["pi-1", "pi-3"])
        self.assertEqual(failures[0]["playlistItemId"], "pi-2")
        self.assertEqual(failures[0]["reason"], "RuntimeError")


if __name__ == "__main__":
    unittest.main()
