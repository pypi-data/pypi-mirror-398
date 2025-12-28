from .error_utils import xerror


def xfind(container, target):
    try:
        # STRING, LIST, TUPLE
        if isinstance(container, (str, list, tuple)):
            indexes = []

            for i in range(len(container)):
                if container[i] == target:
                    indexes.append(i)

            if len(indexes) == 0:
                return -1
            elif len(indexes) == 1:
                return indexes[0]
            else:
                return indexes

        # DICTIONARY
        elif isinstance(container, dict):
            results = []

            for key, value in container.items():
                if key == target or value == target:
                    results.append(key)

            if len(results) == 0:
                return -1
            elif len(results) == 1:
                return results[0]
            else:
                return results

        # SET
        elif isinstance(container, set):
            if target in container:
                return target
            else:
                return -1

        else:
            return xerror("TypeError", "unsupported container type")

    except TypeError as e:
        return xerror("TypeError", str(e))

    except ValueError as e:
        return xerror("ValueError", str(e))

    except KeyError as e:
        return xerror("KeyError", "key not found")

    except AttributeError as e:
        return xerror("AttributeError", str(e))

    except Exception:
        # Unknown error → silent fallback
        return -1