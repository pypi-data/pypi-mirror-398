try:
    from tf2onnx.graph_matcher import OpTypePattern, GraphMatcher
    from tf2onnx import utils as tf2onnx_utils
    import onnx
except ImportError as e:
    raise Exception(
        f"Exception was {e}. We probably couldn't import tf/onnx. "
        f"Please install with onnx extra requires. e.g. pip install fmot[onnx2fqir]"
    )

import numpy as np


def rewrite_bias_squeeze_conv2d_expand_with_fused_conv1d(g, ops):
    pattern_bias = OpTypePattern(
        "BiasAdd",
        name="biasadd",
        inputs=[
            OpTypePattern(
                "Squeeze",
                name="squeeze",
                inputs=[
                    OpTypePattern(
                        "Conv2D",
                        name="conv",
                        inputs=[
                            OpTypePattern(
                                "ExpandDims", name="expand", inputs=["*", "*"]
                            ),
                            "*",
                        ],
                    )
                ],
            ),
            "*",
        ],
    )

    pattern_no_bias = OpTypePattern(
        "Squeeze",
        name="squeeze",
        inputs=[
            OpTypePattern(
                "Conv2D",
                name="conv",
                inputs=[
                    OpTypePattern("ExpandDims", name="expand", inputs=["*", "*"]),
                    "*",
                ],
            )
        ],
    )

    def _rewrite(match_results, bias_present):
        for match in match_results:
            if bias_present:
                biasadd = match.get_op("biasadd")
            expand = match.get_op("expand")
            conv = match.get_op("conv")
            squeeze = match.get_op("squeeze")

            # Backup the conv and biasadd values
            expand_input = expand.input[0]
            conv_input = conv.input
            conv_dtype = g.get_dtype(conv.output[0])
            conv_name = squeeze.name
            squeeze_shape = g.get_shape(squeeze.output[0])
            if bias_present:
                squeeze_output = biasadd.output
            else:
                squeeze_output = squeeze.output

            # Create new weight const node with squeezed dims
            expand_weight = g.get_node_by_output(conv_input[1])
            if expand_weight.is_const():
                val = expand_weight.get_tensor_value(as_list=False)
                initial_name = tf2onnx_utils.make_name("Const")
                new_val = np.squeeze(val, axis=0)
                const_node = g.make_const(initial_name, new_val)
            else:
                assert False, "Weight for Conv2D is not constant."

            # Update attrs for conv to Conv1D
            d = conv.get_attr_value("dilations")[2]
            conv.set_attr("dilations", [d])
            s = conv.get_attr_value("strides")[2]
            conv.set_attr("strides", [s])
            conv_attr = conv.attr

            # Set inputs for new conv node
            if bias_present:
                conv_inputs = [expand_input, const_node.output[0], biasadd.input[1]]
            else:
                conv_inputs = [expand_input, const_node.output[0]]

            # Remove existing nodes
            g.remove_node(expand.name)
            g.remove_node(conv.name)
            g.remove_node(squeeze.name)
            if bias_present:
                g.remove_node(biasadd.name)

            g.make_node(
                "Conv1D",
                conv_inputs,
                attr=conv_attr,
                name=conv_name,
                outputs=squeeze_output,
                shapes=[squeeze_shape],
                dtypes=[conv_dtype],
                skip_conversion=False,
            )

    matcher = GraphMatcher(pattern_bias)
    match_results_bias = list(matcher.match_ops(ops))
    _rewrite(match_results_bias, bias_present=True)

    matcher = GraphMatcher(pattern_no_bias)
    match_results_no_bias = list(matcher.match_ops(ops))
    _rewrite(match_results_no_bias, bias_present=False)

    return ops


def edit_qdq_scales_to_power_of_two(model: onnx.ModelProto) -> onnx.ModelProto:
    """Edits the scales of all QuantizeLinear and DequantizeLinear nodes in the model
    to be the nearest power-of-two value.
    """
    graph_def = model.graph

    nodes = graph_def.node
    initializers_list = []
    # Find all quantizelinear and dequantizelinear nodes and get their scale initializers
    for node in nodes:
        if node.op_type == "QuantizeLinear":
            initializers_list.append(node.input[1])
        elif node.op_type == "DequantizeLinear":
            initializers_list.append(node.input[1])

    for initializer in graph_def.initializer:
        if initializer.name in initializers_list:
            if len(initializer.float_data) == 0 and initializer.dims != []:
                raw_data = initializer.raw_data
                float_data = np.frombuffer(raw_data, dtype=np.float32)
                # Change float data to nearest power of 2 and update initializer
                power_of_2_data = np.power(2, np.ceil(np.log2(float_data)))
                initializer.raw_data = power_of_2_data.tobytes()
            else:
                float_data = np.array(initializer.float_data)
                power_of_2_data = np.power(2, np.ceil(np.log2(float_data)))
                initializer.float_data[:] = power_of_2_data.tolist()
    return model
