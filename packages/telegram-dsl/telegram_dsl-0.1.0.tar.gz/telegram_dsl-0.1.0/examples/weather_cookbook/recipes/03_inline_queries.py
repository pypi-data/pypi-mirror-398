from telegram import InlineQueryResultArticle, InputTextMessageContent

from telegram_dsl.framework.handlers import (
    command_handler,
    inline_query_handler,
    chosen_inline_result_handler,
)
from telegram_dsl.framework import outputs
from examples.weather_cookbook.shared import weather_service


@command_handler(add_to_commands=True)
async def inline_hint(args, user):
    """Explain how to use inline mode for this bot."""
    return outputs.text("Type @YourBotName <city> in any chat.")


@inline_query_handler()
async def inline_query(args, user, payload):
    query = (payload.inline_query_text or "").strip()
    if not query:
        return outputs.answer_inline_query(
            results=[],
            cache_time=1,
            is_personal=True,
            switch_pm_text="Type a city name (e.g. Rome)",
            switch_pm_parameter="city",
        )
    if not weather_service.is_supported_city(query):
        examples = ", ".join(c.title() for c in weather_service.SUPPORTED_CITIES)
        results = [
            InlineQueryResultArticle(
                id="weather-unknown-city",
                title="Unknown city",
                description=f"Try: {examples}",
                input_message_content=InputTextMessageContent(
                    f"Unknown city. Try: {examples}"
                ),
            )
        ]
        return outputs.answer_inline_query(
            results=results, cache_time=1, is_personal=True
        )
    forecast = weather_service.get_forecast(query)
    if not forecast:
        return outputs.answer_inline_query(results=[], cache_time=1, is_personal=True)
    results = []
    for i, item in enumerate(forecast):
        title = f"{item['day']}: {item['summary']} {item['temp_c']}C"
        results.append(
            InlineQueryResultArticle(
                id=f"weather-{i}",
                title=title,
                input_message_content=InputTextMessageContent(
                    f"{query.title()} - {title}"
                ),
            )
        )
    return outputs.answer_inline_query(
        results=results,
        cache_time=1,
        is_personal=True,
    )


@chosen_inline_result_handler()
async def chosen_inline(args, user):
    return outputs.none()
