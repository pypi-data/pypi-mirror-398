import enum


class WireType(enum.IntEnum):
    """The wire type tells the parser how big the payload after it is."""

    VARINT = 0
    """
    Used for int32, int64, uint32, uint64, sint32, sint64, bool and
    enum.
    """

    I64 = 1
    """
    Used for fixed64, sfixed64 and double.
    """

    LEN = 2
    """
    Used for string, bytes, embedded messages and packed repeated
    fields.
    """

    SGROUP = 3
    """
    A deprecated wire type to indicate the start of a group.
    """

    EGROUP = 4
    """
    A deprecated wire type to indicate the end of a group.
    """

    I32 = 5
    """
    Used for fixed32, sfixed32 and float.
    """
