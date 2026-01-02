from __future__ import annotations

import importlib.util
from collections.abc import Mapping
from typing import Any

from .pack import core_pack


def handlers(*, require_http: bool = False) -> Mapping[str, Any]:
    if require_http and importlib.util.find_spec("httpx") is None:
        raise RuntimeError("HTTP nodes require httpx; install arp-jarvis-atomic-nodes[runtime].")
    return core_pack.handlers()
