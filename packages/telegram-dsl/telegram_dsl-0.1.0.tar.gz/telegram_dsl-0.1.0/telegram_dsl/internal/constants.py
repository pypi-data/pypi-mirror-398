from dataclasses import dataclass


@dataclass(frozen=True)
class RESPONSE_TYPE:
    TEXT: str = "text"
    PHOTO: str = "photo"
    VIDEO: str = "video"
    AUDIO: str = "audio"
    DOCUMENT: str = "document"
    STICKER: str = "sticker"
    ANIMATION: str = "animation"
    VOICE: str = "voice"
    VIDEO_NOTE: str = "video_note"
    LOCATION: str = "location"
    VENUE: str = "venue"
    CONTACT: str = "contact"
    DICE: str = "dice"
    NONE: str = "none"
    ACTION: str = "action"

    @staticmethod
    def all():
        return {
            RESPONSE_TYPE.TEXT,
            RESPONSE_TYPE.PHOTO,
            RESPONSE_TYPE.VIDEO,
            RESPONSE_TYPE.AUDIO,
            RESPONSE_TYPE.DOCUMENT,
            RESPONSE_TYPE.STICKER,
            RESPONSE_TYPE.ANIMATION,
            RESPONSE_TYPE.VOICE,
            RESPONSE_TYPE.VIDEO_NOTE,
            RESPONSE_TYPE.LOCATION,
            RESPONSE_TYPE.VENUE,
            RESPONSE_TYPE.CONTACT,
            RESPONSE_TYPE.DICE,
            RESPONSE_TYPE.NONE,
            RESPONSE_TYPE.ACTION,
        }
