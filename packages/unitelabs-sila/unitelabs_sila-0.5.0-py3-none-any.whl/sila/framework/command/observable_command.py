import dataclasses

import typing_extensions as typing

from .command import Command

if typing.TYPE_CHECKING:
    from ..data_types import Element


@dataclasses.dataclass
class ObservableCommand(Command):
    """Any command for which observing the progress of execution is possible or does make sense."""

    observable: bool = dataclasses.field(init=False, repr=False, default=True)

    intermediate_responses: dict[str, "Element"] = dataclasses.field(default_factory=dict)
    """An intermediate response of the command execution."""
