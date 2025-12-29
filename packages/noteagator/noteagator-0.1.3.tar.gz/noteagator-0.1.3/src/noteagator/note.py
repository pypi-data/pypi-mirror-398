import re
from functools import cached_property
from pathlib import Path
from typing import Any, Dict

import yaml

_YAML_FRONT_MATTER_RE = re.compile(
    r"^(?:\ufeff)?---[ \t]*\r?\n"
    r"(?P<meta>.*?)"
    r"(?:\r?\n)?"
    r"---[ \t]*\r?\n"
    r"(?P<body>.*)\Z",
    re.DOTALL,
)


class Note:
    def __init__(self, note_path: str) -> None:
        self._note_path = note_path
        self._raw_note: str = Path(note_path).read_text(encoding="utf-8")
        self._match = _YAML_FRONT_MATTER_RE.match(self._raw_note)

    @property
    def raw_note(self) -> str:
        return self._raw_note

    @cached_property
    def metadata(self) -> Dict[str, Any]:
        if not self._match:
            return {"note": self._note_path}
        yaml_text = self._match.group("meta")
        try:
            meta = yaml.safe_load(yaml_text)
            if not isinstance(meta, dict):
                meta = {"note": self._note_path}
        except yaml.YAMLError:
            meta = {"note": self._note_path}
        meta["note"] = self._note_path
        return meta

    @cached_property
    def body(self) -> str:
        if not self._match:
            return self.raw_note
        body = self._match.group("body")
        if body.startswith("\r\n"):
            body = body[2:]
        elif body.startswith("\n"):
            body = body[1:]
        return body

    @cached_property
    def description(self) -> str:
        return self.metadata.get("description", "")

    @raw_note.setter
    def raw_note(self, value: str) -> None:
        self._raw_note = value
        self._match = _YAML_FRONT_MATTER_RE.match(self._raw_note)
        for key in ("metadata", "body", "description"):
            self.__dict__.pop(key, None)
