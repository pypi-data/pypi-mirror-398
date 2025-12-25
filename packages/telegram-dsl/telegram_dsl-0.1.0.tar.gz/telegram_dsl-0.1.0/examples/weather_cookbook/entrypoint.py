import os
import signal
import logging
import traceback
import asyncio

from telegram_dsl.app import build_app


def _require_token() -> str:
    token = os.getenv("TELEGRAM_TOKEN")
    if token:
        return token
    raise SystemExit(
        "\n".join(
            [
                "Missing TELEGRAM_TOKEN.",
                "Set it in `dockerfiles/environments/secret.env` (Docker) or export it in your shell.",
                "Example: TELEGRAM_TOKEN=123456:ABCDEF...",
            ]
        )
    )


async def _run() -> None:
    token = _require_token()

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    print(f"[ENTRYPOINT] TELEGRAM_TOKEN length={len(token)}")
    app = build_app(token=token, debug=True)

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _request_stop(signum: int) -> None:
        print(f"[ENTRYPOINT] Received signal: {signum}")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _request_stop, sig)
        except Exception:
            try:
                signal.signal(
                    sig,
                    lambda signum, _frame: loop.call_soon_threadsafe(
                        _request_stop, signum
                    ),
                )
            except Exception:
                pass

    print("[ENTRYPOINT] Starting polling...")
    await app.initialize()
    try:
        if callable(getattr(app, "post_init", None)):
            maybe = app.post_init(app)
            if asyncio.iscoroutine(maybe):
                await maybe
        await app.start()
        await app.updater.start_polling()
        await stop_event.wait()
    finally:
        try:
            await app.updater.stop()
        except Exception:
            pass
        try:
            await app.stop()
        except Exception:
            pass
        try:
            await app.shutdown()
        except Exception:
            pass
        try:
            if callable(getattr(app, "post_shutdown", None)):
                maybe = app.post_shutdown(app)
                if asyncio.iscoroutine(maybe):
                    await maybe
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(_run())
    except Exception as exc:
        print("[ENTRYPOINT] Polling crashed:", repr(exc))
        traceback.print_exception(type(exc), exc, exc.__traceback__)
        raise
    finally:
        print("[ENTRYPOINT] Polling exited.")
