_error_handlers = []


def register_error_handler(func):
    _error_handlers.append(func)
    return func


def get_error_handlers():
    return list(_error_handlers)


def clear_error_handlers():
    _error_handlers.clear()
