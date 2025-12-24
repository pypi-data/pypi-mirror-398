import networkx as nx
from fmot.fqir import GraphProto, NodeProto, TensorProto
from fmot.fqir.writer.fqir_writer import FQIRWriter, new_fqir_graph
from fmot.fqir.writer.utils import find_fqir_tensor_with_name
import logging

logger = logging.getLogger(__name__)


class MissingFQIRDependencyError(Exception):
    pass


def get_all_buffers(fqir: GraphProto):
    init = fqir.subgraphs.get("INIT", GraphProto())
    return set([x for x in init.all_tensors()])


def get_all_params(fqir: GraphProto):
    return set(fqir.subgraphs["ARITH"].parameters)


def parse_fqir_to_digraph(fqir: GraphProto, dag_mode=False):
    """
    Parses FQIR to a DAG nx.DiGraph.

    Arguments:
        fqir (GraphProto): the main-level FQIR graph to parse
        dag_mode (bool, optional): if True, assign nodes will not
            induce loops and the graph will be DAG. If False, assign
            nodes will induce loops (which can help to identify the
            set of nodes needed to split out subgraphs)
    """
    graph = nx.DiGraph()

    arith = fqir.subgraphs["ARITH"]
    init = fqir.subgraphs.get("INIT", GraphProto())

    for node in init.nodes:
        for x in node.inputs.values():
            graph.add_edge(x, node)
        for y in node.outputs:
            graph.add_edge(y, node)

    assign_dependencies = {}

    for node in arith.nodes:
        for x in node.inputs.values():
            graph.add_edge(x, node)
            if x in assign_dependencies:
                graph.add_edge(assign_dependencies[x], node)
        for y in node.outputs:
            graph.add_edge(node, y)

        if node.opname == "assign":
            if not dag_mode:
                graph.add_edge(node, node.inputs["y"])
            assign_dependencies[node.inputs["y"]] = node

    return graph


def _nodes_on_all_uv_paths_inefficient(G: nx.DiGraph, u, v):
    """Brute-force method to get all nodes between u and v
    Arguments:
        G (nx.DiGraph): DiGraph
        u (Any): starting node
        v (Any): ending node
    """
    all_paths = nx.all_simple_paths(G, u, v)
    node_sets = [set(path) for path in all_paths]
    return set.union(*node_sets) if node_sets else set()


def nodes_on_all_paths_between_pairs(G: nx.DiGraph, inputs: list, outputs: list):
    """Brute-force method...
    Arguments:
        G (nx.DiGraph): DiGraph
        inputs (list): starting nodes
        outputs (list): ending nodes
    """
    nodeset = set()
    for a in inputs:
        for b in outputs:
            if nx.has_path(G, a, b):
                nodeset = nodeset.union(_nodes_on_all_uv_paths_inefficient(G, a, b))

    return nodeset


def nodes_on_all_paths_between_pairs_efficient(
    G: nx.DiGraph, inputs: list, outputs: list
):
    """Single traversal method
    Arguments:
        G (nx.DiGraph): DiGraph
        inputs (list): starting nodes
        outputs (list): ending nodes
    """
    if not inputs or not outputs:
        return set()

    # Use unique, non-colliding sentinel nodes
    source = object()
    sink = object()

    H = nx.DiGraph(G)  # copy to avoid mutating caller's graph

    # sever preds -> inputs, outputs -> succs
    for x in inputs:
        H.remove_edges_from((pred, x) for pred in list(H.predecessors(x)))
    for x in outputs:
        H.remove_edges_from((x, succ) for succ in list(H.successors(x)))

    H.add_node(source)
    H.add_node(sink)
    H.add_edges_from((source, x) for x in inputs if x in H)
    H.add_edges_from((y, sink) for y in outputs if y in H)

    # Forward reachability from super-source
    from_source = set(nx.descendants(H, source)) | {source}

    # Backward reachability to super-sink (i.e., forward in reversed graph)
    R = H.reverse(copy=False)
    to_sink = set(nx.descendants(R, sink)) | {sink}

    # Nodes that are both reachable from inputs and can reach outputs
    nodeset = (from_source & to_sink) - {source, sink}

    # (Optional) ensure we only return original nodes
    return nodeset & set(G.nodes)


def identity_missing_predecessors(G: nx.DiGraph, nodeset: set, ignore: set):
    missing_preds = set()

    nodecheck = nodeset.copy()
    for x in ignore:
        if x in nodecheck:
            nodecheck.remove(x)

    for node in nodecheck:
        for x in G.predecessors(node):
            if x not in nodeset:
                missing_preds.add(x)

    return missing_preds


PREC_MAP = {"fqint8": "int8", "fqint16": "int16", "fqint24": "int24"}


def get_fqir_between(
    fqir: GraphProto,
    inputs: list[TensorProto | str | int],
    outputs: list[TensorProto | str | int],
) -> GraphProto:
    """Extract the FQIR subgraph that produces `outputs` from `inputs`.

    This builds a new FQIR graph that contains exactly the operators, parameters,
    and buffers that lie on **some** path from any `inputs` tensor to any
    `outputs` tensor.
    Any unsatisfied upstream dependency causes a :class:`MissingFQIRDependencyError`.

    Behavior summary:
    - Parses the source FQIR to a directed graph and finds all nodes on paths
      from the provided `inputs` to the provided `outputs`.
    - Adds any required INIT buffers (if referenced).
    - Copies only the necessary parameters and nodes
    - Sets the returned graph's outputs to correspond 1:1 with `outputs`.

    Args:
        fqir (GraphProto): The source FQIR graph to slice.
        inputs (list[TensorProto | str | int]): Tensors to expose as inputs of the returned subgraph. These may
            be original graph inputs **or** intermediate tensors. If str, will use :attr:`fmot.fqir.writer.find_fqir_tensor_with_name` to
            locate the corresponding TensorProto. If `int`, this refers to the index of the input to the top-level graph.
        outputs (list[TensorProto | str | int]): Tensors to expose as outputs of the returned subgraph. These may
            be original graph outputs **or** intermediate tensors. If str, will use :attr:`fmot.fqir.writer.find_fqir_tensor_with_name` to
            locate the corresponding TensorProto. If `int`, this refers to the index of the output from the top-level graph.

    Returns:
        GraphProto: A new FQIR graph containing only the ops/params/buffers
        necessary to compute `outputs` from `inputs`.

    Raises:
        MissingFQIRDependencyError: If there exists an upstream dependency that
        is neither in `inputs` nor is a buffer (i.e., it cannot be satisfied
        by copying in the buffer and its update operations).

    .. note::
        - All `outputs` must be reachable from the (possibly augmented) input
          set. If an `output` is unreachable in the original graph, this will
          fail with an unsatisfied dependency.
    """
    inputs = inputs.copy()
    outputs = outputs.copy()

    logger.debug("getting inputs...")
    for i, x in enumerate(inputs):
        if isinstance(x, str):
            logging.debug(f"looking for input with name {x}")
            inputs[i] = find_fqir_tensor_with_name(fqir, x)
        elif isinstance(x, int):
            logging.debug(f"looking for arith input index {x}")
            inputs[i] = fqir.subgraphs["ARITH"].inputs[x]
        elif isinstance(x, TensorProto):
            pass
        else:
            raise ValueError(
                f"input {i} was of type {type(x)}, expected TensorProto, str, or int"
            )

    logger.debug("getting outputs...")
    for i, x in enumerate(outputs):
        if isinstance(x, str):
            logging.debug(f"looking for output with name {x}")
            outputs[i] = find_fqir_tensor_with_name(fqir, x)
        elif isinstance(x, int):
            logging.debug(f"looking for arith output index {x}")
            outputs[i] = fqir.subgraphs["ARITH"].outputs[x]
        elif isinstance(x, TensorProto):
            pass
        else:
            raise ValueError(
                f"output {i} was of type {type(x)}, expected TensorProto, str, or int"
            )

    # find a set of all FQIR nodes that are on the subgraph induced between inputs and outputs
    G = parse_fqir_to_digraph(fqir, dag_mode=False)
    logger.debug("Parsed DiGraph. Now looking for nodes along all paths.")
    nodeset = nodes_on_all_paths_between_pairs_efficient(G, inputs, outputs)

    # identify and flag any missing predecessors
    missing_preds = identity_missing_predecessors(G, nodeset, ignore=set(inputs))

    # if these missing predecessors are buffers, add them to the input set and iterate

    buffers = get_all_buffers(fqir)
    params = get_all_params(fqir)

    if len(missing_preds) != 0:
        buff_param_preds = []
        for node in missing_preds:
            if node in buffers or node in params:
                buff_param_preds.append(node)

        nodeset = nodeset.union(
            nodes_on_all_paths_between_pairs_efficient(
                G, inputs + buff_param_preds, outputs
            )
        )
        missing_preds = identity_missing_predecessors(
            G, nodeset, set(inputs + buff_param_preds)
        )

    prev_missing_preds = set()

    R = G.reverse(copy=False)

    niter = 0
    while len(missing_preds) != 0 and prev_missing_preds != missing_preds:
        # if missing_preds is nonemtpy, construct the backwards-reachable subgraph from them.
        # this should identify the set of hidden-state buffers that we still need to include
        backwards_reachable = set()
        for node in missing_preds:
            backwards_reachable = (
                set(nx.descendants(R, node)) | backwards_reachable | set([node])
            )

        for node in backwards_reachable:
            if node in buffers or node in params:
                buff_param_preds.append(node)

        nodeset = nodeset.union(
            nodes_on_all_paths_between_pairs_efficient(
                G, inputs + buff_param_preds, outputs
            )
        )
        prev_missing_preds = missing_preds
        missing_preds = identity_missing_predecessors(
            G, nodeset, set(inputs + buff_param_preds)
        )
        niter += 1
    logger.debug(f"Added buffer/param predecessors in {niter} iterations")

    if len(missing_preds) != 0:
        n_nodes = len(nodeset)
        # brute-force try adding predecessors to the graph (need to verify that the nodes we add are reachable)
        for node in missing_preds:
            nodeset = nx.descendants(R, node) | nodeset | set([node])

        missing_preds = identity_missing_predecessors(
            G, nodeset, set(inputs + buff_param_preds)
        )
        n_nodes_final = len(nodeset)
        logger.debug(f"added {n_nodes_final - n_nodes} nodes via brute-force method")

    # now any remaining missing predecessors means that there is a true missing dependency
    if len(missing_preds) != 0:
        raise MissingFQIRDependencyError(f"missing predecessor nodes {missing_preds}")

    for node in nodeset:
        if len(list(G.predecessors(node))) == 0:
            if node not in inputs + list(buffers) + list(params):
                raise MissingFQIRDependencyError(
                    f"subgraph depends on root-node {node} which is not a specified input, parameter, or buffer"
                )

    # generate a new FQIR graph
    # while iterating through the original graph, add only the nodes from nodeset
    new_graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(new_graph)

    new_inputs = writer.add_inputs_like(inputs, copy_names=True)
    varmap = {x_orig: x_new for x_orig, x_new in zip(inputs, new_inputs)}

    init = fqir.subgraphs.get("INIT", GraphProto())
    arith = fqir.subgraphs["ARITH"]

    for buffer in init.all_tensors():
        if buffer in nodeset:
            precision = PREC_MAP.get(buffer.dtype, buffer.dtype)

            new_buffer = writer.add_zeros_buffer(
                buffer.shape[0], buffer.quanta, name=buffer.name, precision=precision
            )
            varmap[buffer] = new_buffer

    for param in arith.parameters:
        if param in nodeset:
            precision = PREC_MAP.get(param.dtype, param.dtype)
            new_param = writer.add_parameter(
                param.value, name=param.name, precision=precision, quanta=param.quanta
            )
            varmap[param] = new_param

    for node in arith.nodes:
        if node in nodeset:
            writer.copy_fqir_node(node, varmap)

    new_outputs = [varmap[y] for y in outputs]
    logger.debug(f"{new_outputs=}")
    writer.add_outputs(new_outputs)

    return new_graph
