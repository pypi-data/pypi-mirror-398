import sys

import pytest

from telegram import BotCommand

from telegram_dsl import app as dsl_app
from telegram_dsl.internal.lifecycle import register_lifecycle, LIFECYCLE
from telegram_dsl.framework.handlers import command_handler
from telegram_dsl.internal.handlers import map as handler_map


class DummyBot:
    def __init__(self):
        self.commands = None

    async def set_my_commands(self, commands):
        self.commands = commands


class DummyApp:
    def __init__(self):
        self.bot = DummyBot()
        self.handlers = []
        self.error_handlers = []

    def add_handler(self, handler):
        self.handlers.append(handler)

    def add_error_handler(self, handler):
        self.error_handlers.append(handler)


@pytest.mark.asyncio
async def test_initialize_app_registers_commands(tmp_path, clean_handler_registry):
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "commands.py").write_text(
        "from telegram_dsl.framework.handlers import command_handler\n"
        "@command_handler(add_to_commands=True)\n"
        "async def hello(args, user):\n"
        "    return 'ok'\n"
    )
    (pkg_dir / "runner.py").write_text(
        "from telegram_dsl import app as dsl_app\n"
        "async def run(app):\n"
        "    await dsl_app.initialize_app(app)\n"
    )

    sys.path.insert(0, str(tmp_path))
    try:
        import pkg.runner

        app = DummyApp()
        await pkg.runner.run(app)
        assert isinstance(app.bot.commands[0], BotCommand)
        assert app.handlers
    finally:
        sys.path.remove(str(tmp_path))


@pytest.mark.asyncio
async def test_initialize_app_validation_error_exits(tmp_path, clean_handler_registry):
    pkg_dir = tmp_path / "pkg2"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("")
    (pkg_dir / "bad_handlers.py").write_text(
        "from telegram.ext import MessageHandler, filters\n"
        "from telegram_dsl.framework.decorators import register_handler\n"
        "@register_handler(MessageHandler, filters.TEXT)\n"
        "async def bad(args, user):\n"
        "    return None\n"
    )
    (pkg_dir / "runner.py").write_text(
        "from telegram_dsl import app as dsl_app\n"
        "async def run(app):\n"
        "    await dsl_app.initialize_app(app)\n"
    )

    sys.path.insert(0, str(tmp_path))
    try:
        import pkg2.runner

        app = DummyApp()
        with pytest.raises(SystemExit) as exc:
            await pkg2.runner.run(app)
        assert "validation" in str(exc.value).lower()
    finally:
        sys.path.remove(str(tmp_path))


@pytest.mark.asyncio
async def test_lifecycle_hooks(clean_handler_registry):
    calls = []

    @register_lifecycle(LIFECYCLE.STARTUP)
    async def on_start():
        calls.append("start")

    @register_lifecycle(LIFECYCLE.SHUTDOWN)
    async def on_stop():
        calls.append("stop")

    app = DummyApp()
    await dsl_app.initialize_app(app)
    await dsl_app.shutdown_app()

    assert calls == ["start", "stop"]
