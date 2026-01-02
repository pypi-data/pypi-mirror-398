from __future__ import annotations

from . import __version__
from .http_nodes import web_fetch
from .core_nodes import core_echo, core_hash_sha256, core_sleep, core_time_now, core_uuid4
from .sdk import NodePack

core_pack = NodePack(
    pack_id="jarvis.core",
    version=__version__,
    nodes=[
        core_echo,
        core_sleep,
        core_uuid4,
        core_time_now,
        core_hash_sha256,
        web_fetch,
    ],
)

