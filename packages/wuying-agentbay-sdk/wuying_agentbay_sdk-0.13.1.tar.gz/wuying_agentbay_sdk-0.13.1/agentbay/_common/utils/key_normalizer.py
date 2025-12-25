"""
Key name normalization utilities for press_keys tool.

This module provides utilities to normalize key names to the correct case format
expected by the press_keys MCP tool, improving case compatibility.
"""

from typing import List

# Define key name mappings with correct case formats
# Category 1: Modifier keys - should be Title Case
MODIFIER_KEYS = {
    "ctrl": "Ctrl",
    "control": "Ctrl",
    "alt": "Alt",
    "shift": "Shift",
    "win": "Win",
    "windows": "Win",
    "meta": "Meta",
    "super": "Super",
    "command": "Command",
    "cmd": "Command",
}

# Category 2: Function keys - should be Title Case
FUNCTION_KEYS = {
    "tab": "Tab",
    "enter": "Enter",
    "return": "Enter",
    "escape": "Escape",
    "esc": "Escape",
    "backspace": "Backspace",
    "delete": "Delete",
    "del": "Delete",
    "insert": "Insert",
    "ins": "Insert",
    "home": "Home",
    "end": "End",
    "pageup": "PageUp",
    "pagedown": "PageDown",
    "pgup": "PageUp",
    "pgdn": "PageDown",
    "space": "Space",
    "capslock": "CapsLock",
    "numlock": "NumLock",
    "scrolllock": "ScrollLock",
    "printscreen": "PrintScreen",
    "prtsc": "PrintScreen",
    "pause": "Pause",
    "break": "Pause",
}

# Category 3: Arrow keys - should be Title Case
ARROW_KEYS = {
    "arrowup": "ArrowUp",
    "arrowdown": "ArrowDown",
    "arrowleft": "ArrowLeft",
    "arrowright": "ArrowRight",
    "up": "ArrowUp",
    "down": "ArrowDown",
    "left": "ArrowLeft",
    "right": "ArrowRight",
}

# Category 4: Special characters - as-is
SPECIAL_CHARS = {
    "minus": "-",
    "equal": "=",
    "leftbracket": "[",
    "rightbracket": "]",
    "backslash": "\\",
    "semicolon": ";",
    "quote": "'",
    "comma": ",",
    "period": ".",
    "slash": "/",
    "backtick": "`",
}

# Category 5: F-keys - Title Case (F1, F2, ..., F12)
# Generate F1-F24 mappings
F_KEYS = {}
for i in range(1, 25):
    f_key_lower = f"f{i}"
    f_key_upper = f"F{i}"
    F_KEYS[f_key_lower] = f_key_upper


def _normalize_single_key(key: str) -> str:
    """
    Normalize a single key name to the correct case format.

    Args:
        key: The key name to normalize (can be any case)

    Returns:
        str: The normalized key name with correct case

    Rules:
        - Letter keys (a-z): Convert to lowercase
        - Number keys (0-9): Keep as-is
        - Modifier keys: Convert to Title Case (Ctrl, Alt, Shift, Win, etc.)
        - Function keys: Convert to Title Case (Tab, Enter, Escape, etc.)
        - Arrow keys: Convert to Title Case (ArrowUp, ArrowDown, etc.)
        - F-keys: Convert to correct format (F1, F2, ..., F12)
        - Unknown keys: Return as-is

    Examples:
        >>> _normalize_single_key("A")
        'a'
        >>> _normalize_single_key("ctrl")
        'Ctrl'
        >>> _normalize_single_key("CTRL")
        'Ctrl'
        >>> _normalize_single_key("TAB")
        'Tab'
        >>> _normalize_single_key("f1")
        'F1'
    """
    if not key:
        return key

    # Convert to lowercase for comparison
    key_lower = key.lower()

    # Check if it's a single letter (a-z)
    if len(key) == 1 and key.isalpha():
        return key.lower()

    # Check if it's a single digit (0-9)
    if len(key) == 1 and key.isdigit():
        return key

    # Check modifier keys
    if key_lower in MODIFIER_KEYS:
        return MODIFIER_KEYS[key_lower]

    # Check function keys
    if key_lower in FUNCTION_KEYS:
        return FUNCTION_KEYS[key_lower]

    # Check arrow keys
    if key_lower in ARROW_KEYS:
        return ARROW_KEYS[key_lower]

    # Check F-keys
    if key_lower in F_KEYS:
        return F_KEYS[key_lower]

    # Check special characters
    if key_lower in SPECIAL_CHARS:
        return SPECIAL_CHARS[key_lower]

    # If the key is already in a known good format (starts with uppercase letter
    # and is not all uppercase), assume it's already correct
    if (
        key[0].isupper()
        and not key.isupper()
        and key not in ["Control", "Windows", "Command"]
    ):
        return key

    # Unknown key - return as-is
    return key


def normalize_keys(keys: List[str]) -> List[str]:
    """
    Normalize a list of key names to the correct case format for press_keys tool.

    This function automatically converts key names to the format expected by the
    press_keys MCP tool, improving case compatibility and user experience.

    Args:
        keys: List of key names to normalize (can be any case)

    Returns:
        List[str]: List of normalized key names with correct case

    Examples:
        >>> normalize_keys(["CTRL", "C"])
        ['Ctrl', 'c']
        >>> normalize_keys(["ctrl", "shift", "Z"])
        ['Ctrl', 'Shift', 'z']
        >>> normalize_keys(["alt", "TAB"])
        ['Alt', 'Tab']
        >>> normalize_keys(["win", "d"])
        ['Win', 'd']

    Note:
        - Modifier keys are converted to Title Case (Ctrl, Alt, Shift, Win)
        - Function keys are converted to Title Case (Tab, Enter, Escape)
        - Letter keys are converted to lowercase (a, b, c)
        - Number keys remain unchanged (0, 1, 2)
        - Unknown keys are returned as-is
    """
    if not keys:
        return keys

    normalized = []
    for key in keys:
        if isinstance(key, str):
            normalized.append(_normalize_single_key(key))
        else:
            # Non-string keys are passed through unchanged
            normalized.append(key)

    return normalized


def get_supported_key_names() -> dict:
    """
    Get a dictionary of all supported key name mappings.

    Returns:
        dict: Dictionary with categories and their supported key names

    Example:
        >>> mappings = get_supported_key_names()
        >>> print(mappings["modifier_keys"])
        {'ctrl': 'Ctrl', 'alt': 'Alt', ...}
    """
    return {
        "modifier_keys": MODIFIER_KEYS,
        "function_keys": FUNCTION_KEYS,
        "arrow_keys": ARROW_KEYS,
        "f_keys": F_KEYS,
        "special_chars": SPECIAL_CHARS,
    }
