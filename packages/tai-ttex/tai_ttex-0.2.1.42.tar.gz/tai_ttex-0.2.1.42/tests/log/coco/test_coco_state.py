from ttex.log.coco import COCOState, COCOStart, COCOEval, COCOEnd
from .test_coco_events import get_coco_start_params, end_params, random_eval_params
import pytest
import os.path as osp
import math


def test_coco_state_end():
    state = COCOState()
    assert state._needs_start is True, "State should require a start event"
    with pytest.raises(ValueError):
        state.update(
            "invalid_event"
        )  # Should raise an error for invalid event best_dist_prev

    state._needs_start = False  # Simulate that a start event has been process
    end_event = COCOEnd(**end_params)
    state.update(end_event)
    assert (
        state._needs_start is True
    ), "State should require a start event after COCOEnd"


@pytest.mark.parametrize(
    "coco_start_params",
    [get_coco_start_params(fopt=True), get_coco_start_params(fopt=False)],
)
def test_coco_state_start(coco_start_params):
    state = COCOState()
    start_event = COCOStart(**coco_start_params)
    state.update(start_event)

    assert state.f_evals == 0
    assert state.g_evals == 0
    assert state.best_mf == float("inf")
    assert state.fopt == coco_start_params["fopt"]
    assert state.inst == coco_start_params["inst"]
    assert state.coco_start == start_event
    assert state.best_diff_opt is None
    assert state.last_imp is None


@pytest.mark.parametrize(
    "coco_start_params",
    [get_coco_start_params(fopt=True), get_coco_start_params(fopt=False)],
)
def test_ordered_error(coco_start_params):
    state = COCOState()
    eval_params = random_eval_params(dim=coco_start_params["dim"])
    eval_event = COCOEval(**eval_params)

    # Update state with eval event
    with pytest.raises(
        AssertionError
    ):  # Expect an error since COCOStart must be processed first
        state.update(eval_event)


@pytest.mark.parametrize(
    "coco_start_params",
    [get_coco_start_params(fopt=True), get_coco_start_params(fopt=False)],
)
def test_coco_state_eval(coco_start_params):
    state = COCOState()
    start_event = COCOStart(**coco_start_params)
    state.update(start_event)
    eval_params = random_eval_params(dim=coco_start_params["dim"])
    eval_event = COCOEval(**eval_params)
    state.update(eval_event)
    assert state.f_evals == 1
    assert state.g_evals == 0
    assert state.best_mf == eval_params["mf"]
    if state.fopt is not None:
        assert state.best_diff_opt == eval_params["mf"] - state.fopt
    else:
        assert state.best_diff_opt == state.best_mf
    assert state.last_imp is not None
    assert state.last_eval == eval_event

    eval2_params = eval_params.copy()
    eval2_params["mf"] = eval_params["mf"] + 0.1  # Simulate a worse evaluation
    eval_event2 = COCOEval(**eval2_params)
    state.update(eval_event2)  # Process the same eval again
    assert state.f_evals == 2
    assert state.g_evals == 0
    assert state.best_mf == eval_params["mf"]
    assert state.last_eval.mf == eval2_params["mf"]
    if state.fopt is not None:
        assert state.best_diff_opt == eval_params["mf"] - state.fopt
    else:
        assert state.best_diff_opt == state.best_mf
    assert state.last_imp == 0  # No improvement, evaluation is worse

    imp = 0.2
    eval3_params = eval_params.copy()
    eval3_params["mf"] = eval_params["mf"] - imp  # Simulate a better evaluation
    eval_event3 = COCOEval(**eval3_params)
    state.update(eval_event3)  # Process the same eval again
    assert state.f_evals == 3
    assert state.g_evals == 0
    assert state.best_mf == eval3_params["mf"]
    assert state.last_eval.mf == eval3_params["mf"]
    if state.fopt is not None:
        assert state.best_diff_opt == eval3_params["mf"] - state.fopt
    else:
        assert state.best_diff_opt == state.best_mf
    assert math.isclose(state.last_imp, imp)


def test_coco_state_set_dat_filepath():
    state = COCOState()

    dat_filepath = osp.join("root_dir", "dir", "test_dat.txt")
    info_filepath = osp.join("root_dir", "test_info.txt")
    state.set_dat_filepath(dat_filepath, info_filepath)

    expected_path = osp.join("dir", "test_dat.txt")
    assert state.dat_filepath == expected_path


def test_without_dim():
    state = COCOState()
    start_params = get_coco_start_params(fopt=False)
    del start_params["dim"]  # Remove dim to test without it
    start_event = COCOStart(**start_params)
    state.update(start_event)

    eval_params = random_eval_params(dim=3)
    eval_event = COCOEval(**eval_params)
    state.update(eval_event)

    assert state.f_evals == 1
    assert state.g_evals == 0
    assert state.best_mf == eval_params["mf"]
    assert state.last_imp is not None
    assert state.last_eval == eval_event
