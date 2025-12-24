def to_bool(value: str | bool | int | None) -> bool:
    """Convert a value to a boolean, with special handling for strings.

    Args:
        value: The value to convert. Can be:
            - A string (e.g. "true", "yes", "1", "false", "no", "0")
            - A boolean
            - An integer
            - None

    Returns:
        bool: The boolean interpretation of the value.

    Examples:
        >>> to_bool("true")
        True
        >>> to_bool("yes")
        True
        >>> to_bool("1")
        True
        >>> to_bool("false")
        False
        >>> to_bool("no")
        False
        >>> to_bool("0")
        False
        >>> to_bool(True)
        True
        >>> to_bool(1)
        True
        >>> to_bool(None)
        False
    """
    if value is None:
        return False

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return bool(value)

    if isinstance(value, str):
        # Convert to lowercase for case-insensitive comparison
        value = value.lower().strip()

        # Handle common truthy values
        if value in ("true", "yes", "1", "on", "t", "y"):
            return True

        # Handle common falsy values
        if value in ("false", "no", "0", "off", "f", "n"):
            return False

        # For any other string, treat as falsy
        return False

    # For any other type, use Python's bool() conversion
    return bool(value)
