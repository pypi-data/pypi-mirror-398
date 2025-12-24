import tensorflow as tf
import numpy as np
import onnx
import onnxruntime as ort
import tf2onnx
import tempfile
from onnxruntime.quantization import quantize_static, QuantType, QuantFormat
from fmot.onnx2fqir.converters.custom_rewriters import (
    rewrite_bias_squeeze_conv2d_expand_with_fused_conv1d,
    edit_qdq_scales_to_power_of_two,
)
from onnxruntime.quantization import CalibrationDataReader
from fmot.onnx2fqir.converters import quantize_to_QOperator
from fmot.onnx2fqir.converters import convert_streaming_tdnn_to_fqir
from fmot.onnx2fqir import parse_onnx_graph
from tempfile import NamedTemporaryFile
import pytest


def create_keras_tdnn_model(final_act="softmax", use_bias=True):
    # Create a simple Keras model with Conv1d having bias and activation, flatten, and Dense layer with softmax
    input_layer = tf.keras.Input(shape=(10, 16))  # (time, channels)

    x = input_layer

    for _ in range(2):
        x = tf.keras.layers.Conv1D(
            filters=32,
            kernel_size=3,
            padding="valid",
            use_bias=use_bias,
            activation="relu",
            bias_initializer=tf.keras.initializers.RandomUniform(
                minval=-0.1, maxval=0.1, seed=None
            ),
        )(x)
    x = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dense(10, activation=final_act)(x)

    output_layer = x

    model = tf.keras.Model(inputs=input_layer, outputs=output_layer)
    return model


def create_keras_tdnn_mixed_bias_model(final_act="softmax", use_bias=True):
    # Create a simple Keras model with Conv1d having bias and activation, flatten, and Dense layer with softmax
    input_layer = tf.keras.Input(shape=(10, 16))  # (time, channels)

    x = input_layer

    x = tf.keras.layers.Conv1D(
        filters=32,
        kernel_size=3,
        padding="valid",
        use_bias=use_bias,
        activation="relu",
        bias_initializer=tf.keras.initializers.RandomUniform(
            minval=-0.1, maxval=0.1, seed=None
        ),
    )(input_layer)
    # invert bias usage for second conv layer
    x = tf.keras.layers.Conv1D(
        filters=32,
        kernel_size=3,
        padding="valid",
        use_bias=not use_bias,
        activation="relu",
        bias_initializer=tf.keras.initializers.RandomUniform(
            minval=-0.1, maxval=0.1, seed=None
        ),
    )(x)

    x = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dense(10, activation=final_act)(x)

    output_layer = x

    model = tf.keras.Model(inputs=input_layer, outputs=output_layer)
    return model


@pytest.mark.parametrize("use_bias", [True, False])
@pytest.mark.parametrize(
    "model_func", [create_keras_tdnn_model, create_keras_tdnn_mixed_bias_model]
)
def test_rewrite_bias_squeeze_conv2d_expand_with_fused_conv1d_if_squeeze_present(
    use_bias, model_func
):
    model = model_func(use_bias=use_bias)

    # Convert the Keras model to ONNX with the custom rewriter
    input_signature = [
        tf.TensorSpec(model.inputs[0].shape, model.inputs[0].dtype, name="input")
    ]
    onnx_model, _ = tf2onnx.convert.from_keras(
        model,
        input_signature,
        opset=18,
        custom_rewriter=[rewrite_bias_squeeze_conv2d_expand_with_fused_conv1d],
    )

    # Check if there are any Squeeze nodes remaining in the ONNX graph
    squeeze_nodes = [
        node for node in onnx_model.graph.node if node.op_type == "Squeeze"
    ]
    assert (
        len(squeeze_nodes) == 0
    ), "Squeeze nodes still present in the ONNX graph after applying the rewriter"


@pytest.mark.parametrize("use_bias", [True, False])
@pytest.mark.parametrize(
    "model_func", [create_keras_tdnn_model, create_keras_tdnn_mixed_bias_model]
)
def test_rewrite_bias_squeeze_conv2d_expand_with_fused_conv1d_output(
    use_bias, model_func
):
    # Create a simple Keras model with Conv1d having bias and activation, flatten, and Dense layer with softmax
    model = model_func(use_bias=use_bias)

    # run the model with sample input
    sample_input = np.random.rand(1, 10, 16).astype(np.float32)
    keras_output = model.predict(sample_input)

    # Convert the Keras model to ONNX with the custom rewriter
    input_signature = [
        tf.TensorSpec(model.inputs[0].shape, model.inputs[0].dtype, name="input")
    ]
    onnx_model, _ = tf2onnx.convert.from_keras(
        model,
        input_signature,
        opset=18,
        custom_rewriter=[rewrite_bias_squeeze_conv2d_expand_with_fused_conv1d],
    )

    # Run the ONNX model with the same input
    session = ort.InferenceSession(onnx_model.SerializeToString())
    input_name = session.get_inputs()[0].name
    onnx_output = session.run(None, {input_name: sample_input})[0]

    # Compare the outputs
    assert np.allclose(keras_output, onnx_output), "Outputs do not match"


def test_edit_qdq_scales_to_power_of_two():
    # Create a simple Keras model
    model = create_keras_tdnn_model()

    # Convert the Keras model to ONNX
    input_signature = [
        tf.TensorSpec(model.inputs[0].shape, model.inputs[0].dtype, name="input")
    ]
    onnx_model, _ = tf2onnx.convert.from_keras(
        model,
        input_signature,
        opset=18,
    )

    # Quantize the ONNX model to introduce QuantizeLinear and DequantizeLinear nodes
    with tempfile.NamedTemporaryFile(suffix=".onnx") as f:
        temp_model_path = f.name

        class FakeCalibrationDataReader:
            def __init__(self):
                super().__init__()
                self.dataset = [
                    (np.random.uniform(-1, 1, size=(1, 10, 16)).astype(np.float32))
                    for _ in range(100)
                ]
                self.iterator = iter(self.dataset)

            def get_next(self) -> dict:
                try:
                    return {"input": next(self.iterator)}
                except Exception:
                    return None

        quantize_static(
            onnx_model,
            temp_model_path,
            weight_type=QuantType.QInt8,
            activation_type=QuantType.QInt8,
            quant_format=QuantFormat.QDQ,
            calibration_data_reader=FakeCalibrationDataReader(),
        )
        onnx_model = onnx.load(temp_model_path)

    # Apply the edit_qdq_scales_to_power_of_two rewriter
    modified_model = edit_qdq_scales_to_power_of_two(onnx_model)

    # Check that all QuantizeLinear and DequantizeLinear scales are powers of two
    scale_input_names = set()
    for node in modified_model.graph.node:
        if node.op_type == "QuantizeLinear" or node.op_type == "DequantizeLinear":
            scale_input_names.add(node.input[1])
    # Find the corresponding initializer
    for initializer in modified_model.graph.initializer:
        if initializer.name in scale_input_names:
            if len(initializer.float_data) == 0 and initializer.dims != []:
                raw_data = initializer.raw_data
                float_data = np.frombuffer(raw_data, dtype=np.float32)
            else:
                float_data = np.array(initializer.float_data)
            # Check if all scales are powers of two
            for scale in float_data:
                log2_scale = np.log2(scale)
                assert np.isclose(
                    log2_scale, np.round(log2_scale)
                ), f"Scale {scale} is not a power of two"


def get_quantized_onnx_graph(final_act="softmax", use_bias=True):
    model = create_keras_tdnn_model(final_act=final_act, use_bias=use_bias)

    for _ in range(10):
        _ = model(np.random.rand(8, 10, 16).astype(np.float32), training=True)

    # freeze batchnorm
    for layer in model.layers:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False

    # Convert the Keras model to ONNX with the custom rewriter
    input_signature = [
        tf.TensorSpec(model.inputs[0].shape, model.inputs[0].dtype, name="input")
    ]
    onnx_model, _ = tf2onnx.convert.from_keras(
        model,
        input_signature,
        opset=18,
        custom_rewriter=[rewrite_bias_squeeze_conv2d_expand_with_fused_conv1d],
    )

    # Find model input shape for calibration data reader
    input_shape = onnx_model.graph.input[0].type.tensor_type.shape
    input_shape = [dim.dim_value for dim in input_shape.dim]
    input_shape[0] = 1  # Set batch size to 1
    print("Model input shape:", input_shape)

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

    with NamedTemporaryFile(suffix=".onnx") as temp:
        quantize_to_QOperator(
            model_input=onnx_model,
            model_output=temp.name,
            calibration_data_reader=FakeCalibrationDataReader(),
        )

        onnx_model = onnx.load(temp.name)

    return model, onnx_model


@pytest.mark.parametrize("final_act", [None, "softmax"])
@pytest.mark.parametrize("use_bias", [True, False])
def test_quantization_error(final_act, use_bias):
    batch = 32

    model, onnx_model = get_quantized_onnx_graph(final_act=final_act, use_bias=use_bias)

    # run the model with sample input
    sample_input = np.random.rand(batch, 10, 16).astype(np.float32)
    keras_output = model(sample_input, training=False)

    # run the onnx model with sample input
    with NamedTemporaryFile(suffix=".onnx") as temp:
        onnx.save(onnx_model, temp.name)
        session = ort.InferenceSession(temp.name)
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        onnx_output = session.run([output_name], {input_name: sample_input})[0]

    keras_output = keras_output.numpy()

    rmse = np.sqrt(np.mean((keras_output - onnx_output) ** 2))
    print(rmse)

    if final_act is None:
        if use_bias:
            assert rmse < 2e-1
        else:
            assert rmse < 2e-2

    elif final_act == "softmax":
        if use_bias:
            assert rmse < 2e-1
        else:
            assert rmse < 1e-2


@pytest.mark.parametrize("final_act", [None, "softmax"])
@pytest.mark.parametrize("use_bias", [True, False])
def test_fqir_conversion(final_act, use_bias, plot=False):
    tf.random.set_seed(0)
    np.random.seed(0)

    model, onnx_model = get_quantized_onnx_graph(final_act=final_act, use_bias=use_bias)
    # onnx.save(onnx_model, "test_model.onnx")

    cstate = convert_streaming_tdnn_to_fqir(
        onnx_model, batch_dim=0, seq_dim=1, feature_dim=2, options=["conv1d_via_unfold"]
    )

    sample_input = np.random.rand(1, 10, 16).astype(np.float32)
    with NamedTemporaryFile(suffix=".onnx") as temp:
        onnx.save(onnx_model, temp.name)
        session = ort.InferenceSession(temp.name)
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        onnx_output = session.run([output_name], {input_name: sample_input})[0]

    if onnx_output.ndim == 3:
        onnx_output = onnx_output[0]

    (x_quant,) = cstate.quantize_inputs([sample_input[0]])
    fqir_output = cstate.fqir.run(x_quant)
    (fqir_output,) = cstate.dequantize_outputs([fqir_output])
    # remove receptive-field's worth of initial data points
    fqir_output = fqir_output[cstate.receptive_field :]

    error = np.mean((fqir_output - onnx_output) ** 2)
    error = error / np.mean(onnx_output**2)
    error = np.sqrt(error)

    print(fqir_output.shape)
    print(onnx_output.shape)

    print(f"normalized RMSE: {error}")

    if plot:
        import matplotlib.pyplot as plt

        plt.plot(fqir_output.flatten(), onnx_output.flatten(), ".")
        plt.title(f"{error=} {use_bias=} {final_act=}")
        plt.grid()
        plt.show()

    assert error < 0.02


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    test_fqir_conversion(None, True, plot=True)
    test_fqir_conversion(None, False, plot=True)
    test_fqir_conversion("softmax", True, plot=True)
    test_fqir_conversion("softmax", False, plot=True)
