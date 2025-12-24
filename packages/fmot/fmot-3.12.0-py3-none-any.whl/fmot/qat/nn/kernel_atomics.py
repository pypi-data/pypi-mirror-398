"""Definitions of Atomic Modules that generate FQIRWriter kernels rather than 
1-to-1 mappings to FQIR OpTypes."""
from .atomics import (
    AtomicModule,
    check_for_annotations,
    supports_int24,
    quantizers,
    Bitwidth,
    copy_dim_annotations,
    fake_quantize,
)
from .qat_cumulative_linear import quant_distributed_flat_linear
import torch
from torch import nn, Tensor
from functools import partial
from fmot.fqir import GraphProto, TensorProto
from fmot.fqir.writer import FQIRWriter
from fmot.fqir.writer import kernels
from typing import Optional, Any, Callable
from dataclasses import dataclass
import numpy as np


@dataclass
class KernelInfo:
    kernel_name: str
    kernel_writer: Callable
    kernel_kwargs: dict
    input_protos: dict[str, TensorProto]


class KernelAtomicModule(AtomicModule):
    def _get_kernel_kwargs(self, inputs: Any) -> KernelInfo:
        raise NotImplementedError(
            "Each KernelAtomicModule must define its own _get_kernel_kwargs method"
        )


class F_CumulativeFlattenedLinear(KernelAtomicModule):
    def __init__(
        self,
        bitwidth: Bitwidth,
        n_keep: int,
        n_discard: int,
        observer=quantizers.DEFAULT_OBSERVERS["default"],
    ):
        super().__init__(round=False)  # don't support rounding initially...
        self.n_keep = n_keep
        self.n_discard = n_discard

        self.quantizer = quantizers.Quantizer(bitwidth, observer=observer)
        self.quanta = None
        self.bits = bitwidth.bitwidth
        self.tracing_mode = False

    @check_for_annotations
    @supports_int24(
        False, reason="CumulativeFlattenedLinear does not support int24 activations"
    )
    def forward(self, x: Tensor, weight: Tensor, bias: Optional[Tensor]):
        if self.quantize:
            quanta = self.quanta
        else:
            quanta = None

        if self.tracing_mode:
            out_shape = [shp for shp in x.shape[:-1]] + [weight.shape[0]]
            output = torch.zeros(out_shape, device=x.device)

        else:
            output = quant_distributed_flat_linear(
                x=x,
                weight=weight,
                bias=bias,
                n_keep=self.n_keep,
                n_discard=self.n_discard,
                bits=self.bits,
                quanta=quanta,
                rounded=self.round,
            )

        output = self.quantizer(copy_dim_annotations(x, output))
        if output.quanta is not None:
            self.quanta = output.quanta.detach()
        return output

    def _get_kernel_kwargs(self, inputs: list[Tensor]) -> KernelInfo:
        x, weight, bias = inputs

        quant_weight = fake_quantize(
            weight, quanta=weight.quanta, bits=weight.bitwidth.bitwidth, rounded=True
        )
        quant_weight = quant_weight / 2 ** (weight.quanta)
        quant_weight = quant_weight.detach().cpu().numpy().astype(np.int32)
        if bias is not None:
            quant_bias = fake_quantize(
                bias, quanta=bias.quanta, bits=bias.bitwidth.bitwidth, rounded=True
            )
            quant_bias = quant_bias / 2 ** (bias.quanta)
            quant_bias = quant_bias.detach().cpu().numpy().astype(np.int32)
            q_bias = int(bias.quanta.detach().cpu().item())
        else:
            quant_bias = None
            q_bias = None

        config = dict(
            weight=quant_weight,
            pad_pre=self.n_discard,
            in_channels=x.shape[1],
            out_channels=weight.shape[0],
            kernel_size=self.n_keep,
            pad_post=0,
            quanta_weight=int(weight.quanta.detach().cpu().item()),
            quanta_out=int(self.quanta.detach().cpu().item()),
            quanta_bias=q_bias,
            bias=quant_bias,
            precision="int16",
            dot_method="tree",
            debug=False,
        )

        input_protos = {"x_t": x.proto}

        return KernelInfo(
            kernel_name="distributed_flat_linear",
            kernel_writer=self._write_kernel,
            kernel_kwargs=config,
            input_protos=input_protos,
        )

    @staticmethod
    def _write_kernel(
        writer: FQIRWriter, inputs: dict[str, TensorProto], **kwargs
    ) -> list[TensorProto]:
        y_proto = kernels.write_distributed_flat_linear(
            writer=writer, **inputs, **kwargs
        )

        return [y_proto]


class CumulativeFlattenedLinear(nn.Module):
    def __init__(
        self,
        bitwidth_act,
        bitwidth_weight,
        in_channels: int,
        out_channels: int,
        n_keep: int,
        n_discard: int = 0,
        bias: bool = True,
        observer=quantizers.DEFAULT_OBSERVERS["default"],
    ):
        super().__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.n_keep = n_keep
        self.n_discard = n_discard

        self.weight = nn.Parameter(torch.empty((out_channels, in_channels * n_keep)))
        self.quant_weight = quantizers.ParameterQuantizer(bitwidth_weight, observer)

        if bias:
            self.quant_bias = quantizers.ParameterQuantizer(bitwidth_act, observer)
            self.bias = nn.Parameter(torch.empty(out_channels))
        else:
            self.bias = None
            self.quant_bias = None

        self.F_block = F_CumulativeFlattenedLinear(
            bitwidth=bitwidth_act,
            n_keep=n_keep,
            n_discard=n_discard,
            observer=observer,
        )

        self.reset_parameters()

    def reset_parameters(self):
        nn.Linear.reset_parameters(self)

    def forward(self, x):
        weight = self.quant_weight(self.weight)
        if self.bias is not None:
            bias = self.quant_bias(self.bias)
        else:
            bias = None

        output = self.F_block(x, weight, bias)
        return output

    @classmethod
    def _from_float(
        cls,
        parent,
        bw_conf,
        interpolate,
        observer=quantizers.DEFAULT_OBSERVERS["default"],
        **kwargs,
    ):
        observer = partial(observer, **kwargs)

        layer = cls(
            bitwidth_act=bw_conf.activations,
            bitwidth_weight=bw_conf.weights,
            observer=observer,
            in_channels=parent.in_channels,
            out_channels=parent.out_channels,
            n_keep=parent.n_keep,
            n_discard=parent.n_discard,
            bias=parent.bias is not None,
        )

        layer.weight.data = parent.weight.data
        if layer.bias is not None:
            layer.bias.data = parent.bias.data

        return layer
