import re


def check_uuid(value: str) -> str:
    """
    Validate whether the given value is a Universally Unique IDentifier according to RFC 4122.

    Args:
      value: The input value to validate.

    Returns:
      The input value, allowing for method chaining.

    Raises:
      ValueError: If the provided value does not follow the expected
        schema.
    """

    if not isinstance(value, str):
        msg = f"UUID must be a string of unicode characters, received '{value}'."
        raise ValueError(msg)

    if not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", value):
        msg = f"UUID may only contain letters and digits, received '{value}'."
        raise ValueError(msg)

    return value
