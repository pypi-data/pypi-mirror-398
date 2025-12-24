from ttex.log.coco import COCOKeySplitter, COCOState, COCOStart, COCOEval, COCOEnd
import pytest
from .test_coco_events import random_eval_params


def get_started_state(splitter: COCOKeySplitter, dim=10):
    state = COCOState()
    start_event = COCOStart(
        fopt=0.1,
        algo="test_algo",
        problem=1,
        dim=dim,
        inst=1,
        suite="test_suite",
        exp_id="test_exp_id",
    )
    state.update(start_event)  # Update state with start event
    result = splitter.process(state, start_event)
    return state, result


def test_process_coco_start():
    state, result = get_started_state(COCOKeySplitter())

    assert "info" in result
    assert "log_dat" in result
    assert "log_tdat" in result
    assert state.dat_filepath is not None


def test_process_coco_eval():
    splitter = COCOKeySplitter()
    state, _ = get_started_state(splitter)

    eval_params = random_eval_params(dim=10)
    eval_event = COCOEval(**eval_params)
    state.update(eval_event)
    result = splitter.process(state, eval_event)

    # First eval should always emit both records
    assert "log_dat" in result
    assert "log_tdat" in result
    assert state.f_evals == 1
    assert state.best_mf == eval_params["mf"]
    assert state.last_tdat_emit == state.f_evals


def test_process_coco_end_assert():
    splitter = COCOKeySplitter()
    state, _ = get_started_state(splitter)

    end_event = COCOEnd()
    state.update(end_event)
    with pytest.raises(AssertionError):
        splitter.process(state, end_event)


@pytest.mark.parametrize("add_last", [True, False])
def test_process_coco_end_default(add_last):
    splitter = COCOKeySplitter()
    state, _ = get_started_state(splitter)
    eval_params = random_eval_params(dim=10)
    eval_event = COCOEval(**eval_params)
    state.update(eval_event)  # Add an eval to avoid assert
    splitter.process(state, eval_event)
    log_tdat_emitted = True
    if add_last:
        # Keep adding evals until log_dat is not emitted
        while log_tdat_emitted:
            eval_event = COCOEval(**eval_params)
            state.update(
                eval_event
            )  # Add another eval so we have one that is not already emitted
            result = splitter.process(state, eval_event)
            log_tdat_emitted = "log_tdat" in result
    end_event = COCOEnd()
    state.update(end_event)
    result = splitter.process(state, end_event)
    assert "info" in result
    assert (
        state._needs_start is True
    )  # After COCOEnd, state should require a new start event
    assert ("log_tdat" in result) == add_last


def test_val_passthrough():
    splitter = COCOKeySplitter(
        number_evaluation_triggers=0,
        number_target_triggers=0,
        improvement_steps=0,
        base_evaluation_triggers=[],
    )
    state, _ = get_started_state(splitter)

    eval_params = random_eval_params(dim=10)
    eval_event = COCOEval(**eval_params)
    state.update(eval_event)
    result = splitter.process(state, eval_event)
    # First eval should always emit both records
    assert "log_dat" in result
    assert "log_tdat" in result
    for _ in range(10):
        eval_event = COCOEval(**eval_params)
        state.update(eval_event)
        result = splitter.process(state, eval_event)
        assert "log_dat" not in result
        assert "log_tdat" not in result


def test_changing_dim():
    splitter = COCOKeySplitter()
    state, _ = get_started_state(splitter, dim=0)

    eval_params = random_eval_params(dim=10)
    eval_event = COCOEval(**eval_params)
    state.update(eval_event)
    result = splitter.process(state, eval_event)
    assert "log_tdat" in result
    assert result["log_tdat"].dim == 10

    eval_params = random_eval_params(dim=20)
    eval_event = COCOEval(**eval_params)
    state.update(eval_event)
    result = splitter.process(state, eval_event)
    assert "log_tdat" in result
    assert result["log_tdat"].dim == 20
