"""Qué ve cada país: México/Chile solo la lámina para imprimir; EE. UU. sin «Península»; España como siempre."""
import asyncio

import pytest
from fastapi.testclient import TestClient

from fe import config, db, main, market, shop

PROD = {"slug": "la-cruz", "title": "La cruz", "kind": "lienzo", "orient": "v", "images": [], "theme": "cruz"}


@pytest.fixture
def page(monkeypatch):
    async def product(slug): return dict(PROD)
    async def products(): return []
    async def reviews_for(slug): return []
    monkeypatch.setattr(db, "product", product)
    monkeypatch.setattr(db, "products", products)
    monkeypatch.setattr(main, "reviews_for", reviews_for)
    c = TestClient(main.app)

    def get(country=None):
        r = c.get("/cuadro/la-cruz", headers={"cf-ipcountry": country} if country else {})
        assert r.status_code == 200
        return r.text
    return get


def test_mercado_por_pais():
    assert [market.market(c) for c in ("MX", "cl", "US", "PR", "ES", "", None)] == ["digital", "digital", "us", "us", "es", "es", "es"]


def test_mexico_solo_para_imprimir(page):
    t = page("MX")
    assert 'id="add" hidden' in t and 'id="buyNow" hidden' in t and 'id="buyDigital"' in t
    assert "Península" not in t.split('<details class="acc"><summary>Envío')[0] and "pagas en tu moneda" in t
    assert "if (true) document.getElementById('price').textContent = \"$399\\u00a0MXN\"" in t   # en pesos (19-nov)


def test_eeuu(page):
    t = page("US")
    assert "Envío gratis a Estados Unidos y Puerto Rico" in t and "Impreso bajo pedido en EE. UU." in t and 'id="add">' in t


def test_espana_y_sin_cabecera_igual_que_antes(page):
    for c in ("ES", None):
        t = page(c)
        assert "<span>Envío gratis a Península y Baleares</span>" in t and "IVA incluido · envío gratis" in t
        assert 'id="add">' in t and "if (false)" in t


def test_cuadro_desde_mexico_se_rechaza(monkeypatch):
    async def validate_items(raw): return [{"slug": "la-cruz", "size": "30x40", "frame": "none", "qty": 1, "cents": 6500}]
    monkeypatch.setattr(shop, "validate_items", validate_items)
    with pytest.raises(ValueError, match="no enviamos cuadros"):
        asyncio.run(shop.create_checkout([{}], country="MX"))
