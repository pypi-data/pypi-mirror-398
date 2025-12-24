import logging
import os.path as osp

from ttex.log.handler import ManualRotatingFileHandler
from ttex.log.formatter import KeyFormatter
from ttex.log.filter import KeyFilter, EventKeysplitFilter

from typing import Optional, List


def setup_coco_logger(
    name: str = "coco_logger",
    base_evaluation_triggers: Optional[List[int]] = None,
    number_evaluation_triggers: int = 20,
    improvement_steps: float = 1e-5,
    number_target_triggers: int = 20,
    target_precision: float = 1e-8,
) -> logging.Logger:
    # TODO: make this into a default setup to make it easier
    logger = logging.getLogger(name)

    # Ensure we only set up the logger once
    if not getattr(logger, "_coco_setup", None):
        logger._coco_setup = True  # type: ignore[attr-defined]

        logger.propagate = False  # Prevent double logging
        logger.setLevel(logging.INFO)

        splitter_args = {
            "base_evaluation_triggers": base_evaluation_triggers,
            "number_evaluation_triggers": number_evaluation_triggers,
            "improvement_steps": improvement_steps,
            "number_target_triggers": number_target_triggers,
            "target_precision": target_precision,
        }
        coco_filter = EventKeysplitFilter(
            key_splitter_cls="ttex.log.coco.COCOKeySplitter",
            key_splitter_args=splitter_args,
        )
        logger.addFilter(coco_filter)

        # Create a ManualRotatingFileHandler instance for log and info
        for type_str in ["info", "log_dat", "log_tdat"]:
            # Make some dummy files that should be deleted after
            filepath = osp.join("test_dir", f"coco_{type_str}.txt")
            handler = ManualRotatingFileHandler(
                filepath=filepath, key=type_str, mode="a"
            )
            formatter = KeyFormatter(key=type_str)
            handler.setFormatter(formatter)
            filter = KeyFilter(key=type_str)
            handler.addFilter(filter)
            logger.addHandler(handler)
    return logger


def teardown_coco_logger(name: str = "coco_logger") -> None:
    logger = logging.getLogger(name)
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    for filter in logger.filters[:]:
        logger.removeFilter(filter)
    logger._coco_setup = False  # type: ignore[attr-defined] # Reset setup flag
