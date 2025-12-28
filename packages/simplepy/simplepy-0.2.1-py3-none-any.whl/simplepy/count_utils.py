from .error_utils import xerror


def xcount(container, target):
    try:
        # STRING
        if isinstance(container, str):
            return container.count(target)

        # LIST or TUPLE
        elif isinstance(container, (list, tuple)):
            count = 0
            for item in container:
                if item == target:
                    count += 1
            return count

        # DICTIONARY (count keys + values)
        elif isinstance(container, dict):
            count = 0
            for key, value in container.items():
                if key == target:
                    count += 1
                if value == target:
                    count += 1
            return count

        # SET (either present or not)
        elif isinstance(container, set):
            return 1 if target in container else 0

        else:
            return xerror("TypeError", "unsupported container type")

    except TypeError as e:
        return xerror("TypeError", str(e))

    except ValueError as e:
        return xerror("ValueError", str(e))

    except AttributeError as e:
        return xerror("AttributeError", str(e))

    except Exception:
        return -1
