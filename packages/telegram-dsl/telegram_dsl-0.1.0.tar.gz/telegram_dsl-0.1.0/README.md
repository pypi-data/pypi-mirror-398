# telegram-dsl

Lightweight DSL on top of python-telegram-bot (PTB) that lets you build bots by
registering handlers with simple decorators and returning explicit outputs.

## Quick start

```python
import os

from telegram_dsl.app import build_app
from telegram_dsl.framework.handlers import command_handler
from telegram_dsl.framework import outputs

# When a user sends /start, the bot replies with a welcome message.
@command_handler(add_to_commands=True)
async def start(args, user):
    return outputs.text("Hello! Try /help.")

if __name__ == "__main__":
    app = build_app(token=os.getenv("TELEGRAM_TOKEN"), debug=True)
    app.run_polling()
```

`build_app` auto-loads the caller package (and subpackages) so handlers,
middleware, lifecycle hooks, and error handlers are discovered.

## How it works

- You decorate async functions with handlers like `@command_handler`, `@text_handler`, `@buttons_handler`, etc.
- Importing those modules triggers the decorators, which register the handlers in the framework registry.
- `build_app(...)` is your entrypoint: it builds a PTB `Application`, auto-imports (autoloads) your package so all decorators run, then adds the registered handlers to the app.
- When you run the app (e.g. `app.run_polling()`), PTB routes incoming updates (messages, button clicks, …) to the first matching registered handler.
- During startup, the framework validates that registered handlers don’t overlap in ambiguous ways (e.g. two handlers that would both match the same update). If a conflict is found, startup fails with a clear error so you can tighten your rules.

## Decorators overview

Decorators fall into a few categories. In general, you:
- import a decorator
- apply it to an `async def` function
- return an `outputs.*` result from that function

Outputs define what the bot sends back to the user. Common outputs include:
- `outputs.text(...)` for a text message
- `outputs.buttons(...)` for a text message with inline buttons
- `outputs.photo(...)`, `outputs.video(...)`, `outputs.audio(...)`, `outputs.document(...)` for media
- `outputs.location(...)`, `outputs.venue(...)`, `outputs.contact(...)` for structured messages
- `outputs.answer_inline_query(...)`, `outputs.answer_callback_query(...)` for Telegram “answer” flows
- `outputs.none()` to send nothing

| Category | What it’s for | Decorators (examples) | How to use (in general) | Example file |
| --- | --- | --- | --- | --- |
| Command handlers | Handle `/commands` (Telegram messages starting with `/`). | `@command_handler`, `@unknown_command_handler`, `@any_command`, `@prefix_handler`, `@string_command_handler`, `@string_regex_handler` | Decorate an async function; validate `args` if required; return `outputs.text(...)` (or other outputs). | `examples/weather_cookbook/recipes/00_basics.py` |
| Text/media handlers | Handle non-command messages (text and media). | `@text_handler`, `@photo_handler`, `@video_handler`, `@audio_handler`, `@document_handler`, `@location_handler`, `@animation_handler`, `@sticker_handler`, `@customfilter_text_handler` | Pick the handler that matches the input type; use `payload` when you need file IDs/metadata; return an `outputs.*` response. | `examples/weather_cookbook/recipes/01_messages.py` |
| Buttons (callback queries) | Handle inline button presses from `outputs.buttons(...)`. | `@buttons_handler` | Use `pattern=...` to match specific buttons; handler receives callback data in `args`/`payload`; return an output; buttons can auto-hide. | `examples/weather_cookbook/recipes/02_buttons.py` |
| Conversations (stateful flows) | Build multi-step flows with state. | `@conversation_handler`, `@register_entry_point`, `@register_state`, `@register_fallback` | Define an entry point and states; each state is a handler; return `outputs.conversation(message, next_state)` to move through the flow. | `examples/weather_cookbook/recipes/04_conversations.py` |
| Inline mode | Support Telegram inline mode “result lists”. | `@inline_query_handler`, `@chosen_inline_result_handler` | Answer inline queries via `outputs.answer_inline_query(...)`; handle chosen results if needed. | `examples/weather_cookbook/recipes/03_inline_queries.py` |
| Update-type handlers | React to specific update types (edits, polls, members, etc.). | `@edited_message_handler`, `@poll_handler`, `@chat_member_handler`, `@pre_checkout_query_handler`, … | Use when you need a specific Telegram event; access the raw `update` when required; return outputs or `outputs.none()`. | `examples/weather_cookbook/recipes/09_update_types.py` |
| Middleware | Run code before/around handlers. | `@register_global_middleware`, `@register_middleware` | Middleware gets `(update, context, next)`; call `await next(...)` to continue; can modify/replace the handler’s output. | `examples/weather_cookbook/recipes/05_middleware.py` |
| Lifecycle hooks | Run code at startup/shutdown. | `@register_lifecycle` | Register functions to run when the app starts/stops (e.g. scheduling, setup/teardown). | `examples/weather_cookbook/recipes/06_lifecycle.py` |
| Error handling | Catch and respond to exceptions. | `@register_error_handler` | Register an async function to handle errors; can log and reply with a user-friendly message. | `examples/weather_cookbook/recipes/07_errors.py` |

## Make commands

This repo is set up to run everything via Docker using `make`:

Release notes:
- Releases are triggered locally via `make release VERSION=X.Y.Z` and must be run from the `main` branch with a clean working tree.
- `VERSION` must be newer than the latest existing `v*` tag (tags are the source of truth for the package version via `setuptools-scm`).

| Command | What it does |
| --- | --- |
| `make docker-build` | Build the Docker image. |
| `make cookbook-up` | Run the weather cookbook bot (builds if needed). |
| `make docker-down` | Stop and remove containers. |
| `make docker-test` | Run the test suite inside Docker. |
| `make pkg` | Clean (optional), build, and validate package artifacts into `dist/` (`make pkg CLEAN=0` skips cleaning). |
| `make release VERSION=0.1.0` | Create and push annotated tag `v0.1.0`; GitHub Actions runs tests, builds artifacts, creates a GitHub Release, and publishes to PyPI. |
