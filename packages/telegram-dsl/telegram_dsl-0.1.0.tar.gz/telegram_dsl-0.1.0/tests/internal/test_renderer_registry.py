from telegram_dsl.internal.responses import matchers


def test_register_renderer_and_get(restore_renderers):
    class C:
        pass

    @matchers.register_renderer(request_type=C, response_type="text")
    def render(content):
        return "ok"

    entry = matchers.get_renderer(C())
    assert entry["func"] is render
    assert entry["response_type"] == "text"
