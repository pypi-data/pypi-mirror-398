import logging
import ast
from wandb.sdk.wandb_run import Run, AlertLevel
import wandb
from typing import Optional, Dict, List
from ttex.log import LOGGER_NAME
import os.path as osp
from dataclasses import dataclass

logger = logging.getLogger(LOGGER_NAME)


class WandbHandler(logging.Handler):
    """
    Custom logging handler to log to wandb
    """

    def __init__(
        self,
        custom_metrics: Optional[Dict] = None,
        snapshot: bool = True,
        snapshot_sensitive_keys: Optional[List[str]] = None,
        project: Optional[str] = None,
        group: Optional[str] = None,
        level=logging.NOTSET,
    ):
        """
        Args:
            wandb_run (Run): Wandb run object
            custom_metrics (Optional[Dict], optional): Custom metrics to define. Defaults to None.
            level ([type], optional): Logging level. Defaults to logging.NOTSET.
        """
        super().__init__(level)
        self.snapshot = snapshot
        self.snapshot_sensitive_keys = snapshot_sensitive_keys
        self._run: Optional[Run] = None
        self.custom_metrics = custom_metrics if custom_metrics else {}
        self.project = project
        self.group = group

    @property
    def run(self):
        return self._run

    @run.setter
    def run(self, value: Run):
        self._run = value
        assert self._run is not None, "Wandb run cannot be None"
        # Define custom metrics if any
        for step_metric, metrics in self.custom_metrics.items():
            self._run.define_metric(step_metric)
            for metric in metrics:
                self._run.define_metric(metric, step_metric=step_metric)

    def emit(self, record):
        """
        Emit the record to wandb
        Args:
            record (LogRecord): Log record
        """
        if self._run is None:
            logger.handle(record)
            logger.warning("WandbHandler not initialized with wandb run")
            return
        msg = record.getMessage()
        step = record.step if hasattr(record, "step") else None
        commit = record.commit if hasattr(record, "commit") else None

        try:
            msg_dict = ast.literal_eval(msg)
            assert isinstance(msg_dict, dict), "Message is not a dict"
            self._run.log(msg_dict, step=step, commit=commit)
        except SyntaxError as e:
            logger.handle(record)
            logger.warning(f"Non-dict passed to WandbHandler {e} msg:{msg}")

    @staticmethod
    def wandb_init(
        run_config: Dict,
        project: Optional[str] = None,
        group: Optional[str] = None,
    ) -> Run:
        """
        Initialize wandb run
        Args:
            run_config (Dict): Run configuration
            project (Optional[str], optional): Wandb project. Defaults to None.
            group (Optional[str], optional): Wandb group. Defaults to None.
        Returns:
            wandb.sdk.wandb_run.Run: Wandb run
        """
        if not project:
            run = wandb.init(config=run_config, group=group)
        else:
            run = wandb.init(config=run_config, project=project, group=group)

        return run

    @staticmethod
    def create_wandb_artifact(
        run: Run,
        artifact_name: str,
        local_path: str,
        artifact_type: str = "evaluation",
        description: Optional[str] = "",
    ) -> Optional[wandb.Artifact]:
        artifact_name = f"{artifact_name}_{run.id}"
        artifact = wandb.Artifact(
            name=artifact_name, type=artifact_type, description=description
        )

        if osp.isfile(local_path):
            artifact.add_file(local_path=local_path, name=artifact_name)
        elif osp.isdir(local_path):
            artifact.add_dir(local_path=local_path, name=artifact_name)
        else:
            logger.warning(f"Path {local_path} does not exist. Cannot log artifact.")
            return None

        run.log_artifact(artifact)
        return artifact

    @staticmethod
    def log_snapshot(
        run: Run,
        extra_info: Optional[Dict] = None,
        extra_sensitive_keys: Optional[List[str]] = None,
    ) -> Optional[wandb.Artifact]:
        from ttex.log import capture_snapshot

        snapshot_path = f"snapshot_{run.id}.json"
        capture_snapshot(
            output_path=snapshot_path,
            extra_info=extra_info,
            extra_sensitive_keys=extra_sensitive_keys,
        )
        artifact = WandbHandler.create_wandb_artifact(
            run=run,
            artifact_name="system_snapshot",
            local_path=snapshot_path,
            artifact_type="dataset",
            description="System snapshot captured at the end of the run",
        )
        return artifact

    def close(self):
        if self._run is not None:
            if self.snapshot:
                self.log_snapshot(
                    run=self._run,
                    extra_sensitive_keys=self.snapshot_sensitive_keys,
                )
            self._run.alert(
                title=f"Run {self._run.id} finished",
                text=f"Run {self._run.id} has finished. Check the results at {self._run.url}",
                level=AlertLevel.INFO,
            )
            self._run.finish()
            self._run = None  # Reset to avoid triggering again
        super().close()
