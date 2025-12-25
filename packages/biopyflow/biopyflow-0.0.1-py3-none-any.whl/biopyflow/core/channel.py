from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class Channel:
    """
    Lightweight data conduit that remembers producers/consumers for DAG wiring.
    """

    name: str
    val: Any = None
    producers: List["Step"] = field(default_factory=list)
    consumers: List["Step"] = field(default_factory=list)