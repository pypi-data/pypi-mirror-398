from ttex.log.coco import COCOEnd, COCOEval, COCOStart, COCOState
from ttex.log.filter import KeySplitter, LogEvent
from ttex.log.filter.event_keysplit_filter import LoggingState
from ttex.log.formatter import StrRecord
from ttex.log.coco.record import (
    COCOInfoHeader,
    COCOInfoRecord,
    COCOtdatHeader,
    COCOtdatRecord,
    COCOdatHeader,
    COCOdatRecord,
)
from typing import List, Dict, Optional


class COCOKeySplitter(KeySplitter):
    def __init__(
        self,
        base_evaluation_triggers: Optional[List[int]] = None,
        number_evaluation_triggers: int = 20,
        improvement_steps: float = 1e-5,
        number_target_triggers: int = 20,
        target_precision: float = 1e-8,
    ):
        self.base_evaluation_triggers = base_evaluation_triggers
        self.number_evaluation_triggers = number_evaluation_triggers
        self.improvement_steps = improvement_steps
        self.number_target_triggers = number_target_triggers
        self.target_precision = target_precision

    def process(self, state: LoggingState, event: LogEvent) -> Dict[str, StrRecord]:
        assert isinstance(state, COCOState)
        return_dict: Dict[str, StrRecord] = {}

        if isinstance(event, COCOStart):
            info_header = COCOInfoHeader(state)
            log_tdat_header = COCOtdatHeader(state)
            log_dat_header = COCOdatHeader(state)
            state.set_dat_filepath(log_tdat_header.filepath, info_header.filepath)
            if info_header.emit():
                return_dict["info"] = info_header
            if log_tdat_header.emit():
                return_dict["log_tdat"] = log_tdat_header
            if log_dat_header.emit():
                return_dict["log_dat"] = log_dat_header
        elif isinstance(event, COCOEval):
            log_tdat_record = COCOtdatRecord(state)
            log_dat_record = COCOdatRecord(state)
            if log_tdat_record.emit(
                base_evaluation_triggers=self.base_evaluation_triggers,
                number_evaluation_triggers=self.number_evaluation_triggers,
                last_tdat_emit=None,
            ):
                # explicitly not the last eval
                return_dict["log_tdat"] = log_tdat_record
                state.last_tdat_emit = state.f_evals
            if log_dat_record.emit(
                improvement_step=self.improvement_steps,
                number_target_triggers=self.number_target_triggers,
                target_precision=self.target_precision,
            ):
                return_dict["log_dat"] = log_dat_record
                # Update best target reached for COCOInfoRecord
                assert hasattr(
                    log_dat_record, "best_target"
                ), "log_dat_record must have best_target attribute"
                assert log_dat_record.best_target is not None, "best_target must be set"
                state.best_target = log_dat_record.best_target
        elif isinstance(event, COCOEnd):
            # Emit last evaluation if not already done
            log_tdat_record = COCOtdatRecord(state)
            if log_tdat_record.emit(
                base_evaluation_triggers=self.base_evaluation_triggers,
                number_evaluation_triggers=self.number_evaluation_triggers,
                last_tdat_emit=state.last_tdat_emit,
            ):
                return_dict["log_tdat"] = log_tdat_record
            info_record = COCOInfoRecord(state)
            if info_record.emit():
                return_dict["info"] = info_record
        return return_dict

    def init_logging_state(self) -> COCOState:
        return COCOState()
