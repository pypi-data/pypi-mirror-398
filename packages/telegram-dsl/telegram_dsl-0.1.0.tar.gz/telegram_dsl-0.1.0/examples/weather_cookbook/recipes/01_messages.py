from telegram.ext import filters

from telegram_dsl.framework import outputs
from telegram_dsl.framework.handlers import (
    customfilter_text_handler,
    photo_handler,
    video_handler,
    audio_handler,
    voice_handler,
    video_note_handler,
    document_handler,
    sticker_handler,
    animation_handler,
)


@customfilter_text_handler(
    filters.TEXT
    & ~filters.COMMAND
    & ~filters.Regex(r"^/")
    & ~filters.Regex(r"^!")
    & ~filters.Regex(r"^(weather|temp)\b"),
)
async def on_text(args, user, payload):
    return outputs.text(f"You said: {args}")


@photo_handler()
async def on_photo(args, user, payload):
    photo = payload.photo[-1] if payload.photo else None
    if not photo:
        return outputs.text("No photo found.")
    return outputs.photo(photo=photo.file_id, caption="Photo echo.")


@video_handler()
async def on_video(args, user, payload):
    if not payload.video:
        return outputs.text("No video found.")
    return outputs.video(video=payload.video.file_id, caption="Video echo.")


@audio_handler()
async def on_audio(args, user, payload):
    if not payload.audio:
        return outputs.text("No audio found.")
    return outputs.audio(audio=payload.audio.file_id, caption="Audio echo.")


@voice_handler()
async def on_voice(args, user, payload):
    if not payload.voice:
        return outputs.text("No voice note found.")
    return outputs.voice(voice=payload.voice.file_id, caption="Voice echo.")


@video_note_handler()
async def on_video_note(args, user, payload):
    if not payload.video_note:
        return outputs.text("No video note found.")
    return outputs.video_note(video_note=payload.video_note.file_id)


@document_handler()
async def on_document(args, user, payload):
    if not payload.document:
        return outputs.text("No document found.")
    return outputs.document(document=payload.document.file_id, caption="Document echo.")


@animation_handler()
async def on_animation(args, user, payload):
    if not payload.animation:
        return outputs.text("No animation found.")
    return outputs.animation(
        animation=payload.animation.file_id, caption="Animation echo."
    )


@sticker_handler()
async def on_sticker(args, user, payload):
    if not payload.sticker:
        return outputs.text("No sticker found.")
    return outputs.sticker(sticker=payload.sticker.file_id)
