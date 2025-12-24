from fmot.fqir import GraphProto, TensorProto
from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from fmot.fqir.writer import FQIRWriter


def temporal_unfold_to_assign(arith: GraphProto, init: GraphProto):
    from fmot.fqir.writer import FQIRWriter, new_fqir_graph

    n_unfold = 0
    for node in arith.nodes:
        if node.opname.startswith("temporal"):
            n_unfold += 1

    if n_unfold == 0:
        return arith, init

    varmap = {}
    inputs = []
    for x in arith.inputs:
        x_prime = TensorProto(
            name=f"{x.name}-copy",
            shape=x.shape,
            dtype=x.dtype,
            quanta=x.quanta if x.quanta is not None else 0,
        )
        inputs.append(x_prime)
        varmap[x] = x_prime

    ngraph = new_fqir_graph(inputs)
    writer = FQIRWriter(
        ngraph.subgraphs["ARITH"], ngraph.subgraphs["INIT"], act_precision="int16"
    )
    for p in arith.parameters:
        pp = writer.add_parameter(
            p.value, p.name, p.dtype, p.quanta if p.quanta is not None else 0
        )
        varmap[p] = pp
    for x in init.all_tensors():
        b = writer.add_zeros_buffer(x.shape[0], x.quanta, x.name, x.dtype)
        varmap[x] = b

    for node in arith.nodes:
        if node.opname == "temporal_unfold":
            x_orig = node.inputs["x"]
            b_orig = node.inputs["buffer"]
            y_orig = node.outputs[0]
            k = node.constants["kernel_size"]
            d = node.constants["dilation"]

            x = varmap[x_orig]
            b = varmap[b_orig]

            if d != 1:
                raise ValueError(
                    "temporal_unfold with dilation != 1 not supported at this time"
                )

            y = writer.cat([b, x])
            _, b_prime = writer.split(y, [x.shape[0], b.shape[0]])
            b.quanta = b_prime.quanta
            writer.assign(b, b_prime)
            varmap[y_orig] = y

        elif node.opname == "temporal_conv2d":
            raise NotImplementedError("TemporalConv2d does not have an assign mapping")
        else:
            writer.copy_fqir_node(node, varmap)

    for y_orig in arith.outputs:
        y = varmap[y_orig]
        ngraph.subgraphs["ARITH"].add_output(y)
        ngraph.add_output(y)

    return ngraph.subgraphs["ARITH"], ngraph.subgraphs["INIT"]


def nest_as_sequential_loop(
    writer: "FQIRWriter",
    n_iter: int,
    inputs: list[TensorProto],
    graph: GraphProto,
    decomp_temp_unfold: bool = False,
):
    """
    Nests the given FQIR graph into a *sequential* loop.

    """
    sub_arith = graph.subgraphs["ARITH"]
    sub_init = graph.subgraphs.get("INIT", GraphProto())

    if decomp_temp_unfold:
        sub_arith, sub_init = temporal_unfold_to_assign(sub_arith, sub_init)

    # check that each input in inputs_to_slice matches
    # the quanta / has the correct shape to match its counterpart in sub_arith.
    assert len(inputs) == len(sub_arith.inputs)
    for x_slice, x_sub in zip(inputs, sub_arith.inputs):
        if x_slice.shape[0] != n_iter * x_sub.shape[0]:
            raise ValueError(
                f"Subgraph input {x_sub} has size {x_sub.shape[0]}, expected {x_slice} to have "
                f"shape n_iter = {n_iter} times larger, but got {x_slice.shape[0]}"
            )
        assert (
            x_slice.quanta == x_sub.quanta
        ), f"{x_slice} has quanta {x_slice.quanta}, mismatches {x_sub} quanta {x_sub.quanta}"

    # collect all of the variables that assigned
    assigned_vars = set()
    for node in sub_arith.nodes:
        if node.opname == "assign":
            assigned_vars.add(node.inputs["y"])
        elif node.opname in ["temporal_unfold", "temporal_conv1d", "temporal_conv2d"]:
            if "buffer" in node.inputs:
                assigned_vars.add(node.inputs["buffer"])
    for x in assigned_vars:
        assert x in sub_init.all_tensors()

    assigned_var_map = {}
    for x in assigned_vars:
        if x.value is not None:
            x_init = writer.add_init_buffer(
                x=x.value, quanta=x.quanta, name=f"{x.name_init}", precision=x.dtype
            )
        else:
            x_init = writer.add_zeros_buffer(
                channels=x.shape[0],
                quanta=x.quanta,
                name=f"{x.name}_init",
                precision=x.dtype,
            )
        assigned_var_map[x_init] = x

    assign_var_updates = {}

    with writer.for_loop_writer(
        n_iter=n_iter,
        x_to_slice=inputs,
        x_recurse_init=list(assigned_var_map.keys()),
    ) as lwriter:
        x_slices = lwriter.sliced_inputs
        state = lwriter.recursed_inputs

        varmap = {}
        for x, y in zip(sub_arith.inputs, x_slices):
            varmap[x] = y
        for x, y in zip(assigned_var_map.values(), state):
            varmap[x] = y

        for p in sub_arith.parameters:
            new_p = lwriter.add_parameter(
                p.value, name=f"{p.name}_copy", precision=p.dtype, quanta=p.quanta
            )
            varmap[p] = new_p

        for node in sub_arith.nodes:
            if node.opname == "assign":
                orig = varmap[node.inputs["y"]]
                update = varmap[node.inputs["x"]]
                lwriter.update_recursed_state(orig, update)
                x_final = lwriter.return_final(update)
                idx = state.index(orig)
                assign_var_updates[list(assigned_var_map.keys())[idx]] = x_final
            elif node.opname in [
                "temporal_unfold",
                "temporal_conv1d",
                "temporal_conv2d",
            ]:
                lwriter.copy_fqir_node(node, varmap)
                if "buffer" in node.inputs:
                    orig = varmap[node.inputs["buffer"]]
                    update = orig
                    lwriter.update_recursed_state(orig, update)
                    x_final = lwriter.return_final(update)
                    idx = state.index(orig)
                    assign_var_updates[list(assigned_var_map.keys())[idx]] = x_final
            else:
                lwriter.copy_fqir_node(node, varmap)

        cat_outs = []
        for y in sub_arith.outputs:
            y_cat = lwriter.return_concatenated(varmap[y])
            cat_outs.append(y_cat)

    for src, update in assign_var_updates.items():
        writer.assign(src, update)

    return cat_outs


def nest_as_parallel_loop(
    writer: "FQIRWriter",
    n_iter: int,
    inputs: list[TensorProto],
    graph: GraphProto,
    scope_input_indices: list[int] = None,
    decomp_temp_unfold: bool = False,
):
    """
    Nests the given FQIR graph into a *parallel* loop.

    """
    sub_arith = graph.subgraphs["ARITH"]
    sub_init = graph.subgraphs.get("INIT", GraphProto())

    if decomp_temp_unfold:
        sub_arith, sub_init = temporal_unfold_to_assign(sub_arith, sub_init)

    if scope_input_indices is None:
        scope_input_indices = []

    # check that each input in inputs_to_slice matches
    # the quanta / has the correct shape to match its counterpart in sub_arith.
    assert len(inputs) == len(sub_arith.inputs)
    for i, (x_slice, x_sub) in enumerate(zip(inputs, sub_arith.inputs)):
        if i not in scope_input_indices:
            if x_slice.shape[0] != n_iter * x_sub.shape[0]:
                raise ValueError(
                    f"Subgraph input {x_sub} has size {x_sub.shape[0]}, expected {x_slice} to have "
                    f"shape n_iter = {n_iter} times larger, but got {x_slice.shape[0]}"
                )
        assert (
            x_slice.quanta == x_sub.quanta
        ), f"{x_slice} has quanta {x_slice.quanta}, mismatches {x_sub} quanta {x_sub.quanta}"

    # collect all of the variables that assigned
    assigned_vars = set()
    for node in sub_arith.nodes:
        if node.opname == "assign":
            assigned_vars.add(node.inputs["y"])
        elif node.opname in ["temporal_unfold", "temporal_conv1d", "temporal_conv2d"]:
            if "buffer" in node.inputs:
                assigned_vars.add(node.inputs["buffer"])
    for x in assigned_vars:
        assert x in sub_init.all_tensors()

    assigned_var_map = {}
    for x in assigned_vars:
        if x.value is not None:
            x_init = writer.add_init_buffer(
                x=np.concat([x.value] * n_iter),
                quanta=x.quanta,
                name=f"{x.name_init}",
                precision=x.dtype,
            )
        else:
            x_init = writer.add_zeros_buffer(
                channels=x.shape[0] * n_iter,
                quanta=x.quanta,
                name=f"{x.name}_init",
                precision=x.dtype,
            )
        assigned_var_map[x_init] = x

    x_to_slice = [x for i, x in enumerate(inputs) if i not in scope_input_indices]
    x_scope = [x for i, x in enumerate(inputs) if i in scope_input_indices]
    x_to_slice += list(assigned_var_map.keys())

    assigned_var_concats = {}

    with writer.for_loop_writer(
        n_iter=n_iter, x_to_slice=x_to_slice, x_recurse_init=[], x_scope=x_scope
    ) as lwriter:
        x_slices = lwriter.sliced_inputs
        x_scope = lwriter.scoped_inputs

        varmap = {}
        slice_j = 0
        scope_j = 0
        for i, x in enumerate(sub_arith.inputs):
            if i in scope_input_indices:
                varmap[x] = x_scope[scope_j]
                scope_j += 1
            else:
                varmap[x] = x_slices[slice_j]
                slice_j += 1

        state = []
        for x in assigned_var_map.values():
            varmap[x] = x_slices[slice_j]
            state.append(x_slices[slice_j])
            slice_j += 1

        for p in sub_arith.parameters:
            new_p = lwriter.add_parameter(
                p.value, name=f"{p.name}_copy", precision=p.dtype, quanta=p.quanta
            )
            varmap[p] = new_p

        for node in sub_arith.nodes:
            if node.opname == "assign":
                orig = varmap[node.inputs["y"]]
                update = varmap[node.inputs["x"]]
                x_concat = lwriter.return_concatenated(update)
                idx = state.index(orig)
                assigned_var_concats[list(assigned_var_map.keys())[idx]] = x_concat

            elif node.opname in [
                "temporal_unfold",
                "temporal_conv1d",
                "temporal_conv2d",
            ]:
                lwriter.copy_fqir_node(node, varmap)
                if "buffer" in node.inputs:
                    orig = varmap[node.inputs["buffer"]]
                    update = orig
                    x_concat = lwriter.return_concatenated(update)
                    idx = state.index(orig)
                    assigned_var_concats[list(assigned_var_map.keys())[idx]] = x_concat
            else:
                lwriter.copy_fqir_node(node, varmap)

        cat_outs = []
        for y in sub_arith.outputs:
            y_cat = lwriter.return_concatenated(varmap[y])
            cat_outs.append(y_cat)

    for src, update in assigned_var_concats.items():
        writer.assign(src, update)

    return cat_outs
