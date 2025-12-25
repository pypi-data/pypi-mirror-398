import re


def check_url(value: str) -> str:
    """
    Validate whether the given value is URL as defined in RFC 1738.

    Args:
      value: The input value to validate.

    Returns:
      The input value, allowing for method chaining.

    Raises:
      ValueError: If the provided value does not follow the expected
        schema.
    """

    if not isinstance(value, str):
        msg = f"URL must be a string of unicode characters, received '{value}'."
        raise ValueError(msg)

    if not re.fullmatch(r"https?://.+", value):
        msg = f"URL must start with 'https://' or 'http://', received '{value}'."
        raise ValueError(msg)

    return value
