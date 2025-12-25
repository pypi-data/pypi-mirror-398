_responder_entries = []


def register_responder(*, match=lambda r: False):
    def decorator(func):
        _responder_entries.append(
            {
                "name": func.__name__,
                "match": match,
                "func": func,
            }
        )
        return func

    return decorator


def get_responder(response_type):
    for entry in _responder_entries:
        if entry["match"](response_type):
            return entry["func"]


def list_responders():
    return _responder_entries
