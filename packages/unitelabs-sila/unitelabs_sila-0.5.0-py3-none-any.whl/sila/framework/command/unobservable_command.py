import dataclasses

from .command import Command


@dataclasses.dataclass
class UnobservableCommand(Command):
    """Any command for which observing the progress of execution is not possible or does not make sense."""

    observable: bool = dataclasses.field(init=False, repr=False, default=False)
