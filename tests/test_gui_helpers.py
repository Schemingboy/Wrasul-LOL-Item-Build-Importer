from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrasul_lol_item_build_importer.gui import find_default_lol_dir, friendly_error, validate_inputs
from wrasul_lol_item_build_importer.importer import ImporterError


class GuiHelperTests(unittest.TestCase):
    def test_validate_inputs_requires_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ImporterError) as context:
                validate_inputs("", tmp)

        self.assertIn("B 站动态链接", str(context.exception))

    def test_validate_inputs_requires_existing_lol_dir(self) -> None:
        with self.assertRaises(ImporterError) as context:
            validate_inputs("https://www.bilibili.com/opus/1", "Z:\\not-here")

        self.assertIn("League of Legends", str(context.exception))

    def test_validate_inputs_accepts_existing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lol_root = Path(tmp) / "League of Legends"
            lol_root.mkdir()
            source, lol_dir = validate_inputs(" https://www.bilibili.com/opus/1 ", str(lol_root))

        self.assertEqual(source, "https://www.bilibili.com/opus/1")
        self.assertTrue(lol_dir.is_absolute())

    def test_find_default_lol_dir_uses_first_existing_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_lol = Path(first) / "League of Legends"
            second_lol = Path(second) / "League of Legends"
            first_lol.mkdir()
            second_lol.mkdir()
            found = find_default_lol_dir((Path("Z:\\missing"), first_lol, second_lol))

        self.assertEqual(found, first_lol)

    def test_friendly_error_maps_common_messages(self) -> None:
        self.assertIn("关闭英雄联盟", friendly_error("close League of Legends before installing item sets"))
        self.assertIn("有效出装 JSON", friendly_error("could not find a valid League of Legends item set JSON array"))
        self.assertIn("英雄数据", friendly_error("failed to load champion map from Data Dragon"))


if __name__ == "__main__":
    unittest.main()
