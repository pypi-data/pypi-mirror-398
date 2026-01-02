import asyncio
from datetime import datetime

from arp_standard_model import AtomicExecuteRequest, NodeTypeRef

from jarvis_atomic_nodes import __version__
from jarvis_atomic_nodes.catalog import node_types
from jarvis_atomic_nodes.handlers import handlers


def _request(node_type_id: str, inputs: dict[str, object]) -> AtomicExecuteRequest:
    return AtomicExecuteRequest(
        node_run_id="n1",
        run_id="r1",
        node_type_ref=NodeTypeRef(node_type_id=node_type_id, version=__version__),
        inputs=inputs,
    )


async def _call(handler, request: AtomicExecuteRequest) -> dict[str, object]:
    return await handler(request)


def test_node_types_contains_core_and_http() -> None:
    ids = {node.node_type_id for node in node_types()}
    assert {
        "jarvis.core.echo",
        "jarvis.core.sleep",
        "jarvis.core.uuid4",
        "jarvis.core.time.now",
        "jarvis.core.hash.sha256",
        "jarvis.web.fetch",
    }.issubset(ids)


def test_core_handlers_roundtrip() -> None:
    registry = handlers(require_http=False)

    echo = registry["jarvis.core.echo"]
    result = asyncio.run(_call(echo, _request("jarvis.core.echo", {"ping": "pong"})))
    assert result == {"echo": {"ping": "pong"}}

    uuid_out = asyncio.run(_call(registry["jarvis.core.uuid4"], _request("jarvis.core.uuid4", {})))
    assert isinstance(uuid_out.get("uuid4"), str)

    time_out = asyncio.run(_call(registry["jarvis.core.time.now"], _request("jarvis.core.time.now", {})))
    assert isinstance(time_out["time"], str)
    datetime.fromisoformat(time_out["time"])

    sha_out = asyncio.run(_call(registry["jarvis.core.hash.sha256"], _request("jarvis.core.hash.sha256", {"text": "abc"})))
    assert sha_out["sha256"] == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
