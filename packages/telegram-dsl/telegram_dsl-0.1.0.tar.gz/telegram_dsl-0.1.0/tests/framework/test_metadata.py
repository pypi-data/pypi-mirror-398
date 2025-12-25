from telegram_dsl.framework.handlers import command_handler
from telegram_dsl.framework import outputs
from telegram_dsl.internal.handlers import map as handler_map


def test_metadata_fields(clean_handler_registry):
    @command_handler(add_to_commands=True, group="g", tags=["t1"], scope="s")
    async def hello(args, user):
        """Doc"""
        return outputs.text("ok")

    meta = handler_map._get_all_entries()[-1]["meta"]
    assert meta["name"] == "hello"
    assert meta["doc"] == "Doc"
    assert meta["group"] == "g"
    assert meta["tags"] == ["t1"]
    assert meta["scope"] == "s"
    assert meta["add_to_commands"] is True
