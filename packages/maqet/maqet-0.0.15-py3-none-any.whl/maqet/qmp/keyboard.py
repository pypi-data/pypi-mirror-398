"""
QMP Keyboard Emulator

Provides keyboard input functionality for QMP commands.
Ported from old maqet implementation to work with the unified API system.
"""

from typing import Any, Dict, List


class KeyboardEmulatorError(Exception):
    """Keyboard Emulator Error"""


class KeyboardEmulator:
    """
    QMP keyboard emulation utilities.

    Provides methods to generate QMP commands for keyboard input,
    including key presses and text typing.
    """

    @classmethod
    def get_keys(cls) -> List[str]:
        """Get list of available key names."""
        return KEYS

    @classmethod
    def press_keys(cls, *keys: str, hold_time: int = 100) -> Dict[str, Any]:
        """
        Generate QMP command for pressing specified keys.

        Args:
            *keys: Key names to press (e.g., 'ctrl', 'alt', 'f2')
            hold_time: How long to hold keys in milliseconds

        Returns:
            QMP command dictionary
        """
        return {
            "command": "send-key",
            "arguments": {
                "keys": [{"type": "qcode", "data": key} for key in keys],
                "hold-time": hold_time,
            },
        }

    @classmethod
    def type_string(
        cls, string: str, hold_time: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Generate sequence of QMP commands to type a string.

        Args:
            string: Text to type
            hold_time: How long to hold each key in milliseconds

        Returns:
            List of QMP command dictionaries
        """
        if not isinstance(string, str):
            raise KeyboardEmulatorError(
                f"Got {type(string)} instead of string"
            )

        return [
            cls.press_keys(*cls._char_to_keys(char), hold_time=hold_time)
            for char in string
        ]

    @classmethod
    def _char_to_keys(cls, char: str) -> List[str]:
        """Convert character to key sequence."""
        if len(char) != 1:
            raise KeyboardEmulatorError("Got string instead of one char")

        if char in KEYS:
            return [char]
        elif char.lower() in KEYS:
            return ["shift", char.lower()]
        elif char in BASIC_KEYS:
            return BASIC_KEYS[char]
        elif char in CHAR_KEYS:
            return [CHAR_KEYS[char]]
        elif char in SHIFT_CHAR_KEYS:
            return ["shift", SHIFT_CHAR_KEYS[char]]
        else:
            raise KeyboardEmulatorError(
                f"Character {char} cannot be translated into keys"
            )


# QMP key names from QEMU documentation
# https://qemu-project.gitlab.io/qemu/interop/qemu-qmp-ref.html#qapidoc-0
KEYS = [
    "unmapped",
    "pause",
    "ro",
    "kp_comma",
    "kp_equals",
    "power",
    "hiragana",
    "henkan",
    "yen",
    "sleep",
    "wake",
    "audionext",
    "audioprev",
    "audiostop",
    "audioplay",
    "audiomute",
    "volumeup",
    "volumedown",
    "mediaselect",
    "mail",
    "calculator",
    "computer",
    "ac_home",
    "ac_back",
    "ac_forward",
    "ac_refresh",
    "ac_bookmarks",
    "muhenkan",
    "katakanahiragana",
    "lang1",
    "lang2",
    "f13",
    "f14",
    "f15",
    "f16",
    "f17",
    "f18",
    "f19",
    "f20",
    "f21",
    "f22",
    "f23",
    "f24",
    "shift",
    "shift_r",
    "alt",
    "alt_r",
    "ctrl",
    "ctrl_r",
    "menu",
    "esc",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "0",
    "minus",
    "equal",
    "backspace",
    "tab",
    "q",
    "w",
    "e",
    "r",
    "t",
    "y",
    "u",
    "i",
    "o",
    "p",
    "bracket_left",
    "bracket_right",
    "ret",
    "a",
    "s",
    "d",
    "f",
    "g",
    "h",
    "j",
    "k",
    "l",
    "semicolon",
    "apostrophe",
    "grave_accent",
    "backslash",
    "z",
    "x",
    "c",
    "v",
    "b",
    "n",
    "m",
    "comma",
    "dot",
    "slash",
    "asterisk",
    "spc",
    "caps_lock",
    "f1",
    "f2",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "f9",
    "f10",
    "num_lock",
    "scroll_lock",
    "kp_divide",
    "kp_multiply",
    "kp_subtract",
    "kp_add",
    "kp_enter",
    "kp_decimal",
    "sysrq",
    "kp_0",
    "kp_1",
    "kp_2",
    "kp_3",
    "kp_4",
    "kp_5",
    "kp_6",
    "kp_7",
    "kp_8",
    "kp_9",
    "less",
    "f11",
    "f12",
    "print",
    "home",
    "pgup",
    "pgdn",
    "end",
    "left",
    "up",
    "down",
    "right",
    "insert",
    "delete",
    "stop",
    "again",
    "props",
    "undo",
    "front",
    "copy",
    "open",
    "paste",
    "find",
    "cut",
    "lf",
    "help",
    "meta_l",
    "meta_r",
    "compose",
]

BASIC_KEYS = {
    "\r": ["ret"],
    "\n": ["ret"],
    " ": ["spc"],
}

CHAR_KEYS = {
    # Row 1
    "`": "grave_accent",
    "=": "equal",
    "-": "minus",
    # Row 2
    "[": "bracket_left",
    "]": "bracket_right",
    "\\": "backslash",
    # Row 3
    ";": "semicolon",
    "'": "apostrophe",
    # Row 4
    ",": "comma",
    ".": "dot",
    "/": "slash",
}

SHIFT_CHAR_KEYS = {
    # Row 1
    "~": "grave_accent",
    "!": "1",
    "@": "2",
    "#": "3",
    "$": "4",
    "%": "5",
    "^": "6",
    "&": "7",
    "*": "8",
    "(": "9",
    ")": "0",
    "_": "minus",
    "+": "equal",
    # Row 2
    "{": "bracket_left",
    "}": "bracket_right",
    "|": "backslash",
    # Row 3
    ":": "semicolon",
    '"': "apostrophe",
    # Row 4
    "<": "comma",
    ">": "dot",
    "?": "slash",
}
