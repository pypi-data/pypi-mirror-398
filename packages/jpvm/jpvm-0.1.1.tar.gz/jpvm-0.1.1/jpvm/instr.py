# jpvm/instr.py
from dataclasses import dataclass
from typing import Any

@dataclass
class Instr:
    op: str
    arg: Any = None
