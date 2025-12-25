from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Tuple, Callable

from telegram_dsl.internal.telegram_methods import BOT_METHODS


@dataclass(frozen=True)
class Action:
    method: str
    kwargs: Dict[str, Any] = field(default_factory=dict)

    def with_kwargs(self, **kwargs):
        merged = dict(self.kwargs)
        merged.update(kwargs)
        return Action(self.method, merged)


@dataclass(frozen=True)
class ActionGroup:
    actions: Tuple[Action, ...]

    @staticmethod
    def of(actions: Iterable[Action]) -> "ActionGroup":
        return ActionGroup(tuple(actions))


def action(method: str, **kwargs) -> Action:
    return Action(method, kwargs)


def send_message(text: str, **kwargs) -> Action:
    return Action("send_message", {"text": text, **kwargs})


def reply_text(text: str, **kwargs) -> Action:
    return Action("reply_text", {"text": text, **kwargs})


def call(method: str, **kwargs) -> Action:
    return Action(method, kwargs)


def sleep(seconds: float) -> Action:
    """Delay within an actions.group(...) sequence (no Telegram API call)."""
    return Action("sleep", {"seconds": seconds})


class BotActions:
    def __getattr__(self, name: str) -> Callable[..., Action]:
        def _method(**kwargs):
            return Action(name, kwargs)

        return _method


bot = BotActions()


def _make_action_func(name: str):
    def _func(**kwargs):
        return Action(name, kwargs)

    _func.__name__ = name
    return _func


for _name in BOT_METHODS:
    if _name not in globals():
        globals()[_name] = _make_action_func(_name)


def group(*actions: Action) -> ActionGroup:
    return ActionGroup.of(actions)


__all__ = [
    "Action",
    "ActionGroup",
    "action",
    "call",
    "sleep",
    "bot",
    "group",
    "send_message",
    "reply_text",
    *BOT_METHODS,
]
