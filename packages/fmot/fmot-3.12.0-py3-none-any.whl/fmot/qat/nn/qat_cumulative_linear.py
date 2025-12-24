import torch
from torch import nn, Tensor
import math
from typing import Optional
from ..fake_quantization import fake_quantize


def quant_cumsum_lastdim(
    x: Tensor, quanta: int, bits: int, rounded: bool = False, bias: Tensor = None
):
    y = torch.empty_like(x)
    if bias is None:
        y_prev = 0
    else:
        y_prev = bias

    T = x.shape[-1]
    for t in range(T):
        y_curr = x[..., t] + y_prev
        if quanta is not None:
            y_curr = fake_quantize(y_curr, quanta=quanta, bits=bits, rounded=rounded)
        y[..., t] = y_curr
        y_prev = y_curr

    return y


def quant_distributed_flat_linear(
    x: Tensor,
    weight: Tensor,
    n_discard: int,
    n_keep: int,
    quanta: int,
    bits: int,
    rounded: bool,
    bias: Optional[Tensor] = None,
):
    tracing = x.ndim == 2
    if tracing:
        x = x.unsqueeze(-1)

    T = x.shape[-1]
    group_size = n_keep + n_discard
    n_groups = int(math.ceil(T / (group_size)))
    padding = n_groups * group_size - T

    x = nn.functional.pad(x, (0, padding))

    channels_in = x.shape[1]
    channels_out = weight.shape[0]

    if weight.shape[1] != channels_in * n_keep:
        raise ValueError(
            f"{weight.shape[1]=}, expected {channels_in * n_keep=}. {x.shape=}"
        )

    # reshape the weight matrix to (group_size x channels_out x channels_in)
    # including zero-padding for the first n_discard frames
    weight_eff = weight.reshape(channels_out, channels_in, n_keep)
    weight_eff = weight_eff.permute(2, 1, 0)  # (n_keep, ch_in, ch_out)
    weight_eff = nn.functional.pad(
        weight_eff, (0, 0, 0, 0, n_discard, 0)
    )  # (group_size, ch_in, ch_out)

    y = torch.empty(x.shape[0], channels_out, T + padding)

    for i in range(n_groups):
        x_grp = x[..., i * group_size : (i + 1) * group_size]
        x_grp = torch.permute(x_grp, (0, 2, 1))

        y_grp = torch.einsum("bnd,ndo->bno", x_grp, weight_eff)

        y_grp = quant_cumsum_lastdim(
            y_grp.transpose(1, 2), quanta, bits, rounded, bias=bias
        )

        y[..., i * group_size : (i + 1) * group_size] = y_grp

    # discard padding (if any)
    if padding != 0:
        y = y[..., :T]

    if tracing:
        y = y.unsqueeze(-1)

    return y
