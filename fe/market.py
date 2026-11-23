"""Qué ve cada visita según su país (cabecera cf-ipcountry de Cloudflare)."""

DIGITAL_ONLY = {"MX", "CL"}  # Gelato no produce allí: solo la lámina para imprimir, por email
US = {"US", "PR"}

SHIP_NOTE = {"es": "IVA incluido · envío gratis", "us": "Envío gratis a EE. UU. · pagas en dólares",
             "digital": "Para imprimir · te llega por email al momento"}
ANNOUNCE = {"es": "Envío gratis a Península y Baleares", "us": "Envío gratis a Estados Unidos y Puerto Rico",
            "digital": "Lámina para imprimir · te llega al momento"}
PRINTED = {"es": "Impreso bajo pedido en España", "us": "Impreso bajo pedido en EE. UU.", "digital": "Te llega por email al momento"}


def market(country: str | None) -> str:
    c = (country or "").upper()
    return "digital" if c in DIGITAL_ONLY else "us" if c in US else "es"


# --- Moneda del visitante (19-nov, María): la página enseña y Stripe cobra exactamente el mismo importe ----------------
# EE. UU. en dólares (euros × 1,15 redondeado a ,90), México en pesos (euros × 20 → $399), Chile en pesos (euros × 1000 → $19.990).
CURRENCY = {"US": "usd", "PR": "usd", "MX": "mxn", "CL": "clp"}
ZERO_DECIMAL = {"clp"}   # Stripe cobra los pesos chilenos sin céntimos


def currency(country: str | None) -> str:
    return CURRENCY.get((country or "").upper(), "eur")


def to_local(eur_cents: int, cur: str) -> int:
    """Precio en euros (céntimos) → importe en la moneda del visitante, en la unidad que usa Stripe (céntimos; pesos chilenos enteros)."""
    if cur == "usd":
        return (-(-(eur_cents * 115 - 90 * 100) // 10000)) * 100 + 90   # ×1,15 y hacia arriba a ,90: 19,90 € → $22.90
    if cur == "mxn":
        return (-(-eur_cents * 20 // 10000)) * 10000 - 100   # ×20 y hacia arriba a …99: 19,90 € → $399
    if cur == "clp":
        return (-(-eur_cents * 10 // 1000)) * 1000 - 10      # ×1000 y hacia arriba a …990: 19,90 € → $19.990
    return eur_cents


def major(amount: int, cur: str) -> float:
    return amount if cur in ZERO_DECIMAL else amount / 100


def fmt(amount: int, cur: str) -> str:
    """Importe en la unidad de Stripe → texto: «19,90 €», «$22.90 USD», «$399 MXN», «$19.990 CLP»."""
    x = major(amount, cur)
    if cur == "eur":
        s = f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return s.replace(",00", "") + " €"
    if cur == "usd":
        return f"${x:,.2f}".replace(".00", "") + " USD"
    if cur == "mxn":
        return f"${x:,.0f}" + " MXN"
    return f"${x:,.0f}".replace(",", ".") + " CLP"
