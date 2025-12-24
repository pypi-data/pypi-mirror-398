from ttex.log.formatter import StrHeader, StrRecord
import os.path as osp
from ttex.log.coco import COCOState
from uuid import uuid4


class COCOInfoHeader(StrHeader):
    template = "suite = '{suite}', funcId = {funcId}, DIM = {dim}, Precision = {prec:.3e}, algId = '{algId}', coco_version = '{coco_version}', logger = '{logger}', data_format = '{data_format}'\n% {alg_info}"

    def __init__(self, state: COCOState):
        """
        Initialize a COCOInfoHeader with the given COCOState and COCOStart.

        Args:
            state (COCOState): The current state of the COCO logging.
            coco_log (COCOStart): The COCO start log containing problem and algorithm details.
        """
        assert (
            state.coco_start is not None
        ), "COCOStart event must be processed before header"
        self.funcId = state.coco_start.problem
        self.algId = state.coco_start.algo
        self.alg_info = (
            state.coco_start.algo_info if state.coco_start.algo_info else self.algId
        )
        self.dim = state.coco_start.dim
        self.suite = state.coco_start.suite
        self.inst = state.coco_start.inst
        self.exp_id = state.coco_start.exp_id
        self.prec = 1e-8  # TODO: At some point make this configurable
        self.coco_version = ""
        self.logger = "bbob"
        self.data_format = "bbob-new2"
        self._filepath = osp.join(
            f"{self.exp_id}",
            f"{self.suite}",
            f"{self.algId}",
            f"f{self.funcId}_i{self.inst}.info",
        )
        self._uuid = str(uuid4())  # always emit header

    @property
    def filepath(self) -> str:
        """
        Get the file path for the COCOInfoHeader.

        Returns:
            str: File path for the COCOInfoHeader.
        """
        return self._filepath

    @property
    def uuid(self) -> str:
        """
        Get the UUID for the COCOInfoHeader.

        Returns:
            str: UUID for the COCOInfoHeader.
        """
        return self._uuid

    def __str__(self) -> str:
        """
        Format the COCOInfoHeader as a string.

        Returns:
            str: Formatted COCOInfoHeader string.
        """
        return COCOInfoHeader.template.format(
            suite=self.suite,
            funcId=self.funcId,
            dim=self.dim,
            prec=self.prec,
            algId=self.algId,
            coco_version=self.coco_version,
            logger=self.logger,
            data_format=self.data_format,
            alg_info=self.alg_info,
        )


class COCOInfoRecord(StrRecord):
    template = "{file_path}, {inst}:{f_evals}|{best_target:.1e}"

    def __init__(self, state: COCOState):
        """
        Initialize a COCOInfoRecord with the given COCOState.

        Args:
            state (COCOState): The current state of the COCO logging.
        """
        self.file_path = state.dat_filepath
        self.inst = state.inst
        self.f_evals = state.f_evals
        self.best_target = state.best_target

    def emit(self) -> bool:  # type: ignore[override]
        # Only emit if there has been at least one function evaluation
        if self.f_evals > 0:
            return True
        else:
            return False

    def __str__(self) -> str:
        """
        Format the COCOInfoRecord as a string.
        Returns:
            str: Formatted COCOInfoRecord string.
        """
        return COCOInfoRecord.template.format(
            file_path=self.file_path,
            inst=self.inst,
            f_evals=self.f_evals,
            best_target=(
                self.best_target if self.best_target is not None else float("nan")
            ),
        )
