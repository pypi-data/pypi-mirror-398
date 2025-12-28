"""Telemetry"""

from pathlib import Path
from typing import Dict, Optional, Union

import numpy as np
from aim import Distribution, Run

KVDict = Dict[str, Union[str, int, float, bool]]
Array = np.ndarray


class Telemetry:
    """Telemetry class for logging metrics and hyperparameters using Aim"""

    def __init__(self, repo: Path, experiment: str):
        self.run = Run(
            repo=str(repo.expanduser().absolute()),
            experiment=experiment,
            log_system_params=True,
            capture_terminal_logs=False,
        )

    def hparams(self, params: KVDict):
        """Log hyperparameters"""
        self.run["hparams"] = params

    def log(
        self,
        metrics: KVDict,
        step: Optional[int] = None,
        epoch: Optional[int] = None,
        context: Optional[KVDict] = None,
    ):
        """Log metrics"""
        self.run.track(
            metrics,
            step=step,
            epoch=epoch,
            context=context,
        )

    def distribution(
        self,
        name: str,
        values: Array,
        step: Optional[int] = None,
        epoch: Optional[int] = None,
        context: Optional[KVDict] = None,
        bin_count: int = 64,
    ):
        """Log distribution"""
        d = Distribution(
            distribution=values,
            bin_count=bin_count,
        )
        self.run.track(d, name=name, step=step, epoch=epoch, context=context)

    def close(self):
        """Close the telemetry run"""
        self.run.close()
