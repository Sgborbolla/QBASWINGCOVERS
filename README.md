# QBASWING COVERS

Programa de escritorio para Windows que recorre tus discos, encuentra las
carpetas con video y descarga el póster oficial de cada serie, película,
anime, animado o telenovela para que toda la colección tenga carátula.

**Regla de oro:** no borra, no mueve y no sobrescribe nada tuyo. El póster
descargado se guarda dentro de la propia carpeta del video, con el mismo
nombre que la carpeta (`<nombre de la carpeta>.jpg`, con sufijo `-2`, `-3`…
si el nombre ya está ocupado).

## Uso

1. Doble clic en `iniciar.bat` (elige solo el ejecutable de 64 o 32 bits) o
   abre `QBASWING COVERS.exe` directamente.
2. En el navegador eliges los tipos de contenido y los discos, esperas el
   escaneo y la búsqueda de pósters.
3. En la galería descargas todo lo encontrado, revisas uno por uno o marcas
   con el ✓ de cada tarjeta.
4. Al terminar se genera `inventario.csv` y se abre la primera carpeta
   descargada, con su póster dentro.

Solo escucha en `127.0.0.1` (puerto 8080): nadie desde la red puede
conectarse.

## Requisitos

- Windows 10/11, de 32 o de 64 bits.
- Conexión a internet para buscar los pósters.
- Solo para desarrollo: Python 3.12 o superior. Solo librería estándar,
  sin dependencias externas.

## Estructura del repositorio

| Archivo | Qué es |
| --- | --- |
| `qbaswing_covers.py` | Punto de entrada; `--check` ejecuta el diagnóstico |
| `servidor.py` | Servidor web local y todas las pantallas |
| `escaneo.py` | Escaneo de discos y carpetas |
| `fuentes.py` | APIs: TMDB, AniList, TVmaze, Internet Archive |
| `posters.py`, `iconos.py`, `fondo.py`, `estilos.py` | Imágenes e interfaz |
| `base.py` | Base de datos SQLite del programa |
| `i18n.py` | Textos ES/EN; se lee de disco, va junto al ejecutable |
| `QBASWING_COVERS_ESPECIFICACION.txt` | Especificación completa (fuente de verdad) |
| `LEEME.txt` | Manual rápido del usuario |
| `pruebas/` | Batería de pruebas |
| `build64/`, `build32/` | Specs de PyInstaller (lo único que se versiona de la compilación) |

`config.json`, la base de datos, el registro (`*.log`) y las carpetas de
compilación quedan fuera del repositorio: son datos locales.

## Desarrollo

Se ejecuta desde la raíz del repositorio:

```powershell
$env:PYTHONIOENCODING='utf-8'
python pruebas\_smoke.py
python pruebas\_descarga.py
```

La batería completa son 14 pruebas: `_bug_scan`, `_escaneo_reglas`,
`_smoke`, `_http`, `_paginas`, `_fondos`, `_clases`, `_i18n`,
`_fondo_test`, `_dispositivos`, `_descarga`, `_spec`, `_galeria_bella`
y `_galeria_iconos`.

## Compilar

```powershell
# 64 bits
python -m PyInstaller --noconfirm --clean --distpath dist64 "build64\QBASWING COVERS x64.spec"

# 32 bits
& "C:\...\Python312-32\python.exe" -m PyInstaller --noconfirm --clean --distpath dist32 "build32\QBASWING COVERS.spec"
```

El ejecutable de 64 bits y el de 32 se despliegan juntos en la carpeta del
programa; los textos externos (`i18n.py`, `LEEME.txt`) se copian aparte.

## Documentación

- `LEEME.txt` — manual rápido (va junto al ejecutable).
- `QBASWING_COVERS_ESPECIFICACION.txt` — especificación completa del
  programa, incluidas las reglas de escritura y seguridad.
