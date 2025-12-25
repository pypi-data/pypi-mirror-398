# Weather Cookbook (telegram_dsl examples)

This folder contains a working, weather-themed cookbook for every framework feature.
Each recipe registers real handlers you can trigger from Telegram.

## Run

The cookbook is designed to be run via Docker using `make` (from the repo root).

```bash
# Start the cookbook bot (builds image if needed)
make cookbook-up
```

Stop containers:

```bash
make docker-down
```

Run tests:

```bash
make docker-test
```

Environment:
- Create `dockerfiles/environments/secret.env` (not committed) and set `TELEGRAM_TOKEN=...`
- Optional: `PROVIDER_TOKEN` (for `/invoice`)
- Optional: `GAME_SHORT_NAME` (for `/game_button`, only meaningful if you have a real Telegram game)

## Recipes

| Recipe | What It Demonstrates | Things To Try (Telegram) |
| --- | --- | --- |
| `00_basics` | Commands, unknown commands, prefix + string matchers | `/start`, `/help`, `/ping`, `/weather Rome`, `/temp Rome`, `!forecast Zurich`, `weather`, `temp Rome` |
| `01_messages` | Text/media handlers and typed outputs | Send any normal text, send photo/video/audio/voice/document/video note, send sticker, send GIF |
| `02_buttons` | Inline buttons + callback handlers + other inline keyboard types | `/buttons`, `/url_button`, `/login_button`, `/web_app_button`, `/switch_inline`, `/switch_inline_current`, `/switch_inline_chosen`, `/game_button`, `/pay_button` |
| `03_inline_queries` | Results list (inline queries) + chosen result | `/inline_hint`, then type `@YourBotName rome` in any chat |
| `04_conversations` | Stateful flows (entry/state/fallback), multiple handlers per same state_id | `/onboard` then send city text or share location; then tap a units button |
| `05_middleware` | Global + per-handler middleware | `/alert` (watch logs + message prefix) |
| `06_lifecycle` | Startup/shutdown hooks | Start/stop the bot and watch logs |
| `07_errors` | Custom error handler | `/boom` |
| `08_actions_outputs` | Outputs helpers, bot method calls, edit flows via callbacks | `/forecast Rome`, `/location`, `/venue`, `/contact`, `/dice`, `/poll`, `/media_group`, `/chat_action`, `/silent`, `/raw_call`, `/bot_send`, `/actions_multi`, `/outputs_multi`, `/actions_reply`, `/actions_call`, `/actions_bot`, `/edit_demo`, `/edit_caption_demo`, `/invoice` |
| `09_update_types` | Less common update handlers (channel edits, business, reactions, polls, payments, etc.) | Depends on Telegram features; most are no-op in private chats |
| `10_payloads` | Payload accessors | `/payload` |
| `11_introspection` | Listing commands/handlers + reference generation | `/commands`, `/handlers`, `/reference` |

Inline mode must be enabled for the bot (BotFather -> enable inline) for `03_inline_queries`.
