"""Classical pack stage: 3 payloads multiplexed into ONE image via
MultiSpecQR RGB mode (one independent QR layer per color channel)."""

import multispecqr


def pack(payloads, image_path=None):
    """Encode exactly 3 string payloads into a single RGB QR image."""
    assert len(payloads) == 3, "RGB mode carries exactly 3 payloads"
    img = multispecqr.encode_rgb(payloads[0], payloads[1], payloads[2])
    if image_path is not None:
        img.save(image_path)
    return img


def unpack(img):
    """Decode an RGB MultiSpecQR image back to its 3 payloads."""
    return multispecqr.decode_rgb(img)


def roundtrip(payloads, image_path=None):
    img = pack(payloads, image_path=image_path)
    decoded = unpack(img)
    return {
        "payloads": list(payloads),
        "decoded": decoded,
        "per_payload_ok": [d == p for d, p in zip(decoded, payloads)],
        "all_ok": decoded == list(payloads),
        "image_size": img.size,
        "image_mode": img.mode,
    }
