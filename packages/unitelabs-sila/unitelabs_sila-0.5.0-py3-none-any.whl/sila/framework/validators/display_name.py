def check_display_name(value: str) -> str:
    """
    Validate whether the given value is a human readable display name.

    Args:
      value: The input value to validate.

    Returns:
      The input value, allowing for method chaining.

    Raises:
      ValueError: If the provided value does not follow the expected
        schema.
    """

    if not isinstance(value, str):
        msg = f"Display name must be a string of unicode characters, received '{value}'."
        raise ValueError(msg)

    if not value:
        msg = f"Display name must not be empty, received '{value}'."
        raise ValueError(msg)

    if len(value) > 255:
        msg = f"Display name must not exceed 255 characters in length, received '{value}'."
        raise ValueError(msg)

    return value
