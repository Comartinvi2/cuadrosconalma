# Cuadros con Alma

Tienda online de cuadros de arte cristiano contemporáneo — https://cuadrosconalma.com

- Código de la web: `fe/` (FastAPI + plantillas Jinja).
- Despliegue: Render, servicio `cuadros-fe` (rama `main`, despliegue automático en cada commit).
  - Build: `pip install -r requirements.txt`
  - Start: `uvicorn fe.main:app --host 0.0.0.0 --port $PORT`
- Datos: Supabase, proyecto `tiendas-cuadros` (tablas `fe_*`).

Antes vivía en la rama `cuadros` del repo `evavillaro/caricaturas`.
