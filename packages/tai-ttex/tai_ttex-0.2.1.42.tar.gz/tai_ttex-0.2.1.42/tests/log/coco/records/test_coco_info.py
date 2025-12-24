from ttex.log.coco.record import COCOInfoHeader, COCOInfoRecord
from ..test_coco_events import get_coco_start_params, end_params, random_eval_params
from ttex.log.coco import COCOState, COCOStart, COCOEval, COCOEnd
import os.path as osp
import pytest


@pytest.mark.parametrize(
    "coco_start_params",
    [get_coco_start_params(fopt=True), get_coco_start_params(fopt=False)],
)
def test_coco_info(coco_start_params):
    state = COCOState()
    start_event = COCOStart(**coco_start_params)
    state.update(start_event)  # Update state with start event

    header = COCOInfoHeader(state)
    ## filepath
    expected_filepath = osp.join(
        f"{start_event.exp_id}",
        f"{start_event.suite}",
        f"{start_event.algo}",
        f"f{start_event.problem}_i{start_event.inst}.info",
    )
    assert header.filepath == expected_filepath
    dummy_dat_filepath = osp.join(
        f"{start_event.exp_id}",
        f"{start_event.suite}",
        f"{start_event.algo}",
        f"data_f{start_event.problem}",
        "dummy.dat",
    )
    state.set_dat_filepath(dummy_dat_filepath, header.filepath)

    ## uuid
    assert header.uuid is not None and len(header.uuid) > 0

    expected_header = (
        f"suite = '{state.coco_start.suite}', funcId = {state.coco_start.problem}, DIM = {state.coco_start.dim}, Precision = 1.000e-08, "
        f"algId = '{state.coco_start.algo}', coco_version = '{header.coco_version}', logger = '{header.logger}', "
        f"data_format = '{header.data_format}'\n% {state.coco_start.algo}"
    )
    assert str(header) == expected_header

    evals = 3
    for _ in range(evals):
        eval_event = COCOEval(**random_eval_params(dim=coco_start_params["dim"]))
        state.update(eval_event)  # Update state with eval event

    end_event = COCOEnd(**end_params)
    state.update(end_event)  # Update state with end event
    state.best_target = 0.9  # dummy best target for testing
    record = COCOInfoRecord(state)
    expected_output = (
        f"data_f1/dummy.dat, {start_event.inst}:{evals}|{state.best_target:.1e}"
    )
    assert str(record) == expected_output


@pytest.mark.parametrize(
    "coco_start_params",
    [get_coco_start_params(fopt=True), get_coco_start_params(fopt=False)],
)
def test_with_alg_info(coco_start_params):
    state = COCOState()
    start_params = coco_start_params.copy()
    start_params["algo_info"] = "test info"
    start_event = COCOStart(**start_params)
    state.update(start_event)  # Update state with start event

    header = COCOInfoHeader(state)
    expected_header = (
        f"suite = '{state.coco_start.suite}', funcId = {state.coco_start.problem}, DIM = {state.coco_start.dim}, Precision = 1.000e-08, "
        f"algId = '{state.coco_start.algo}', coco_version = '{header.coco_version}', logger = '{header.logger}', "
        f"data_format = '{header.data_format}'\n% {state.coco_start.algo_info}"
    )
    assert str(header) == expected_header
