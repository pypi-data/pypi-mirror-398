import os
import shutil
from .error_utils import xerror



def xchdir(path):
    try:
        if not isinstance(path, str):
            return xerror("TypeError", "path must be a string")

        # If relative path, resolve from current directory
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        os.chdir(path)

        # return new current directory
        return os.getcwd()

    except FileNotFoundError:
        return xerror("FileNotFoundError", "directory not found")

    except NotADirectoryError:
        return xerror("NotADirectoryError", "path is not a directory")

    except PermissionError:
        return xerror("PermissionError", "permission denied")

    except OSError as e:
        return xerror("OSError", str(e))

    except Exception:
        return -1
# -------------------------
# PRESENT WORKING DIRECTORY
# -------------------------

def xpwd():
    try:
        return os.getcwd()
    except OSError as e:
        return xerror("OSError", str(e))
    except Exception:
        return -1


# -------------------------
# SAFE FILE OPEN
# -------------------------

def xopen(path, mode="r"):
    try:
        if not isinstance(path, str):
            return xerror("TypeError", "path must be a string")

        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        return open(path, mode)

    except FileNotFoundError:
        return xerror("FileNotFoundError", "file not found")
    except PermissionError:
        return xerror("PermissionError", "permission denied")
    except IsADirectoryError:
        return xerror("IsADirectoryError", "path is a directory")
    except TypeError as e:
        return xerror("TypeError", str(e))
    except Exception:
        return -1


# -------------------------
# DIRECTORY OPERATIONS
# -------------------------

def xmkdir(path=None, name=None):
    try:
        if not name:
            return xerror("ValueError", "folder name not provided")

        base = path if path else os.getcwd()
        full = os.path.join(base, name)

        os.makedirs(full, exist_ok=True)
        return full

    except PermissionError:
        return xerror("PermissionError", "permission denied")
    except OSError as e:
        return xerror("OSError", str(e))
    except Exception:
        return -1


def xrmdir(path=None, name=None):
    try:
        if not name:
            return xerror("ValueError", "folder name not provided")

        base = path if path else os.getcwd()
        full = os.path.join(base, name)

        os.rmdir(full)
        return True

    except FileNotFoundError:
        return xerror("FileNotFoundError", "folder not found")
    except PermissionError:
        return xerror("PermissionError", "permission denied")
    except OSError:
        return xerror("OSError", "folder not empty")
    except Exception:
        return -1


# -------------------------
# FILE CREATE / DELETE
# -------------------------

def xmkfile(path=None, name=None):
    try:
        if not name:
            return xerror("ValueError", "file name not provided")

        base = path if path else os.getcwd()
        full = os.path.join(base, name)

        with open(full, "a"):
            pass

        return full

    except PermissionError:
        return xerror("PermissionError", "permission denied")
    except OSError as e:
        return xerror("OSError", str(e))
    except Exception:
        return -1


def xrmfile(path=None, name=None):
    try:
        if not name:
            return xerror("ValueError", "file name not provided")

        base = path if path else os.getcwd()
        full = os.path.join(base, name)

        os.remove(full)
        return True

    except FileNotFoundError:
        return xerror("FileNotFoundError", "file not found")
    except PermissionError:
        return xerror("PermissionError", "permission denied")
    except IsADirectoryError:
        return xerror("IsADirectoryError", "path is a directory")
    except Exception:
        return -1


# -------------------------
# READ / WRITE
# -------------------------

def xread(path):
    try:
        if not isinstance(path, str):
            return xerror("TypeError", "path must be a string")

        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    except FileNotFoundError:
        return xerror("FileNotFoundError", "file not found")
    except PermissionError:
        return xerror("PermissionError", "permission denied")
    except IsADirectoryError:
        return xerror("IsADirectoryError", "path is a directory")
    except Exception:
        return -1


def xwrite(path, data, mode="w"):
    try:
        if not isinstance(path, str):
            return xerror("TypeError", "path must be a string")

        if not isinstance(data, str):
            return xerror("TypeError", "data must be a string")

        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        with open(path, mode, encoding="utf-8") as f:
            f.write(data)

        return True

    except PermissionError:
        return xerror("PermissionError", "permission denied")
    except IsADirectoryError:
        return xerror("IsADirectoryError", "path is a directory")
    except Exception:
        return -1


# -------------------------
# COPY / MOVE
# -------------------------

def xcopy(src, dst):
    try:
        if not isinstance(src, str) or not isinstance(dst, str):
            return xerror("TypeError", "paths must be strings")

        if not os.path.isabs(src):
            src = os.path.join(os.getcwd(), src)

        if not os.path.isabs(dst):
            dst = os.path.join(os.getcwd(), dst)

        shutil.copy2(src, dst)
        return True

    except FileNotFoundError:
        return xerror("FileNotFoundError", "source file not found")
    except PermissionError:
        return xerror("PermissionError", "permission denied")
    except IsADirectoryError:
        return xerror("IsADirectoryError", "source is a directory")
    except Exception:
        return -1


def xmove(src, dst):
    try:
        if not isinstance(src, str) or not isinstance(dst, str):
            return xerror("TypeError", "paths must be strings")

        if not os.path.isabs(src):
            src = os.path.join(os.getcwd(), src)

        if not os.path.isabs(dst):
            dst = os.path.join(os.getcwd(), dst)

        shutil.move(src, dst)
        return True

    except FileNotFoundError:
        return xerror("FileNotFoundError", "source file not found")
    except PermissionError:
        return xerror("PermissionError", "permission denied")
    except Exception:
        return -1
