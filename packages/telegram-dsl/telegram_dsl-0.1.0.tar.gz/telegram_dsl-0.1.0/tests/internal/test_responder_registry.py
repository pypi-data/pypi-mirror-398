from telegram_dsl.internal.responses import send


def test_register_responder_and_get(restore_responders):
    send._responder_entries.clear()

    @send.register_responder(match=lambda r: r == "x")
    async def responder(update, context, content):
        return "ok"

    func = send.get_responder("x")
    assert func is responder
    assert send.list_responders()
