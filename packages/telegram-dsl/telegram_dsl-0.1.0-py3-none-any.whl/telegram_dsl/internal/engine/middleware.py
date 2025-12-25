import inspect

from telegram_dsl.internal.middleware.hooks import get_global_middleware, get_middleware
from telegram_dsl.framework.payloads import Payload


def _extract_args(update, context):
    message = getattr(update, "effective_message", None)
    if message:
        text = getattr(message, "text", None) or getattr(message, "caption", None)
        entities = getattr(message, "entities", None) or []
        ctx_args = (
            " ".join(getattr(context, "args", []) or []) if context is not None else ""
        )
        if (
            ctx_args
            and text
            and text[:1] in {"/", "!"}
            and text.strip().endswith(ctx_args)
        ):
            return ctx_args
        for entity in entities:
            if (
                getattr(entity, "type", None) == "bot_command"
                and getattr(entity, "offset", 0) == 0
            ):
                if context is not None and hasattr(context, "args"):
                    return " ".join(getattr(context, "args") or [])
                break
        for entity in entities:
            if getattr(entity, "type", None) == "bot_command":
                offset = getattr(entity, "offset", 0)
                length = getattr(entity, "length", 0)
                if text and offset == 0:
                    remainder = text[length:].strip()
                    return remainder
        return text
    callback = getattr(update, "callback_query", None)
    if callback:
        return callback.data
    inline = getattr(update, "inline_query", None)
    if inline:
        return inline.query
    chosen = getattr(update, "chosen_inline_result", None)
    if chosen:
        return getattr(chosen, "query", None) or getattr(chosen, "result_id", None)
    return None


async def apply_middleware_stack(func, update, context):
    stack = []
    stack.extend(get_global_middleware())
    stack.extend(get_middleware(func))

    async def final_handler(update, context):
        extracted_args = _extract_args(update, context)
        user = update.effective_user
        return await _call_handler(func, extracted_args, user, update, context)

    async def call_chain(index):
        if index >= len(stack):
            return await final_handler(update, context)
        middleware = stack[index]

        async def next_middleware(u, c):
            return await call_chain(index + 1)

        return await middleware(update, context, next_middleware)

    return await call_chain(0)


async def _call_handler(func, args, user, update, context):
    params = list(inspect.signature(func).parameters.values())
    values = [args, user]
    names = {p.name for p in params}
    if "payload" in names:
        values.append(Payload(update, context))
    if len(params) >= 3 or "update" in names:
        values.append(update)
    if len(params) >= 4 or "context" in names:
        values.append(context)
    return await func(*values[: len(params)])
