"""Lámina para imprimir a 300 ppp de verdad: la obra (1536x1024) se amplía con IA (Real-ESRGAN en Replicate).

Se hace una vez por cuadro, la primera vez que alguien la compra, y se guarda en Storage.
Sin REPLICATE_API_TOKEN, o si Replicate falla, se entrega la obra original como hasta ahora.
"""
import asyncio
import io
import logging

import httpx
from PIL import Image

from . import config, db

log = logging.getLogger(__name__)
API = "https://api.replicate.com/v1"
VERSION = config.env("REPLICATE_UPSCALE_VERSION", "42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b")  # nightmareai/real-esrgan
A4_LONG_PX = 3508   # lado largo de un A4 (297 mm) a 300 ppp


def enabled() -> bool:
    return bool(config.env("REPLICATE_API_TOKEN"))


def to_300ppp(big: Image.Image) -> bytes:
    """Lo ampliado (x4) se deja en A4 a 300 ppp (lado largo de 3508 píxeles), en JPEG de máxima calidad. Pura."""
    k = A4_LONG_PX / max(big.size)
    if k < 1:
        big = big.resize((round(big.width * k), round(big.height * k)), Image.LANCZOS)
    buf = io.BytesIO()
    big.convert("RGB").save(buf, format="JPEG", quality=95, dpi=(300, 300))
    return buf.getvalue()


async def replicate_x4(image_url: str) -> bytes:
    h = {"Authorization": f"Bearer {config.env('REPLICATE_API_TOKEN')}"}
    async with httpx.AsyncClient(timeout=120) as c:
        p = (await c.post(f"{API}/predictions", headers={**h, "Prefer": "wait=60"},
                          json={"version": VERSION, "input": {"image": image_url, "scale": 4, "face_enhance": False}})).json()
        if "urls" not in p:   # p. ej. 402 sin saldo en Replicate
            raise RuntimeError(f"Replicate: {p.get('detail') or p}")
        for _ in range(60):
            if p.get("status") in ("succeeded", "failed", "canceled"):
                break
            await asyncio.sleep(2)
            p = (await c.get(p["urls"]["get"], headers=h)).json()
        if p.get("status") != "succeeded":
            raise RuntimeError(f"Replicate: {p.get('status')} {p.get('error')}")
        out = p["output"] if isinstance(p["output"], str) else p["output"][0]
        return (await c.get(out)).content


async def art_300(p: dict) -> bytes | None:
    """La obra a 300 ppp para la descarga, o None si no se puede (y entonces va la original)."""
    path = f"{p['slug']}/art-300.jpg"
    try:
        return await db.download(db.public_url(path))
    except Exception:
        pass
    if not enabled():
        return None
    try:
        big = Image.open(io.BytesIO(await replicate_x4(p["art_url"])))
        data = await asyncio.to_thread(to_300ppp, big)
        await db.upload(path, data, "image/jpeg")
        return data
    except Exception as e:  # noqa: BLE001
        log.warning("ampliación de %s falló: %s", p["slug"], e)
        return None
