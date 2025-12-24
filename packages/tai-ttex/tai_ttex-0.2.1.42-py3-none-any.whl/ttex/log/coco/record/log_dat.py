from ttex.log.coco.record import COCOLogRecord, COCOLogHeader
from ttex.log.coco import COCOState
import math
from typing import Optional


class COCOdatRecord(COCOLogRecord):
    def __init__(self, state: COCOState):
        """
        Initialize a COCO dat record with the current state.

        Args:
            state (COCOState): The current state of the COCO logging.
        """
        super().__init__(state)
        self.reason: Optional[str] = None
        self.best_target: Optional[
            float
        ] = None  # Best target reached (from .dat logging)

    @staticmethod
    def ceil_to_target(value: float, improvement_step: float = 1e-5) -> float:
        return math.ceil(value / improvement_step) * improvement_step

    def improvement_trigger(self, improvement_step: float) -> bool:
        """
        Check if a new target has been reached based on the last improvement.
        Args:
            improvement_step (float): The step size for improvement targets.
        Returns:
            bool: True if a new target has been reached, False otherwise.
        """
        assert (
            self.last_imp is not None and self.last_imp > 0
        ), "last_imp must be positive to check for improvement"
        new_target_reached = COCOdatRecord.ceil_to_target(self.mf, improvement_step)
        prev_target_reached = COCOdatRecord.ceil_to_target(
            self.mf + self.last_imp, improvement_step
        )
        if new_target_reached < prev_target_reached:
            # New target reached.
            self.best_target = new_target_reached
            return True
        else:
            return False

    def log_target_trigger(
        self, number_target_triggers: int, target_precision: float = 1e-8
    ) -> bool:
        assert (
            self.best_diff_opt is not None
        ), "best_diff_opt must be set to check for log targets"
        if self.best_diff_opt < target_precision:
            # No best distance to optimum recorded or already within precision of optimum
            return False
        else:  # Check if a new target has been reached based on the last improvement.
            assert (
                self.last_imp is not None and self.last_imp > 0
            ), "last_imp must be positive to check for target triggers"

            new_value = COCOLogRecord.get_exp_bin(
                number_target_triggers, self.best_diff_opt
            )
            prev_value = COCOLogRecord.get_exp_bin(
                number_target_triggers, self.best_diff_opt + self.last_imp
            )
            if new_value < prev_value:
                self.best_target = new_value
                return True
            else:
                return False

    def emit(
        self,
        improvement_step: float = 1e-5,
        number_target_triggers: int = 20,
        target_precision: float = 1e-8,
    ) -> bool:  # type: ignore[override]
        """
        Determine if the current record should be emitted based on target triggers.
        If possible, uses log target triggers, otherwise uses linear targets based on improvement
        Args:
            improvement_step (float): Step size for improvement targets.
            number_target_triggers (int): Number of target triggers between each power of 10.
            target_precision (float): Precision threshold for considering proximity to the optimum.
        Returns:
            bool: True if the record should be emitted, False otherwise.
        """
        if self.f_evals <= 0:
            return False
        elif self.f_evals == 1:
            # Always log the first evaluation
            self.reason = "first"
            self.best_target = (
                self.mf
            )  # This is not super meaningful, but we need to set it to something just for info logging
            return True
        elif self.last_imp is None or self.last_imp <= 0:
            self.reason = "noimp"
            # No improvement in the last evaluation, therefore has not hit any new targets
            return False
        elif (
            number_target_triggers > 0 and target_precision > 0
        ):  # Prefer log target triggers if possible
            self.reason = "target"
            return self.log_target_trigger(number_target_triggers, target_precision)
        elif improvement_step > 0:
            self.reason = "imp"
            return self.improvement_trigger(improvement_step)
        # No valid triggers set, so never emit
        self.reason = "notrg"
        return False


class COCOdatHeader(COCOLogHeader):
    def __init__(self, state: COCOState):
        """
        Initialize a COCO dat header with the optimal function value.

        Args:
            state (COCOState): The current state of the COCO logging.
        """
        super().__init__(state, file_type="dat")
