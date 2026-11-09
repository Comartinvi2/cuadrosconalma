# Plan: carga más ligera en móvil (ficha y portada)

Objetivo de negocio: subir el % de clics de anuncios que terminan de cargar
(misma serie de arreglos que en caricaturas; Maria lo mide en adengine ~10-11 nov).

## Diagnóstico (medido en producción el 9 nov)

A diferencia de caricaturas, aquí las páginas se renderizan en servidor (sin JSON
de catálogo en el cliente) y ya existen versiones WebP de 600 px (`thumb`) y
1200 px (`md`) con backfill al arrancar. Los problemas 2 (ficha baja el catálogo)
y 4 (JSON de portada con campos sin usar) **no aplican**. Lo que sí pesa:

| Recurso | Hoy | Debería |
|---|---|---|
| Favicon: las páginas declaran `icon-512.png` | 37 KB | `favicon-32.png` ya existe (1,6 KB) y no se usa |
| Ficha: tira de 10 miniaturas bajo la foto (WebP de 600 px para huecos de 60-100 px) | ~194 KB | versión de 240 px: ~30-40 KB |
| Ficha: imagen principal siempre `md` 1200 px, sin srcset | 76 KB | en móvil basta la de 600 px (~12 KB) |
| Portada: hero `md` 1200 px sin srcset | 118 KB | en móvil alta densidad, 600 px (~26 KB) |
| Portada/colecciones: cada tarjeta baja 2 fotos (la 2ª solo se ve al pasar el ratón) | ~26 KB × tarjeta | en táctil no bajar la foto de hover |

Carga típica de una ficha en móvil hoy: ~300 KB solo en imágenes above-the-fold + 37 KB de favicon.

## TODOs (uno por commit, push a main → autodeploy en Render, verificar en producción)

- [x] 1. **Favicon ligero**: en `base.html`, usar `/static/favicon-32.png` como icono
  (el `icon-512.png` se queda para el logo del JSON-LD y apple-touch-icon aparte).
  → verificar: curl al HTML muestra favicon-32; la petición pesa ~1,6 KB.
- [x] 2. **Miniatura pequeña (`sm`, 240 px) para la tira de la ficha**: `_web_versions()`
  genera también `name-240.webp`; `_thumbs_job` y el arranque hacen backfill de las
  fotos que no tengan `sm`; `g-thumbs` usa `im.sm or im.thumb or im.url`.
  → verificar: `/admin/thumbs` termina sin errores; la ficha en producción pide
  los `-240.webp` y pesan ~2-5 KB cada uno.
- [x] 3. **srcset en la imagen principal de la ficha**: `srcset="thumb 600w, md 1200w"`
  con `sizes="(max-width: 700px) and (min-resolution: 2.5dppx) 200px, (max-width: 900px) 92vw, 630px"`
  (lección de caricaturas: sin el tope, un DPR 3 calcula ~1100 px y elige siempre la grande).
  OJO: el JS que cambia de foto hace `gMain.src = …`; con srcset hay que actualizar
  también `gMain.srcset` (botones con `data-thumb` además de `data-src`).
  → verificar: en el navegador con emulación móvil (DPR 3), `currentSrc` es `main-600.webp`;
  al pulsar una miniatura la foto grande sigue cambiando.
- [x] 4. **Portada más ligera en móvil**: (a) hero con el mismo srcset/sizes con tope
  de alta densidad; (b) en pantallas táctiles no bajar la foto de hover de las
  tarjetas: `@media (hover: none){.card-img img.alt{display:none}}` (con
  `loading="lazy"`, sin caja no se descarga).
  → verificar: en emulación móvil el hero carga `-600.webp` y no hay peticiones
  `room*-600.webp` de las tarjetas; en escritorio el hover sigue funcionando.

## Review

Los cuatro TODOs desplegados y verificados en producción el 9 nov
(commits a528f3e, 8f7d330, e68bc21, 4c17880):

- Favicon: todas las páginas declaran `favicon-32.png` (1,6 KB; antes 37 KB).
- Tira de la ficha: pide los `-240.webp` (1,3–4,7 KB; ~27 KB en total,
  antes ~194 KB). El backfill de arranque generó las 240 px de todo el
  catálogo solo, en ~media hora.
- Imagen principal de la ficha: srcset activo; al pulsar miniaturas la foto
  sigue cambiando (el JS actualiza también `srcset`). En DPR 2 elige la de
  1200 px (previsto); el tope de 2,5dppx hará que DPR 3 use la de 600 px
  (la emulación del navegador solo llega a DPR 2; misma regla ya verificada
  en caricaturas con DPR 3).
- Portada en móvil: hero con srcset; las 20 tarjetas ya no bajan la foto de
  hover (0 descargas, `display:none` con `hover:none`); en escritorio el
  hover sigue funcionando y la foto carga.

Imágenes above-the-fold de una ficha en móvil: de ~307 KB a ~40 KB (DPR 3)
/ ~105 KB (DPR 2), favicon incluido.

Matiz para leer el % de adengine: las «visitas» las cuenta el píxel de Meta,
que aquí (igual que en caricaturas) solo se carga tras aceptar el banner de
cookies. Parte de la pérdida clic→visita es gente que rechaza o ignora el
banner, así que el % nunca llegará a 100 aunque la web vuele. El píxel debe
seguir cargándose solo con consentimiento (RGPD).

Aprendizajes:
- El patrón de caricaturas aplicaba solo a medias: aquí el render es de
  servidor y ya había thumb/md con backfill; el peso estaba en la tira de
  miniaturas (600 px para huecos de 60 px), el favicon y la falta de srcset,
  no en JSON de catálogo.
- Con `srcset` presente, cambiar solo `src` por JS no hace nada: hay que
  escribir también `srcset`.
- `loading="lazy"` + `display:none` (media query `hover:none`) evita la
  descarga de la foto de hover en táctil sin tocar JS.
