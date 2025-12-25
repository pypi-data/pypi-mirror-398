_global_middleware = []
_per_handler_middleware = {}


def register_global_middleware(func):
    _global_middleware.append(func)
    return func


def get_global_middleware():
    return _global_middleware


def register_middleware(middleware_func):
    def wrapper(handler_func):
        # When stacked above telegram_dsl handler decorators, the function we receive
        # is often the wrapper returned by @command_handler/@text_handler/etc.
        # The engine middleware stack is keyed by the original function, so resolve it.
        original = getattr(handler_func, "__wrapped__", handler_func)
        _per_handler_middleware.setdefault(original, []).append(middleware_func)
        return handler_func

    return wrapper


def get_middleware(handler):
    return _per_handler_middleware.get(handler, [])
