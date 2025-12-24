import os.path as osp
from ttex.log.formatter import StrHeader, StrRecord
from ttex.log.coco import COCOState
import math
from uuid import uuid4


class COCOLogRecord(StrRecord):
    template = (
        "{f_evals} {g_evals} {best_diff_opt:+.9e} {mf:+.9e} {best_mf:+.9e} {x_str}"
    )

    def __init__(self, state: COCOState):
        assert hasattr(
            state, "last_eval"
        ), "COCOLogRecord requires at least one COCOEval event"
        assert state.last_eval is not None
        self.x = state.last_eval.x
        self.dim = len(self.x)
        self.mf = state.last_eval.mf
        self.f_evals = state.f_evals
        self.g_evals = state.g_evals
        self.best_diff_opt = state.best_diff_opt
        self.best_mf = state.best_mf
        self.last_imp = state.last_imp

    @staticmethod
    def get_exp_bin(n_bins: int, val: float) -> float:
        """
        Get the exponential bin for a given value.
        There are n_bins between each power of 10.
        Args:
            n_bins (int): Number of bins between each power of 10.
            val (float): The value to bin.
        Returns:
            float: The binned value.
        """
        if val <= 0:
            raise ValueError("Value must be positive")
        if n_bins <= 0:
            raise ValueError("Number of bins must be positive")
        exponent = math.ceil(n_bins * math.log10(val))
        value = 10 ** (exponent / n_bins)
        return value

    def __str__(self):
        """
        Format the COCO step as a string.
        Returns:
            str: Formatted COCO step string.
        """
        x_str = " ".join(f"{val:+.4e}" for val in self.x)
        return COCOLogRecord.template.format(
            f_evals=self.f_evals,
            g_evals=self.g_evals,
            best_diff_opt=self.best_diff_opt,
            mf=self.mf,
            best_mf=self.best_mf,
            x_str=x_str,
        )


class COCOLogHeader(StrHeader):
    template = "% f evaluations | g evaluations | best noise-free fitness - Fopt ({fopt:.12e}) + sum g_i+ | measured fitness | best measured fitness or single-digit g-values | x1 | x2..."

    def __init__(self, state: COCOState, file_type: str):
        """
        Initialize a COCO header with the optimal function value.

        Args:
            state (COCOState): The current state of the COCO logging.
        """
        self.fopt = state.fopt
        assert (
            state.coco_start is not None
        ), "COCOStart event must be processed before header"
        self._filepath = osp.join(
            state.coco_start.exp_id,
            state.coco_start.suite,
            state.coco_start.algo,
            f"data_{state.coco_start.problem}",
            f"f{state.coco_start.problem}_d{state.coco_start.dim}_i{state.coco_start.inst}.{file_type}",
        )
        self._uuid = str(uuid4())  # always emit header

    def __str__(self):
        """
        Format the COCO header with the optimal function value.

        Returns:
            str: Formatted header string.
        """
        return COCOLogHeader.template.format(
            fopt=self.fopt if self.fopt is not None else float("nan")
        )

    @property
    def filepath(self):
        """
        Get the file path for the COCO header.

        Returns:
            str: File path for the COCO header.
        """
        return self._filepath

    @property
    def uuid(self):
        """
        Get the UUID for the COCO header.

        Returns:
            str: UUID for the COCO header.
        """
        return self._uuid
