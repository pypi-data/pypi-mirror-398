import io
import zlib


_CACHED: bytes | None = None


def sample_png() -> io.BytesIO:
    """Return an in-memory PNG suitable for send_photo/InputMediaPhoto.

    We generate a simple RGB PNG (no external URLs, no external libs) to keep the
    cookbook fully runnable offline and avoid Telegram rejecting remote images.
    """
    global _CACHED
    if _CACHED is None:
        _CACHED = _generate_png_rgb(width=128, height=128, rgb=(120, 180, 255))

    bio = io.BytesIO(_CACHED)
    bio.name = "sample.png"
    bio.seek(0)
    return bio


def _generate_png_rgb(*, width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    # PNG file signature
    signature = b"\x89PNG\r\n\x1a\n"
    r, g, b = rgb
    row = bytes([0]) + bytes([r, g, b]) * width  # filter=0 + RGB pixels
    raw = row * height
    compressed = zlib.compress(raw, level=6)

    def _chunk(kind: bytes, data: bytes) -> bytes:
        length = len(data).to_bytes(4, "big")
        crc = zlib.crc32(kind)
        crc = zlib.crc32(data, crc) & 0xFFFFFFFF
        return length + kind + data + crc.to_bytes(4, "big")

    ihdr = (
        width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + bytes(
            [
                8,  # bit depth
                2,  # color type: truecolor (RGB)
                0,  # compression
                0,  # filter
                0,  # interlace
            ]
        )
    )

    return (
        signature
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", compressed)
        + _chunk(b"IEND", b"")
    )
