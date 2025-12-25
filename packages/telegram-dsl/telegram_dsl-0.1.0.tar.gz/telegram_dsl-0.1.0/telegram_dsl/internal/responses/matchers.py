_renderer_entries = []


def register_renderer(*, request_type, response_type):
    def decorator(func):
        _renderer_entries.append(
            {"type": request_type, "response_type": response_type, "func": func}
        )
        return func

    return decorator


def get_renderer(content):
    for entry in _renderer_entries:
        if isinstance(content, entry["type"]):
            return entry
    return None
