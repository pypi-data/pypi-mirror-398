import torch
import fmot
import numpy as np
import pytest


class MimoModel(torch.nn.Module):
    def forward(self, x, y):
        out1 = x * y
        out2 = x + y
        fmot.tag(out1, "out1")
        fmot.tag(out2, "out2")
        return out1, out2


@pytest.mark.parametrize("return_dict", [True, False])
def test_batch_run(return_dict):
    SIZE_X = 8
    SIZE_Y = 1
    BATCH = 64

    model = MimoModel()
    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize(
        [(torch.randn(BATCH, SIZE_X), torch.randn(BATCH, SIZE_Y)) for _ in range(4)]
    )

    graph = cmodel.trace()
    print(graph)

    x = np.random.randn(BATCH, SIZE_X)
    y = np.random.randn(BATCH, SIZE_Y)
    z, r_dicts = graph.run_batch(
        x, y, dequant=True, return_objs=True, return_dict=return_dict
    )

    error_count = 0

    for i in range(BATCH):
        step_z = graph.run(x[i], y[i], dequant=True)

        if return_dict is False:
            assert np.array_equal(z[0][i], step_z[0]) and np.array_equal(
                z[1][i], step_z[1]
            )
        elif return_dict is True:
            assert np.array_equal(z["out1"][i], step_z[0]) and np.array_equal(
                z["out2"][i], step_z[1]
            )
        else:
            assert False


class SingleOutputModel(torch.nn.Module):
    def forward(self, x, y):
        out1 = x * y
        fmot.tag(out1, "out1")
        return out1


@pytest.mark.parametrize("return_dict", [True, False])
def test_batch_run_single_output_model(return_dict):
    SIZE_X = 8
    SIZE_Y = 1
    BATCH = 64

    model = SingleOutputModel()
    cmodel = fmot.ConvertedModel(model)
    cmodel.quantize(
        [(torch.randn(BATCH, SIZE_X), torch.randn(BATCH, SIZE_Y)) for _ in range(4)]
    )

    graph = cmodel.trace()
    print(graph)

    x = np.random.randn(BATCH, SIZE_X)
    y = np.random.randn(BATCH, SIZE_Y)
    z, r_dicts = graph.run_batch(
        x, y, dequant=True, return_objs=True, return_dict=return_dict
    )

    error_count = 0

    for i in range(BATCH):
        step_z = graph.run(x[i], y[i], dequant=True)

        if return_dict is False:
            assert np.array_equal(z[i], step_z)
        elif return_dict is True:
            assert np.array_equal(z["out1"][i], step_z)
        else:
            assert False


if __name__ == "__main__":
    test_batch_run()
