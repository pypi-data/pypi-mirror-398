# src/paramiko_batch/models.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, List
import time

@dataclass(frozen=True)
class Command:
    cmd: str
    timeout: Optional[float] = None
    env: Optional[Dict[str, str]] = None
    cwd: Optional[str] = None
    sudo: bool = False
    name: Optional[str] = None  # for nicer batch output

@dataclass
class CommandResult:
    command: Command
    exit_status: Optional[int]
    stdout: str
    stderr: str
    started_at: float
    finished_at: float

    @property
    def ok(self) -> bool:
        return self.exit_status == 0

    @property
    def duration_s(self) -> float:
        return self.finished_at - self.started_at

@dataclass(frozen=True)
class BatchPolicy:
    stop_on_failure: bool = True

@dataclass
class BatchResult:
    results: List[CommandResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(r.ok for r in self.results)

    @property
    def failed(self) -> List[CommandResult]:
        return [r for r in self.results if not r.ok]
