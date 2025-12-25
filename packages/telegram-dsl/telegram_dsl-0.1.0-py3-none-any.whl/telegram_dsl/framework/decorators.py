import functools
import warnings
from telegram_dsl.internal.handlers.metadata import build_metadata
from telegram_dsl.internal.handlers.map import add_handler_entry
from telegram_dsl.internal.constants import RESPONSE_TYPE
from telegram_dsl.internal.engine.rendering import render_response, infer_response_type
from telegram_dsl.internal.engine.responders import respond
from telegram_dsl.internal.engine.middleware import apply_middleware_stack
from telegram_dsl.internal.handlers.states import is_conversation_handler
from telegram_dsl.framework.outputs import ConversationResult


def _async_handler_wrapper(func):
    @functools.wraps(func)
    async def _wrapper(update, context):
        print(
            f"[WRAPPER] handler wrapper executing for id={id(func)} name={func.__name__}"
        )
        result = await apply_middleware_stack(func, update, context)
        if is_conversation_handler(func):
            if not isinstance(result, ConversationResult):
                raise ValueError(
                    f"Conversation handler '{func.__name__}' must return ConversationResult(message, next_state)"
                )
            if isinstance(result.message, str):
                raise ValueError(
                    f"Conversation handler '{func.__name__}' must use outputs.text(...) for message text"
                )
            raw_output, next_state = result.message, result.next_state
        else:
            if isinstance(result, ConversationResult):
                raw_output, next_state = result.message, result.next_state
            else:
                if isinstance(result, str):
                    raise ValueError(
                        f"Handler '{func.__name__}' must return outputs.text(...) instead of a raw string"
                    )
                raw_output, next_state = result, None
        rendered = await render_response(raw_output)
        response_type = infer_response_type(rendered) or RESPONSE_TYPE.TEXT
        await respond(update, context, response_type, rendered)
        callback = getattr(update, "callback_query", None)
        if callback and getattr(func, "__telegram_dsl_auto_hide_buttons__", False):
            try:
                await callback.answer()
            except Exception:
                pass
            try:
                message = getattr(callback, "message", None)
                if message and hasattr(message, "edit_reply_markup"):
                    await message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass
        print(f"[WRAPPER] Returning next_state={next_state} from {func.__name__}")
        return next_state

    return _wrapper


def register_handler(handler_cls, *handler_args, **handler_kwargs):
    def decorator_func(func):
        callback = _async_handler_wrapper(func)
        setattr(func, "__wrapped_handler__", callback)

        meta_keys = {"add_to_commands", "group", "tags", "scope", "auto_hide_buttons"}
        meta = {k: handler_kwargs.pop(k) for k in meta_keys if k in handler_kwargs}
        if handler_cls.__name__ == "CallbackQueryHandler":
            setattr(
                func,
                "__telegram_dsl_auto_hide_buttons__",
                meta.get("auto_hide_buttons", True),
            )
        args = handler_args
        if handler_cls.__name__ != "ConversationHandler":
            if _callback_first(handler_cls.__name__):
                args = (callback,) + handler_args
            else:
                args = handler_args + (callback,)

        if handler_cls.__name__ == "ConversationHandler":
            try:
                from telegram.warnings import PTBUserWarning
            except Exception:  # pragma: no cover
                PTBUserWarning = UserWarning
            with warnings.catch_warnings():
                # PTB emits PTBUserWarning for ConversationHandler per_* settings. We compute
                # sane defaults in telegram_dsl (and validate overlaps ourselves), so these
                # warnings are noisy for framework users.
                warnings.simplefilter("ignore", category=PTBUserWarning)
                instance = handler_cls(*args, **handler_kwargs)
        else:
            instance = handler_cls(*args, **handler_kwargs)
        metadata = build_metadata(
            func,
            handler_cls,
            add_to_commands=meta.get("add_to_commands", False),
            group=meta.get("group"),
            tags=meta.get("tags", []),
            scope=meta.get("scope"),
        )
        add_handler_entry(func, callback, instance, metadata)
        return callback if handler_cls.__name__ != "ConversationHandler" else func

    return decorator_func


def _callback_first(handler_name: str) -> bool:
    return handler_name in {
        "CallbackQueryHandler",
        "InlineQueryHandler",
        "ChosenInlineResultHandler",
        "ChatMemberHandler",
        "MessageReactionHandler",
        "BusinessConnectionHandler",
        "BusinessMessagesDeletedHandler",
        "ChatBoostHandler",
        "ChatJoinRequestHandler",
        "PaidMediaPurchasedHandler",
        "PollHandler",
        "PollAnswerHandler",
        "PreCheckoutQueryHandler",
        "ShippingQueryHandler",
    }
