# Handler registry for telegram_dsl.

_handler_entries = []  # List of dicts: {orig_id, final_id, handler, meta}


def add_handler_entry(orig_func, final_func, handler, metadata):
    metadata["handler_instance"] = handler
    _handler_entries.append(
        {
            "orig_id": id(orig_func),
            "final_id": id(final_func),
            "handler": handler,
            "meta": metadata,
        }
    )


def get_handler(func):
    for entry in _handler_entries:
        if id(func) == entry["final_id"]:
            return entry["handler"]
    for entry in _handler_entries:
        if id(func) == entry["orig_id"]:
            return entry["handler"]
    raise ValueError(f"No handler registered for function id={id(func)}")


def _get_all_entries():
    return list(_handler_entries)


def get_all_metadata():
    return [entry["meta"] for entry in _handler_entries]


def clear_registry():
    _handler_entries.clear()
