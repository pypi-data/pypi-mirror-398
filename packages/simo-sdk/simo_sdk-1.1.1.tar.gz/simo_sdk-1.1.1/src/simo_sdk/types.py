from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


JSON = Any


@dataclass(frozen=True)
class FeedEvent:
    model: str
    obj_id: int
    instance_uid: str
    payload: Mapping[str, Any]


FeedCallback = Callable[[FeedEvent], None]

