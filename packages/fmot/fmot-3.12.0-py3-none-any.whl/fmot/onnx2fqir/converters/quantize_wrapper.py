from pathlib import Path
from fmot.onnx2fqir.converters.custom_rewriters import edit_qdq_scales_to_power_of_two
import tempfile

try:
    import onnx
    import onnxruntime as ort
    from onnx import shape_inference
    from onnxruntime.quantization import (
        quantize_static,
        QuantType,
        QuantFormat,
        CalibrationDataReader,
    )
    from onnxruntime.quantization.shape_inference import quant_pre_process
except ImportError as e:
    raise Exception(
        f"Exception was {e}. We probably couldn't import tf/onnx. "
        f"Please install with onnx extra requires. e.g. pip install fmot[onnx2fqir]"
    )


def quantize_to_QOperator(
    model_input: str | Path | onnx.ModelProto,
    model_output: str | Path,
    calibration_data_reader: CalibrationDataReader,
):
    # Preprocess the model for quantization
    preprocessed_out_file = tempfile.NamedTemporaryFile(delete=False)
    quant_pre_process(model_input, preprocessed_out_file.name)

    # Quantize the model to QDQ format
    quantized_out_file = tempfile.NamedTemporaryFile(delete=False)
    quantize_static(
        model_input=preprocessed_out_file.name,
        model_output=quantized_out_file.name,
        quant_format=QuantFormat.QDQ,
        calibration_data_reader=calibration_data_reader,
        activation_type=QuantType.QInt8,
        weight_type=QuantType.QInt8,
        extra_options={
            "ActivationSymmetric": True,
            "WeightSymmetric": True,
            "AddQDQPairToWeight": True,
        },
    )
    preprocessed_out_file.close()

    # Edit QDQ scales to be power-of-two
    onnx_model = onnx.load(quantized_out_file.name)
    quantized_out_file.close()
    power_of_two_file = tempfile.NamedTemporaryFile(delete=False)
    onnx_model = edit_qdq_scales_to_power_of_two(onnx_model)
    onnx.save(onnx_model, power_of_two_file.name)

    # Optimize the ONNX model to QOperator format
    qoperator_file = tempfile.NamedTemporaryFile(delete=False)
    sess_options = ort.SessionOptions()
    sess_options.add_session_config_entry("session.qdqisint8allowed", "1")
    sess_options.graph_optimization_level = (
        ort.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
    )
    sess_options.optimized_model_filepath = qoperator_file.name
    ort.InferenceSession(power_of_two_file.name, sess_options)
    power_of_two_file.close()

    # Perform shape inference
    model = onnx.load(qoperator_file.name)
    model = shape_inference.infer_shapes(model)
    onnx.save_model(model, model_output)
    qoperator_file.close()
