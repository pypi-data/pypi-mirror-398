def validate_conversation(group, entry_points, states):
    if not entry_points:
        raise ValueError(f"Conversation '{group}' has no entry points")
    if not states:
        raise ValueError(f"Conversation '{group}' has no states")
    if 0 in states:
        raise ValueError(f"Conversation '{group}' has entry state in states map")
    for state_id, handlers in states.items():
        if state_id is None:
            raise ValueError(f"Conversation '{group}' has invalid state id None")
        if not handlers:
            raise ValueError(
                f"Conversation '{group}' has empty handlers for state {state_id}"
            )
        if any(h is None for h in handlers):
            raise ValueError(
                f"Conversation '{group}' has None handler for state {state_id}"
            )
        handler_types = [handler.__class__.__name__ for handler in handlers]
        non_message_types = [t for t in handler_types if t != "MessageHandler"]
        duplicates = {t for t in non_message_types if non_message_types.count(t) > 1}
        if duplicates:
            raise ValueError(
                "\n".join(
                    [
                        f"Conversation validation error in group '{group}', state {state_id}.",
                        "Rule: for a single state, non-message handler types must be unique.",
                        f"Conflict: multiple handlers of type {sorted(duplicates)} were registered for the same state.",
                        "Fix: remove one of the duplicates, or move it to a different state_id.",
                    ]
                )
            )
        filter_signatures = []
        filters_list = []
        for handler in handlers:
            if handler.__class__.__name__ != "MessageHandler":
                continue
            filters = getattr(handler, "filters", None)
            if filters is not None:
                filter_signatures.append(repr(filters))
                filters_list.append(filters)
        overlaps = {f for f in filter_signatures if filter_signatures.count(f) > 1}
        if overlaps:
            raise ValueError(
                "\n".join(
                    [
                        f"Conversation validation error in group '{group}', state {state_id}.",
                        "Rule: within the same state, multiple MessageHandlers must be mutually exclusive.",
                        f"Conflict: the same filter was registered more than once: {sorted(overlaps)}",
                        "Fix: use a different filter (or add extra constraints) so only one handler can match.",
                    ]
                )
            )
        if _filters_overlap(filters_list):
            raise ValueError(
                "\n".join(
                    [
                        f"Conversation validation error in group '{group}', state {state_id}.",
                        "Rule: within the same state, multiple MessageHandlers must be mutually exclusive.",
                        "Conflict: two or more MessageHandler filters can match the same incoming update.",
                        "Why this is a problem: Telegram would route the same user message ambiguously.",
                        "Fix: tighten filters (e.g. text vs photo, regex patterns, etc.) so each message matches exactly one handler.",
                    ]
                )
            )


def _filters_overlap(filters_list):
    if len(filters_list) < 2:
        return False

    from telegram import Bot, Update

    bot = Bot(token="123:TEST")

    def _update(payload):
        return Update.de_json(payload, bot)

    samples = [
        _update(
            {
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "text": "hi",
                    "entities": [],
                },
            }
        ),
        _update(
            {
                "update_id": 2,
                "message": {
                    "message_id": 2,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "text": "/start",
                    "entities": [{"type": "bot_command", "offset": 0, "length": 6}],
                },
            }
        ),
        _update(
            {
                "update_id": 3,
                "message": {
                    "message_id": 3,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "photo": [
                        {
                            "file_id": "x",
                            "file_unique_id": "ux",
                            "width": 1,
                            "height": 1,
                        }
                    ],
                    "caption": None,
                },
            }
        ),
        _update(
            {
                "update_id": 4,
                "message": {
                    "message_id": 4,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "photo": [
                        {
                            "file_id": "x",
                            "file_unique_id": "ux",
                            "width": 1,
                            "height": 1,
                        }
                    ],
                    "caption": "cap",
                },
            }
        ),
        _update(
            {
                "update_id": 5,
                "message": {
                    "message_id": 5,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "document": {"file_id": "x", "file_unique_id": "ux"},
                    "caption": None,
                },
            }
        ),
        _update(
            {
                "update_id": 6,
                "message": {
                    "message_id": 6,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "video": {
                        "file_id": "x",
                        "file_unique_id": "ux",
                        "width": 1,
                        "height": 1,
                        "duration": 1,
                    },
                    "caption": None,
                },
            }
        ),
        _update(
            {
                "update_id": 7,
                "message": {
                    "message_id": 7,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "audio": {
                        "file_id": "x",
                        "file_unique_id": "ux",
                        "duration": 1,
                    },
                    "caption": None,
                },
            }
        ),
        _update(
            {
                "update_id": 8,
                "message": {
                    "message_id": 8,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "voice": {
                        "file_id": "x",
                        "file_unique_id": "ux",
                        "duration": 1,
                    },
                },
            }
        ),
        _update(
            {
                "update_id": 9,
                "message": {
                    "message_id": 9,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "video_note": {
                        "file_id": "x",
                        "file_unique_id": "ux",
                        "length": 1,
                        "duration": 1,
                    },
                },
            }
        ),
    ]

    for i, left in enumerate(filters_list):
        for right in filters_list[i + 1 :]:
            for update in samples:
                try:
                    if _matches(left, update) and _matches(right, update):
                        return True
                except Exception:
                    continue
    return False


def validate_global_registry(to_add):
    """Validate that the set of handlers to add has no ambiguous overlaps."""
    handlers = [
        (handler, meta) for handler, meta in to_add if hasattr(handler, "check_update")
    ]
    if not handlers:
        return

    command_names = [
        meta.get("name")
        for _handler, meta in handlers
        if meta.get("handler_cls") == "CommandHandler" and meta.get("name")
    ]
    samples = _sample_updates(command_names=command_names)

    # Enforce: MessageHandlers that match plain text must not also match '/...'.
    # (A dedicated "unknown command" MessageHandler that *only* matches '/...' is OK.)
    slash_text = next(s for s in samples if s.update_id == 301)
    plain_text = next(s for s in samples if s.update_id == 304)
    for handler, meta in handlers:
        if handler.__class__.__name__ != "MessageHandler":
            continue
        try:
            matches_slash = bool(handler.check_update(slash_text))
            matches_plain = bool(handler.check_update(plain_text))
        except Exception:
            continue
        if matches_slash and matches_plain:
            raise ValueError(
                "\n".join(
                    [
                        "Handler validation error.",
                        "Rule: a MessageHandler that matches plain text must not also match '/...'.",
                        f"Conflict: '{meta.get('origin')}' can match both normal text and '/command ...'.",
                        "Why this is a problem: '/...' messages can be routed ambiguously between CommandHandlers and MessageHandlers.",
                        r"Fix: add `& ~filters.Regex(r'^/')` (or otherwise exclude '/...') to the MessageHandler filter.",
                    ]
                )
            )

    if len(handlers) < 2:
        return

    for i, (left, left_meta) in enumerate(handlers):
        for right, right_meta in handlers[i + 1 :]:
            overlap = _first_overlap_sample(left, right, samples)
            if overlap is None:
                continue
            raise ValueError(
                "\n".join(
                    [
                        "Handler validation error.",
                        "Rule: your bot must not have ambiguous handlers (the same update must not match multiple handlers).",
                        f"Conflict: '{left_meta.get('origin')}' overlaps with '{right_meta.get('origin')}'.",
                        f"Example: {overlap}",
                        "Fix: narrow one of the handlers so only one can match (regex constraints, different update types, different filters).",
                    ]
                )
            )


def _first_overlap_sample(left, right, samples):
    for sample in samples:
        try:
            l = left.check_update(sample)
            r = right.check_update(sample)
        except Exception:
            continue
        if l and r:
            return _describe_sample(sample)
    return None


def _describe_sample(update):
    msg = getattr(update, "effective_message", None) or getattr(update, "message", None)
    text = getattr(msg, "text", None) if msg else None
    kind = "message" if msg else "update"
    return f"{kind} text={text!r}"


def _sample_updates(*, command_names):
    from telegram import Bot, Update

    bot = Bot(token="123:TEST")

    def _u(payload):
        return Update.de_json(payload, bot)

    samples = [
        _u(
            {
                "update_id": 300,
                "message": {
                    "message_id": 300,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "text": "weather",
                    "entities": [],
                },
            }
        ),
        _u(
            {
                "update_id": 301,
                "message": {
                    "message_id": 301,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "text": "/weather Rome",
                    "entities": [],
                },
            }
        ),
        _u(
            {
                "update_id": 302,
                "message": {
                    "message_id": 302,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "text": "/weather Rome",
                    "entities": [{"type": "bot_command", "offset": 0, "length": 8}],
                },
            }
        ),
        _u(
            {
                "update_id": 303,
                "message": {
                    "message_id": 303,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "text": "temp Rome",
                    "entities": [],
                },
            }
        ),
        _u(
            {
                "update_id": 304,
                "message": {
                    "message_id": 304,
                    "date": 0,
                    "chat": {"id": 1, "type": "private"},
                    "from": {"id": 1, "is_bot": False, "first_name": "T"},
                    "text": "hello",
                    "entities": [],
                },
            }
        ),
    ]

    update_id = 320
    for name in sorted(set(command_names)):
        cmd = f"/{name}"
        samples.append(
            _u(
                {
                    "update_id": update_id,
                    "message": {
                        "message_id": update_id,
                        "date": 0,
                        "chat": {"id": 1, "type": "private"},
                        "from": {"id": 1, "is_bot": False, "first_name": "T"},
                        "text": f"{cmd} arg",
                        "entities": [
                            {
                                "type": "bot_command",
                                "offset": 0,
                                "length": len(cmd),
                            }
                        ],
                    },
                }
            )
        )
        update_id += 1

    return samples


def _matches(filter_obj, update):
    if hasattr(filter_obj, "check_update"):
        return filter_obj.check_update(update)
    return filter_obj(update)


__all__ = ["validate_conversation", "validate_global_registry"]
