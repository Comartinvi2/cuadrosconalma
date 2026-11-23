"""23-nov: GA4 contaba la compra con 0 € porque el evento se enviaba sin moneda."""
from tests.test_paises import page  # noqa: F401


def test_eventos_de_analytics_llevan_moneda(page):
    assert "gtag('event', ev, Object.assign({currency: cur}, d))" in page()
