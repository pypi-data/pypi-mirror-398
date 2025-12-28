from dataclasses import dataclass
from typing import List, Tuple

import equinox as eqx
import orbax.checkpoint as ocp
import orbax.checkpoint.future as ocp_future
from etils import epath


class EquinoxCheckpointHandler(ocp.AsyncCheckpointHandler):
    """Handler for equinox pytree."""

    def __init__(self):
        pass

    def save(
        self,
        directory: epath.Path,
        args: "EquinoxSave",
        **kwargs,
    ):
        eqx.tree_serialise_leaves(
            str(directory / "model.eqx"), (args.model, args.state)
        )

    async def _save(self, directory, args, **kwargs):
        self.save(directory, args, **kwargs)

    def restore(
        self,
        directory: epath.Path,
        args: "EquinoxRestore",
        **kwargs,
    ) -> Tuple[eqx.Module, eqx.nn.State]:
        model, state = eqx.tree_deserialise_leaves(
            str(directory / "model.eqx"), (args.model, args.state)
        )
        if args.state._state == {}:
            return model
        return model, state

    async def async_save(
        self,
        directory: epath.Path,
        args: "EquinoxSave",
        **kwargs,
    ) -> List[ocp_future.CommitFutureAwaitingContractedSignals]:
        return [
            ocp_future.CommitFutureAwaitingContractedSignals(
                self._save(directory, args),
                name="equinox_save",
            )
        ]

    def close(self):
        pass


@ocp.args.register_with_handler(EquinoxCheckpointHandler, for_save=True)
@dataclass
class EquinoxSave(ocp.args.CheckpointArgs):
    """Arguments for saving an equinox model."""

    model: eqx.Module
    state: eqx.nn.State = eqx.nn.State(None)


@ocp.args.register_with_handler(EquinoxCheckpointHandler, for_restore=True)
@dataclass
class EquinoxRestore(ocp.args.CheckpointArgs):
    """Arguments for restoring equinox model."""

    model: eqx.Module
    state: eqx.nn.State = eqx.nn.State(None)


CheckpointManager = ocp.CheckpointManager
CheckpointManagerOptions = ocp.CheckpointManagerOptions
Checkpointer = ocp.Checkpointer
AsyncCheckpointer = ocp.AsyncCheckpointer

args = ocp.args
