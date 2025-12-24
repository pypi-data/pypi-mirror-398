"""Streaming TDNN Conversion to FQIR

A TDNN model is of the following format:
input -> [pointwise ops] -> {ValidConv1d -> [pointwise ops]} x N -> {Flatten -> Linear} (optional) -> [pointwise ops]

Here, ValidConv1d refers to a Conv1d operation with "valid" padding, e.g. padding=(0, 0).

When converting to streaming format, we do the following transformations:
1) Convert ValidConv1d -> TemporalConv1d
2) If the graph terminates in a Flatten -> Linear pattern, we replace it with a CumulativeFlattenedLinear
    operation, where we use the receptive field from the Conv1d layers to determine the number
    of frames to discard
"""
from fmot.onnx2fqir import parse_onnx_graph, ParsedTensor, ParsedOperator, ParsedGraph
from fmot.fqir.writer import new_fqir_graph, FQIRWriter
from fmot.fqir import GraphProto, TensorProto, NodeProto
import numpy as np
import logging
import math
from dataclasses import dataclass, field

try:
    from onnx.shape_inference import infer_shapes
    import onnx
except ImportError as e:
    raise Exception(
        f"Exception was {e}. We probably couldn't import tf/onnx. "
        f"Please install with onnx extra requires. e.g. pip install fmot[onnx2fqir]"
    )

logger = logging.getLogger(__name__)


def is_pointwise(op: ParsedOperator) -> bool:
    """TODO: extend this / implement elsewhere. Limited for now to QOperator style quantization."""
    PWISE_OPTYPES = ["QuantizeLinear", "DequantizeLinear", "QLinearMul"]
    return op.op_type in PWISE_OPTYPES


def is_valid_conv1d(op: ParsedOperator) -> bool:
    """Checks if an op is a valid-padded Conv1d.
    valid-padding: padding of (0, 0)

    RESTRICTION (may be lifted in the future): the stride must also be 1
    """
    if op.op_type != "QLinearConv":
        return False
    attrs = op.attributes
    if attrs["auto_pad"] != "VALID":
        return False
    if attrs["strides"][0] != 1:
        return False

    return True


def check_valid_tdnn(model: onnx.ModelProto):
    """
    A valid TDNN model satisfies the following:
    1. The model has a single input (for now... we might be able to relax this)
    2. Initial part of the graph consists of ValidConv1d and pointwise ops
    3. The graph may terminate in a flatten -> Linear pattern. pointwise ops are allowed
        within this pattern, but nothing else is allowed. Only one Flatten and one Linear
        is allowed. (for now... we may be able to relax this)
    """
    model = infer_shapes(model)
    graph = parse_onnx_graph(model)

    # 1. single input
    if len(graph.inputs) != 1:
        logger.info(
            f"Not valid TDNN because graph has {len(graph.inputs)} inputs instead of 1"
        )
        return False

    # 2. start of the graph is valid-conv1d and pointwise nodes
    idx = 0
    is_validconv1d_or_pwise = True
    while idx < len(graph.nodes) and is_validconv1d_or_pwise:
        node = graph.nodes[idx]
        is_validconv1d_or_pwise = is_pointwise(node) or is_valid_conv1d(node)
        idx += 1

    # 3. Graph optionally terminates in a Flatten -> Linear pattern
    if idx == len(graph.nodes):
        # simple case without a Flatten -> Linear endpoint
        return True
    else:
        raise NotImplementedError("Need to implement a Flatten -> Linear checker")


def _get_quanta_and_precision(dtype, scale: float, zero_point: int):
    bits = {np.int8: 8, np.int16: 16, np.dtype("int8"): 8, np.dtype("int16"): 16}[dtype]
    quanta = np.log2(scale) - bits + 1
    return quanta, f"int{bits}"


def add_input(
    writer: FQIRWriter,
    input: ParsedTensor,
    channels: int,
    pgraph: ParsedGraph,
    varmap: dict[ParsedTensor, TensorProto],
):
    if input.dtype in [np.float32, np.float16, np.double]:
        quant_node = None
        for node in pgraph.nodes:
            if input in node.inputs.values() and node.op_type == "QuantizeLinear":
                quant_node = node
                break

        if quant_node is None:
            raise ValueError(f"Could not locate a QuantNode for input {input}")

        quant_input = next(iter(quant_node.outputs.values()))
        print(f"{quant_input=}")

        scale = quant_node.inputs["y_scale"].value.item()
        zero_point = quant_node.inputs["y_zero_point"].value.item()

        logger.info(f"Input {input.name} has {scale=} {zero_point=}")

        quanta, precision = _get_quanta_and_precision(
            quant_input.dtype, scale, zero_point
        )
        x_mapped = writer.add_input(
            channels=channels, quanta=quanta, name=quant_input.name, precision=precision
        )

        varmap[quant_input] = x_mapped

        return x_mapped
    else:
        raise ValueError(f"Unexpected precision {input.dtype = }")


def get_quant_info(op: ParsedOperator, name: str):
    quanta = math.log2(op.inputs[f"{name}_scale"].value)
    if quanta % 1 != 0:
        raise ValueError(
            f"Scale for {name} in {op.op_type} was not an integer power of 2"
        )
    quanta = int(quanta)

    zp = op.inputs[f"{name}_zero_point"].value
    if zp != 0:
        raise ValueError(f"zero-point for {name} in {op.op_type} was not zero")

    if name in op.inputs:
        x = op.inputs[name]
    elif name in op.outputs:
        x = op.outputs[name]
    else:
        raise ValueError(
            f"Argument {x} does not appear in {op.op_type} inputs or outputs"
        )

    if x.dtype == np.int8:
        prec = "int8"
    elif x.dtype == np.int16:
        prec = "int16"
    elif x.dtype == np.int32:
        prec = "int32"
    elif x.dtype is None:
        prec = None
    else:
        raise ValueError(f"Unrecognized dtype {x.dtype}")

    if prec is None and x.value is not None:
        value = x.value
        if np.max(x.value) < 2**7 and np.min(x.value) >= -(2**7):
            prec = "int8"
        elif np.max(x.value) < 2**15 and np.min(x.value) >= -(2**15):
            prec = "int16"
        elif np.max(x.value) < 2**23 and np.min(x.value) >= -(2**23):
            prec = "int24"
        elif np.max(x.value) < 2**31 and np.min(x.value) >= -(2**31):
            prec = "int32"

    if prec is None:
        print(f"WARNING: argument {name} in op_type {op.op_type} has dtype=None")

    return quanta, prec


@dataclass
class TDNNConverterState:
    writer: FQIRWriter
    fqir: GraphProto
    pgraph: ParsedGraph
    vmap: dict[ParsedTensor, TensorProto]
    dims: str
    options: list[str] = field(default_factory=list)
    converted_ops: set[ParsedOperator] = field(default_factory=set)
    input_quanta: dict[str, int] = field(default_factory=dict)
    output_quanta: dict[str, int] = field(default_factory=dict)

    # TDNN-specific details
    receptive_field: int = 0
    in_encoder: bool = True
    num_time: int = None
    num_feat: int = None

    @property
    def ndim(self):
        return len(self.dims)

    @property
    def batch_dim(self):
        if "B" in self.dims:
            return self.dims.index("B")
        else:
            return None

    @property
    def seq_dim(self):
        if "T" in self.dims:
            return self.dims.index("T")
        else:
            return None

    @property
    def feature_dim(self):
        if "F" in self.dims:
            return self.dims.index("F")
        else:
            return None

    def quantize_inputs(self, inputs: list[np.ndarray]):
        quant_inputs = []
        for i, quanta in enumerate(self.input_quanta.values()):
            x = inputs[i]
            y = np.round(x * 2 ** (-quanta))
            y = np.clip(y, -128, 127)
            y = y.astype(np.int32)

            quant_inputs.append(y)

        return quant_inputs

    def dequantize_outputs(self, outputs: list[np.ndarray]):
        dequant_outputs = []
        for x, quanta in zip(outputs, self.output_quanta.values()):
            y = x.astype(np.float32) * 2 ** (quanta)

            dequant_outputs.append(y)

        return dequant_outputs


def convert_transpose(node: ParsedOperator, cstate: TDNNConverterState):
    assert node.op_type == "Transpose"
    assert cstate.in_encoder

    input = node.inputs["data"]
    output = node.outputs["transposed"]
    perm: list = node.attributes["perm"]

    newdims = ""
    for p in perm:
        newdims += cstate.dims[p]

    logger.info(f"Transpose {cstate.dims} -> {newdims}")

    cstate.dims = newdims

    cstate.vmap[output] = cstate.vmap[input]

    cstate.converted_ops.add(node)


def convert_qlinearconv(node: ParsedOperator, cstate: TDNNConverterState):
    assert cstate.in_encoder
    assert cstate.batch_dim == 0
    assert node.op_type == "QLinearConv"

    x = node.inputs["x"]
    q_x, prec_x = get_quant_info(node, "x")

    w = node.inputs["w"]
    q_w, prec_w = get_quant_info(node, "w")

    if "B" in node.inputs:
        bias = node.inputs["B"]
        q_bias = q_w + q_x

        bias = cstate.writer.add_parameter(
            bias.value, name=bias.name, precision="int16", quanta=q_bias
        )

    else:
        bias = None

    y = node.outputs["y"]
    q_y, prec_y = get_quant_info(node, "y")

    if cstate.ndim == 3:
        assert cstate.seq_dim == 2
        assert cstate.feature_dim == 1

        # add weight:
        w_val = w.value
        w_val = np.expand_dims(w_val, axis=-2)

        kernel_size_t = node.attributes["kernel_shape"][0]
        dilation_t = node.attributes["dilations"][0]
        groups = node.attributes["group"]
        stride_t = node.attributes["strides"][0]

        if stride_t != 1:
            raise NotImplementedError(
                f"strided Conv1d not yet supported, got stide: {stride_t}"
            )

    elif cstate.ndim == 4:
        assert cstate.seq_dim == 3
        assert cstate.feature_dim == 1

        # add weight:
        w_val = w.value
        assert w_val.shape[-2] == 1

        kernel_size_t = node.attributes["kernel_shape"][1]
        dilation_t = node.attributes["dilations"][1]
        groups = node.attributes["group"]
        stride_t = node.attributes["strides"][1]

    cstate.receptive_field += (kernel_size_t - 1) * dilation_t

    if "conv1d_via_unfold" in cstate.options and groups == 1:
        # w_val reshape: (c_out, c_in, 1, k_t) -> (c_out, c_in * k_t)
        cout, cin, one, kt = w_val.shape
        assert one == 1
        assert kt == kernel_size_t
        w_val = w_val.transpose(0, 3, 1, 2)
        w_val = w_val.reshape(cout, cin * kt)

        weight_fqir = cstate.writer.add_parameter(
            w_val, name=w.name, precision=prec_w, quanta=q_w
        )

        unfold = cstate.writer.temporal_unfold1d(
            cstate.vmap[x], kernel_size_t, dilation_t
        )
        with cstate.writer.with_precision(precision=prec_y) as prec_writer:
            y_fqir = prec_writer.matmul(
                weight=weight_fqir,
                x=unfold,
                quanta=q_y,
                bias=bias,
            )

    else:
        weight_fqir = cstate.writer.add_parameter(
            w_val, name=w.name, precision=prec_w, quanta=q_w
        )

        with cstate.writer.with_precision(precision=prec_y) as prec_writer:
            y_fqir = prec_writer.temporal_conv2d(
                weight=weight_fqir,
                x=cstate.vmap[x],
                quanta=q_y,
                kernel_size_t=kernel_size_t,
                kernel_size_band=1,
                n_band_in=1,
                dilation_t=dilation_t,
                dilation_band=1,
                stride_band=1,
                padding_band=0,
                groups=groups,
                bias=bias,
            )

    cstate.vmap[y] = y_fqir
    cstate.converted_ops.add(node)


def convert_DQQ_pattern(node: ParsedOperator, cstate: TDNNConverterState):
    # TODO: traverse the graph properly to get the next two ops (don't rely on consistent node order)
    dq_op = node

    pgraph = cstate.pgraph
    i = pgraph.nodes.index(node)

    op = pgraph.nodes[i + 1]
    q_op = pgraph.nodes[i + 2]

    if q_op.op_type != "QuantizeLinear":
        raise RuntimeError("Expected a Dequantize -> <Op> -> Quantize pattern")

    # pattern 1: DequantizeLinear -> Relu -> QuantizeLinear
    if op.op_type == "Relu":
        x = dq_op.inputs["x"]
        y = q_op.outputs["y"]
        q_x, dtype_x = get_quant_info(dq_op, "x")
        q_y, dtype_y = get_quant_info(q_op, "y")

        if q_x != q_y:
            raise ValueError("mismatched quanta through DQ -> Relu -> Q pattern")
        if dtype_x != dtype_y:
            raise ValueError("mismatched precision through DQ -> Relu -> Q pattern")

        x_fqir = cstate.vmap[x]
        y_fqir = cstate.writer.relu(x_fqir, quanta=q_y)
        cstate.vmap[y] = y_fqir

    else:
        raise RuntimeError(
            f"{op.op_type} not currently supported in DQ -> Op -> Q pattern"
        )

    cstate.converted_ops.add(dq_op)
    cstate.converted_ops.add(op)
    cstate.converted_ops.add(q_op)


def convert_reshape(node: ParsedOperator, cstate: TDNNConverterState):
    assert cstate.in_encoder

    x = node.inputs["data"]
    y = node.outputs["reshaped"]
    shape_out = node.inputs["shape"].value

    cstate.num_time = x.shape[cstate.seq_dim]
    cstate.num_feat = x.shape[cstate.feature_dim]
    # num_flattened_feat = num_time * num_feat

    if "1" in cstate.dims:
        raise RuntimeError(f"Unary dim not currently supported in reshape")

    assert shape_out[0] == -1
    assert shape_out[1] == cstate.num_time * cstate.num_feat

    cstate.dims = "BF"
    cstate.in_encoder = False

    cstate.vmap[y] = cstate.vmap[x]
    cstate.converted_ops.add(node)


def _get_vector(node: ParsedOperator, cstate: TDNNConverterState, name: str):
    x = node.inputs[name]
    quanta, dtype = get_quant_info(node, name)

    if x in cstate.vmap:
        x_fqir = cstate.vmap[x]
        assert x_fqir.quanta == quanta
    elif x.value is not None:
        value = x.value
        if value.ndim != 1 and value.ndim == cstate.ndim:
            assert value.shape[cstate.batch_dim] == 1
            assert value.shape[cstate.seq_dim] == 1
            value = value.flatten()

        x_fqir = cstate.writer.add_parameter(
            value, name=x.name, precision=dtype, quanta=quanta
        )
        cstate.vmap[x] = x_fqir

    else:
        raise RuntimeError(f"Could not find mapping for tensor {x.name}")

    return x_fqir, quanta, dtype


def convert_qlinearmul(node: ParsedOperator, cstate: TDNNConverterState):
    a_fqir, q_a, dtype_a = _get_vector(node, cstate, "a")
    b_fqir, q_b, dtype_b = _get_vector(node, cstate, "b")

    y = node.outputs["y"]
    q_y, dtype_y = get_quant_info(node, "y")

    if dtype_y is None:
        assert (
            a_fqir.dtype == b_fqir.dtype
        ), f"{dtype_a=} {dtype_b=} {a_fqir=} {b_fqir=}"
        dtype_y = a_fqir.dtype

    writer = cstate.writer

    with writer.with_precision(dtype_y) as pwriter:
        y_fqir = pwriter.multiply(a_fqir, b_fqir, quanta=q_y)

    cstate.vmap[y] = y_fqir
    cstate.converted_ops.add(node)


def convert_qlinearadd(node: ParsedOperator, cstate: TDNNConverterState):
    a_fqir, q_a, dtype_a = _get_vector(node, cstate, "a")
    b_fqir, q_b, dtype_b = _get_vector(node, cstate, "b")

    y = node.outputs["y"]
    q_y, dtype_y = get_quant_info(node, "y")

    if dtype_y is None:
        assert (
            a_fqir.dtype == b_fqir.dtype
        ), f"{dtype_a=} {dtype_b=} {a_fqir=} {b_fqir=}"
        dtype_y = a_fqir.dtype

    writer = cstate.writer

    with writer.with_precision(dtype_y) as pwriter:
        y_fqir = pwriter.add(a_fqir, b_fqir, quanta=q_y)

    cstate.vmap[y] = y_fqir
    cstate.converted_ops.add(node)


def convert_qlinearmatmul(node: ParsedOperator, cstate: TDNNConverterState):
    assert not cstate.in_encoder

    x = node.inputs["a"]
    x_fqir = cstate.vmap[x]
    q_x, dtype_x = get_quant_info(node, "a")
    assert x_fqir.quanta == q_x

    mat = node.inputs["b"]
    q_m, dtype_m = get_quant_info(node, "b")
    q_y, dtype_y = get_quant_info(node, "y")

    y = node.outputs["y"]

    with cstate.writer.with_precision(dtype_y) as prec_writer:
        if cstate.num_time == 1:
            # TODO: mask x to all zeros for timesteps t != 100
            mat_fqir = cstate.writer.add_parameter(
                mat.value.T, name=mat.name, precision=dtype_m, quanta=q_m
            )
            assert mat_fqir.shape[1] == x_fqir.shape[0]
            y_fqir = prec_writer.matmul(mat_fqir, x_fqir, quanta=q_y)

        elif "conv1d_via_unfold" in cstate.options:
            cin = x_fqir.shape[0]
            cin_times_kt, cout = mat.shape
            assert (
                cin_times_kt == cstate.num_time * cin
            ), f"{mat.shape=} {x_fqir.shape=} {cstate.num_time=}"

            weight_fqir = prec_writer.add_parameter(
                mat.value.T, name=mat.name, precision=dtype_m, quanta=q_m
            )
            unfold = prec_writer.temporal_unfold1d(x_fqir, cstate.num_time, 1)
            y_fqir = prec_writer.matmul(
                weight=weight_fqir, x=unfold, quanta=q_y, bias=None
            )
            cstate.receptive_field += cstate.num_time - 1

        else:
            # use a TemporalConv1d layer
            M = mat.value  # (in_channels, out_channels)
            Cin, Cout = M.shape
            M = M.T.reshape(
                Cout, cstate.num_time, Cin // cstate.num_time, 1
            )  # (out_channels, in_channels/K, 1, K)
            M = np.permute_dims(M, (0, 2, 3, 1))
            mat_fqir = cstate.writer.add_parameter(
                M, name=mat.name, precision=dtype_m, quanta=q_m
            )
            assert (
                mat_fqir.shape[1] == x_fqir.shape[0]
            ), f"{mat_fqir.shape = } {x_fqir.shape = }"

            y_fqir = prec_writer.temporal_conv2d(
                weight=mat_fqir,
                x=x_fqir,
                quanta=q_y,
                kernel_size_t=cstate.num_time,
                kernel_size_band=1,
                n_band_in=1,
                dilation_t=1,
                dilation_band=1,
                stride_band=1,
                padding_band=0,
                groups=1,
                bias=None,
            )
            cstate.receptive_field += cstate.num_time - 1

    cstate.vmap[y] = y_fqir
    cstate.converted_ops.add(node)


def _apply_unsqueeze(layout: str, axes: list[int]) -> str:
    """
    Insert unary ('1') dimensions at the given axes into the layout string.

    Axes follow ONNX-style semantics:
      - They are indices into the *output* shape.
      - Negative axes are allowed and are normalized using the final rank.
    """
    n = len(layout)
    k = len(axes)
    if k == 0:
        return layout

    expanded_rank = n + k  # rank after unsqueeze

    # Normalize negative axes w.r.t. the expanded rank
    norm_axes = []
    for ax in axes:
        if ax < 0:
            ax += expanded_rank
        if ax < 0 or ax >= expanded_rank:
            raise IndexError(f"axis {ax} out of range for output rank {expanded_rank}")
        norm_axes.append(ax)

    # Sort (ONNX requires distinct, sorted axes)
    norm_axes = sorted(norm_axes)
    axes_set = set(norm_axes)

    # Build the new layout: put '1' at unsqueezed axes, original dims otherwise
    out = []
    dim_iter = iter(layout)
    for i in range(expanded_rank):
        if i in axes_set:
            out.append("1")
        else:
            out.append(next(dim_iter))
    return "".join(out)


def convert_unsqueeze(node: ParsedOperator, cstate: TDNNConverterState):
    x = node.inputs["data"]
    axes = node.inputs["axes"]
    y = node.outputs["expanded"]

    if axes.value is None:
        raise ValueError(f"Unsqueeze with dynamic axes is not supported")
    axes = axes.value

    layout = cstate.dims
    new_layout = _apply_unsqueeze(layout, axes)

    logger.info(f"Unsqueeze: {cstate.dims} -> {new_layout}")

    cstate.dims = new_layout

    cstate.vmap[y] = cstate.vmap[x]
    cstate.converted_ops.add(node)


def _apply_squeeze(layout: str, axes: list[int]) -> str:
    """
    Remove unary ('1') dimensions from the layout string.

    Semantics (ONNX-style):

    - If `axes` is None or empty:
        Squeeze *all* dimensions that are '1' in the layout.

    - If `axes` is a sequence of ints:
        * Axes are indices into the *input* shape (i.e., current layout).
        * Negative axes are allowed and are normalized using the input rank.
        * Each axis must refer to a '1' dimension; otherwise we raise ValueError.
    """
    n = len(layout)

    # Case 1: axes is None or []
    if not axes:
        # Remove all '1' dims
        return "".join(ch for ch in layout if ch != "1")

    # Case 2: explicit axes
    # Normalize negative axes with respect to input rank
    norm_axes = []
    for ax in axes:
        if ax < 0:
            ax += n
        if ax < 0 or ax >= n:
            raise IndexError(f"axis {ax} out of range for input rank {n}")
        norm_axes.append(ax)

    # ONNX requires unique, sorted axes
    norm_axes = sorted(set(norm_axes))

    # Check each axis refers to a '1' dimension
    for ax in norm_axes:
        if layout[ax] != "1":
            raise ValueError(
                f"Cannot squeeze axis {ax} in layout '{layout}': "
                f"dimension is '{layout[ax]}', not '1'"
            )

    remove_set = set(norm_axes)

    # Build new layout by skipping axes in remove_set
    out = [ch for i, ch in enumerate(layout) if i not in remove_set]
    return "".join(out)


def convert_squeeze(node: ParsedOperator, cstate: TDNNConverterState):
    x = node.inputs["data"]
    axes = node.inputs["axes"]
    y = node.outputs["squeezed"]

    if axes.value is None:
        raise ValueError(f"Unsqueeze with dynamic axes is not supported")
    axes = axes.value

    layout = cstate.dims
    new_layout = _apply_squeeze(layout, axes)

    logger.info(f"Squeeze: {cstate.dims} -> {new_layout}")

    cstate.dims = new_layout

    cstate.vmap[y] = cstate.vmap[x]
    cstate.converted_ops.add(node)


def convert_qlinearsoftmax(node: ParsedOperator, cstate: TDNNConverterState):
    assert node.op_type == "QLinearSoftmax"

    x = node.inputs["x"]
    y = node.outputs["y"]

    if "remove_final_softmax" in cstate.options:
        cstate.vmap[y] = cstate.vmap[x]
        print(f"Skipping Softmax! quanta: {get_quant_info(node, 'x')[0]}")
        return

    q_x, dtype_x = get_quant_info(node, "x")
    q_y, dtype_y = get_quant_info(node, "y")

    if dtype_y is None:
        logger.warning(
            f"QLinearSoftmax output has unknown integer datatype, assuming it is {dtype_y}"
        )
        dtype_y = dtype_x

    x_fqir = cstate.vmap[x]
    writer = cstate.writer

    if x.shape[0] == 2:
        # sigmoid trick
        if dtype_x == "int8":
            x_fqir = writer.add(x_fqir, 0, quanta=x_fqir.quanta - 8)

        a, b = writer.split(x_fqir, [1, 1])
        d = writer.sub(a, b, quanta=a.quanta + 1)

        def sigmoid(x):
            return 1 / (1 + np.exp(-x))

        sig = writer.interpolating_lut(d, sigmoid, name="sigmoid")
        om_sig = writer.add(1, writer.multiply(sig, -1), quanta=-15)
        sig = writer.add(sig, 0, quanta=-15)

        res = writer.cat([sig, om_sig])

        with writer.with_precision(dtype_y) as pwriter:
            y_fqir = pwriter.add(res, 0, quanta=q_y)

        cstate.vmap[y] = y_fqir
        cstate.converted_ops.add(node)

    else:
        if dtype_x == "int8":
            x_fqir = writer.add(x_fqir, 0, quanta=x_fqir.quanta - 8)

        x_max = writer.max(x_fqir)
        x_normed = writer.sub(x_fqir, x_max, quanta=x_fqir.quanta + 1)
        x_normed = writer.add(
            x_normed, 2 ** (x_normed.quanta + 14), quanta=x_fqir.quanta
        )

        exp_x = writer.interpolating_lut(x_normed, func=np.exp, name="exp")
        sum_exp = writer.sum(exp_x)
        y_fqir = writer.divide(exp_x, sum_exp, pos_only=True, quanta=-15)

        with writer.with_precision(dtype_y) as pwriter:
            y_fqir = pwriter.add(y_fqir, 0, quanta=q_y)

        cstate.vmap[y] = y_fqir
        cstate.converted_ops.add(node)


CONVERTERS = {
    "Transpose": convert_transpose,
    "Unsqueeze": convert_unsqueeze,
    "Squeeze": convert_squeeze,
    "QLinearConv": convert_qlinearconv,
    # "DequantizeLinear": convert_DQQ_pattern,
    "Reshape": convert_reshape,
    "QLinearMatMul": convert_qlinearmatmul,
    "QLinearSoftmax": convert_qlinearsoftmax,
    "QLinearMul": convert_qlinearmul,
    "QLinearAdd": convert_qlinearadd,
}


def convert_streaming_tdnn_to_fqir(
    model: onnx.ModelProto,
    batch_dim=0,
    seq_dim=1,
    feature_dim=2,
    options: list[str] = ["conv1d_via_unfold"],
):
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)
    pgraph = parse_onnx_graph(model)

    # mapping from onnx tensors to FQIR tensors
    vmap = {}

    dims = list("XXX")
    dims[batch_dim] = "B"
    dims[seq_dim] = "T"
    dims[feature_dim] = "F"
    dims = "".join(dims)

    cstate = TDNNConverterState(
        writer=writer, fqir=graph, pgraph=pgraph, vmap=vmap, dims=dims, options=options
    )

    # add inputs to the FQIR graph
    for name, input in pgraph.inputs.items():
        for node in pgraph.nodes:
            if input in node.inputs.values():
                y = node.outputs["y"]
                quanta, precision = get_quant_info(node, "y")
                cstate.vmap[y] = writer.add_input(
                    channels=y.shape[feature_dim],
                    quanta=quanta,
                    precision=precision,
                    name=name,
                )
                cstate.converted_ops.add(node)
                cstate.input_quanta[node.inputs["x"].name] = quanta

    # parse the graph
    for i, node in enumerate(pgraph.nodes):
        if node in cstate.converted_ops:
            continue

        if node.op_type in CONVERTERS:
            logger.info(f"Converting to FQIR: node {node.op_type}")
            CONVERTERS[node.op_type](node, cstate)
        elif node.op_type == "DequantizeLinear":
            if node.outputs["y"] in list(pgraph.outputs.values()):
                x = node.inputs["x"]
                y = node.outputs["y"]

                q_out, dtype_out = get_quant_info(node, "x")
                if dtype_out is None:
                    dtype_out = vmap[x].dtype

                # this is probably a no-op, but to be sure, apply a cast
                with cstate.writer.with_precision(dtype_out) as pwriter:
                    y_fqir = pwriter.add(vmap[x], 0, quanta=q_out)
                    y_fqir.name = y.name

                # no-op
                vmap[y] = y_fqir
            else:
                logger.info(f"Converting to FQIR: DQD starting with {node.op_type}")
                convert_DQQ_pattern(node, cstate)
        else:
            raise RuntimeError(f"Unsupported op_type: {node.op_type}")

    # attach outputs
    for name, x in pgraph.outputs.items():
        cstate.writer.add_outputs([cstate.vmap[x]])
        cstate.output_quanta[name] = cstate.vmap[x].quanta

    return cstate
