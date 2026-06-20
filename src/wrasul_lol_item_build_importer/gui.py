from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

from .importer import (
    DEFAULT_PREFIX,
    ImporterError,
    extract_item_sets,
    install_item_sets,
    load_champion_map,
    load_source,
    summarize_item_sets,
)


APP_TITLE = "Wrasul LOL 装备导入器"
DEFAULT_SOURCE_URL = "https://www.bilibili.com/opus/1213040949301608448"
COMMON_LOL_DIRS = (
    Path(r"C:\Riot Games\League of Legends"),
    Path(r"D:\Riot Games\League of Legends"),
)


def find_default_lol_dir(candidates: tuple[Path, ...] = COMMON_LOL_DIRS) -> Path | None:
    for candidate in candidates:
        if is_lol_dir(candidate):
            return candidate
    return None


def is_lol_dir(path: Path) -> bool:
    if not path:
        return False
    expanded = path.expanduser()
    if not expanded.exists() or not expanded.is_dir():
        return False
    return (
        expanded.name.lower() == "league of legends"
        or (expanded / "LeagueClient.exe").exists()
        or (expanded / "Config").exists()
    )


def validate_inputs(source: str, lol_dir: str) -> tuple[str, Path]:
    source = source.strip()
    lol_path = Path(lol_dir.strip()).expanduser()
    if not source:
        raise ImporterError("请先粘贴 B 站动态链接。")
    if not lol_dir.strip():
        raise ImporterError("请选择 League of Legends 文件夹。")
    if not is_lol_dir(lol_path):
        raise ImporterError("请选择有效的 League of Legends 文件夹。")
    return source, lol_path


def friendly_error(message: str) -> str:
    lower = message.lower()
    if "close league of legends" in lower:
        return "请先关闭英雄联盟客户端和游戏，再重新导入。"
    if "could not find a valid" in lower or "no blocks" in lower:
        return "没有找到有效出装 JSON，请检查 B 站链接是否正确。"
    if "source not found" in lower or "failed to fetch source url" in lower:
        return "读取链接失败，请检查网络和 B 站动态链接。"
    if "league of legends directory does not exist" in lower:
        return "请选择有效的 League of Legends 文件夹。"
    if "unknown champion id" in lower or "failed to load champion map" in lower:
        return "英雄数据读取失败，请检查网络后重试。"
    return message


class ImporterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("760x560")
        self.minsize(680, 500)
        self._messages: queue.Queue[tuple[str, str]] = queue.Queue()
        self._worker: threading.Thread | None = None

        default_lol_dir = find_default_lol_dir()
        self.source_var = tk.StringVar(value=DEFAULT_SOURCE_URL)
        self.lol_dir_var = tk.StringVar(value=str(default_lol_dir) if default_lol_dir else "")

        self._build_ui()
        self.after(100, self._drain_messages)

    def _build_ui(self) -> None:
        root = ttk_frame(self, padding=18)
        root.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(root, text=APP_TITLE, font=("Microsoft YaHei UI", 18, "bold"), anchor="w")
        title.pack(fill=tk.X)

        intro = tk.Label(
            root,
            text="粘贴 Wrasul 的 B 站动态链接，确认英雄联盟目录，然后点导入。",
            font=("Microsoft YaHei UI", 10),
            anchor="w",
        )
        intro.pack(fill=tk.X, pady=(4, 18))

        tk.Label(root, text="B 站动态链接", anchor="w").pack(fill=tk.X)
        source_entry = tk.Entry(root, textvariable=self.source_var, font=("Microsoft YaHei UI", 10))
        source_entry.pack(fill=tk.X, pady=(4, 14))

        tk.Label(root, text="League of Legends 文件夹", anchor="w").pack(fill=tk.X)
        path_row = tk.Frame(root)
        path_row.pack(fill=tk.X, pady=(4, 14))
        path_entry = tk.Entry(path_row, textvariable=self.lol_dir_var, font=("Microsoft YaHei UI", 10))
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(path_row, text="浏览...", command=self._browse_lol_dir, width=10).pack(side=tk.LEFT, padx=(8, 0))

        button_row = tk.Frame(root)
        button_row.pack(fill=tk.X, pady=(0, 14))
        self.import_button = tk.Button(
            button_row,
            text="导入出装",
            command=self._start_import,
            height=2,
            font=("Microsoft YaHei UI", 11, "bold"),
        )
        self.import_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_label = tk.Label(button_row, text="准备就绪", width=18, anchor="e")
        self.status_label.pack(side=tk.LEFT, padx=(12, 0))

        tk.Label(root, text="导入日志", anchor="w").pack(fill=tk.X)
        self.log_box = scrolledtext.ScrolledText(root, height=14, wrap=tk.WORD, font=("Consolas", 10))
        self.log_box.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self._log("使用前请关闭英雄联盟客户端和游戏。")
        if not self.lol_dir_var.get():
            self._log("没有自动找到 LoL 目录，请点击“浏览...”选择 League of Legends 文件夹。")

    def _browse_lol_dir(self) -> None:
        selected = filedialog.askdirectory(title="选择 League of Legends 文件夹")
        if selected:
            self.lol_dir_var.set(selected)

    def _start_import(self) -> None:
        try:
            source, lol_dir = validate_inputs(self.source_var.get(), self.lol_dir_var.get())
        except ImporterError as exc:
            messagebox.showerror(APP_TITLE, friendly_error(str(exc)))
            return

        if self._worker and self._worker.is_alive():
            return

        self.import_button.config(state=tk.DISABLED)
        self.status_label.config(text="导入中...")
        self._log("")
        self._log("开始导入。")
        self._worker = threading.Thread(target=self._run_import, args=(source, lol_dir), daemon=True)
        self._worker.start()

    def _run_import(self, source: str, lol_dir: Path) -> None:
        try:
            self._messages.put(("log", "正在读取 B 站动态和出装 JSON..."))
            item_sets = extract_item_sets(load_source(source))
            self._messages.put(("log", f"读取成功：{summarize_item_sets(item_sets)}"))
            self._messages.put(("log", "正在读取英雄数据..."))
            champion_map = load_champion_map()
            self._messages.put(("log", f"英雄数据读取成功：{len(champion_map)} 个英雄"))
            result = install_item_sets(
                item_sets,
                lol_dir,
                champion_map=champion_map,
                target="champion",
                prefix=DEFAULT_PREFIX,
                install=True,
                replace_old=True,
                allow_running_client=False,
            )
            self._messages.put(("log", f"导入完成：写入 {len(result.written)} 个文件。"))
            if result.backup_dir:
                self._messages.put(("log", f"备份位置：{result.backup_dir}"))
            self._messages.put(("done", "导入完成。打开英雄联盟后，在商店的物品方案里查看。"))
        except ImporterError as exc:
            self._messages.put(("error", friendly_error(str(exc))))
        except Exception as exc:  # pragma: no cover - GUI safety net
            self._messages.put(("error", f"导入失败：{exc}"))

    def _drain_messages(self) -> None:
        try:
            while True:
                kind, message = self._messages.get_nowait()
                if kind == "log":
                    self._log(message)
                elif kind == "done":
                    self._log(message)
                    self.status_label.config(text="完成")
                    self.import_button.config(state=tk.NORMAL)
                    messagebox.showinfo(APP_TITLE, message)
                elif kind == "error":
                    self._log(message)
                    self.status_label.config(text="失败")
                    self.import_button.config(state=tk.NORMAL)
                    messagebox.showerror(APP_TITLE, message)
        except queue.Empty:
            pass
        self.after(100, self._drain_messages)

    def _log(self, message: str) -> None:
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)


def ttk_frame(parent: tk.Misc, padding: int) -> tk.Frame:
    frame = tk.Frame(parent, padx=padding, pady=padding)
    return frame


def main() -> None:
    app = ImporterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
