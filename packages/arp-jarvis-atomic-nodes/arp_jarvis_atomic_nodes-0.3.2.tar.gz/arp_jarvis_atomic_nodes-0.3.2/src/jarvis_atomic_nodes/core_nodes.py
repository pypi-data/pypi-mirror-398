from __future__ import annotations

import asyncio
import base64
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, RootModel, model_validator

from .sdk import NodeContext, atomic_node


class EchoInput(RootModel[dict[str, Any]]):
    pass


class EchoOutput(BaseModel):
    echo: dict[str, Any]


@atomic_node(name="jarvis.core.echo", side_effect="read")
async def core_echo(inp: EchoInput, ctx: NodeContext) -> EchoOutput:
    """Return inputs as-is under the `echo` field."""
    _ = ctx
    return EchoOutput(echo=inp.root)




class SleepInput(BaseModel):
    seconds: float | None = None
    duration_seconds: float | None = None


class SleepOutput(BaseModel):
    slept_seconds: float


@atomic_node(name="jarvis.core.sleep", side_effect="read")
async def core_sleep(inp: SleepInput, ctx: NodeContext) -> SleepOutput:
    """Sleep for a number of seconds (best-effort)."""
    _ = ctx
    seconds = inp.seconds if inp.seconds is not None else (inp.duration_seconds or 0.0)
    if seconds < 0:
        raise ValueError("seconds must be >= 0")
    if seconds:
        await asyncio.sleep(seconds)
    return SleepOutput(slept_seconds=seconds)


class Uuid4Input(BaseModel):
    pass


class Uuid4Output(BaseModel):
    uuid4: str


@atomic_node(name="jarvis.core.uuid4", side_effect="read")
async def core_uuid4(inp: Uuid4Input, ctx: NodeContext) -> Uuid4Output:
    """Generate a UUIDv4 string."""
    _ = inp, ctx
    return Uuid4Output(uuid4=str(uuid.uuid4()))


class TimeNowInput(BaseModel):
    pass


class TimeNowOutput(BaseModel):
    time: str


@atomic_node(name="jarvis.core.time.now", side_effect="read")
async def core_time_now(inp: TimeNowInput, ctx: NodeContext) -> TimeNowOutput:
    """Return the current UTC time in ISO-8601 format."""
    _ = inp, ctx
    return TimeNowOutput(time=datetime.now(timezone.utc).isoformat())


class HashSha256Input(BaseModel):
    content_base64: str | None = None
    text: str | None = None
    encoding: str = "utf-8"

    @model_validator(mode="after")
    def _validate_source(self) -> "HashSha256Input":
        if self.content_base64 is None and self.text is None:
            raise ValueError("Provide either content_base64 or text")
        return self


class HashSha256Output(BaseModel):
    sha256: str


@atomic_node(name="jarvis.core.hash.sha256", side_effect="read")
async def core_hash_sha256(inp: HashSha256Input, ctx: NodeContext) -> HashSha256Output:
    """Compute SHA-256 for text or base64 content."""
    _ = ctx
    if inp.content_base64 is not None:
        data = base64.b64decode(inp.content_base64.encode("utf-8"), validate=True)
    else:
        data = (inp.text or "").encode(inp.encoding)
    digest = hashlib.sha256(data).hexdigest()
    return HashSha256Output(sha256=digest)
