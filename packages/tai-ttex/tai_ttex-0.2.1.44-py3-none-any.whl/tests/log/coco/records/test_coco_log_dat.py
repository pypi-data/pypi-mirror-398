from ttex.log.coco.record import COCOdatRecord, COCOdatHeader
from ..test_coco_events import get_coco_start_params, random_eval_params
from ttex.log.coco import COCOState, COCOStart, COCOEval
import math
import pytest


def test_ceil_to_target():
    assert math.isclose(COCOdatRecord.ceil_to_target(0.123456, 1), 1.0)
    assert math.isclose(COCOdatRecord.ceil_to_target(0.123456, 0.1), 0.2)
    assert math.isclose(COCOdatRecord.ceil_to_target(0.123456, 0.01), 0.13)
    assert math.isclose(COCOdatRecord.ceil_to_target(0.123456, 0.001), 0.124)
    assert math.isclose(COCOdatRecord.ceil_to_target(0.123456, 0.0001), 0.1235)
    assert math.isclose(COCOdatRecord.ceil_to_target(0.123456, 0.00001), 0.12346)


@pytest.mark.parametrize(
    "coco_start_params",
    [get_coco_start_params(fopt=True), get_coco_start_params(fopt=False)],
)
def test_improvement_trigger(coco_start_params):
    state = COCOState()
    start_event = COCOStart(**coco_start_params)
    state.update(start_event)

    ## dummy initialise
    eval_event = COCOEval(**random_eval_params(dim=coco_start_params["dim"]))
    state.update(eval_event)

    record = COCOdatRecord(state)
    precision = 0.1
    record.mf = 0.25  # prev best mf = 0.3, so last target reached = 0.3
    record.last_imp = 0.05
    assert not record.improvement_trigger(
        precision
    )  # new target reached = 0.3, so no new target
    assert record.best_target is None

    record = COCOdatRecord(state)
    record.mf = 0.2  # prev best mf = 0.3, so last target reached = 0.3
    record.last_imp = 0.05
    assert record.improvement_trigger(
        precision
    )  # new target reached = 0.2, so new target
    assert record.best_target == 0.2

    record = COCOdatRecord(state)
    record.mf = 0.15  # prev best mf = 0.2 (mf+last_imp), so last target reached = 0.2
    record.last_imp = 0.05
    assert not record.improvement_trigger(
        precision
    )  # new target reached = 0.2, so no new target
    assert record.best_target is None


@pytest.mark.parametrize(
    "coco_start_params",
    [get_coco_start_params(fopt=True), get_coco_start_params(fopt=False)],
)
def test_log_target_trigger(coco_start_params):
    state = COCOState()
    start_event = COCOStart(**coco_start_params)
    state.update(start_event)

    ## dummy initialise
    eval_event = COCOEval(**random_eval_params(dim=coco_start_params["dim"]))
    state.update(eval_event)
    n_triggers = 10

    record = COCOdatRecord(state)
    record.best_diff_opt = 1.0
    record.last_imp = 0.2  # so prev best_dist_opt = 1.2, prev target = 1.2589
    assert record.log_target_trigger(n_triggers)
    assert record.best_target == 1.0

    record = COCOdatRecord(state)
    record.best_diff_opt = 9
    record.last_imp = 1  # so prev best_dist_opt = 10, prev target = 10
    assert not record.log_target_trigger(n_triggers)
    assert record.best_target is None

    record = COCOdatRecord(state)
    # Check we stop logging when within precision of optimum
    record.best_diff_opt = 1e-9
    record.last_imp = 1
    assert not record.log_target_trigger(n_triggers, target_precision=1e-8)
    assert record.best_target is None


@pytest.mark.parametrize(
    "coco_start_params",
    [get_coco_start_params(fopt=True), get_coco_start_params(fopt=False)],
)
def test_emit(coco_start_params):
    state = COCOState()
    start_event = COCOStart(**coco_start_params)
    state.update(start_event)

    ## dummy initialise
    eval_event = COCOEval(**random_eval_params(dim=coco_start_params["dim"]))
    state.update(eval_event)
    state.f_evals = 2  # to avoid first eval auto-emit

    record = COCOdatRecord(state)
    # No triggers set, should not emit
    assert not record.emit(improvement_step=0, number_target_triggers=0)
    assert record.reason == "notrg"

    # Improvement trigger only (no best_diff_opt)
    record = COCOdatRecord(state)
    precision = 0.1
    record.mf = 0.25  # prev best mf = 0.3, so last target reached = 0.3
    record.last_imp = 0.05
    assert not record.emit(
        improvement_step=precision, number_target_triggers=0
    )  # no new target
    assert record.reason == "imp"

    record = COCOdatRecord(state)
    record.mf = 0.2  # prev best mf = 0.3, so last target reached = 0.3
    record.last_imp = 0.05
    assert record.emit(
        improvement_step=precision, number_target_triggers=0
    )  # new target
    assert record.reason == "imp"

    # Target triggers only, they should take priority
    n_triggers = 10
    record = COCOdatRecord(state)
    record.best_diff_opt = 1.0
    record.last_imp = 0.2  # so prev best_dist_opt = 1.2, prev target = 1.2589
    assert record.emit(
        improvement_step=1e-12, number_target_triggers=n_triggers, target_precision=1e-8
    )
    assert record.reason == "target"
    record = COCOdatRecord(state)
    record.best_diff_opt = 9
    record.last_imp = 1  # so prev best_dist_opt = 10, prev target = 10
    # imp trigger would fire, but target trigger does not, so no emit
    assert not record.emit(
        improvement_step=1e-12, number_target_triggers=n_triggers, target_precision=1e-8
    )
    assert record.reason == "target"


@pytest.mark.parametrize(
    "coco_start_params, nt_triggers",
    [
        (get_coco_start_params(fopt=True), 0),
        (get_coco_start_params(fopt=False), 0),
        (get_coco_start_params(fopt=True), 10),
        (get_coco_start_params(fopt=False), 20),
    ],
)
def test_first_eval_emit(coco_start_params, nt_triggers):
    state = COCOState()
    start_event = COCOStart(**coco_start_params)
    state.update(start_event)

    ## dummy initialise
    eval_event = COCOEval(**random_eval_params(dim=coco_start_params["dim"]))
    state.update(eval_event)

    record = COCOdatRecord(state)
    assert record.last_imp is not None
    assert record.last_imp > 0  # last_imp set from eval
    record.f_evals = 1
    assert record.emit(number_target_triggers=nt_triggers)
    assert hasattr(record, "best_target")
