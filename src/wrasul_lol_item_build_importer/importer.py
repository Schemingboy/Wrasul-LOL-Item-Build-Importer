from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


BILIBILI_HOST = "bilibili.com"
DATA_DRAGON_VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
DATA_DRAGON_CHAMPION_URL = "https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
DEFAULT_PREFIX = "wrasul"
LOL_PROCESS_NAMES = {
    "LeagueClient.exe",
    "LeagueClientUx.exe",
    "LeagueClientUxRender.exe",
    "League of Legends.exe",
}


class ImporterError(RuntimeError):
    """Raised when an item build cannot be imported safely."""


@dataclass(frozen=True)
class InstallResult:
    planned: list[Path]
    written: list[Path]
    removed: list[Path]
    backup_dir: Path | None


def load_source(source: str) -> str:
    if is_url(source):
        return fetch_text(source)

    path = Path(source)
    if not path.exists():
        raise ImporterError(f"source not found: {source}")
    return path.read_text(encoding="utf-8-sig")


def is_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def fetch_text(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) WrasulLoLItemImporter/0.1",
        "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
    }
    if BILIBILI_HOST in url:
        headers["Referer"] = "https://www.bilibili.com/"

    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except URLError as exc:
        raise ImporterError(f"failed to fetch source URL: {exc}") from exc


def extract_item_sets(raw_text: str) -> list[dict[str, Any]]:
    text = html.unescape(raw_text).strip()
    parsed = _try_json(text)
    if parsed is not None:
        return normalize_item_sets(parsed)

    decoder = json.JSONDecoder()
    for match in re.finditer(r"\[\s*\{", text):
        try:
            parsed, _ = decoder.raw_decode(text[match.start() :])
        except json.JSONDecodeError:
            continue
        try:
            return normalize_item_sets(parsed)
        except ImporterError:
            continue

    raise ImporterError("could not find a valid League of Legends item set JSON array")


def _try_json(text: str) -> Any | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def normalize_item_sets(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        item_sets = [value]
    elif isinstance(value, list):
        item_sets = value
    else:
        raise ImporterError("item set JSON must be an object or an array of objects")

    normalized: list[dict[str, Any]] = []
    for index, item_set in enumerate(item_sets, start=1):
        if not isinstance(item_set, dict):
            raise ImporterError(f"item set #{index} is not an object")
        normalized.append(normalize_item_set(item_set, index))
    if not normalized:
        raise ImporterError("item set JSON is empty")
    return normalized


def normalize_item_set(item_set: dict[str, Any], index: int) -> dict[str, Any]:
    title = item_set.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ImporterError(f"item set #{index} is missing a title")

    blocks = item_set.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise ImporterError(f"item set '{title}' has no blocks")

    normalized_blocks: list[dict[str, Any]] = []
    for block_index, block in enumerate(blocks, start=1):
        if not isinstance(block, dict):
            raise ImporterError(f"item set '{title}' block #{block_index} is not an object")
        normalized_blocks.append(normalize_block(block, title, block_index))

    result = dict(item_set)
    result["title"] = title.strip()
    result["type"] = str(result.get("type") or "custom")
    result["map"] = str(result.get("map") or "any")
    result["mode"] = str(result.get("mode") or "any")
    result["priority"] = bool(result.get("priority", False))
    result["sortrank"] = int(result.get("sortrank", 0))
    result["associatedMaps"] = normalize_int_list(result.get("associatedMaps", []), "associatedMaps", title)
    result["associatedChampions"] = normalize_int_list(
        result.get("associatedChampions", []), "associatedChampions", title
    )
    result["blocks"] = normalized_blocks
    return result


def normalize_block(block: dict[str, Any], title: str, block_index: int) -> dict[str, Any]:
    block_type = block.get("type")
    if not isinstance(block_type, str) or not block_type.strip():
        raise ImporterError(f"item set '{title}' block #{block_index} is missing a type")

    items = block.get("items")
    if not isinstance(items, list) or not items:
        raise ImporterError(f"item set '{title}' block '{block_type}' has no items")

    normalized_items: list[dict[str, Any]] = []
    for item_index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ImporterError(f"item set '{title}' block '{block_type}' item #{item_index} is not an object")

        item_id = str(item.get("id", "")).strip()
        if not item_id.isdigit():
            raise ImporterError(f"item set '{title}' block '{block_type}' item #{item_index} has invalid id")

        try:
            count = int(item.get("count", 1))
        except (TypeError, ValueError) as exc:
            raise ImporterError(f"item set '{title}' block '{block_type}' item '{item_id}' has invalid count") from exc
        if count < 1:
            raise ImporterError(f"item set '{title}' block '{block_type}' item '{item_id}' count must be positive")

        normalized_item = dict(item)
        normalized_item["id"] = item_id
        normalized_item["count"] = count
        normalized_items.append(normalized_item)

    result = dict(block)
    result["type"] = block_type.strip()
    result["items"] = normalized_items
    result.setdefault("showIfSummonerSpell", "")
    result.setdefault("hideIfSummonerSpell", "")
    return result


def normalize_int_list(value: Any, field: str, title: str) -> list[int]:
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise ImporterError(f"item set '{title}' field '{field}' must be a list")

    result: list[int] = []
    for entry in value:
        try:
            number = int(entry)
        except (TypeError, ValueError) as exc:
            raise ImporterError(f"item set '{title}' field '{field}' contains a non-number value") from exc
        result.append(number)
    return result


def load_champion_map(champion_map_path: Path | None = None) -> dict[int, str]:
    if champion_map_path is not None:
        data = json.loads(champion_map_path.read_text(encoding="utf-8-sig"))
        return parse_champion_map(data)

    try:
        versions = json.loads(fetch_text(DATA_DRAGON_VERSIONS_URL))
        if not isinstance(versions, list) or not versions:
            raise ImporterError("Data Dragon returned no versions")
        champion_data = json.loads(fetch_text(DATA_DRAGON_CHAMPION_URL.format(version=versions[0])))
        return parse_champion_map(champion_data)
    except (json.JSONDecodeError, ImporterError) as exc:
        raise ImporterError(f"failed to load champion map from Data Dragon: {exc}") from exc


def parse_champion_map(data: Any) -> dict[int, str]:
    if isinstance(data, dict) and "data" in data:
        champions = data["data"]
    else:
        champions = data
    if not isinstance(champions, dict):
        raise ImporterError("champion map must be a Data Dragon response or an id-to-key object")

    result: dict[int, str] = {}
    for key, value in champions.items():
        if isinstance(value, dict) and "key" in value and "id" in value:
            result[int(value["key"])] = str(value["id"])
        else:
            result[int(key)] = str(value)
    return result


def install_item_sets(
    item_sets: list[dict[str, Any]],
    lol_dir: Path,
    *,
    champion_map: dict[int, str] | None,
    target: str = "champion",
    prefix: str = DEFAULT_PREFIX,
    install: bool = False,
    replace_old: bool = True,
    allow_running_client: bool = False,
) -> InstallResult:
    lol_dir = lol_dir.expanduser().resolve()
    config_dir = lol_dir / "Config"
    if not lol_dir.exists():
        raise ImporterError(f"League of Legends directory does not exist: {lol_dir}")
    if install and not allow_running_client:
        running = detect_lol_processes()
        if running:
            names = ", ".join(sorted(running))
            raise ImporterError(f"close League of Legends before installing item sets: {names}")

    plan = build_install_plan(item_sets, config_dir, champion_map=champion_map, target=target, prefix=prefix)
    planned_paths = [entry[0] for entry in plan]
    if not install:
        return InstallResult(planned=planned_paths, written=[], removed=[], backup_dir=None)

    backup_dir = create_backup(config_dir, prefix)
    removed = remove_old_generated_files(config_dir, prefix, backup_dir) if replace_old else []
    written: list[Path] = []
    for destination, payload in plan:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(destination)

    return InstallResult(planned=planned_paths, written=written, removed=removed, backup_dir=backup_dir)


def build_install_plan(
    item_sets: list[dict[str, Any]],
    config_dir: Path,
    *,
    champion_map: dict[int, str] | None,
    target: str,
    prefix: str,
) -> list[tuple[Path, dict[str, Any]]]:
    if target not in {"champion", "global"}:
        raise ImporterError("target must be 'champion' or 'global'")

    plan: list[tuple[Path, dict[str, Any]]] = []
    seen: set[Path] = set()
    for index, item_set in enumerate(item_sets, start=1):
        champions = item_set.get("associatedChampions") or []
        if target == "champion" and champions:
            if champion_map is None:
                raise ImporterError("champion target requires a champion map")
            for champion_id in champions:
                champion_key = champion_map.get(int(champion_id))
                if not champion_key:
                    raise ImporterError(f"unknown champion id from item set '{item_set['title']}': {champion_id}")
                payload = dict(item_set)
                payload["champion"] = champion_key
                destination = (
                    config_dir
                    / "Champions"
                    / champion_key
                    / "Recommended"
                    / build_filename(prefix, index, item_set["title"])
                )
                if destination not in seen:
                    plan.append((destination, payload))
                    seen.add(destination)
        else:
            destination = config_dir / "Global" / "Recommended" / build_filename(prefix, index, item_set["title"])
            if destination not in seen:
                plan.append((destination, item_set))
                seen.add(destination)
    return plan


def build_filename(prefix: str, index: int, title: str) -> str:
    slug = slugify(title)
    return f"{slugify(prefix)}-{index:03d}-{slug}.json"


def slugify(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return normalized[:80] or "item-set"


def create_backup(config_dir: Path, prefix: str) -> Path:
    backup_dir = config_dir / "wrasul-backups" / time.strftime("%Y%m%d-%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    for file_path in find_generated_files(config_dir, prefix):
        relative = file_path.relative_to(config_dir)
        target = backup_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, target)
    return backup_dir


def remove_old_generated_files(config_dir: Path, prefix: str, backup_dir: Path) -> list[Path]:
    removed: list[Path] = []
    backup_root = backup_dir.resolve()
    for file_path in find_generated_files(config_dir, prefix):
        if backup_root in file_path.resolve().parents:
            continue
        file_path.unlink()
        removed.append(file_path)
    return removed


def find_generated_files(config_dir: Path, prefix: str) -> list[Path]:
    if not config_dir.exists():
        return []
    pattern = f"{slugify(prefix)}-*.json"
    roots = [config_dir / "Global" / "Recommended", config_dir / "Champions"]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(path for path in root.rglob(pattern) if path.is_file())
    return sorted(files)


def detect_lol_processes() -> set[str]:
    if os.name != "nt":
        return set()
    try:
        completed = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.CalledProcessError):
        return set()

    running: set[str] = set()
    for line in completed.stdout.splitlines():
        match = re.match(r'"([^"]+)"', line)
        if match and match.group(1) in LOL_PROCESS_NAMES:
            running.add(match.group(1))
    return running


def write_export(item_sets: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(item_sets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def summarize_item_sets(item_sets: list[dict[str, Any]]) -> str:
    champion_refs = sum(len(item_set.get("associatedChampions") or []) for item_set in item_sets)
    block_count = sum(len(item_set["blocks"]) for item_set in item_sets)
    item_count = sum(len(block["items"]) for item_set in item_sets for block in item_set["blocks"])
    return f"{len(item_sets)} item sets, {champion_refs} champion assignments, {block_count} blocks, {item_count} items"


def exit_with_error(message: str) -> int:
    print(f"Error: {message}", file=sys.stderr)
    return 1
