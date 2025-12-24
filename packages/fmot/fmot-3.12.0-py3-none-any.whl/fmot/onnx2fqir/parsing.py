import numpy as np
from dataclasses import dataclass, field
from typing import Any, Optional

try:
    import onnx
    from onnx import numpy_helper, defs
    from onnx.helper import tensor_dtype_to_np_dtype
except ImportError as e:
    raise Exception(
        f"Exception was {e}. We probably couldn't import tf/onnx. "
        f"Please install with onnx extra requires. e.g. pip install fmot[onnx2fqir]"
    )

__all__ = ["ParsedTensor", "ParsedOperator", "ParsedGraph", "parse_onnx_graph"]


@dataclass
class ParsedTensor:
    name: str
    shape: list[Any]
    dtype: Any
    value: Optional[np.ndarray] = field(default=None, repr=False)
    data_location: Optional[int] = field(default=None, repr=False)
    doc_string: str = field(default_factory=lambda: "", repr=False)

    def __hash__(self):
        return hash(self.name)


@dataclass
class ParsedOperator:
    name: str
    op_type: str
    domain: str
    inputs: dict[str, ParsedTensor]  # formal_name -> tensor
    outputs: dict[str, ParsedTensor]  # formal_name -> tensor
    attributes: dict[str, Any]
    subgraphs: dict[str, "ParsedGraph"]

    def __hash__(self):
        return hash(self.name)


@dataclass
class ParsedGraph:
    name: str
    inputs: dict[str, ParsedTensor]
    parameters: dict[str, ParsedTensor]
    outputs: dict[str, ParsedTensor]
    value_info: dict[str, ParsedTensor]
    nodes: list[ParsedOperator]

    def __hash__(self):
        return hash(self.name)


# ------------ helpers (unchanged parts omitted for brevity) ------------


def _shape_and_dtype_from_value_info(vi: onnx.ValueInfoProto):
    tt = vi.type.tensor_type
    dtype = tensor_dtype_to_np_dtype(tt.elem_type) if tt.elem_type else None
    shape = []
    if tt.HasField("shape"):
        for d in tt.shape.dim:
            if d.HasField("dim_value"):
                shape.append(d.dim_value)
            elif d.HasField("dim_param"):
                shape.append(d.dim_param)
            else:
                shape.append(None)
    return shape, dtype


def _tensorinfo_from_initializer(t: onnx.TensorProto) -> ParsedTensor:
    arr = numpy_helper.to_array(t)
    return ParsedTensor(
        name=t.name,
        shape=list(arr.shape),
        dtype=arr.dtype,
        value=arr,
        data_location=t.data_location if t.HasField("data_location") else None,
        doc_string="",
    )


def _tensorinfo_from_valueinfo(vi: onnx.ValueInfoProto) -> ParsedTensor:
    shape, dtype = _shape_and_dtype_from_value_info(vi)
    return ParsedTensor(
        name=vi.name,
        shape=shape,
        dtype=dtype,
        value=None,
        data_location=None,
        doc_string=getattr(vi, "doc_string", "") or "",
    )


def _unknown_tensorinfo(name: str) -> ParsedTensor:
    return ParsedTensor(name=name, shape=[], dtype=None, value=None)


def _parse_attribute(attr: onnx.AttributeProto) -> Any:
    from onnx import AttributeProto as AP

    if attr.type == AP.FLOAT:
        return float(attr.f)
    if attr.type == AP.INT:
        return int(attr.i)
    if attr.type == AP.STRING:
        return (
            attr.s.decode("utf-8", "ignore")
            if isinstance(attr.s, (bytes, bytearray))
            else str(attr.s)
        )
    if attr.type == AP.TENSOR:
        return numpy_helper.to_array(attr.t)
    if attr.type == AP.SPARSE_TENSOR:
        return {"sparse_tensor": "unsupported_here"}
    if attr.type == AP.FLOATS:
        return [float(x) for x in attr.floats]
    if attr.type == AP.INTS:
        return [int(x) for x in attr.ints]
    if attr.type == AP.STRINGS:
        return [
            x.decode("utf-8", "ignore") if isinstance(x, (bytes, bytearray)) else str(x)
            for x in attr.strings
        ]
    if attr.type == AP.TENSORS:
        return [numpy_helper.to_array(t) for t in attr.tensors]
    return None


# -------- NEW: schema -> formal I/O names --------

# Common formal I/O for contrib/quant ops (domain-insensitive override)
# see: https://github.com/microsoft/onnxruntime/blob/main/docs/ContribOperators.md
# and https://github.com/onnx/onnx/blob/main/docs/Operators.md
FORMAL_IO_OVERRIDES: dict[str, tuple[list[str], list[str]]] = {
    "QLinearConv": (
        [
            "x",
            "x_scale",
            "x_zero_point",
            "w",
            "w_scale",
            "w_zero_point",
            "y_scale",
            "y_zero_point",
            "B",
        ],
        ["y"],
    ),
    "QLinearMatMul": (
        [
            "a",
            "a_scale",
            "a_zero_point",
            "b",
            "b_scale",
            "b_zero_point",
            "y_scale",
            "y_zero_point",
        ],
        ["y"],
    ),
    "QuantizeLinear": (["x", "y_scale", "y_zero_point"], ["y"]),
    "DequantizeLinear": (["x", "x_scale", "x_zero_point"], ["y"]),
    "Transpose": (["data"], ["transposed"]),
    "Reshape": (["data", "shape"], ["reshaped"]),
    "QLinearSoftmax": (
        ["x", "x_scale", "x_zero_point", "y_scale", "y_zero_point"],
        ["y"],
    ),
    "Unsqueeze": (["data", "axes"], ["expanded"]),
    "Squeeze": (["data", "axes"], ["squeezed"]),
    "QLinearMul": (
        [
            "a",
            "a_scale",
            "a_zero_point",
            "b",
            "b_scale",
            "b_zero_point",
            "y_scale",
            "y_zero_point",
        ],
        ["y"],
    ),
    "QLinearAdd": (
        [
            "a",
            "a_scale",
            "a_zero_point",
            "b",
            "b_scale",
            "b_zero_point",
            "y_scale",
            "y_zero_point",
        ],
        ["y"],
    ),
}


def _formal_io_names(
    op_type: str,
    domain: str,
    num_inputs: int,
    num_outputs: int,
    opset_imports: Optional[dict[str, int]] = None,
):
    """
    Returns two lists of formal input/output names sized to the actual counts.
    Falls back to ai.onnx and to overrides for contrib ops (e.g., com.microsoft).
    """

    # 1) Try to fetch a schema for the declared domain/version
    def try_schema(dom: str):
        # pick a version <= model's declared version for this domain, else use global latest
        if opset_imports and dom in opset_imports:
            ver = opset_imports[dom]
        else:
            ver = defs.onnx_opset_version()
        try:
            return defs.get_schema(op_type, dom, ver)
        except Exception:
            return None

    schema = try_schema(domain or "")
    # 2) If not found and domain looks contrib, try the standard domain (ai.onnx / "")
    if schema is None:
        for alt in ("ai.onnx", ""):
            schema = try_schema(alt)
            if schema is not None:
                break

    # 3) If still nothing, try the override table (domain-insensitive)
    if schema is None and op_type in FORMAL_IO_OVERRIDES:
        base_in, base_out = FORMAL_IO_OVERRIDES[op_type]

        def expand(base, n):
            if not base:
                return [f"input_{i}" for i in range(n)]
            out = []
            while len(out) < n:
                if len(out) < len(base):
                    out.append(base[len(out)])
                else:
                    # repeat last with suffix for variadics
                    out.append(f"{base[-1]}_{len(out)-(len(base)-1)}")
            return out

        return expand(base_in, num_inputs), expand(base_out, num_outputs)

    # 4) Normal path: expand schema-provided names (handling variadics)
    def expand(names_from_schema, actual_count, fallback_prefix):
        if not names_from_schema:
            return [f"{fallback_prefix}_{i}" for i in range(actual_count)]
        base_names = [p.name for p in names_from_schema]
        out = []
        idx = 0
        while len(out) < actual_count:
            if idx < len(base_names):
                out.append(base_names[idx])
            else:
                last = base_names[-1] if base_names else fallback_prefix
                out.append(f"{last}_{len(out)-(len(base_names)-1)}")
            idx += 1
        return out

    if schema is None:
        # final fallback: positional keys
        return [f"input_{i}" for i in range(num_inputs)], [
            f"output_{i}" for i in range(num_outputs)
        ]

    return (
        expand(schema.inputs, num_inputs, "input"),
        expand(schema.outputs, num_outputs, "output"),
    )


# ---------- Main parser (only node loop changed) ----------


def parse_onnx_graph(
    model: onnx.ModelProto,
    *,
    graph_name: Optional[str] = None,
    opset_imports: Optional[dict[str, int]] = None,
) -> ParsedGraph:
    if opset_imports is None:
        opset_imports = {imp.domain or "": imp.version for imp in model.opset_import}

    graph = model.graph

    gname = graph_name or (graph.name if hasattr(graph, "name") else "")

    # 1) parameters
    parameters: dict[str, ParsedTensor] = {}
    for init in graph.initializer:
        parameters[init.name] = _tensorinfo_from_initializer(init)

    # 2) value_info
    value_info: dict[str, ParsedTensor] = {}
    for vi in list(graph.input) + list(graph.value_info) + list(graph.output):
        if vi.name not in value_info and vi.name not in parameters:
            value_info[vi.name] = _tensorinfo_from_valueinfo(vi)

    # 3) runtime inputs
    init_names = set(parameters.keys())
    inputs: dict[str, ParsedTensor] = {}
    for vi in graph.input:
        if vi.name not in init_names:
            inputs[vi.name] = _tensorinfo_from_valueinfo(vi)

    # 4) graph outputs
    outputs: dict[str, ParsedTensor] = {}
    for vo in graph.output:
        outputs[vo.name] = value_info.get(vo.name, _tensorinfo_from_valueinfo(vo))

    # 5) Constant nodes -> parameters
    for node in graph.node:
        if node.op_type == "Constant":
            out_names = [n for n in node.output if n]
            if not out_names:
                continue
            out_name = out_names[0]
            val_attr = next(
                (a for a in node.attribute if a.name == "value" and a.HasField("t")),
                None,
            )
            if val_attr is not None:
                arr = numpy_helper.to_array(val_attr.t)
                parameters[out_name] = ParsedTensor(
                    name=out_name,
                    shape=list(arr.shape),
                    dtype=arr.dtype,
                    value=arr,
                    data_location=val_attr.t.data_location
                    if val_attr.t.HasField("data_location")
                    else None,
                )
                value_info[out_name] = parameters[out_name]

    def resolve_tensor(name: str) -> ParsedTensor:
        if not name:
            return _unknown_tensorinfo(name)
        if name in parameters:
            return parameters[name]
        if name in value_info:
            return value_info[name]
        ti = _unknown_tensorinfo(name)
        value_info[name] = ti
        return ti

    # 6) nodes
    nodes: list[ParsedOperator] = []
    for node in graph.node:
        # Get formal names for this (domain, op_type)
        fin_names, fout_names = _formal_io_names(
            node.op_type,
            node.domain or "",
            len(node.input),
            len(node.output),
            opset_imports=opset_imports,
        )

        # Build dicts keyed by formal names
        in_dict: dict[str, ParsedTensor] = {}
        for formal, actual in zip(fin_names, node.input):
            if actual:  # may be empty for optional
                in_dict[formal] = resolve_tensor(actual)

        out_dict: dict[str, ParsedTensor] = {}
        for formal, actual in zip(fout_names, node.output):
            if actual:
                out_dict[formal] = resolve_tensor(actual)

        # Attributes / subgraphs
        attrs: dict[str, Any] = {}
        subgraphs: dict[str, ParsedGraph] = {}
        for a in node.attribute:
            if a.HasField("g"):
                subgraphs[a.name] = parse_onnx_graph(
                    a.g,
                    graph_name=a.g.name or f"{node.name}:{a.name}",
                    opset_imports=opset_imports,
                )
                continue
            if a.graphs:
                for i, gsub in enumerate(a.graphs):
                    subgraphs[f"{a.name}_{i}"] = parse_onnx_graph(
                        gsub,
                        graph_name=gsub.name or f"{node.name}:{a.name}_{i}",
                        opset_imports=opset_imports,
                    )
                continue
            attrs[a.name] = _parse_attribute(a)

        nodes.append(
            ParsedOperator(
                name=node.name or "",
                op_type=node.op_type,
                domain=node.domain or "",
                inputs=in_dict,
                outputs=out_dict,
                attributes=attrs,
                subgraphs=subgraphs,
            )
        )

    return ParsedGraph(
        name=gname,
        inputs=inputs,
        parameters=parameters,
        outputs=outputs,
        value_info=value_info,
        nodes=nodes,
    )
