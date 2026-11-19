"""Moneda de la visita: la ficha, el carrito y Stripe usan el mismo importe (19-nov, María: «haz que casen con los de stripe»)."""
import asyncio
import json
import re
from types import SimpleNamespace

from fastapi.testclient import TestClient

from fe import config, db, main, market, shop
from tests.test_paises import PROD, page  # noqa: F401

LIENZO = {"slug": "la-cruz", "size": "30x45", "frame": "none", "qty": 1}
DIGITAL = {"slug": "la-cruz", "size": config.DIGITAL_SIZE, "frame": "none", "qty": 1}


def checkout(monkeypatch, items, country, discount=False):
    calls = []
    fake = SimpleNamespace(StripeError=Exception, checkout=SimpleNamespace(Session=SimpleNamespace(
        create=lambda **p: calls.append(p) or SimpleNamespace(id="cs_1", url="https://pay"))))
    async def noop(*a, **k): return None
    monkeypatch.setattr(config, "STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setattr(shop, "_stripe", lambda: fake)
    monkeypatch.setattr(db, "upsert", noop); monkeypatch.setattr(db, "patch", noop)
    asyncio.run(shop.create_checkout(items, country=country, discount=discount))
    return calls[-1]


def test_ficha_en_la_moneda_de_la_visita(page):
    t = page("US")
    p = json.loads(re.search(r"const PRICES = (\{.*?\});", t).group(1))
    assert p["30x45|none"] == market.major(market.to_local(6500, "usd"), "usd") == 74.9
    assert 'window.CUR = "usd"' in t and "$22.90 USD" in t
    assert "$399 MXN" in page("MX")
    t = page("ES")
    assert 'window.CUR = "eur"' in t and "19,90" in t and "USD" not in t


def test_carrito_y_stripe_cobran_lo_mismo(page, monkeypatch):
    c = TestClient(main.app)
    for country, cur, items in (("US", "usd", [LIENZO, DIGITAL]), ("MX", "mxn", [DIGITAL]), ("CL", "clp", [DIGITAL]), ("ES", "eur", [LIENZO])):
        q = c.post("/api/cart/quote", json={"items": items}, headers={"cf-ipcountry": country}).json()
        p = checkout(monkeypatch, items, country)
        charged = sum(li["price_data"]["unit_amount"] * li["quantity"] for li in p["line_items"])
        assert q["currency"] == cur and all(li["price_data"]["currency"] == cur for li in p["line_items"])
        assert market.fmt(charged, cur) == q["total_text"]   # lo que pone el carrito = lo que cobra Stripe
        assert ("adaptive_pricing" in p) == (cur == "eur")


def test_cupon_de_bienvenida_en_euros(page, monkeypatch):
    p = checkout(monkeypatch, [LIENZO], "US", discount=True)
    assert p["line_items"][0]["price_data"]["currency"] == "eur"
