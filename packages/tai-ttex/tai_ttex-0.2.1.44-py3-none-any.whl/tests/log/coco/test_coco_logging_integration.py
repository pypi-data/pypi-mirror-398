# integration test for coco logging
import os.path as osp
import cocopp
from ttex.log.coco import (
    COCOStart,
    COCOEval,
    COCOEnd,
)
import numpy as np
from cocopp.pproc import DictAlg
import shutil
import pytest
from typing import Optional
from ttex.log.utils.coco_logging_setup import teardown_coco_logger, setup_coco_logger


def get_dummy_start_params(
    problem: int = 3, dim: Optional[int] = 2, inst: Optional[int] = 2
) -> dict:
    return_dict = {
        "fopt": np.random.randn() * 100,
        "algo": "test_algo",
        "problem": problem,
        "dim": dim,
        "inst": inst,
        "suite": "bbob",
        "exp_id": "test_exp_id",
    }
    if dim is None:
        del return_dict["dim"]
    if inst is None:
        del return_dict["inst"]
    return return_dict


def generate_events(
    num_evals: int, problem: int, dim: Optional[int], inst: Optional[int]
):
    events = []
    start_record = COCOStart(**get_dummy_start_params(problem, dim, inst))
    events.append(start_record)
    for _ in range(num_evals):
        curr_dim = dim if dim is not None else np.random.randint(2, 6)
        x = np.random.rand(curr_dim)
        mf = np.random.rand() + start_record.fopt
        events.append(COCOEval(x=x.tolist(), mf=mf))
    events.append(COCOEnd())
    return events


@pytest.fixture(scope="function", autouse=True)
def cleanup_dummy_files():
    shutil.rmtree("test_exp_id", ignore_errors=True)
    shutil.rmtree("test_dir", ignore_errors=True)

    yield

    shutil.rmtree("test_dir", ignore_errors=True)
    shutil.rmtree("test_exp_id", ignore_errors=True)


def simulate_once(
    logger,
    num_evals: int,
    problem: int,
    dim: Optional[int] = None,
    inst: Optional[int] = None,
):
    events = generate_events(num_evals, problem, dim, inst)
    for event in events:
        logger.info(event)

    return events[0]  # return start record for further checks


def check_files_exist(start_record: COCOStart):
    for type_str in ["info", "log_dat", "log_tdat"]:
        # Check if the dummy files are deleted
        filepath = osp.join("test_dir", f"coco_{type_str}.txt")
        assert not osp.exists(filepath), f"{type_str} dummy log file retained"
    # Check if the log files are created
    log_file_base = osp.join(
        f"{start_record.exp_id}",
        f"{start_record.suite}",
        f"{start_record.algo}",
        f"data_{start_record.problem}",
        f"f{start_record.problem}_d{start_record.dim}_i{start_record.inst}",
    )
    assert osp.exists(f"{log_file_base}.dat"), "COCO dat log file not created"
    assert osp.exists(f"{log_file_base}.tdat"), "COCO tdat log file not created"
    # Check that tdat file has at least one record (more than just header)
    with open(
        f"{log_file_base}.tdat",
        "r",
    ) as f:
        lines = f.readlines()
        assert len(lines) > 1, "COCO tdat log file is empty"

    assert osp.exists(
        osp.join(
            f"{start_record.exp_id}",
            f"{start_record.suite}",
            f"{start_record.algo}",
            f"f{start_record.problem}_i{start_record.inst}.info",
        )
    ), "COCO info file not created"


def test_coco_logging_integration():
    logger = setup_coco_logger("coco_logger1")
    start_records = [None] * 4
    start_records[0] = simulate_once(logger, num_evals=50, problem=3, dim=2, inst=2)
    start_records[1] = simulate_once(logger, num_evals=30, problem=3, dim=2, inst=3)
    start_records[2] = simulate_once(logger, num_evals=30, problem=3, dim=3, inst=4)
    start_records[3] = simulate_once(logger, num_evals=30, problem=5, dim=2, inst=2)
    # Close handlers and remove from logger
    teardown_coco_logger("coco_logger1")  # Ensure handlers are closed
    # Check files exist for first start record
    for start_rec in start_records:
        assert isinstance(start_rec, COCOStart)
        check_files_exist(start_rec)
    ## check with cocopp
    res = cocopp.main(
        f"-o test_exp_id/ppdata test_exp_id/{start_records[0].suite}/test_algo"
    )
    assert isinstance(res, DictAlg)
    result_dict = res[("test_algo", "")][0]
    assert result_dict.funcId == 3
    assert result_dict.dim == 2
    assert result_dict.algId == "test_algo"
    assert len(result_dict.instancenumbers) == 2  # 2,3
    assert result_dict.instancenumbers[0] == 2


def test_coco_logging_integration_no_dim_inst():
    logger = setup_coco_logger("coco_logger2")
    start_record = simulate_once(logger, num_evals=20, problem=4)
    # Close handlers and remove from logger
    teardown_coco_logger("coco_logger2")  # Ensure handlers are closed
    # Check files exist for first start record
    assert isinstance(start_record, COCOStart)
    check_files_exist(start_record)
    # TODO: This won't work with cocopp as dim and inst are not set
