import pytest

from telegram.ext import (
    BusinessConnectionHandler,
    BusinessMessagesDeletedHandler,
    ChatBoostHandler,
    ChatJoinRequestHandler,
    ChatMemberHandler,
    MessageReactionHandler,
    PaidMediaPurchasedHandler,
    PollAnswerHandler,
    PollHandler,
    PreCheckoutQueryHandler,
    ShippingQueryHandler,
    PrefixHandler,
    TypeHandler,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    ChosenInlineResultHandler,
)

from telegram_dsl.framework import handlers, outputs
from telegram_dsl.internal.handlers import map as handler_map


@pytest.mark.parametrize(
    "factory,expected",
    [
        (handlers.business_connection_handler, BusinessConnectionHandler),
        (handlers.business_messages_deleted_handler, BusinessMessagesDeletedHandler),
        (handlers.chat_boost_handler, ChatBoostHandler),
        (handlers.chat_join_request_handler, ChatJoinRequestHandler),
        (handlers.message_reaction_handler, MessageReactionHandler),
        (handlers.paid_media_purchased_handler, PaidMediaPurchasedHandler),
        (handlers.poll_handler, PollHandler),
        (handlers.poll_answer_handler, PollAnswerHandler),
        (handlers.shipping_query_handler, ShippingQueryHandler),
        (handlers.pre_checkout_query_handler, PreCheckoutQueryHandler),
    ],
)
def test_handler_factories(clean_handler_registry, factory, expected):
    @factory()
    async def fn(args, user):
        return outputs.text("ok")

    entry = handler_map._get_all_entries()[-1]
    assert entry["handler"].__class__ is expected


def test_chat_member_handlers(clean_handler_registry):
    @handlers.my_chat_member_handler()
    async def fn1(args, user):
        return outputs.text("ok")

    assert (
        handler_map._get_all_entries()[-1]["handler"].chat_member_types
        == ChatMemberHandler.MY_CHAT_MEMBER
    )

    @handlers.chat_member_handler()
    async def fn2(args, user):
        return outputs.text("ok")

    assert (
        handler_map._get_all_entries()[-1]["handler"].chat_member_types
        == ChatMemberHandler.CHAT_MEMBER
    )


def test_message_reaction_variants(clean_handler_registry):
    @handlers.message_reaction_updated_handler()
    async def fn1(args, user):
        return outputs.text("ok")

    assert (
        handler_map._get_all_entries()[-1]["handler"].message_reaction_types
        == MessageReactionHandler.MESSAGE_REACTION_UPDATED
    )

    @handlers.message_reaction_count_handler()
    async def fn2(args, user):
        return outputs.text("ok")

    assert (
        handler_map._get_all_entries()[-1]["handler"].message_reaction_types
        == MessageReactionHandler.MESSAGE_REACTION_COUNT_UPDATED
    )


def test_prefix_string_type_handlers(clean_handler_registry):
    @handlers.prefix_handler("/", "start")
    async def fn1(args, user):
        return outputs.text("ok")

    assert handler_map._get_all_entries()[-1]["handler"].__class__ is PrefixHandler

    @handlers.string_command_handler(["start"])
    async def fn2(args, user):
        return outputs.text("ok")

    assert handler_map._get_all_entries()[-1]["handler"].__class__ is MessageHandler

    @handlers.string_regex_handler(r"^/hello")
    async def fn3(args, user):
        return outputs.text("ok")

    assert handler_map._get_all_entries()[-1]["handler"].__class__ is MessageHandler

    @handlers.type_handler(dict)
    async def fn4(args, user):
        return outputs.text("ok")

    assert handler_map._get_all_entries()[-1]["handler"].__class__ is TypeHandler


def test_message_handler_variants(clean_handler_registry):
    factories = [
        handlers.text_handler,
        handlers.photo_handler,
        handlers.location_handler,
        handlers.video_handler,
        handlers.audio_handler,
        handlers.voice_handler,
        handlers.video_note_handler,
        handlers.document_handler,
        handlers.any_command,
        handlers.edited_message_handler,
        handlers.channel_post_handler,
        handlers.edited_channel_post_handler,
        handlers.business_message_handler,
        handlers.edited_business_message_handler,
    ]
    for factory in factories:

        @factory()
        async def fn(args, user):
            return outputs.text("ok")

        assert handler_map._get_all_entries()[-1]["handler"].__class__ is MessageHandler


def test_basic_handler_types(clean_handler_registry):
    @handlers.command_handler()
    async def cmd(args, user):
        return outputs.text("ok")

    assert handler_map._get_all_entries()[-1]["handler"].__class__ is CommandHandler

    @handlers.callback_handler()
    async def cb(args, user):
        return outputs.text("ok")

    assert (
        handler_map._get_all_entries()[-1]["handler"].__class__ is CallbackQueryHandler
    )

    @handlers.unknown_command_handler()
    async def unk(args, user):
        return outputs.text("ok")

    assert handler_map._get_all_entries()[-1]["handler"].__class__ is MessageHandler

    @handlers.inline_query_handler()
    async def iq(args, user):
        return outputs.text("ok")

    assert handler_map._get_all_entries()[-1]["handler"].__class__ is InlineQueryHandler

    @handlers.chosen_inline_result_handler()
    async def cr(args, user):
        return outputs.text("ok")

    assert (
        handler_map._get_all_entries()[-1]["handler"].__class__
        is ChosenInlineResultHandler
    )
