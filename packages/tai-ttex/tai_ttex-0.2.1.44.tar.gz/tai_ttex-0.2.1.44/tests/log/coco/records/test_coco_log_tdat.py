from ttex.log.coco.record import COCOtdatRecord, COCOtdatHeader
from ..test_coco_events import get_coco_start_params, random_eval_params
from ttex.log.coco import COCOState, COCOStart, COCOEval
import pytest
import math
import os.path as osp


def correct_n_triggers(number_of_triggers=20):
    exponent = 0
    val = 1
    trigger_vals = []

    for feval in range(1, 1000):
        if feval >= val:
            while math.floor(10 ** (exponent / number_of_triggers)) <= val:
                exponent += 1
            val = math.floor(10 ** (exponent / number_of_triggers))
            trigger_vals.append(val)
    return trigger_vals


def test_trigger_nth():
    assert not COCOtdatRecord.trigger_nth(10, 9)  # smaller than 9
    correct_triggers = correct_n_triggers(number_of_triggers=20)
    for tval in correct_triggers:
        assert COCOtdatRecord.trigger_nth(20, tval)

    non_triggers = [i for i in range(2, 1000) if i not in correct_triggers]
    for ntval in non_triggers:
        assert not COCOtdatRecord.trigger_nth(20, ntval)


def correct_base_triggers(base_evaluation_triggers=[1, 2, 5], dim=3):
    trigger_vals = []
    for exp in range(0, 6):
        for base in base_evaluation_triggers:
            val = base * dim * (10**exp)
            trigger_vals.append(val)
    trigger_vals = list(sorted(set(trigger_vals)))

    return trigger_vals


def test_base_eval():
    correct_triggers = correct_base_triggers(base_evaluation_triggers=[1, 2, 5], dim=3)
    assert 3 in correct_triggers  # 1*dim=3*10^0
    assert 6000 in correct_triggers  # 2 * 10^3 * dim=3  for tval in correct_triggers:
    for tval in correct_triggers:
        assert COCOtdatRecord.base_eval([1, 2, 5], 3, tval)
    non_triggers = [i for i in range(2, 20) if i not in correct_triggers]
    for ntval in non_triggers:
        assert not COCOtdatRecord.base_eval([1, 2, 5], 3, ntval)


@pytest.mark.parametrize(
    "coco_start_params",
    [get_coco_start_params(fopt=True), get_coco_start_params(fopt=False)],
)
def test_coco_tdat(coco_start_params):
    state = COCOState()
    start_event = COCOStart(**coco_start_params)
    state.update(start_event)

    header = COCOtdatHeader(state)
    expected_file_path = osp.join(
        f"{start_event.exp_id}",
        f"{start_event.suite}",
        f"{start_event.algo}",
        f"data_{start_event.problem}",
        f"f{start_event.problem}_d{start_event.dim}_i{start_event.inst}.tdat",
    )
    assert header.filepath == expected_file_path

    ## dummy initialise
    eval_event = COCOEval(**random_eval_params(dim=coco_start_params["dim"]))
    state.update(eval_event)
    record = COCOtdatRecord(state)

    # get all triggers
    correct_base_trigg = correct_base_triggers(
        base_evaluation_triggers=[1, 2, 5], dim=coco_start_params["dim"]
    )
    correct_n_trigg = correct_n_triggers(number_of_triggers=20)
    correct_triggers = sorted(list(set(correct_base_trigg + correct_n_trigg)))

    record.f_evals = 0
    assert not record.emit()

    record.f_evals = 1
    assert record.emit()  # first eval always

    for tval in correct_triggers:
        record.f_evals = tval
        assert record.emit(), f"Should trigger at {tval}"

    non_triggers = [i for i in range(2, 1000) if i not in correct_triggers]
    for ntval in non_triggers:
        record.f_evals = ntval
        assert not record.emit(), f"Should not trigger at {ntval}"

    # Test last emit
    record.f_evals = non_triggers[0]
    assert not record.emit()
    assert record.emit(last_tdat_emit=record.f_evals - 1)


@pytest.mark.parametrize(
    "coco_start_params",
    [get_coco_start_params(fopt=True), get_coco_start_params(fopt=False)],
)
def test_coco_dat_no_double_emit_last(coco_start_params):
    state = COCOState()
    start_event = COCOStart(**coco_start_params)
    state.update(start_event)

    eval_event = COCOEval(**random_eval_params(dim=coco_start_params["dim"]))
    state.update(eval_event)
    record = COCOtdatRecord(state)

    record.f_evals = 1
    assert record.emit()  # first eval always
    assert not record.emit(last_tdat_emit=record.f_evals)  # should not double emit
