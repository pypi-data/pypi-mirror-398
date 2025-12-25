from collections import defaultdict

_state_registry = defaultdict(lambda: defaultdict(list))
_lazy_state_registrations = []


def register_state_handler(group, state_id, handler):
    _state_registry[group][state_id].append(handler)
    print(
        f"[STATE_REGISTRY] Registered handler id={id(handler.callback) if hasattr(handler, 'callback') else id(handler)} for group='{group}' state={state_id}"
    )


def get_state_handlers(group):
    trigger_lazy_state_registrations()
    return _state_registry[group]


def trigger_lazy_state_registrations():
    from telegram_dsl.internal.handlers.map import get_handler

    global _lazy_state_registrations
    for func, group, state_id in _lazy_state_registrations:
        try:
            handler = get_handler(func)
            register_state_handler(group, state_id, handler)
            print(
                f"[LAZY] Triggered registration for {func.__name__} (id={id(func)}) to state {state_id}"
            )
        except ValueError as e:
            print(f"[LAZY] Failed to register {func.__name__}: {e}")
    _lazy_state_registrations.clear()


def get_conversation_entry_points(group):
    trigger_lazy_state_registrations()
    return _state_registry[group].get(0, [])


def get_conversation_states(group):
    trigger_lazy_state_registrations()
    return {k: v for k, v in _state_registry[group].items() if k != 0}


def list_conversation_groups():
    trigger_lazy_state_registrations()
    return list(_state_registry.keys())


def is_conversation_handler(func) -> bool:
    trigger_lazy_state_registrations()
    from telegram_dsl.internal.handlers.map import get_handler

    try:
        handler = get_handler(func)
    except ValueError:
        return False
    for group in _state_registry.values():
        for handlers in group.values():
            if handler in handlers:
                return True
    return False
