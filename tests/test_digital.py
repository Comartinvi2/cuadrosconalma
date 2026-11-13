import asyncio

from fe import config, shop

PRODUCT = {"slug": "la-cruz", "title": "Calvario al alba", "kind": "lienzo", "images": [{"kind": "main", "url": "https://x/main.jpg"}]}


def validate(raw, monkeypatch):
    async def product(slug):
        return PRODUCT if slug == "la-cruz" else None
    monkeypatch.setattr(shop.db, "product", product)
    return asyncio.run(shop.validate_items(raw))


def test_archivo_a_19_90_y_una_unidad(monkeypatch):
    [it] = validate([{"slug": "la-cruz", "size": "digital", "frame": "natural", "qty": 5}], monkeypatch)
    assert it["cents"] == 1990 and it["qty"] == 1 and it["frame"] == "none"
    assert "Archivo para imprimir" in it["name"]


def test_solo_archivo_no_pide_envio(monkeypatch):
    items = validate([{"slug": "la-cruz", "size": "digital", "frame": "none"}], monkeypatch)
    assert not shop.needs_shipping(items)
    items += validate([{"slug": "la-cruz", "size": "30x45", "frame": "none"}], monkeypatch)
    assert shop.needs_shipping(items)


def test_enlaces_solo_de_pedido_pagado_y_firmados():
    o = {"id": "FM261113ABC123", "status": "paid", "items": [{"size": "30x45", "title": "A"}, {"size": "digital", "title": "B"}]}
    [f] = shop.downloads(o)
    assert f["url"].startswith(f"{config.BASE_URL}/api/descarga/FM261113ABC123/2.jpg?t=")
    assert f["url"].endswith(shop.download_sig("FM261113ABC123", 2))
    assert shop.download_sig("FM261113ABC123", 2) != shop.download_sig("FM261113ABC124", 2)
    assert shop.downloads({**o, "status": "checkout"}) == []


def test_descarga_sin_firma_o_sin_pagar_no_da_el_archivo(monkeypatch):
    from fastapi.testclient import TestClient
    from fe import main
    o = {"id": "FM1", "status": "checkout", "items": [{"slug": "la-cruz", "size": "digital"}]}

    async def get_order(oid):
        return o if oid == "FM1" else None
    monkeypatch.setattr(shop, "get_order", get_order)
    c = TestClient(main.app)
    assert c.get("/api/descarga/FM1/1.jpg?t=falsa").status_code == 403
    assert c.get(f"/api/descarga/FM1/1.jpg?t={shop.download_sig('FM1', 1)}").status_code == 404  # sin pagar
    assert c.get(f"/api/descarga/FM2/1.jpg?t={shop.download_sig('FM2', 1)}").status_code == 404  # no existe
