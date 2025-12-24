def _get_dir():
    import pathlib

    return pathlib.Path(__file__).parent.resolve()


# __version__ = (_get_dir() / "VERSION").read_text(encoding="utf-8").strip()

from .parsing import ParsedTensor, ParsedOperator, ParsedGraph, parse_onnx_graph
from .converters import convert_streaming_tdnn_to_fqir
from .add_debug_outputs import add_intermediate_outputs_to_model
