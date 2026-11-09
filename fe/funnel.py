"""Embudo propio sin cookies: solo totales por día y paso.

No guarda IP, identificadores ni nada en el navegador, así que no necesita
consentimiento (LSSI 22.2). Los contadores viven en memoria y se copian cada
minuto a fe_settings (clave «embudo») y al apagar.
"""
import asyncio
import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from . import db

log = logging.getLogger("fe.funnel")

STEPS = ["ficha", "carrito", "pago", "venta"]
BASE = {"carrito": "ficha", "pago": "ficha", "venta": "pago"}  # «Comprar ya» va a pagar sin pasar por el carrito  # para el %
_BOT = re.compile(r"bot|crawl|spider|slurp|preview|facebookexternalhit|headless|lighthouse|curl|wget|python|httpx", re.I)
_counts: dict[str, dict[str, int]] = {}
_dirty = False
_loaded = False  # no se guarda nada hasta haber leído lo anterior (para no pisarlo)


def today():
    return datetime.now(ZoneInfo("Europe/Madrid")).date()


def is_bot(ua: str | None) -> bool:
    return not ua or bool(_BOT.search(ua))


def hit(step: str) -> None:
    global _dirty
    day = _counts.setdefault(today().isoformat(), {})
    day[step] = day.get(step, 0) + 1
    _dirty = True


def counts() -> dict[str, dict[str, int]]:
    return _counts


async def load() -> None:
    global _loaded
    if not db.ENABLED:
        return
    try:
        rows = await db.get("fe_settings", {"select": "v", "k": "eq.embudo"})
    except Exception:
        log.exception("no se pudo leer el embudo")
        return
    _loaded = True
    for d, steps in ((rows[0]["v"] if rows else None) or {}).items():  # suma lo guardado a lo contado mientras arrancaba
        for k, n in steps.items():
            _counts.setdefault(d, {})[k] = _counts.get(d, {}).get(k, 0) + n


async def save() -> None:
    global _dirty
    if not db.ENABLED or not _dirty or not _loaded:
        return
    _dirty = False
    for d in sorted(_counts)[:-120]:  # guarda 4 meses
        _counts.pop(d, None)
    try:
        await db.set_setting("embudo", _counts)
    except Exception:
        _dirty = True
        log.exception("no se pudo guardar el embudo")


async def loop() -> None:
    await load()
    while True:
        await asyncio.sleep(60)
        if not _loaded:
            await load()
        await save()
