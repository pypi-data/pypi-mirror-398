import shlex
from urllib.parse import urlsplit, urlunsplit


class Payload:
    def __init__(self, update, context=None):
        self.update = update
        self.context = context

    @property
    def message(self):
        return getattr(self.update, "message", None) or getattr(
            self.update, "effective_message", None
        )

    @property
    def edited_message(self):
        return getattr(self.update, "edited_message", None)

    @property
    def channel_post(self):
        return getattr(self.update, "channel_post", None)

    @property
    def edited_channel_post(self):
        return getattr(self.update, "edited_channel_post", None)

    @property
    def business_connection(self):
        return getattr(self.update, "business_connection", None)

    @property
    def business_message(self):
        return getattr(self.update, "business_message", None)

    @property
    def edited_business_message(self):
        return getattr(self.update, "edited_business_message", None)

    @property
    def deleted_business_messages(self):
        return getattr(self.update, "deleted_business_messages", None)

    @property
    def message_reaction(self):
        return getattr(self.update, "message_reaction", None)

    @property
    def message_reaction_count(self):
        return getattr(self.update, "message_reaction_count", None)

    @property
    def inline_query(self):
        return getattr(self.update, "inline_query", None)

    @property
    def chosen_inline_result(self):
        return getattr(self.update, "chosen_inline_result", None)

    @property
    def callback_query(self):
        return getattr(self.update, "callback_query", None)

    @property
    def shipping_query(self):
        return getattr(self.update, "shipping_query", None)

    @property
    def pre_checkout_query(self):
        return getattr(self.update, "pre_checkout_query", None)

    @property
    def purchased_paid_media(self):
        return getattr(self.update, "purchased_paid_media", None)

    @property
    def poll(self):
        return getattr(self.update, "poll", None)

    @property
    def poll_answer(self):
        return getattr(self.update, "poll_answer", None)

    @property
    def my_chat_member(self):
        return getattr(self.update, "my_chat_member", None)

    @property
    def chat_member(self):
        return getattr(self.update, "chat_member", None)

    @property
    def chat_join_request(self):
        return getattr(self.update, "chat_join_request", None)

    @property
    def chat_boost(self):
        return getattr(self.update, "chat_boost", None)

    @property
    def removed_chat_boost(self):
        return getattr(self.update, "removed_chat_boost", None)

    @property
    def callback_data(self):
        if self.callback_query:
            return self.callback_query.data
        return None

    @property
    def message_text(self):
        msg = self.message
        if msg:
            return getattr(msg, "text", None) or getattr(msg, "caption", None)
        return None

    @property
    def chat_id(self):
        chat = getattr(self.update, "effective_chat", None)
        return getattr(chat, "id", None)

    @property
    def chat_type(self):
        chat = getattr(self.update, "effective_chat", None)
        return getattr(chat, "type", None)

    @property
    def chat_title(self):
        chat = getattr(self.update, "effective_chat", None)
        return getattr(chat, "title", None)

    @property
    def user_id(self):
        user = getattr(self.update, "effective_user", None)
        return getattr(user, "id", None)

    @property
    def user_username(self):
        user = getattr(self.update, "effective_user", None)
        return getattr(user, "username", None)

    @property
    def user_language_code(self):
        user = getattr(self.update, "effective_user", None)
        return getattr(user, "language_code", None)

    @property
    def user_is_bot(self):
        user = getattr(self.update, "effective_user", None)
        return getattr(user, "is_bot", None)

    @property
    def message_id(self):
        msg = self.message
        return getattr(msg, "message_id", None) if msg else None

    @property
    def is_private_chat(self):
        chat = getattr(self.update, "effective_chat", None)
        if chat:
            return getattr(chat, "type", None) == "private"
        return False

    @property
    def is_group_chat(self):
        chat = getattr(self.update, "effective_chat", None)
        if chat:
            return getattr(chat, "type", None) in {"group", "supergroup"}
        return False

    @property
    def is_supergroup(self):
        chat = getattr(self.update, "effective_chat", None)
        if chat:
            return getattr(chat, "type", None) == "supergroup"
        return False

    @property
    def is_channel(self):
        chat = getattr(self.update, "effective_chat", None)
        if chat:
            return getattr(chat, "type", None) == "channel"
        return False

    @property
    def has_media(self):
        msg = self.message
        if not msg:
            return False
        return any(
            getattr(msg, name, None)
            for name in [
                "photo",
                "video",
                "audio",
                "voice",
                "document",
                "sticker",
                "animation",
                "video_note",
            ]
        )

    @property
    def photo(self):
        msg = self.message
        return getattr(msg, "photo", None) if msg else None

    @property
    def video(self):
        msg = self.message
        return getattr(msg, "video", None) if msg else None

    @property
    def audio(self):
        msg = self.message
        return getattr(msg, "audio", None) if msg else None

    @property
    def voice(self):
        msg = self.message
        return getattr(msg, "voice", None) if msg else None

    @property
    def document(self):
        msg = self.message
        return getattr(msg, "document", None) if msg else None

    @property
    def sticker(self):
        msg = self.message
        return getattr(msg, "sticker", None) if msg else None

    @property
    def animation(self):
        msg = self.message
        return getattr(msg, "animation", None) if msg else None

    @property
    def video_note(self):
        msg = self.message
        return getattr(msg, "video_note", None) if msg else None

    @property
    def location(self):
        msg = self.message
        return getattr(msg, "location", None) if msg else None

    @property
    def contact(self):
        msg = self.message
        return getattr(msg, "contact", None) if msg else None

    @property
    def venue(self):
        msg = self.message
        return getattr(msg, "venue", None) if msg else None

    @property
    def poll_message(self):
        msg = self.message
        return getattr(msg, "poll", None) if msg else None

    @property
    def dice(self):
        msg = self.message
        return getattr(msg, "dice", None) if msg else None

    @property
    def message_entities(self):
        msg = self.message
        return getattr(msg, "entities", None) if msg else None

    @property
    def reply_to_message(self):
        msg = self.message
        return getattr(msg, "reply_to_message", None) if msg else None

    @property
    def forward_from(self):
        msg = self.message
        return getattr(msg, "forward_from", None) if msg else None

    @property
    def has_text(self):
        return self.message_text is not None

    @property
    def command(self):
        entities = self.message_entities or []
        text = self.message_text
        if not text:
            return None
        for entity in entities:
            if getattr(entity, "type", None) == "bot_command":
                offset = getattr(entity, "offset", 0)
                length = getattr(entity, "length", 0)
                return text[offset : offset + length].strip()
        return None

    @property
    def command_args(self):
        cmd = self.command
        text = self.message_text
        if not cmd or not text:
            return []
        remainder = text[len(cmd) :].strip()
        return remainder.split() if remainder else []

    @property
    def command_args_quoted(self):
        cmd = self.command
        text = self.message_text
        if not cmd or not text:
            return []
        remainder = text[len(cmd) :].strip()
        if not remainder:
            return []
        try:
            return shlex.split(remainder)
        except ValueError:
            return remainder.split()

    @property
    def urls(self):
        entities = self.message_entities or []
        text = self.message_text or ""
        urls = []
        for entity in entities:
            if getattr(entity, "type", None) in {"url", "text_link"}:
                if getattr(entity, "type", None) == "text_link":
                    urls.append(getattr(entity, "url", None))
                else:
                    offset = getattr(entity, "offset", 0)
                    length = getattr(entity, "length", 0)
                    urls.append(text[offset : offset + length])
        return [u for u in urls if u]

    @property
    def normalized_urls(self):
        normalized = []
        for raw in self.urls:
            parts = urlsplit(raw)
            scheme = parts.scheme.lower() if parts.scheme else "http"
            netloc = parts.netloc.lower()
            normalized.append(
                urlunsplit((scheme, netloc, parts.path, parts.query, parts.fragment))
            )
        return normalized

    @property
    def unique_urls(self):
        seen = set()
        unique = []
        for url in self.urls:
            if url not in seen:
                seen.add(url)
                unique.append(url)
        return unique

    @property
    def unique_normalized_urls(self):
        seen = set()
        unique = []
        for url in self.normalized_urls:
            if url not in seen:
                seen.add(url)
                unique.append(url)
        return unique

    @property
    def mentions(self):
        entities = self.message_entities or []
        text = self.message_text or ""
        mentions = []
        for entity in entities:
            if getattr(entity, "type", None) == "mention":
                offset = getattr(entity, "offset", 0)
                length = getattr(entity, "length", 0)
                mentions.append(text[offset : offset + length])
        return mentions

    @property
    def hashtags(self):
        entities = self.message_entities or []
        text = self.message_text or ""
        tags = []
        for entity in entities:
            if getattr(entity, "type", None) == "hashtag":
                offset = getattr(entity, "offset", 0)
                length = getattr(entity, "length", 0)
                tags.append(text[offset : offset + length])
        return tags

    @property
    def cashtags(self):
        entities = self.message_entities or []
        text = self.message_text or ""
        tags = []
        for entity in entities:
            if getattr(entity, "type", None) == "cashtag":
                offset = getattr(entity, "offset", 0)
                length = getattr(entity, "length", 0)
                tags.append(text[offset : offset + length])
        return tags

    @property
    def email_entities(self):
        entities = self.message_entities or []
        text = self.message_text or ""
        emails = []
        for entity in entities:
            if getattr(entity, "type", None) == "email":
                offset = getattr(entity, "offset", 0)
                length = getattr(entity, "length", 0)
                emails.append(text[offset : offset + length])
        return emails

    @property
    def phone_entities(self):
        entities = self.message_entities or []
        text = self.message_text or ""
        phones = []
        for entity in entities:
            if getattr(entity, "type", None) == "phone_number":
                offset = getattr(entity, "offset", 0)
                length = getattr(entity, "length", 0)
                phones.append(text[offset : offset + length])
        return phones

    @property
    def media_items(self):
        items = []
        if self.photo:
            items.extend(self.photo)
        for attr in [
            "video",
            "audio",
            "voice",
            "document",
            "sticker",
            "animation",
            "video_note",
        ]:
            value = getattr(self, attr)
            if value:
                items.append(value)
        return items

    @property
    def media_file_ids(self):
        ids = []
        for item in self.media_items:
            file_id = getattr(item, "file_id", None)
            if file_id:
                ids.append(file_id)
        return ids

    @property
    def entity_spans(self):
        spans = []
        entities = self.message_entities or []
        text = self.message_text or ""
        for entity in entities:
            etype = getattr(entity, "type", None)
            offset = getattr(entity, "offset", 0)
            length = getattr(entity, "length", 0)
            spans.append(
                {
                    "type": etype,
                    "offset": offset,
                    "length": length,
                    "text": (
                        text[offset : offset + length].strip()
                        if etype == "bot_command"
                        else text[offset : offset + length]
                    ),
                }
            )
        return spans

    @property
    def entities_by_type(self):
        groups = {}
        for span in self.entity_spans:
            groups.setdefault(span["type"], []).append(span)
        return groups

    @property
    def media_summary(self):
        types = []
        if self.photo:
            types.append("photo")
        for name in [
            "video",
            "audio",
            "voice",
            "document",
            "sticker",
            "animation",
            "video_note",
        ]:
            if getattr(self, name):
                types.append(name)
        return {"types": types, "count": len(types)}

    @property
    def inline_query_text(self):
        if self.inline_query:
            return getattr(self.inline_query, "query", None)
        return None

    @property
    def chosen_inline_result_id(self):
        if self.chosen_inline_result:
            return getattr(self.chosen_inline_result, "result_id", None)
        return None

    @property
    def poll_id(self):
        if self.poll:
            return getattr(self.poll, "id", None)
        if self.poll_message:
            return getattr(self.poll_message, "id", None)
        return None
