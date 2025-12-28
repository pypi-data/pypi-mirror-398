from .error_utils import xerror


def xfind(container, target):
    try:
        # =========================
        # STRING (character + substring)
        # =========================
        if isinstance(container, str):
            if not isinstance(target, str):
                return xerror("TypeError", "target must be a string for string search")

            indexes = []
            start = 0

            while True:
                pos = container.find(target, start)
                if pos == -1:
                    break
                indexes.append(pos)
                start = pos + 1  # allow overlapping

            if not indexes:
                return -1
            if len(indexes) == 1:
                return indexes[0]
            return indexes

        # =========================
        # LIST / TUPLE
        # =========================
        elif isinstance(container, (list, tuple)):
            indexes = []

            for i, value in enumerate(container):
                if value == target:
                    indexes.append(i)

            if not indexes:
                return -1
            if len(indexes) == 1:
                return indexes[0]
            return indexes

        # =========================
        # DICTIONARY (keys + values)
        # =========================
        elif isinstance(container, dict):
            keys = []

            for k, v in container.items():
                if k == target or v == target:
                    keys.append(k)

            if not keys:
                return -1
            if len(keys) == 1:
                return keys[0]
            return keys

        # =========================
        # SET (no index exists)
        # =========================
        elif isinstance(container, set):
            return target if target in container else -1

        # =========================
        # UNSUPPORTED TYPE
        # =========================
        else:
            return xerror("TypeError", "unsupported container type")

    # =========================
    # KNOWN ERRORS
    # =========================
    except TypeError as e:
        return xerror("TypeError", str(e))
    except ValueError as e:
        return xerror("ValueError", str(e))
    except KeyError as e:
        return xerror("KeyError", str(e))
    except AttributeError as e:
        return xerror("AttributeError", str(e))

    # =========================
    # UNKNOWN ERROR
    # =========================
    except Exception:
        return -1