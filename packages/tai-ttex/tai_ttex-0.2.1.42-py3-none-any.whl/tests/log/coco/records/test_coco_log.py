from ttex.log.coco.record import COCOLogHeader, COCOLogRecord
from ..test_coco_events import get_coco_start_params, eval_params
from ttex.log.coco import COCOState, COCOStart, COCOEval
import math
import pytest
import os.path as osp


@pytest.mark.parametrize(
    "coco_start_params",
    [get_coco_start_params(fopt=True), get_coco_start_params(fopt=False)],
)
def test_coco_log(coco_start_params):
    state = COCOState()
    new_start_params = coco_start_params.copy()
    new_start_params["dim"] = 3  # for testing
    start_event = COCOStart(**new_start_params)
    state.update(start_event)

    header = COCOLogHeader(state, file_type="dummy")
    expected_filepath = osp.join(
        f"{start_event.exp_id}",
        f"{start_event.suite}",
        f"{start_event.algo}",
        f"data_{start_event.problem}",
        f"f{start_event.problem}_d{start_event.dim}_i{start_event.inst}.dummy",
    )

    assert header.filepath == expected_filepath

    if coco_start_params["fopt"] is None:
        expected_header = "% f evaluations | g evaluations | best noise-free fitness - Fopt (nan) + sum g_i+ | measured fitness | best measured fitness or single-digit g-values | x1 | x2..."
    else:
        expected_header = "% f evaluations | g evaluations | best noise-free fitness - Fopt (-1.000000000000e-01) + sum g_i+ | measured fitness | best measured fitness or single-digit g-values | x1 | x2..."
    assert str(header) == expected_header

    eval_event = COCOEval(**eval_params)
    state.update(eval_event)

    record = COCOLogRecord(state)
    if coco_start_params["fopt"] is None:
        expected_output = "1 0 +5.000000000e-01 +5.000000000e-01 +5.000000000e-01 +1.0000e+00 +2.0000e+00 +3.0000e+00"
    else:
        expected_output = "1 0 +6.000000000e-01 +5.000000000e-01 +5.000000000e-01 +1.0000e+00 +2.0000e+00 +3.0000e+00"
    assert str(record) == expected_output


def test_get_exp_bin():
    n_bins = 10
    # 10 bins between 1 and 10 means each bin is a factor of 10^(1/10) ~ 1.2589
    # Test a few values to ensure they fall into the correct bins
    for exp in range(3, 50):
        value = 10 ** (exp / n_bins)
        assert math.isclose(
            COCOLogRecord.get_exp_bin(n_bins, value), value
        ), f"Failed at value: {value}"

        next_value = 10 ** ((exp + 1) / n_bins)
        mid_value = (value + next_value) / 2
        assert math.isclose(
            COCOLogRecord.get_exp_bin(n_bins, mid_value), next_value
        ), f"Failed at mid value: {mid_value}"
