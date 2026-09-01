import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).parents[1] / "skills" / "nutrition-ledger" / "scripts" / "library_revision.py"
spec = importlib.util.spec_from_file_location("library_revision", MODULE)
library_revision = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(library_revision)


class LibraryRevisionTests(unittest.TestCase):
    def test_legacy_document_is_revision_zero(self):
        info = library_revision.revision_info({"entries": []})
        self.assertEqual(info.revision, 0)
        self.assertEqual(len(info.fingerprint), 64)

    def test_stamp_next_revision_links_previous_fingerprint(self):
        previous = {"entries": [{"entry_id": "1"}]}
        current = {"entries": [{"entry_id": "1"}, {"entry_id": "2"}]}
        stamped = library_revision.stamp_next_revision(current, previous)
        info = library_revision.revision_info(stamped)
        self.assertEqual(info.revision, 1)
        self.assertEqual(info.supersedes_fingerprint, library_revision.content_fingerprint(previous))
        self.assertEqual(info.fingerprint, library_revision.content_fingerprint(current))

    def test_selects_highest_revision_not_filename_order(self):
        legacy = {"entries": []}
        one = library_revision.stamp_next_revision({"entries": [{"entry_id": "1"}]}, legacy)
        two = library_revision.stamp_next_revision({"entries": [{"entry_id": "1"}, {"entry_id": "2"}]}, one)
        self.assertIs(library_revision.select_canonical([one, legacy, two]), two)

    def test_conflicting_same_revision_fails_closed(self):
        base = {"entries": []}
        one_a = library_revision.stamp_next_revision({"entries": [{"entry_id": "a"}]}, base)
        one_b = library_revision.stamp_next_revision({"entries": [{"entry_id": "b"}]}, base)
        with self.assertRaises(library_revision.RevisionError):
            library_revision.select_canonical([one_a, one_b])


if __name__ == "__main__":
    unittest.main()
