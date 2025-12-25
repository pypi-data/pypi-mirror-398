from telegram_dsl.internal.responses.send import get_responder


async def respond(update, context, response_type, content):
    responder = get_responder(response_type)
    await responder(update, context, content)
