from telegram_dsl.framework.handlers import command_handler
from telegram_dsl.framework import outputs
from telegram_dsl.framework.docs import generate_reference
from telegram_dsl.internal.inspect import list_commands, list_handlers


@command_handler(add_to_commands=True)
async def commands(args, user):
    """List registered commands."""
    cmds = list_commands()
    lines = [f"/{name} - {doc or 'No description'}" for name, doc in cmds]
    return outputs.long_text("\n".join(lines))


@command_handler(add_to_commands=True)
async def handlers(args, user):
    """List registered handlers."""
    items = list_handlers()
    lines = [f"{h['name']} ({h['origin']})" for h in items]
    return outputs.long_text("\n".join(lines))


@command_handler(add_to_commands=True)
async def reference(args, user):
    """Show counts of commands and handlers."""
    ref = generate_reference()
    return outputs.text(
        f"Commands: {len(ref['commands'])}\nHandlers: {len(ref['handlers'])}"
    )
