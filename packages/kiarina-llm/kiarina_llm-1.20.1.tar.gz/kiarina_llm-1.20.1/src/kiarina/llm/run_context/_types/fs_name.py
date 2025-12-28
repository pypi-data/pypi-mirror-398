from typing import Annotated

from pydantic import AfterValidator, StringConstraints

FS_NAME_PATTERN = r"^[A-Za-z0-9._ -]+$"
"""
File system name pattern

Permit ASCII letters, dots, underscores, hyphens, and spaces.
Detailed constraints are checked by validation functions.
"""

WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *{f"com{i}" for i in range(1, 10)},
    *{f"lpt{i}" for i in range(1, 10)},
}
"""
Set of reserved names in Windows

Uppercase and lowercase letters are ignored.
"""


def _validate_fs_name(v: str) -> str:
    name = v.strip()

    if name.lower() in WINDOWS_RESERVED:
        raise ValueError(f"'{v}' is a reserved name on Windows")

    # Prohibiting names beginning with a dot
    if name.startswith("."):
        raise ValueError(f"'{v}' cannot start with a dot")

    # Prohibiting endings with a dot or space
    if name.endswith(".") or name.endswith(" "):
        raise ValueError(f"'{v}' cannot end with a dot or space")

    return v


FSName = Annotated[
    str,
    StringConstraints(min_length=1, pattern=FS_NAME_PATTERN),
    AfterValidator(_validate_fs_name),
]
"""
Filesystem Safe Name Type
"""
