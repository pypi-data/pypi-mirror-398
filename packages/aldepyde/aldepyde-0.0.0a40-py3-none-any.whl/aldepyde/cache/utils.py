import os
import re

def _verify_cache_directory(path: str) -> bool:
    return os.path.exists(os.path.join(path))

def _parse_memory(memory: str) -> int:
    ALLOWED_PREFIX = "bkmgt" # No, you don't get to use petabytes
    full_re = f"[0-9]+[{ALLOWED_PREFIX}]?i?b?"
    numeric_re = "[0-9]+"

    if memory.isnumeric():
        memory += "mib"
    if re.fullmatch(full_re, memory, flags=re.IGNORECASE) is None:
        raise ValueError(f"Requested memory must be of the following form: {full_re}")

    match = re.match(numeric_re, memory)
    numeric = int(memory[:match.span()[1]])
    unit = memory[match.span()[1]:]
    base = 1024 if "i" in unit else 1000
    multiple = base**(ALLOWED_PREFIX.index(unit[0].lower()))
    return numeric * multiple

def _convert_memory_bits(memory: int) -> str:
    ALLOWED_PREFIX = "bkmgt"
    digits = len(str(memory))
    return f"{memory / (1000 ** (digits//3)):.3f} {ALLOWED_PREFIX[digits//3].upper()}b"

def _convert_memory_bytes(memory: int) -> str:
    ALLOWED_PREFIX = "bkmgt"
    digits = len(str(memory))
    return f"{memory / (1024 ** (digits // 3)):.3f} {ALLOWED_PREFIX[digits // 3].upper()}b"