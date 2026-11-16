"""Qué ve cada visita según su país (cabecera cf-ipcountry de Cloudflare)."""

DIGITAL_ONLY = {"MX", "CL"}  # Gelato no produce allí: solo la lámina para imprimir, por email
US = {"US", "PR"}

SHIP_NOTE = {"es": "IVA incluido · envío gratis", "us": "Envío gratis a EE. UU. · pagas en dólares",
             "digital": "Para imprimir · te llega por email · pagas en tu moneda"}
ANNOUNCE = {"es": "Envío gratis a Península y Baleares", "us": "Envío gratis a Estados Unidos y Puerto Rico",
            "digital": "Lámina para imprimir · te llega al momento"}
PRINTED = {"es": "Impreso bajo pedido en España", "us": "Impreso bajo pedido en EE. UU.", "digital": "Pagas en tu moneda"}


def market(country: str | None) -> str:
    c = (country or "").upper()
    return "digital" if c in DIGITAL_ONLY else "us" if c in US else "es"
