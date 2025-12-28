# simplepy
# Beginner-friendly utility library
#
# Core rules:
# - Functions never crash the program
# - Known errors -> print + return error string
# - Unknown errors -> return -1
# - Successful execution -> return value (no printing)


# ---- error handling ----
from .error_utils import xerror


# ---- search & count ----
from .search_utils import xfind
from .count_utils import xcount


# ---- file & directory I/O ----
from .file_utils import (
    xpwd,
    xopen,
    xmkdir,
    xrmdir,
    xmkfile,
    xrmfile,
    xread,
    xwrite,
    xcopy,
    xmove,
)


__all__ = [
    # error
    "xerror",

    # search & count
    "xfind",
    "xcount",

    # file system
    "xpwd",
    "xopen",
    "xmkdir",
    "xrmdir",
    "xmkfile",
    "xrmfile",
    "xread",
    "xwrite",
    "xcopy",
    "xmove",
]