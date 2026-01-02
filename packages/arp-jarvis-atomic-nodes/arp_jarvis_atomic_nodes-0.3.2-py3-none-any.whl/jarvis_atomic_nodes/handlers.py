from __future__ import annotations

import importlib.util
from collections.abc import Callable, Mapping
from typing import Any

from arp_standard_model import AtomicExecuteRequest

from .pack import core_pack


AtomicHandler = Callable[[AtomicExecuteRequest], Any]


def handlers(*, require_http: bool = False) -> Mapping[str, AtomicHandler]:
    if require_http and importlib.util.find_spec("httpx") is None:
        raise RuntimeError("HTTP nodes require httpx; install arp-jarvis-atomic-nodes[runtime].")
    return core_pack.handlers()
