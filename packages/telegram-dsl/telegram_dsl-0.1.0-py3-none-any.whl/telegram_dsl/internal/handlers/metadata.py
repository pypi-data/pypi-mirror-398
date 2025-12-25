def build_metadata(func, handler_cls, **extras):
    return {
        "name": func.__name__,
        "doc": func.__doc__,
        "origin": f"{func.__module__}.{func.__name__}",
        "handler_cls": handler_cls.__name__,
        "args": extras.get("handler_args", []),
        "kwargs": extras.get("handler_kwargs", {}),
        "add_to_commands": extras.get("add_to_commands", False),
        "group": extras.get("group"),
        "tags": extras.get("tags", []),
        "scope": extras.get("scope"),
    }
