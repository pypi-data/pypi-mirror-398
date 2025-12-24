import onnx
from onnx import shape_inference


def add_intermediate_outputs_to_model(
    model: onnx.ModelProto,
    tensor_names: list[str],
    run_shape_inference: bool = True,
) -> onnx.ModelProto:
    """
    Given an ONNX ModelProto and a list of tensor names (intermediate values),
    add them as extra graph outputs in-place and return the model.

    If `run_shape_inference` is True, we first run ONNX shape inference so that
    intermediate tensors appear in `graph.value_info` with proper types/shapes.
    """
    if run_shape_inference:
        model = shape_inference.infer_shapes(model)

    graph = model.graph

    # Existing outputs, so we don't add duplicates
    existing_outputs = {o.name for o in graph.output}

    # Build a lookup from tensor name -> ValueInfoProto
    # Includes inputs, outputs, and intermediate value_info
    value_info_by_name = {}
    for vi in list(graph.input) + list(graph.output) + list(graph.value_info):
        value_info_by_name[vi.name] = vi

    # Optionally allow initializers too (e.g., if you want weights as outputs)
    initializer_names = {init.name for init in graph.initializer}

    for name in tensor_names:
        if name in existing_outputs:
            # Already an output; skip
            continue

        vi = value_info_by_name.get(name, None)

        if vi is None:
            # If it's an initializer, we can synthesize a ValueInfo
            if name in initializer_names:
                init = next(i for i in graph.initializer if i.name == name)
                # Make a new ValueInfo from the initializer's type/shape
                vi = onnx.helper.make_tensor_value_info(
                    name=init.name,
                    elem_type=init.data_type,
                    shape=list(init.dims),
                )
            else:
                raise ValueError(
                    f"Tensor '{name}' not found in graph.value_info / inputs / outputs / initializers. "
                    "Make sure the name is correct and consider running shape inference first."
                )

        # Append the ValueInfoProto as a new output
        # (protobuf will copy it into the repeated field when serialized)
        graph.output.append(vi)
        existing_outputs.add(name)

    return model
