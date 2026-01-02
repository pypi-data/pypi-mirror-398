# JARVIS Atomic Nodes (Node Pack)

First-party “node pack” for the JARVIS stack. This package provides:
- **NodeType metadata** for Node Registry + Selection
- **Atomic handler implementations** for Atomic Executor

This is a trusted, in-process node pack (v0.x). It does **not** implement runtime code download.

## Install

Metadata-only (safe for Node Registry):

```bash
python3 -m pip install arp-jarvis-atomic-nodes
```

Or explicitly:

```bash
python3 -m pip install "arp-jarvis-atomic-nodes[metadata]"
```

Runtime handlers (Atomic Executor):

```bash
python3 -m pip install "arp-jarvis-atomic-nodes[runtime]"
```

## Usage

### NodeType metadata (Node Registry)

```python
from jarvis_atomic_nodes.catalog import node_types

node_type_list = node_types()
```

### Handler registry (Atomic Executor)

```python
from jarvis_atomic_nodes.handlers import handlers

handler_map = handlers(require_http=True)
```

### Authoring nodes (LangChain-like)

```python
from pydantic import BaseModel, HttpUrl
from jarvis_atomic_nodes.sdk import atomic_node, NodeContext

class WebFetchIn(BaseModel):
    url: HttpUrl

class WebFetchOut(BaseModel):
    status_code: int
    content_base64: str

@atomic_node(name="jarvis.web.fetch", side_effect="read")
async def web_fetch(inp: WebFetchIn, ctx: NodeContext) -> WebFetchOut:
    """Fetch a URL over HTTP(S) and return bytes."""
    resp = await ctx.http.get(str(inp.url))
    return WebFetchOut(status_code=resp.status_code, content_base64=resp.content)
```

### Entry point discovery

This package exposes a NodePack entry point:

- group: `jarvis.nodepacks`
- name: `jarvis.core`
- object: `jarvis_atomic_nodes.pack:core_pack`

```python
from jarvis_atomic_nodes.discovery import load_nodepacks, load_handlers, load_node_types

packs = load_nodepacks()
handlers = load_handlers()
node_types = load_node_types()
```

## Included nodes (v0.3.1 baseline)

Core:
- `jarvis.core.echo`
- `jarvis.core.sleep`
- `jarvis.core.uuid4`
- `jarvis.core.time.now`
- `jarvis.core.hash.sha256`

HTTP:
- `jarvis.web.fetch`
