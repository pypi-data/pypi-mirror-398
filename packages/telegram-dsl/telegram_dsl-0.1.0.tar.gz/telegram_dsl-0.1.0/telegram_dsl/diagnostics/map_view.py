def debug_handlers(application):
    print("\n🔍 [DEBUG] Registered Handlers in Dispatcher:\n")

    for group_id, handlers in application.handlers.items():
        print(f"📦 Group {group_id}:")
        for i, handler in enumerate(handlers):
            kind = handler.__class__.__name__
            callback = getattr(handler, "callback", None)
            cb_name = callback.__name__ if callback else "N/A"
            cb_id = id(callback) if callback else "N/A"
            print(f"  {i}. {kind}")
            print(f"     → callback: {cb_name} (id={cb_id})")
            if kind == "ConversationHandler":
                print(f"     ↪ entry_points:")
                for ep in handler.entry_points:
                    print(f"        - {ep}")
                print(f"     ↪ states:")
                for state_id, state_handlers in handler.states.items():
                    print(f"        - state {state_id}:")
                    for h in state_handlers:
                        h_cb = getattr(h, "callback", None)
                        print(
                            f"            • {h} (cb={getattr(h_cb, '__name__', 'N/A')}, id={id(h_cb) if h_cb else 'N/A'})"
                        )
                print(f"     ↪ fallbacks:")
                for fb in handler.fallbacks:
                    print(f"        - {fb}")


def dump_state_handlers(states: dict):
    for state_id, handlers in states.items():
        print(f"[STATE DUMP] State {state_id}")
        for h in handlers:
            print(f"  -> Handler: {h}")
            print(f"     Filters: {getattr(h, 'filters', 'N/A')}")
