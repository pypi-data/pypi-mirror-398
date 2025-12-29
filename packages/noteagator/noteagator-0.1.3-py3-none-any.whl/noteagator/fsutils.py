import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from .note import Note
from .print_utils import add_colors


class bcolors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_directory_structure(
    c_cwd: str, c_base: str, max_depth=None
) -> dict[str, Any]:
    path = c_cwd
    base = c_base
    note_dir = path.replace(base, "/").replace("\\", "/").replace("//", "/")
    print(f"Notebook Directory: {bcolors.BLUE}{note_dir}{bcolors.ENDC}")
    folder_emoji = "📁"
    file_emoji = "📄"
    structure = {}
    index_counter = 1

    def traverse_and_print(current_path, current_depth, indent=0):
        nonlocal index_counter

        if max_depth is not None and current_depth > max_depth:
            return

        if current_depth > 0:
            print(
                " " * indent
                + f"{index_counter} {folder_emoji} {os.path.basename(current_path)}"
            )
            structure[index_counter] = {"type": "dir", "absolute_path": current_path}
            index_counter += 1

        if max_depth is None or current_depth < max_depth:
            try:
                with os.scandir(current_path) as it:
                    entries = [e for e in it if not (e.is_dir() and e.name == ".git")]
            except PermissionError:
                return

            dirs = sorted(
                (e for e in entries if e.is_dir()), key=lambda e: e.name.lower()
            )
            files = sorted(
                (e for e in entries if e.is_file()), key=lambda e: e.name.lower()
            )

            for entry in dirs:
                traverse_and_print(entry.path, current_depth + 1, indent + 2)

            for entry in files:
                entry_path = entry.path
                description = return_description(entry_path)
                print(
                    " " * (indent + 2)
                    + f"{index_counter} {file_emoji} {entry.name} {description}"
                )
                structure[index_counter] = {"type": "file", "absolute_path": entry_path}
                index_counter += 1

    traverse_and_print(path, current_depth=0)
    return structure


def return_description(entry_path: str) -> str:
    try:
        n = Note(entry_path)
        if not n.description:
            return ""
        else:
            return f" - {add_colors(n.description)}"
    except Exception:
        return ""


def resolve_cd_target(
    arg: str, entry_path: str | None, node_type: str | None, cwd: str, base: str
) -> str:
    if entry_path:
        return entry_path if node_type == "dir" else os.path.dirname(entry_path)
    if arg == ".." and cwd != base:
        return str(Path(cwd).parent)
    if arg == "/":
        return base
    return cwd


def search_files(
    path: str,
    search_term: str,
    exclude_dirs=None,
    *,
    tags_all: Iterable[str] = (),
    tags_any: Iterable[str] = (),
) -> dict[str, Any]:
    exclude_dirs = set(exclude_dirs or {".git"})
    search_term_lower = search_term.lower()

    tags_all_set = {t.strip().lower() for t in tags_all if str(t).strip()}
    tags_any_set = {t.strip().lower() for t in tags_any if str(t).strip()}
    tag_filtering = bool(tags_all_set or tags_any_set)

    index = 1
    display_index: dict[int, Any] = {}

    for root, dirs, files in os.walk(path, topdown=True):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file == ".git":
                continue

            file_path = os.path.join(root, file)
            if tag_filtering:
                note_tags = _extract_tags_fast(file_path)

                if tags_all_set and not tags_all_set.issubset(note_tags):
                    continue
                if tags_any_set and not (note_tags & tags_any_set):
                    continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if search_term_lower in line.lower():
                            rel_path = (
                                file_path.replace(path, "/")
                                .replace("//", "/")
                                .replace("\\", "/")
                            )
                            print(f"{index} {rel_path} {return_description(file_path)}")
                            display_index[index] = {
                                "type": "file",
                                "absolute_path": file_path,
                            }
                            index += 1
                            break
            except Exception as e:
                print(f"Error reading file '{file_path}': {e}")

    return display_index


def append_jot(base_path: str | Path, text: str) -> None:
    now = datetime.now()
    note_dir = Path(base_path).expanduser().resolve() / "jots"
    note_dir.mkdir(parents=True, exist_ok=True)
    note_file = note_dir / f"{now.strftime('%m-%d-%Y')}.md"
    prefix = "\n"
    suffix = "" if text.endswith("\n") else "\n"
    with open(note_file, "a", encoding="utf-8") as f:
        f.write(f"{prefix}{text}{suffix}")


def verify_path(path: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_dir():
        sys.exit(f"'{p}' does not exist or is not a directory.")
    else:
        return str(p)


def _extract_tags_fast(file_path: str, *, max_bytes: int = 16_384) -> set[str]:
    try:
        with open(file_path, "rb") as f:
            head = f.read(max_bytes)
    except Exception:
        return set()

    text = head.decode("utf-8", errors="ignore")

    if not text.startswith("---"):
        return set()

    end_idx = text.find("\n---", 3)
    if end_idx == -1:
        end_idx = text.find("\r\n---", 3)
        if end_idx == -1:
            return set()

    fm = text[:end_idx].splitlines()

    tags: set[str] = set()
    in_tags_block = False

    for raw_line in fm[1:]:
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        lower = line.lower()

        if lower.startswith("tags:"):
            in_tags_block = True
            after = line.split(":", 1)[1].strip()

            if after.startswith("[") and after.endswith("]"):
                inner = after[1:-1].strip()
                if inner:
                    for item in inner.split(","):
                        t = item.strip().strip('"').strip("'").lower()
                        if t:
                            tags.add(t)
                in_tags_block = False
            elif after:
                t = after.strip().strip('"').strip("'").lower()
                if t:
                    tags.add(t)
                in_tags_block = False
            continue

        if in_tags_block:
            if ":" in line and not line.startswith("-"):
                in_tags_block = False
                continue

            if line.startswith("-"):
                item = line[1:].strip().strip('"').strip("'").lower()
                if item:
                    tags.add(item)

    return tags
