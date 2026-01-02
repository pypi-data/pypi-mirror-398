from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Optional, cast, get_origin, get_type_hints, overload

from arp_standard_model import AtomicExecuteRequest, ConstraintEnvelope, Extensions, NodeKind, NodeType
from pydantic import BaseModel, ConfigDict, Field, RootModel, create_model


class NodeContext(BaseModel):
    """Execution context passed into atomic nodes."""

    run_id: str
    node_run_id: str
    trace_id: str | None = None
    principal: str | None = None
    budgets: dict[str, Any] | None = None
    clients: dict[str, Any] = Field(default_factory=dict)

    @property
    def http(self) -> Any | None:
        return self.clients.get("http")


class AtomicNodeSpec(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    side_effect: str = "read"
    trust_tier: str = "first_party"
    egress_policy: str | None = None
    budget_hints: dict[str, Any] | None = None
    tags: list[str] | None = None
    constraints: dict[str, Any] | None = None
    evaluation: dict[str, Any] | None = None

    def input_schema(self) -> dict[str, Any]:
        return self.input_model.model_json_schema()

    def output_schema(self) -> dict[str, Any]:
        return self.output_model.model_json_schema()


class AtomicNode:
    def __init__(self, spec: AtomicNodeSpec, fn: Callable[..., Any]) -> None:
        self.spec = spec
        self.fn = fn

    async def ainvoke(self, inp: Any, ctx: NodeContext) -> BaseModel:
        input_model = self.spec.input_model.model_validate(inp)
        result = self.fn(input_model, ctx)
        if inspect.isawaitable(result):
            result = await result
        if isinstance(result, self.spec.output_model):
            return result
        return self.spec.output_model.model_validate(result)

    def invoke(self, inp: Any, ctx: NodeContext) -> BaseModel:
        result = self.fn(self.spec.input_model.model_validate(inp), ctx)
        if inspect.isawaitable(result):
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return asyncio.run(_awaitable(result))
            raise RuntimeError("invoke() cannot be used while an event loop is running; use ainvoke().")
        if isinstance(result, self.spec.output_model):
            return result
        return self.spec.output_model.model_validate(result)

    def as_handler(self) -> Callable[[AtomicExecuteRequest], Any]:
        async def _handler(request: AtomicExecuteRequest) -> dict[str, object]:
            ctx = NodeContext(run_id=request.run_id, node_run_id=request.node_run_id)
            output = await self.ainvoke(request.inputs or {}, ctx)
            return output.model_dump(exclude_none=True)

        return _handler


class AtomicNodeV1(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    Input: type[BaseModel]
    Output: type[BaseModel]
    side_effect: str = "read"
    trust_tier: str = "first_party"

    def run(self, inp: BaseModel, ctx: NodeContext) -> BaseModel:  # pragma: no cover - interface
        raise NotImplementedError

    async def arun(self, inp: BaseModel, ctx: NodeContext) -> BaseModel:
        return self.run(inp, ctx)

    def as_node(self) -> AtomicNode:
        spec = AtomicNodeSpec(
            name=self.name,
            description=self.description,
            input_model=self.Input,
            output_model=self.Output,
            side_effect=self.side_effect,
            trust_tier=self.trust_tier,
        )

        async def _call(inp: BaseModel, ctx: NodeContext) -> BaseModel:
            return await self.arun(inp, ctx)

        return AtomicNode(spec=spec, fn=_call)


@overload
def atomic_node(fn: Callable[..., Any]) -> AtomicNode: ...


@overload
def atomic_node(
    *,
    name: str | None = None,
    description: str | None = None,
    infer_schema: bool = True,
    side_effect: str = "read",
    trust_tier: str = "first_party",
    egress_policy: str | None = None,
    budget_hints: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    constraints: dict[str, Any] | None = None,
    evaluation: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Any]], AtomicNode]: ...


def atomic_node(
    fn: Optional[Callable[..., Any]] = None,
    *,
    name: str | None = None,
    description: str | None = None,
    infer_schema: bool = True,
    side_effect: str = "read",
    trust_tier: str = "first_party",
    egress_policy: str | None = None,
    budget_hints: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    constraints: dict[str, Any] | None = None,
    evaluation: dict[str, Any] | None = None,
) -> Callable[[Callable[..., Any]], AtomicNode] | AtomicNode:
    def _wrap(fn: Callable[..., Any]) -> AtomicNode:
        spec = _spec_from_callable(
            fn,
            name=name,
            description=description,
            infer_schema=infer_schema,
            side_effect=side_effect,
            trust_tier=trust_tier,
            egress_policy=egress_policy,
            budget_hints=budget_hints,
            tags=tags,
            constraints=constraints,
            evaluation=evaluation,
        )
        return AtomicNode(spec=spec, fn=fn)

    return _wrap if fn is None else _wrap(fn)


@dataclass(frozen=True)
class NodePack:
    pack_id: str
    version: str
    nodes: Iterable[AtomicNode]

    def node_types(self) -> list[NodeType]:
        return [node_to_node_type(self.pack_id, self.version, node) for node in self.nodes]

    def handlers(self) -> Mapping[str, Callable[[AtomicExecuteRequest], Any]]:
        return {node.spec.name: node.as_handler() for node in self.nodes}


def node_to_node_type(pack_id: str, version: str, node: AtomicNode) -> NodeType:
    extensions: dict[str, Any] = {
        "jarvis.pack_id": pack_id,
        "jarvis.pack_version": version,
        "jarvis.node_name": node.spec.name,
        "jarvis.side_effect": node.spec.side_effect,
        "jarvis.trust_tier": node.spec.trust_tier,
    }
    if node.spec.egress_policy is not None:
        extensions["jarvis.egress_policy"] = node.spec.egress_policy
    if node.spec.budget_hints is not None:
        extensions["jarvis.budget_hints"] = node.spec.budget_hints
    if node.spec.tags is not None:
        extensions["jarvis.tags"] = node.spec.tags

    return NodeType(
        node_type_id=node.spec.name,
        version=version,
        kind=NodeKind.atomic,
        description=node.spec.description,
        input_schema=node.spec.input_schema(),
        output_schema=node.spec.output_schema(),
        constraints=ConstraintEnvelope.model_validate(node.spec.constraints)
        if node.spec.constraints is not None
        else None,
        evaluation=node.spec.evaluation,
        extensions=Extensions.model_validate(extensions),
    )


def _spec_from_callable(
    fn: Callable[..., Any],
    *,
    name: str | None,
    description: str | None,
    infer_schema: bool,
    side_effect: str,
    trust_tier: str,
    egress_policy: str | None,
    budget_hints: dict[str, Any] | None,
    tags: list[str] | None,
    constraints: dict[str, Any] | None,
    evaluation: dict[str, Any] | None,
) -> AtomicNodeSpec:
    if not infer_schema:
        raise ValueError("infer_schema=False is not supported in this reference implementation.")

    hints = get_type_hints_safe(fn)
    input_model = _infer_input_model(fn, hints)
    output_model = _infer_output_model(hints)
    if output_model is None:
        raise ValueError("Return annotation is required to infer output schema.")

    desc = description or (inspect.getdoc(fn) or "").strip()
    if not desc:
        desc = f"Atomic node: {fn.__name__}"

    return AtomicNodeSpec(
        name=name or fn.__name__,
        description=desc,
        input_model=input_model,
        output_model=output_model,
        side_effect=side_effect,
        trust_tier=trust_tier,
        egress_policy=egress_policy,
        budget_hints=budget_hints,
        tags=tags,
        constraints=constraints,
        evaluation=evaluation,
    )


def _infer_input_model(fn: Callable[..., Any], hints: dict[str, Any]) -> type[BaseModel]:
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    data_params = [param for param in params if not _is_context_param(param, hints)]

    if not data_params:
        return create_model(f"{fn.__name__}Input")

    if len(data_params) == 1:
        annotation = hints.get(data_params[0].name, data_params[0].annotation)
        model = _annotation_to_model(annotation, f"{fn.__name__}Input")
        if model is not None:
            return model

    fields: dict[str, tuple[Any, Any]] = {}
    for param in data_params:
        annotation = hints.get(param.name, param.annotation)
        if annotation is inspect._empty:
            annotation = Any
        default = param.default if param.default is not inspect._empty else ...
        fields[param.name] = (annotation, default)
    return create_model(f"{fn.__name__}Input", **cast(dict[str, Any], fields))


def _infer_output_model(hints: dict[str, Any]) -> type[BaseModel] | None:
    annotation = hints.get("return")
    if annotation is None or annotation is inspect._empty:
        return None
    model = _annotation_to_model(annotation, "Output")
    if model is not None:
        return model
    if annotation is Any:
        return RootModel[Any]  # type: ignore[valid-type]
    return None


def _annotation_to_model(annotation: Any, name: str) -> type[BaseModel] | None:
    if annotation is inspect._empty:
        return None
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    origin = get_origin(annotation)
    if origin in (dict, Mapping):
        return RootModel[dict[str, Any]]  # type: ignore[valid-type]
    return None


def _is_context_param(param: inspect.Parameter, hints: dict[str, Any]) -> bool:
    annotation = hints.get(param.name, param.annotation)
    if annotation is NodeContext:
        return True
    return param.name in {"ctx", "context"} and annotation is inspect._empty


def get_type_hints_safe(fn: Callable[..., Any]) -> dict[str, Any]:
    return get_type_hints(fn)


async def _awaitable(result: Any) -> Any:
    return await result
