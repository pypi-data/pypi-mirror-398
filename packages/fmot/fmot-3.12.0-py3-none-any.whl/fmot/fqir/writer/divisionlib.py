import numpy as np
from fmot.fqir import TensorProto
from typing import TYPE_CHECKING, Optional
from dataclasses import dataclass

if TYPE_CHECKING:
    from fmot.fqir.writer import FQIRWriter


@dataclass
class ReciprocalComponentsI16:
    recip_hi: TensorProto
    recip_lo: TensorProto
    mask_hi: TensorProto
    eps: float
    sign: Optional[TensorProto] = None


@dataclass
class ReciprocalComponentsI24:
    recip_hi: TensorProto
    recip_mid: TensorProto
    recip_lo: TensorProto
    mask_hi: TensorProto
    mask_mid: TensorProto
    eps: float
    sign: Optional[TensorProto] = None


def get_i16_reciprocal_components(
    writer: "FQIRWriter", x: TensorProto, eps: float, pos_only=False
):
    if pos_only:
        sign = writer.sign(x)
        x = writer.abs(x)
    else:
        sign = None

    x = writer.add(x, eps, quanta=x.quanta)

    x_lo, x_hi = writer._precision_split(x, [8, 7], ["int8", "int8"])

    dx_hi = 2**x_hi.quanta
    dx_lo = 2**x_lo.quanta

    def func_hi(x):
        # eps_eff = max(dx_hi, eps)
        eps_eff = dx_hi
        x[np.abs(x) < eps_eff] = eps_eff
        y = 1 / x
        return y

    def d_func_hi(x):
        y = (func_hi(x + dx_hi) - func_hi(x)) / dx_hi
        return y

    def func_lo(x):
        # eps_eff = max(dx_lo, eps)
        eps_eff = dx_lo
        x[np.abs(x) < eps_eff] = eps_eff
        y = 1 / x
        return y

    f_hi = writer._raw_lut(x_hi, function=func_hi, name="reciprocal_hi")
    df_hi = writer._raw_lut(x_hi, function=d_func_hi, name="grad_reciprocal_hi")
    f_lo = writer._raw_lut(x_lo, function=func_lo, name="reciprocal_lo")

    y_hi = f_hi
    y_hi = writer.add(
        f_hi, writer.multiply(df_hi, x_lo, quanta=f_hi.quanta), quanta=f_hi.quanta
    )
    y_lo = f_lo

    mask_hi = writer.gt(x, 511 * 2 ** (x.quanta))

    return ReciprocalComponentsI16(y_hi, y_lo, mask_hi, eps, sign)


def get_i24_reciprocal_components(
    writer: "FQIRWriter", x: TensorProto, eps: float, pos_only=False
):
    with writer.with_precision("int24") as pwriter:
        if pos_only:
            sign = pwriter.sign(x)
            x = pwriter.abs(x)
        else:
            sign = None

        x = pwriter.add(x, eps, quanta=x.quanta)

    with writer.with_precision("int16") as pwriter:
        x_lo, x_mid, x_hi = pwriter._precision_split(
            x, [8, 8, 7], ["int8", "int8", "int8"]
        )

        if eps is None:
            eps = 2**x_lo.quanta

        dx_hi = 2**x_hi.quanta
        dx_mid = 2**x_mid.quanta

        def f_hi(x):
            eps_hi = min(dx_hi, eps)
            x[x <= eps_hi] = eps_hi
            return 1 / x

        def df_hi(x):
            return (f_hi(x + dx_hi) - f_hi(x)) / dx_hi

        def f_mid(x):
            eps_mid = min(dx_mid, eps)
            x[x <= eps_mid] = eps_mid
            return 1 / x

        def df_mid(x):
            return (f_mid(x + dx_mid) - f_hi(x)) / dx_mid

        def f_lo(x):
            x[x <= eps] = eps
            return 1 / x

        recip_hi = pwriter._raw_lut(x_hi, f_hi, name="recip_hi")
        d_recip_hi = pwriter._raw_lut(x_hi, df_hi, name="d_recip_hi")
        recip_mid = pwriter._raw_lut(x_mid, f_mid, name="recip_mid")
        d_recip_mid = pwriter._raw_lut(x_mid, df_mid, name="d_recip_mid")
        recip_lo = pwriter._raw_lut(x_lo, f_lo, name="recip_lo")

        recip_hi = pwriter.add(
            recip_hi,
            pwriter.multiply(d_recip_hi, x_mid, quanta=recip_hi.quanta),
            quanta=recip_hi.quanta,
        )
        recip_mid = pwriter.add(
            recip_mid,
            pwriter.multiply(d_recip_mid, x_lo, quanta=recip_mid.quanta),
            quanta=recip_mid.quanta,
        )

        is_hi = pwriter.gt(x_hi, 0)
        is_mid = pwriter.gt(x_mid, 0)

    return ReciprocalComponentsI24(
        recip_hi, recip_mid, recip_lo, is_hi, is_mid, eps, sign
    )


def divide_by_components_i16(
    writer: "FQIRWriter",
    num: TensorProto | list[TensorProto],
    components: ReciprocalComponentsI16,
    quanta: int | list[int],
):
    assert isinstance(components, ReciprocalComponentsI16)

    was_list = True
    if isinstance(num, TensorProto):
        was_list = False
        num = [num]

    if isinstance(quanta, int):
        quanta = [quanta] * len(num)

    if len(quanta) != len(num):
        raise ValueError(
            f"Recieved {len(quanta)} quanta values and {len(num)} numerators"
        )

    if writer.act_precision != "int16":
        raise NotImplementedError(
            "int16 divide expects writer to have int16 act_precision"
        )

    outs = []
    for num_i, quanta_i in zip(num, quanta):
        y_hi = writer.multiply(components.recip_hi, num_i, quanta=quanta_i)
        y_lo = writer.multiply(components.recip_lo, num_i, quanta=quanta_i)
        y = writer.masked_construct(components.mask_hi, y_hi, y_lo, quanta=quanta_i)
        if components.sign is not None:
            y = writer.multiply(y, components.sign, quanta=quanta_i)
        outs.append(y)

    if was_list:
        return outs
    else:
        return outs[0]


def divide_by_components_i24(
    writer: "FQIRWriter",
    num: TensorProto | list[TensorProto],
    components: ReciprocalComponentsI24,
    quanta: int | list[int],
) -> TensorProto | list[TensorProto]:
    was_list = True
    if isinstance(num, TensorProto):
        was_list = False
        num = [num]

    if isinstance(quanta, int):
        quanta = [quanta] * len(num)

    if len(quanta) != len(num):
        raise ValueError(
            f"Recieved {len(quanta)} quanta values and {len(num)} numerators"
        )

    outs = []
    for num_i, quanta_i in zip(num, quanta):
        with writer.with_precision("int24") as pwriter:
            y_hi = pwriter.multiply(components.recip_hi, num_i, quanta=quanta_i)
            y_mid = pwriter.multiply(components.recip_mid, num_i, quanta=quanta_i)
            y_lo = pwriter.multiply(components.recip_lo, num_i, quanta=quanta_i)
            y = pwriter.masked_construct(
                components.mask_mid, y_mid, y_lo, quanta=quanta_i
            )
            y = pwriter.masked_construct(components.mask_hi, y_hi, y, quanta=quanta_i)
            if components.sign is not None:
                y = pwriter.multiply(y, components.sign, quanta=quanta_i)
        outs.append(y)

    if was_list:
        return outs
    else:
        return outs[0]


def divide(
    writer: "FQIRWriter",
    num: TensorProto | list[TensorProto],
    den: TensorProto,
    quanta: int | list[int],
    eps: float = 1e-3,
    pos_only=False,
    return_components: bool = False,
) -> TensorProto | list[TensorProto]:
    """
    Divide numerator(s) `num` by denominator `den`. If multiple numerators are provided,
    this operation caches the reciprocal of the denominator for more efficient processing.

    Arguments:
        num (TensorProto | list[TensorProto]): one or multiple numerators to be divided by `den`.
        den (TensorProto): denominator
        quanta (int | list[int]): quanta to use for the final result(s). If a single quanta is provided,
            this will be reused for each numerator in `num`. If a list of quanta is provided, then it must
            match the number of numerators being used.
        eps (float): numerical epsilon for stability. Provided in the floating point domain
        pos_only (bool, optional): if True, the kernel assumes that the denominator is positive.
            If False, the kernel supports negative denominators. Default False. Set to True for a slightly
            more efficient kernel (if it is known that the denominator is always positive).
        return_components (bool, optional): if True, returns reciprocal-components that can be cached and used
            for other division operations using `divide_by_components`

    Returns:
        TensorProto | List[TensorProto]: the result(s) of dividing numerator(s) by the denominator.
            Matches the type of `num`: if `num` is an individual TensorProto, then this returns an individual
            TensorProto, otherwise returns a list of the same length as `num`.
        ReciprocalComponentsI16 | ReciprocalComponentsI16: if `return_components=True`, the reciprocal components
            will be cached and returned for future use.
    """
    if writer.act_precision == "int24":
        components = get_i24_reciprocal_components(writer, den, eps, pos_only)
        output = divide_by_components_i24(writer, num, components, quanta)
    elif writer.act_precision == "int16":
        components = get_i16_reciprocal_components(writer, den, eps, pos_only)
        output = divide_by_components_i16(writer, num, components, quanta)
    else:
        raise RuntimeError(
            f"divide only implemented for act_precision in [in16, int24], got {writer.act_precision}"
        )

    if return_components:
        return output, components
    else:
        return output


def divide_by_components(
    writer: "FQIRWriter",
    num: TensorProto | list[TensorProto],
    components: ReciprocalComponentsI16 | ReciprocalComponentsI24,
    quanta: int | list[int],
):
    """
    Divide numerator(s) `num` by a denominator that has previously be inverted and cached in reciprocal components.
    If multiple numerators are provided, this operation reuses the reciprocal of the denominator for more efficient processing.

    Arguments:
        num (TensorProto | list[TensorProto]): one or multiple numerators to be divided by `den`.
        componenets (ReciprocalComponentsI16 or ReciprocalComponentsI24): cached reciprocal components
        quanta (int | list[int]): quanta to use for the final result(s). If a single quanta is provided,
            this will be reused for each numerator in `num`. If a list of quanta is provided, then it must
            match the number of numerators being used.

    Returns:
        TensorProto | List[TensorProto]: the result(s) of dividing numerator(s) by the denominator.
            Matches the type of `num`: if `num` is an individual TensorProto, then this returns an individual
            TensorProto, otherwise returns a list of the same length as `num`.
    """
    if writer.act_precision == "int24":
        return divide_by_components_i24(writer, num, components, quanta)
    if writer.act_precision == "int16":
        return divide_by_components_i16(writer, num, components, quanta)
    else:
        raise RuntimeError(
            f"divide_by_components only implemented for act_precision in [in16, int24], got {writer.act_precision}"
        )
