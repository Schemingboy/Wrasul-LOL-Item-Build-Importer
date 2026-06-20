from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from wrasul_lol_item_build_importer.importer import (
    extract_item_sets,
    install_item_sets,
    parse_champion_map,
    summarize_item_sets,
)


SAMPLE_SET = {
    "title": "Sample ADC Build",
    "associatedMaps": [11, 12],
    "associatedChampions": [67, 222],
    "blocks": [
        {
            "type": "Core",
            "items": [
                {"id": "6672", "count": 1},
                {"id": 3006, "count": "1"},
            ],
        }
    ],
}


class ImporterTests(unittest.TestCase):
    def test_extracts_json_array_from_bilibili_html(self) -> None:
        html = '<p><span>[{&quot;title&quot;:&quot;Sample&quot;,&quot;associatedChampions&quot;:[67],&quot;blocks&quot;:[{&quot;type&quot;:&quot;Core&quot;,&quot;items&quot;:[{&quot;id&quot;:&quot;6672&quot;,&quot;count&quot;:1}]}]}]</span></p>'

        item_sets = extract_item_sets(html)

        self.assertEqual(item_sets[0]["title"], "Sample")
        self.assertEqual(item_sets[0]["associatedChampions"], [67])
        self.assertEqual(item_sets[0]["blocks"][0]["items"][0]["id"], "6672")

    def test_parses_data_dragon_champion_map(self) -> None:
        data = {
            "data": {
                "Vayne": {"id": "Vayne", "key": "67"},
                "Jinx": {"id": "Jinx", "key": "222"},
            }
        }

        champion_map = parse_champion_map(data)

        self.assertEqual(champion_map[67], "Vayne")
        self.assertEqual(champion_map[222], "Jinx")

    def test_dry_run_does_not_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lol_dir = Path(tmp)
            result = install_item_sets(
                [extract_item_sets(json.dumps([SAMPLE_SET]))[0]],
                lol_dir,
                champion_map={67: "Vayne", 222: "Jinx"},
                install=False,
                allow_running_client=True,
            )

            self.assertEqual(len(result.planned), 2)
            self.assertFalse((lol_dir / "Config").exists())

    def test_installs_champion_item_sets_and_backs_up_old_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lol_dir = Path(tmp)
            old_file = lol_dir / "Config" / "Champions" / "Vayne" / "Recommended" / "wrasul-001-old.json"
            old_file.parent.mkdir(parents=True)
            old_file.write_text('{"title":"Old"}\n', encoding="utf-8")

            item_sets = extract_item_sets(json.dumps([SAMPLE_SET]))
            result = install_item_sets(
                item_sets,
                lol_dir,
                champion_map={67: "Vayne", 222: "Jinx"},
                install=True,
                allow_running_client=True,
            )

            self.assertEqual(len(result.written), 2)
            self.assertEqual(len(result.removed), 1)
            self.assertIsNotNone(result.backup_dir)
            self.assertFalse(old_file.exists())
            self.assertTrue((result.backup_dir / "Champions" / "Vayne" / "Recommended" / "wrasul-001-old.json").exists())

            written_payload = json.loads(result.written[0].read_text(encoding="utf-8"))
            self.assertEqual(written_payload["title"], "Sample ADC Build")
            self.assertIn(written_payload["champion"], {"Vayne", "Jinx"})

    def test_summary_counts_assignments_blocks_and_items(self) -> None:
        item_sets = extract_item_sets(json.dumps([SAMPLE_SET]))

        self.assertEqual(summarize_item_sets(item_sets), "1 item sets, 2 champion assignments, 1 blocks, 2 items")


if __name__ == "__main__":
    unittest.main()
