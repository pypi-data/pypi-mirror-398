import torch
from torch import nn, Tensor
import math
from typing import Optional


@torch.jit.ignore()
def cumulative_flat_linear(
    x: Tensor,
    weight: Tensor,
    n_discard: int,
    n_keep: int,
    bias: Optional[Tensor] = None,
):
    T = x.shape[-1]
    group_size = n_keep + n_discard
    n_groups = int(math.ceil(T / (group_size)))
    padding = n_groups * group_size - T

    x = nn.functional.pad(x, (0, padding))

    channels_in = x.shape[1]
    channels_out = weight.shape[0]
    if weight.shape[1] != channels_in * n_keep:
        raise ValueError(
            f"{weight.shape[1]=}, expected {channels_in * n_keep=} {channels_in=} {n_keep=}"
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

        y_grp = torch.cumsum(y_grp, 1)

        if bias is not None:
            y_grp = y_grp + bias

        y[..., i * group_size : (i + 1) * group_size] = torch.permute(y_grp, (0, 2, 1))

    # discard padding (if any)
    if padding != 0:
        y = y[..., :T]

    return y


class CumulativeFlattenedLinear(nn.Module):
    """
    Linear projection over a fixed-length temporal window, computed cumulatively.

    Input:
        x: Tensor of shape (batch_size, channels_per_timestep, seq_length)

    Output:
        y: Tensor of shape (batch_size, out_channels, seq_length)
        where y[..., t] is the *partial sum* at time t.

    Args:
        seq_length (int): Number of timesteps per processing window.
        trim_frames (int): Number of initial frames to discard (K). Must satisfy 0 ≤ trim_frames ≤ seq_length.
        channels_per_timestep (int): Feature dimension at each timestep.
        out_channels (int): Output feature dimension per timestep.
        bias (bool, optional): If True, include a bias term that seeds each window's cumulative sum. Default: True.

    Computation:
        Let the weight W be partitioned into per-timestep blocks W_t of shape
        (out_channels, channels_per_timestep). Then the layer computes
        a causal cumulative sum with a reset every `seq_length` frames.

            y_t = (y_{t-1} if t % seq_length != 0 else b) + W_t @ x_t

        with y_{-1} := 0 and b = 0 if bias = False else bias.
        The first `trim_frames` blocks W_0, …, W_{trim_frames-1} are all zeros,
        so those frames have no effect. For t ≥ trim_frames, W_t takes the corresponding
        sub-matrix from the packed weight parameter. After every `seq_length` frames,
        the cumulative sum resets to the bias `b` (or zero if `bias=False`), enabling
        continual streaming inference.

        Equivalently, at the final timestep of each window (t = seq_length - 1),
        y_t equals a single linear projection applied to the flattened, *trimmed*
        window:
            flatten([x_{trim_frames}, …, x_{seq_length-1}]), of shape (batch, in_channels)
        projected by a weight of shape (out_channels, in_channels), where
            in_channels = (seq_length - trim_frames) * channels_per_timestep.

    Notes:
        - This layer returns a *partial-sum* result at every timestep (`seq_length` outputs),
          but only the last timestep of each window matches the full flatten→linear result.
        - The cumulative reset every `seq_length` frames makes this suitable for streaming.
        - Setting `trim_frames=0` reduces to a straight cumulative linear over the window.
        - If `bias=False`, the reset value is zero instead of the bias vector.

    Example:

        TODO: write a simple demo of flatten() -> linear() converted to CumulativeFlattenedLinear

        .. code:: python

            import torch
            from fmot.nn import CumulativeFlattenedLinear

            ch_per_timestep = 16
            seq_length = 32
            in_channels = ch_per_timestep * seq_length
            out_channels = 1

            model = torch.nn.Sequential(torch.nn.Flatten(), torch.nn.Linear(in_channels, out_channels))
            converted = CumulativeFlattenedLinear(seq_length, 0, ch_per_timestep, out_channels)

            # can load the state-dict from the linear layer
            converted.load_state_dict(model[1].state_dict())

            x = torch.randn(8, seq_length, ch_per_timestep)
            y0 = model(x)
            y1 = converted(x)

            print(y0.shape)
            >>> (8, 1)
            print(y1.shape)
            >>> (8, 32, 1)

            import matplotlib.pyplot as plt

            plt.axhline(y0[0].detach().item())
            plt.plot(y1[0,:,0].detach())
            plt.show()

        .. image:: /Users/scott/Code/fmot_clean/fmot/docs/images/distributed_flat_linear.png

    """

    def __init__(
        self,
        seq_length: int,
        trim_frames: int,
        channels_per_timestep: int,
        out_channels: int,
        bias: bool = True,
    ):
        super().__init__()
        self.in_channels = channels_per_timestep
        self.out_channels = out_channels
        self.n_keep = seq_length - trim_frames
        self.n_discard = trim_frames

        if bias:
            self.bias = nn.Parameter(torch.empty(out_channels))
        else:
            self.bias = None

        self.weight = nn.Parameter(
            torch.empty((out_channels, self.in_channels * self.n_keep))
        )

        self.reset_parameters()

    def reset_parameters(self):
        nn.Linear.reset_parameters(self)

    def forward(self, x):
        return cumulative_flat_linear(
            x, self.weight, self.n_discard, self.n_keep, self.bias
        )
