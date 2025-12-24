from ttex.log.coco.record import COCOLogRecord, COCOLogHeader
from ttex.log.coco import COCOState
from typing import Optional, List
import math


class COCOtdatRecord(COCOLogRecord):
    @staticmethod
    def trigger_nth(number_evaluation_triggers: int, f_evals: int) -> bool:
        """
        Determine if the current function evaluation count `f_evals` meets the
        trigger condition based on `number_evaluation_triggers`.

        - every 10**(exponent1/number_of_triggers) for exponent1 >= 0
        See: https://github.com/numbbo/coco/blob/master/code-experiments/src/coco_observer.c
        Args:
            number_evaluation_triggers (int): Number of evaluation triggers.
            f_evals (int): Current function evaluation count.

        Returns:
            bool: True if the trigger condition is met, False otherwise.
        """
        if number_evaluation_triggers <= 0:
            return False
        value = COCOLogRecord.get_exp_bin(number_evaluation_triggers, f_evals)
        return f_evals == math.floor(value)

    @staticmethod
    def base_eval(
        base_evaluation_triggers: List[int], dimension: int, f_evals: int
    ) -> bool:
        """
        Determine if the current function evaluation count `f_evals` meets the
        base evaluation trigger condition.

        - every base_evaluation * dimension * (10**exponent2) for exponent2 >= 0
        See: https://github.com/numbbo/coco/blob/master/code-experiments/src/coco_observer.c
        Args:
            base_evaluation_triggers (List[int]): List of base evaluation triggers.
            dimension (int): Problem dimension.
            f_evals (int): Current function evaluation count.
        Returns:
            bool: True if the trigger condition is met, False otherwise.
        """
        if dimension <= 0:
            return False
        for base in base_evaluation_triggers:
            assert base > 0, "base evaluation triggers must be positive"
            scaled_eval = f_evals / (dimension * base)
            if scaled_eval < 1:  # if f_evals is less than dimension * base, skip
                continue
            # check if scaled_eval is a power of 10
            if math.log10(scaled_eval).is_integer():
                return True
        return False

    def emit(  # type: ignore[override]
        self,
        base_evaluation_triggers: Optional[List[int]] = None,
        number_evaluation_triggers: int = 20,
        last_tdat_emit: Optional[int] = None,  # only pass when emitting the last record
    ) -> bool:  # type: ignore[override]
        """
        Check if the record should be emitted based on the trigger_nth condition.
        """
        if self.f_evals <= 0:
            return False
        if base_evaluation_triggers is None:
            base_evaluation_triggers = [1, 2, 5]
        if last_tdat_emit is not None:
            # This is the last evaluation before the end of the run
            if self.f_evals > last_tdat_emit:
                # The last evaluation has not already been emitted
                return True
            else:  # evaluation already emitted
                return False
        if self.f_evals == 1:
            # Always emit the first evaluation (unless it is also the last)
            return True
        trigger_nth = COCOtdatRecord.trigger_nth(
            number_evaluation_triggers, self.f_evals
        )
        trigger_base = COCOtdatRecord.base_eval(
            base_evaluation_triggers, self.dim, self.f_evals
        )
        return trigger_nth or trigger_base


class COCOtdatHeader(COCOLogHeader):
    def __init__(self, state: COCOState):
        """
        Initialize a COCO dat header with the optimal function value.

        Args:
            state (COCOState): The current state of the COCO logging.
        """
        super().__init__(state, file_type="tdat")
