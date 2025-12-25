_entries = []


def _register_lifecycle(func, *, phase, name=None, doc=None):
    _entries.append(
        {
            "func": func,
            "phase": phase,
            "name": name or func.__name__,
            "doc": doc or func.__doc__,
            "origin": f"{func.__module__}.{func.__name__}",
        }
    )
    return func


def register_lifecycle(phase: str, name=None, doc=None):
    return lambda func: _register_lifecycle(func, phase=phase, name=name, doc=doc)


def get_hooks(phase: str):
    return [entry["func"] for entry in _entries if entry["phase"] == phase]


def get_all_lifecycle_entries():
    return list(_entries)


class LIFECYCLE:
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
