"""Cinta de Black Friday: anuncia BLACK26 hasta el 30-nov y luego desaparece."""
from tests.test_paises import page  # noqa: F401  (fixture)

from fe import config


def test_cinta_black_friday(page, monkeypatch):
    monkeypatch.setattr(config, "BLACK_FRIDAY_END", 2e10)
    assert "código BLACK26" in page("ES") and "código BLACK26" in page("MX")
    monkeypatch.setattr(config, "BLACK_FRIDAY_END", 0)
    assert "BLACK26" not in page("ES")
