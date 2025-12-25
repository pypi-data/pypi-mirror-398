import dataclasses

from .property import Property


@dataclasses.dataclass
class ObservableProperty(Property):
    """A property describes certain aspects of a SiLA server that do not require an action on the SiLA server."""

    observable: bool = dataclasses.field(init=False, repr=False, default=True)
