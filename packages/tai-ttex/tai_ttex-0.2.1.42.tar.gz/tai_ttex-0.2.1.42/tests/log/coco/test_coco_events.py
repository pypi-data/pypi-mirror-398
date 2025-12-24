from ttex.log.coco import COCOEval, COCOEnd, COCOStart
from ttex.log.filter import LogEvent
import pytest
from dataclasses import FrozenInstanceError
import random


def get_coco_start_params(fopt: bool = True):
    return {
        "fopt": -0.1 if fopt else None,  # so it is less than mf in eval_params
        "algo": "test_algo",
        "problem": 1,
        "dim": 10,
        "inst": 1,
        "suite": "test_suite",
        "exp_id": "test_exp_id",
    }


def random_eval_params(dim):
    return {
        "x": [random.uniform(-5, 5) for _ in range(dim)],
        "mf": random.uniform(0, 10),
    }


eval_params = {
    "x": [1.0, 2.0, 3.0],
    "mf": 0.5,
}

end_params = {}


@pytest.mark.parametrize(
    "coco_start_params",
    [get_coco_start_params(fopt=True), get_coco_start_params(fopt=False)],
)
def test_coco_start(coco_start_params):
    event = COCOStart(**coco_start_params)
    assert isinstance(event, LogEvent)
    assert event.fopt == coco_start_params["fopt"]
    assert event.algo == coco_start_params["algo"]
    assert event.problem == coco_start_params["problem"]
    assert event.dim == coco_start_params["dim"]
    assert event.inst == coco_start_params["inst"]
    assert event.suite == coco_start_params["suite"]
    assert isinstance(event.exp_id, str)

    with pytest.raises(FrozenInstanceError):
        # Attempting to modify a frozen dataclass should raise an error
        event.exp_id = "custom_id"


@pytest.mark.parametrize(
    "coco_start_params",
    [get_coco_start_params(fopt=True), get_coco_start_params(fopt=False)],
)
def test_coco_start_custom_exp_id(coco_start_params):
    custom_exp_id = "custom_id"
    start_params = coco_start_params.copy()
    start_params["exp_id"] = custom_exp_id
    event = COCOStart(**start_params)
    assert event.exp_id == custom_exp_id


def test_coco_eval():
    event = COCOEval(**eval_params)
    assert isinstance(event, LogEvent)
    assert event.x == eval_params["x"]
    assert event.mf == eval_params["mf"]


def test_coco_end():
    event = COCOEnd(**end_params)
    assert isinstance(event, LogEvent)

    # COCOEnd has no attributes, so we just check that it can be instantiated
    assert event is not None
