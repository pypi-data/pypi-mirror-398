import re


def check_identifier(value: str) -> str:
    """
    Validate whether the given value is a unique identifier.

    Args:
      value: The input value to validate.

    Returns:
      The input value, allowing for method chaining.

    Raises:
      ValueError: If the provided value does not follow the expected
        schema.
    """

    if not isinstance(value, str):
        msg = f"Identifier must be a string of unicode characters, received '{value}'."
        raise ValueError(msg)

    if not value or not value[0].isupper():
        msg = f"Identifier must start with an upper-case letter, received '{value}'."
        raise ValueError(msg)

    if len(value) > 255:
        msg = f"Identifier must not exceed 255 characters in length, received '{value}'."
        raise ValueError(msg)

    if not re.fullmatch(r"[A-Z][a-zA-Z0-9]*", value):
        msg = f"Identifier may only contain letters and digits, received '{value}'."
        raise ValueError(msg)

    return value
