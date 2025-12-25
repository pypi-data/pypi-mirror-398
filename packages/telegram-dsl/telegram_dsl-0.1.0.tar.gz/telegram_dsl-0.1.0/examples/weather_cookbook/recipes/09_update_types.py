from telegram_dsl.framework import outputs
from telegram_dsl.framework.handlers import (
    edited_message_handler,
    channel_post_handler,
    edited_channel_post_handler,
    business_message_handler,
    edited_business_message_handler,
    business_connection_handler,
    business_messages_deleted_handler,
    chat_join_request_handler,
    chat_boost_handler,
    my_chat_member_handler,
    chat_member_handler,
    any_chat_member_handler,
    message_reaction_handler,
    message_reaction_updated_handler,
    message_reaction_count_handler,
    paid_media_purchased_handler,
    poll_handler,
    poll_answer_handler,
    shipping_query_handler,
    pre_checkout_query_handler,
)


@edited_message_handler()
async def on_edited(args, user):
    return outputs.text("Edited message received.")


@channel_post_handler()
async def on_channel_post(args, user):
    return outputs.text("Channel post received.")


@edited_channel_post_handler()
async def on_edited_channel_post(args, user):
    return outputs.text("Edited channel post received.")


@business_message_handler()
async def on_business_message(args, user):
    return outputs.none()


@edited_business_message_handler()
async def on_business_message_edited(args, user):
    return outputs.none()


@business_connection_handler()
async def on_business_connection(args, user):
    return outputs.none()


@business_messages_deleted_handler()
async def on_business_messages_deleted(args, user):
    return outputs.none()


@chat_join_request_handler()
async def on_join_request(args, user):
    return outputs.text("Join request received.")


@chat_boost_handler()
async def on_chat_boost(args, user):
    return outputs.text("Chat boost received.")


@my_chat_member_handler()
async def on_my_chat_member(args, user):
    return outputs.text("Bot membership updated.")


@chat_member_handler()
async def on_chat_member(args, user):
    return outputs.text("Member update received.")


@any_chat_member_handler()
async def on_any_chat_member(args, user):
    return outputs.text("Any member update received.")


@message_reaction_handler()
async def on_reaction(args, user):
    return outputs.none()


@message_reaction_updated_handler()
async def on_reaction_updated(args, user):
    return outputs.none()


@message_reaction_count_handler()
async def on_reaction_count(args, user):
    return outputs.none()


@paid_media_purchased_handler()
async def on_paid_media(args, user):
    return outputs.none()


@poll_handler()
async def on_poll(args, user):
    return outputs.none()


@poll_answer_handler()
async def on_poll_answer(args, user):
    return outputs.none()


@shipping_query_handler()
async def on_shipping_query(args, user, update):
    return outputs.answer_shipping_query(
        shipping_query_id=update.shipping_query.id,
        ok=False,
        error_message="Shipping not supported in this demo.",
    )


@pre_checkout_query_handler()
async def on_pre_checkout_query(args, user, update):
    return outputs.answer_pre_checkout_query(
        pre_checkout_query_id=update.pre_checkout_query.id,
        ok=False,
        error_message="Payments not enabled in this demo.",
    )
