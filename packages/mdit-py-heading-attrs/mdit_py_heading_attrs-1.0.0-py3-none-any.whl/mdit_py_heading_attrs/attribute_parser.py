"""Attribute parsing logic for heading attributes.

This module provides simplified parsing for {#id} syntax (for now).
"""


def parse_id_attribute(text: str) -> tuple[str | None, str, bool]:
    """Parse {#id} attribute from end of text.

    Args:
        text: The heading text that may contain {#id} at the end

    Returns:
        Tuple of (id_value, new_text_without_attrs, success)
        - id_value: The extracted ID (without #), or None if parsing failed
        - new_text_without_attrs: Text with attribute block removed
        - success: True if parsing succeeded, False otherwise

    Examples:
        >>> parse_id_attribute("Hello {#my-id}")
        ('my-id', 'Hello', True)
        >>> parse_id_attribute("Hello {.class}")
        (None, 'Hello {.class}', False)
        >>> parse_id_attribute("Hello \\{#escaped}")
        (None, 'Hello \\{#escaped}', False)
    """
    brace_pos = find_last_unescaped_brace(text)
    if brace_pos == -1:
        return None, text, False

    close_pos = text.find("}", brace_pos)
    if close_pos == -1:
        return None, text, False

    after_brace = text[close_pos + 1 :]
    if after_brace and not after_brace.isspace():
        return None, text, False

    attr_content = text[brace_pos + 1 : close_pos].strip()

    if not attr_content.startswith("#"):
        return None, text, False

    # Check for invalid patterns (multiple attributes, class, etc.)
    # Note: periods and colons are valid IN the ID value, so we can't reject them here
    # We check for spaces (multiple attrs) or equals (key=value syntax)
    if " " in attr_content or "=" in attr_content:
        return None, text, False

    # Check if it starts with a period (class syntax like .class)
    # But allow periods in the ID value after #
    if attr_content.startswith("."):
        return None, text, False

    # Extract ID value (everything after #)
    id_value = attr_content[1:]

    # Validate ID characters (alphanumeric + -_:. per XHTML)
    if not id_value or not is_valid_id(id_value):
        return None, text, False

    new_text = text[:brace_pos].rstrip()
    return id_value, new_text, True


def find_last_unescaped_brace(text: str) -> int:
    """Find the last '{' that is not escaped with backslash.

    Args:
        text: The text to search

    Returns:
        Position of last unescaped '{', or -1 if not found

    Examples:
        >>> find_last_unescaped_brace("Hello {#id}")
        6
        >>> find_last_unescaped_brace("Hello \\{not}")
        -1
        >>> find_last_unescaped_brace("Text \\{escaped} {#id}")
        17
    """
    pos = len(text) - 1

    while pos >= 0:
        if text[pos] == "{":
            # Check if escaped (preceded by odd number of backslashes)
            num_backslashes = 0
            check_pos = pos - 1
            while check_pos >= 0 and text[check_pos] == "\\":
                num_backslashes += 1
                check_pos -= 1

            # If even number of backslashes (including 0), the brace is not escaped
            if num_backslashes % 2 == 0:
                return pos

            # Odd number of backslashes means it's escaped, skip past the backslashes
            pos = check_pos
        else:
            pos -= 1

    return -1


def is_valid_id(id_value: str) -> bool:
    """Check if ID contains only valid characters.

    Valid ID characters (per XHTML):
    - Alphanumeric (a-z, A-Z, 0-9)
    - Hyphen (-)
    - Underscore (_)
    - Colon (:)
    - Period (.)

    Args:
        id_value: The ID value to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> is_valid_id("my-id")
        True
        >>> is_valid_id("my_id:1.0")
        True
        >>> is_valid_id("my id")
        False
        >>> is_valid_id("my@id")
        False
    """
    if not id_value:
        return False

    for char in id_value:
        if not (char.isalnum() or char in "-_:."):
            return False

    return True
