"""Lámina para imprimir a 300 ppp: se amplía con Replicate una vez por cuadro; sin clave o si falla, la original."""
import asyncio
import io

from PIL import Image

from fe import db, upscale

P = {"slug": "la-cruz", "art_url": "https://x/fe/la-cruz/art.jpg"}


def jpg(w, h):
    b = io.BytesIO(); Image.new("RGB", (w, h), (90, 60, 40)).save(b, format="JPEG"); return b.getvalue()


def test_a4_a_300_ppp():
    im = Image.open(io.BytesIO(upscale.to_300ppp(Image.new("RGB", (6144, 4096)))))
    assert im.size == (3508, 2339) and round(im.info["dpi"][0]) == 300


def test_amplia_una_vez_por_cuadro(monkeypatch):
    store = {}
    async def download(url):
        if url not in store: raise RuntimeError("404")
        return store[url]
    async def upload(path, data, ct="image/jpeg"): store[db.public_url(path)] = data
    calls = []
    async def x4(url): calls.append(url); return jpg(6144, 4096)
    monkeypatch.setattr(db, "download", download); monkeypatch.setattr(db, "upload", upload)
    monkeypatch.setattr(upscale, "replicate_x4", x4); monkeypatch.setenv("REPLICATE_API_TOKEN", "r8_x")
    a = asyncio.run(upscale.art_300(P)); b = asyncio.run(upscale.art_300(P))
    assert a == b and Image.open(io.BytesIO(a)).size == (3508, 2339) and calls == [P["art_url"]]


def test_sin_clave_o_si_falla_va_la_original(monkeypatch):
    async def nada(url): raise RuntimeError("404")
    monkeypatch.setattr(db, "download", nada)
    monkeypatch.delenv("REPLICATE_API_TOKEN", raising=False)
    assert asyncio.run(upscale.art_300(P)) is None
    async def boom(url): raise RuntimeError("caído")
    monkeypatch.setattr(upscale, "replicate_x4", boom); monkeypatch.setenv("REPLICATE_API_TOKEN", "r8_x")
    assert asyncio.run(upscale.art_300(P)) is None
