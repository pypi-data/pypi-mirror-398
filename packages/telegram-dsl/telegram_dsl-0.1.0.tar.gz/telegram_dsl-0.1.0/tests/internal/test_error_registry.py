from telegram_dsl.internal import errors


def test_register_error_handler():
    errors.clear_error_handlers()

    @errors.register_error_handler
    async def handler(update, context):
        return None

    assert errors.get_error_handlers() == [handler]
