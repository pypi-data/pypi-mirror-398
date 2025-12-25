from telegram_dsl.internal.handlers.map import _get_all_entries


def list_commands():
    return [
        (meta["name"], meta.get("doc", ""))
        for entry in _get_all_entries()
        for meta in [entry["meta"]]
        if meta.get("add_to_commands")
    ]


def list_handlers(group=None, tag=None):
    def matches(meta):
        return (group is None or meta.get("group") == group) and (
            tag is None or tag in meta.get("tags", [])
        )

    return [
        {
            "name": meta["name"],
            "origin": meta["origin"],
            "doc": meta.get("doc", ""),
            "tags": meta.get("tags", []),
            "group": meta.get("group"),
        }
        for entry in _get_all_entries()
        for meta in [entry["meta"]]
        if matches(meta)
    ]


def get_handler_doc(name):
    entry = next((e for e in _get_all_entries() if e["meta"]["name"] == name), None)
    return entry["meta"].get("doc") if entry else None


def describe_handler(name):
    entry = next((e for e in _get_all_entries() if e["meta"]["name"] == name), None)
    return entry["meta"] if entry else None
