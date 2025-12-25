import inspect

from telegram_dsl.internal.responses.matchers import get_renderer
from telegram_dsl.internal.constants import RESPONSE_TYPE


def infer_response_type(content):
    entry = get_renderer(content)
    if entry:
        return entry["response_type"]

    if isinstance(content, str):
        return RESPONSE_TYPE.TEXT

    print(f"[WARN] Could not infer response type for: {repr(content)}")
    return RESPONSE_TYPE.TEXT  # fallback default


async def render_response(content):
    entry = get_renderer(content)
    if entry:
        result = entry["func"](content)
        if inspect.isawaitable(result):
            return await result
        return result
    return str(content)
