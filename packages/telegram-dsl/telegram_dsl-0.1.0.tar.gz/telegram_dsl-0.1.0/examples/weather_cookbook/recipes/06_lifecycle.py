from telegram_dsl.internal.lifecycle import register_lifecycle, LIFECYCLE


@register_lifecycle(LIFECYCLE.STARTUP)
async def on_startup():
    print("[LIFECYCLE] Weather cookbook starting")


@register_lifecycle(LIFECYCLE.SHUTDOWN)
async def on_shutdown():
    print("[LIFECYCLE] Weather cookbook stopping")
