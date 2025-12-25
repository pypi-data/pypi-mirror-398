from telegram import (
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaDocument,
    InputFile,
)
from telegram_dsl.internal.responses.matchers import register_renderer
from telegram_dsl.internal.constants import RESPONSE_TYPE
from telegram_dsl.framework.actions import Action, ActionGroup
from telegram_dsl.framework.outputs import Response


@register_renderer(request_type=str, response_type=RESPONSE_TYPE.TEXT)
def render_string(content):
    return content


@register_renderer(request_type=dict, response_type=RESPONSE_TYPE.TEXT)
def render_dict(content):
    return "\n".join(f"{k}: {v}" for k, v in content.items())


@register_renderer(request_type=InlineKeyboardMarkup, response_type=RESPONSE_TYPE.TEXT)
def render_markup(content):
    return {"text": "Choose an option:", "reply_markup": content}


@register_renderer(request_type=InputFile, response_type=RESPONSE_TYPE.PHOTO)
def render_photo(content):
    return content


@register_renderer(request_type=InputMediaPhoto, response_type=RESPONSE_TYPE.PHOTO)
def render_input_photo(content):
    return content


@register_renderer(
    request_type=InputMediaDocument, response_type=RESPONSE_TYPE.DOCUMENT
)
def render_input_doc(content):
    return content


@register_renderer(request_type=list, response_type=RESPONSE_TYPE.TEXT)
def render_list(content):
    return "\n".join(map(str, content))


@register_renderer(request_type=Exception, response_type=RESPONSE_TYPE.TEXT)
def render_error(content):
    return f"Error: {content}"


@register_renderer(request_type=type(None), response_type=RESPONSE_TYPE.NONE)
def render_none(content):
    return "No content."


@register_renderer(request_type=bytes, response_type=RESPONSE_TYPE.DOCUMENT)
def render_bytes(content):
    return InputFile(content, filename="file.bin")


@register_renderer(request_type=int, response_type=RESPONSE_TYPE.TEXT)
def render_number(content):
    return str(content)


@register_renderer(request_type=Action, response_type=RESPONSE_TYPE.ACTION)
def render_action(content):
    return content


@register_renderer(request_type=ActionGroup, response_type=RESPONSE_TYPE.ACTION)
def render_action_group(content):
    return content


@register_renderer(request_type=Response, response_type=RESPONSE_TYPE.ACTION)
def render_response_model(content):
    return Action(content.method, content.action_kwargs())
