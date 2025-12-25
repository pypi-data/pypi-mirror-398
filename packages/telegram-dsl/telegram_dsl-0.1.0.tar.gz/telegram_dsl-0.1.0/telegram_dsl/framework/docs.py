from telegram_dsl.internal.inspect import list_commands, list_handlers


def generate_reference():
    return {
        "commands": list_commands(),
        "handlers": list_handlers(),
    }
