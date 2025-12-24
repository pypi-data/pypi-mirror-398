def test_onnx2fqir_doc_example():
    # CELL 0

    import tensorflow as tf

    input_layer = tf.keras.Input(shape=(10, 16))  # (time, channels)

    input_shape = input_layer.shape[1:]

    x = input_layer
    for _ in range(2):
        x = tf.keras.layers.Conv1D(
            filters=32,
            kernel_size=3,
            padding="valid",
            use_bias=True,
            activation="relu",
            bias_initializer=tf.keras.initializers.RandomUniform(
                minval=-0.1, maxval=0.1, seed=None
            ),
        )(x)
    x = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dense(10, activation="softmax")(x)

    output_layer = x
    model = tf.keras.Model(inputs=input_layer, outputs=output_layer)

    # CELL 1

    import tf2onnx
    from fmot.onnx2fqir.converters.custom_rewriters import (
        rewrite_bias_squeeze_conv2d_expand_with_fused_conv1d,
    )

    input_signature = [
        tf.TensorSpec(model.inputs[0].shape, model.inputs[0].dtype, name="input")
    ]
    onnx_model, _ = tf2onnx.convert.from_keras(
        model,
        input_signature,
        opset=18,
        custom_rewriter=[rewrite_bias_squeeze_conv2d_expand_with_fused_conv1d],
    )

    # CELL 2

    from fmot.onnx2fqir.converters import quantize_to_QOperator
    from onnxruntime.quantization import CalibrationDataReader
    import numpy as np

    input_shape = [1] + list(input_layer.shape[1:])

    class FakeCalibrationDataReader(CalibrationDataReader):
        def __init__(self):
            super().__init__()
            self.dataset = [
                (np.random.rand(*input_shape).astype(np.float32)) for _ in range(100)
            ]
            self.iterator = iter(self.dataset)

        def get_next(self) -> dict:
            try:
                return {"input": next(self.iterator)}
            except Exception:
                return None

    QOPERATOR_FILE = "my_qoperator_model.onnx"

    quantize_to_QOperator(
        model_input=onnx_model,
        model_output=QOPERATOR_FILE,
        calibration_data_reader=FakeCalibrationDataReader(),
    )

    # CELL 3

    from fmot.onnx2fqir import convert_streaming_tdnn_to_fqir
    import onnx

    quantized_onnx_model = onnx.load(QOPERATOR_FILE)

    converted_state = convert_streaming_tdnn_to_fqir(
        quantized_onnx_model,
        batch_dim=0,
        seq_dim=1,
        feature_dim=2,
        options=["conv1d_via_unfold"],
    )

    fqir_graph = converted_state.fqir

    print(fqir_graph)

    # CELL 4
    import onnxruntime as ort

    # running the onnx graph
    input = np.random.rand(*input_shape).astype(np.float32)

    session = ort.InferenceSession(QOPERATOR_FILE)
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    (onnx_output,) = session.run([output_name], {input_name: input})
    print("Optimized ONNX model output:")
    print(onnx_output[0])

    # running the FQIR graph
    # - we must remove the batch dimension to run the FQIR, and run it through the converted_state's quantize method
    (fqir_input,) = converted_state.quantize_inputs([input[0]])
    fqir_output = fqir_graph.run(fqir_input)
    (fqir_output,) = converted_state.dequantize_outputs([fqir_output])

    # the FQIR returns an incremental output for each input time-step, so let's print just the final step
    print("FQIR Output (last time-step):")
    print(fqir_output[-1])


if __name__ == "__main__":
    test_onnx2fqir_doc_example()
