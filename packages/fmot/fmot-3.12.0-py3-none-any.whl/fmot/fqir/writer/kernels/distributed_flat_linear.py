import numpy as np
from fmot.fqir.writer import FQIRWriter
from fmot.fqir import GraphProto, TensorProto
from typing import Optional
import logging

logger = logging.getLogger(__name__)

MAX_UNROLLED_OUT_CH = 2
ACC_PRECISION = "int24"


def write_distributed_flat_linear(
    writer: FQIRWriter,
    x_t: TensorProto,
    weight: np.ndarray,
    pad_pre: int,
    in_channels: int,
    out_channels: int,
    kernel_size: int,
    pad_post: int,
    quanta_weight: int,
    quanta_out: int,
    quanta_bias: Optional[int] = None,
    bias: Optional[np.ndarray] = None,
    precision: str = "int16",
    dot_method: str = "tree",
    debug=False,
):
    """
    Writes FQIR kernel for distributed flattened linear

    Arguments:
        writer (FQIRWriter): FQIRWriter instance for kernel insertion
        x_t (TensorProto): input vector (single-frame)
        weight (np.ndarray): integer-valued weight matrix (will be re-formatted into a vector of weights), of shape:
            (out_channels, in_channels * kernel_size)
        pad_pre (int): number of discarded frames at the beginning of each detection window
        kernel_size (int): size of active detection window
        pad_post (int): number of discarded frames at the end of each detection window
        quanta_weight (int): quanta for the weight matrix
        quanta_out (int): output quanta
        quanta_bias (int): bias quanta, optional. Must be non-None if bias is not None
        bias (np.ndarray, optional): optional integer-valued bias, of shape (out_channels)
        precision (str, optional): "int16" or "int8", default "int16"
        dot_method (str, optional): "tree" or "matrix", default "tree"

    Approach:
        - reshapes weights into a circular buffer of weights per frame (including zero-padding at beginning and end)
        - accumulates matmul with each frame
        - resets the accumulated output every `pad_pre + kernel_size + pad_post` frames
    """
    window_size = kernel_size + pad_pre + pad_post

    logger.debug(
        f"{in_channels=} {out_channels=} {kernel_size=} {pad_pre=} {pad_post=}"
    )

    if weight.shape[1] != in_channels * kernel_size:
        raise ValueError(
            f"Shape mismatch: expected weight to have shape ({out_channels}, {in_channels * kernel_size}) but got {weight.shape}"
        )

    # pad and flatten the weight matrix
    # w_flat = weight.reshape(out_channels, kernel_size, in_channels).transpose(1, 2).flatten()
    w_flat = weight.reshape(out_channels, in_channels, kernel_size)
    w_flat = np.permute_dims(w_flat, (2, 0, 1)).flatten()
    w_flat = np.pad(
        w_flat,
        (pad_pre * in_channels * out_channels, pad_post * in_channels * out_channels),
    )
    w_flat = writer.add_init_buffer(w_flat, precision=precision, quanta=quanta_weight)

    # create the "reset" boolean sequence
    g_reset = np.empty(window_size, dtype=np.int16)
    g_reset[0] = 1
    g_reset[1:] = 0
    g_reset = writer.add_init_buffer(g_reset, precision="int16", quanta=0)

    ###############
    #  write the kernel
    ###############

    # read and rotate the reset boolean sequence
    g_t, g_rem = writer.split(g_reset, split_sizes=[1, window_size - 1])
    g_next = writer.cat([g_rem, g_t])
    writer.assign(g_reset, g_next)

    # read and rotate the active weights
    weight_size = in_channels * out_channels
    w_t, w_rem = writer.split(
        w_flat, split_sizes=[weight_size, (window_size - 1) * weight_size]
    )
    w_next = writer.cat([w_rem, w_t])
    writer.assign(w_flat, w_next)

    # matmul between w_t and x_t
    if out_channels == 1:
        y_t = writer.dot(w_t, x_t, quanta=quanta_out, method=dot_method)
    elif out_channels < MAX_UNROLLED_OUT_CH:
        w_t_slices = writer.split(w_t, [in_channels] * out_channels)
        y_t = []
        for w_t_i in w_t_slices:
            y_t.append(writer.dot(w_t_i, x_t, quanta=quanta_out, method=dot_method))
        y_t = writer.cat(y_t)
    else:
        with writer.for_loop_writer(
            n_iter=out_channels, x_to_slice=[w_t], x_recurse_init=[], x_scope=[x_t]
        ) as lwriter:
            (x_t_lwriter,) = lwriter.scoped_inputs
            (w_t_i,) = lwriter.sliced_inputs

            y_t_i = lwriter.dot(
                x_t_lwriter, w_t_i, quanta=quanta_out, method=dot_method
            )
            y_t = lwriter.return_concatenated(y_t_i)

    # accumulation of the y_t updates

    if ACC_PRECISION == "int24":
        quanta_acc = quanta_out - 8
    else:
        quanta_acc = quanta_out

    acc = writer.add_zeros_buffer(
        channels=out_channels, quanta=quanta_acc, precision=ACC_PRECISION
    )

    with writer.with_precision(ACC_PRECISION) as acc_writer:
        accumulated_next = acc_writer.add(acc, y_t, quanta=quanta_acc)

        if bias is not None:
            bias = acc_writer.add_parameter(
                bias, precision=precision, quanta=quanta_bias
            )
            reset_next = acc_writer.add(bias, y_t, quanta=quanta_acc)
        else:
            reset_next = y_t

        acc_next = acc_writer.masked_construct(
            condition=g_t,
            value_true=reset_next,
            value_false=accumulated_next,
            quanta=quanta_acc,
        )

        acc_writer.assign(acc, acc_next)

    if ACC_PRECISION == "int24":
        acc_next = writer.add(acc_next, 0, quanta=quanta_out)

    if not debug:
        return acc_next
    else:
        return acc_next, {
            "w_next": w_next,
            "w_t": w_t,
            "g_next": g_next,
            "g_t": g_t,
            "y_t": y_t,
            "acc_next": acc_next,
        }
