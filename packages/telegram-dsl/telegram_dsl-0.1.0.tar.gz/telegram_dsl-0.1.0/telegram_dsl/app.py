import inspect
import sys
import sysconfig
from pathlib import Path

from telegram import BotCommand
from telegram.ext import Application, ApplicationBuilder

from telegram_dsl.internal.bootstrap import autoload_recursive
from telegram_dsl.diagnostics.map_view import debug_handlers
from telegram_dsl.internal.errors import get_error_handlers
from telegram_dsl.internal.handlers.map import get_all_metadata
from telegram_dsl.internal.handlers.states import (
    get_state_handlers,
    list_conversation_groups,
)
from telegram_dsl.internal.handlers.validation import validate_global_registry
from telegram_dsl.internal.lifecycle import get_hooks, LIFECYCLE


_initialized_app_ids: set[int] = set()


def _infer_load_packages():
    stdlib = Path(sysconfig.get_paths()["stdlib"]).resolve()
    platstdlib = Path(sysconfig.get_paths().get("platstdlib", stdlib)).resolve()
    purelib = Path(sysconfig.get_paths().get("purelib", stdlib)).resolve()
    platlib = Path(sysconfig.get_paths().get("platlib", stdlib)).resolve()

    def _is_user_module(module):
        module_file = getattr(module, "__file__", None)
        if not module_file:
            return False
        path = Path(module_file).resolve()
        for root in (stdlib, platstdlib, purelib, platlib):
            try:
                path.relative_to(root)
                return False
            except ValueError:
                continue
        return True

    frame = inspect.currentframe()
    if not frame:
        return []
    frame = frame.f_back
    while frame:
        module = inspect.getmodule(frame)
        if module and module.__name__ != __name__ and _is_user_module(module):
            package = module.__package__
            if not package and getattr(module, "__spec__", None):
                package = module.__spec__.parent
            if package:
                return [package]
            if module.__name__ != "__main__":
                return [module.__name__]
            break
        frame = frame.f_back
    main_module = sys.modules.get("__main__")
    if main_module and _is_user_module(main_module):
        package = main_module.__package__
        if not package and getattr(main_module, "__spec__", None):
            package = main_module.__spec__.parent
        if package:
            return [package]
    return []


async def initialize_app(app: Application):
    # PTB's Application is slot-based (no __dict__), so we can't attach attributes.
    # Track initialization per-process using the object's id.
    if id(app) in _initialized_app_ids:
        return
    _initialized_app_ids.add(id(app))

    # Ensure core registries are populated.
    import telegram_dsl.framework.rendering  # noqa: F401
    import telegram_dsl.framework.responses  # noqa: F401

    load_packages = _infer_load_packages()
    if not load_packages:
        raise ValueError(
            "Could not infer load_packages; run build_app from your app package."
        )

    for package in load_packages:
        try:
            autoload_recursive(package)
        except ValueError as exc:
            raise SystemExit(
                "\n".join(
                    [
                        "[telegram_dsl] Handler registration/validation failed during autoload.",
                        str(exc),
                        "",
                        "Fix the conflict described above and restart the bot.",
                    ]
                )
            ) from None

    error_handlers = get_error_handlers()
    if not error_handlers:
        from telegram_dsl.framework.errors import default_error_handler

        error_handlers = [default_error_handler]
    for handler in error_handlers:
        app.add_error_handler(handler)

    metadata = get_all_metadata()
    commands = [
        BotCommand(meta["name"], meta.get("doc") or "No description")
        for meta in metadata
        if meta.get("add_to_commands")
    ]
    await app.bot.set_my_commands(commands)

    excluded_ids = {
        id(handler)
        for group in list_conversation_groups()
        for handlers in get_state_handlers(group).values()
        for handler in handlers
    }

    to_add = []
    for meta in metadata:
        handler = meta["handler_instance"]
        if id(handler) not in excluded_ids:
            to_add.append((handler, meta))

    try:
        validate_global_registry(to_add)
    except ValueError as exc:
        raise SystemExit(
            "\n".join(
                [
                    "[telegram_dsl] Handler registration/validation failed during startup.",
                    str(exc),
                    "",
                    "Fix the conflict described above and restart the bot.",
                ]
            )
        ) from None

    # Ensure conversations are evaluated before generic handlers so active stateful flows
    # don't get intercepted by broad MessageHandlers.
    for handler, _meta in sorted(
        to_add,
        key=lambda item: (
            0 if item[0].__class__.__name__ == "ConversationHandler" else 1
        ),
    ):
        app.add_handler(handler)

    for hook in get_hooks(LIFECYCLE.STARTUP):
        await hook()


async def shutdown_app():
    for hook in get_hooks(LIFECYCLE.SHUTDOWN):
        await hook()


def build_app(*, token: str, debug: bool = False) -> Application:
    app = (
        ApplicationBuilder()
        .token(token)
        .post_init(lambda app: initialize_app(app))
        .post_shutdown(lambda app: shutdown_app())
        .build()
    )
    if debug:
        debug_handlers(app)
    print("Bot running...")
    return app
