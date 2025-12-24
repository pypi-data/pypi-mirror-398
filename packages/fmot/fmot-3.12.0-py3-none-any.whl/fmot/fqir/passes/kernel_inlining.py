from fmot.fqir import GraphProto, TensorProto
from fmot.fqir.writer import FQIRWriter
import logging

logger = logging.getLogger(__name__)


def inline_fqir_kernels(graph: GraphProto):
    arith = graph.subgraphs["ARITH"]
    init = graph.subgraphs.get("INIT", GraphProto())

    writer = FQIRWriter(arith=arith, init=init, act_precision="int16", main=graph)

    for node in arith.nodes:
        if node.opname == "fqir_writer_kernel":
            kname = node.constants["kernel_name"]
            kfunc = node.constants["kernel_writer"]
            kwargs = node.constants["kernel_kwargs"]

            logger.debug(f"Inlining FQIRWriter {kname} kernel for node {node}")

            with writer.replacing(node) as rwriter:
                replacements = kfunc(rwriter, node.inputs, **kwargs)
                rwriter.set_replacements(replacements)
