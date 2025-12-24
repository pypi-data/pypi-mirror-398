from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    line: int
    col: int
    reason: str | None = None

    def format(self) -> str:
        head = f"⚠ {self.message} (line {self.line}:{self.col})"
        if self.reason:
            return f"{head}\nReason: {self.reason}"
        return head
