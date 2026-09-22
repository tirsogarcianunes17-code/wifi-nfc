# Wi‑Fi por NFC (Android + iPhone)

Una etiqueta NFC (NTAG215) con una **URL** que abre esta página. Desde ahí:

- **iPhone** → botón que instala un perfil `.mobileconfig` con la red; el iPhone se conecta solo y la recuerda.
- **Android / cualquiera** → código QR `WIFI:` que la cámara reconoce, o contraseña con botón «Copiar».

## Cambiar la contraseña (desde el móvil o el ordenador)

1. Abre `config.txt` en github.com y pulsa el lápiz (Editar).
2. Cambia lo que va después del `=` en la línea `password =` (o `ssid =`).
3. Pulsa **Commit changes**. En 1–2 minutos la web ya muestra la nueva clave.

La etiqueta NFC y la URL no cambian nunca.

## Cómo funciona

| Archivo | Para qué |
|---|---|
| `config.txt` | Lo único que se edita: nombre, red, contraseña, seguridad, URL |
| `template.html` | La página |
| `build.py` | Genera `dist/` (web + perfil iOS) a partir de `config.txt` |
| `.github/workflows/pages.yml` | Al guardar cualquier cambio en GitHub, ejecuta `build.py` y publica `dist/` en GitHub Pages |

`dist/` no se sube al repositorio: GitHub lo regenera en cada cambio.

## Probar en local

```bash
python3 build.py
python3 -m http.server 8791 --directory dist
```

## Grabar la etiqueta

App **NFC Tools** → *Escribir* → *Añadir registro* → **URL/URI** → la URL de GitHub Pages → *Escribir*. Un solo registro URL (no añadas el registro «Red Wi‑Fi»: iPhone lo ignora y Android solo mira el primero).

## Limitaciones

- El cliente necesita **datos móviles** para abrir la página (aún no está en tu Wi‑Fi).
- **iPhone XS o posterior** lee etiquetas sin abrir ninguna app; iPhone 7/8/X necesitan la app de NFC.
- El perfil de iOS aparece como «Sin verificar» (no está firmado); es normal.
- La contraseña es pública para quien tenga la URL. Úsalo solo con la red de clientes.
