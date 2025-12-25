from telegram_dsl.internal.handlers.map import get_handler
from telegram_dsl.internal.handlers.states import (
    register_state_handler,
    _lazy_state_registrations,
)


def register_state(group, state_id):
    def decorator(func):
        try:
            handler = get_handler(func)
            register_state_handler(group, state_id, handler)
            print(
                f"[REGISTER_STATE] Immediately registered {func.__name__} (id={id(func)}) for state {state_id}"
            )
        except ValueError:
            print(
                f"[REGISTER_STATE] Delaying registration for {func.__name__} (id={id(func)}) for state {state_id}"
            )
            _lazy_state_registrations.append((func, group, state_id))
        return func

    return decorator


def register_entry_point(group):
    def decorator(func):
        try:
            handler = get_handler(func)
            register_state_handler(group, 0, handler)
            print(
                f"[REGISTER_ENTRY_POINT] Immediately registered {func.__name__} (id={id(func)}) as entry point for group '{group}'"
            )
        except ValueError:
            print(
                f"[REGISTER_ENTRY_POINT] Delaying registration for {func.__name__} (id={id(func)}) as entry point for group '{group}'"
            )
            _lazy_state_registrations.append((func, group, 0))  # 0 as entry state
        return func

    return decorator
