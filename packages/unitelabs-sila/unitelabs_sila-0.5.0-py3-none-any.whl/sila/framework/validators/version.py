import enum
import re

import typing_extensions as typing


class VersionLevel(enum.IntEnum):
    """Different levels of specificity of a version. A version is written as "major.minor.patch_label"."""

    MAJOR = 1
    MINOR = 2
    PATCH = 3
    LABEL = 4


def check_version(value: str, /, required: VersionLevel, optional: typing.Optional[VersionLevel] = None) -> str:
    """
    Validate whether the given value is a semantic version.

    Args:
      value: The input value to validate.
      required: The minimum level of detail required.
      optional: The minimum level of detail allowed.

    Returns:
      The input value, allowing for method chaining.

    Raises:
      ValueError: If the provided value does not follow the expected
        schema.
    """

    optional = optional or required
    if required.value > optional.value:
        msg = "Optional level can not be less detailed than required level."
        raise ValueError(msg)

    if not isinstance(value, str):
        msg = f"Version must be a string of unicode characters, received '{value}'."
        raise ValueError(msg)

    version = value
    if optional == VersionLevel.LABEL:
        version, _, label = value.partition("_")

        if required == VersionLevel.LABEL and not label:
            msg = f"Version must contain a label after an underscore, received '{value}'."
            raise ValueError(msg)

        if not re.fullmatch(r"[a-zA-Z0-9\_]*", label):
            msg = f"Version label may only contain letters, digits and underscores, received '{value}'."
            raise ValueError(msg)

    parts = version.split(".")
    if len(parts) < min(required.value, VersionLevel.PATCH):
        msg = f"Version must contain at least {required.value} parts separated by dots, received '{value}'."
        raise ValueError(msg)

    if len(parts) > min(optional.value, VersionLevel.PATCH):
        msg = f"Version must contain at most {optional.value} parts separated by dots, received '{value}'."
        raise ValueError(msg)

    for part in parts:
        if not part.isdigit():
            msg = f"Version parts must represent a numeric value, received '{value}'."
            raise ValueError(msg)

    return value
