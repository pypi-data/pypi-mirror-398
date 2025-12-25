import dataclasses

import typing_extensions as typing

if typing.TYPE_CHECKING:
    from ..command import Command
    from ..metadata import Metadata
    from ..property import Property


@dataclasses.dataclass
class Execution:
    """
    Context of the current command execution.

    Arguments:
      command: The command that is currently executed.
      property: The property that is currently converted.
      metadata: Metadata sent from client to server.
    """

    command: "Command"
    property: "Property"
    metadata: "Metadata"
