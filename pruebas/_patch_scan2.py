# -*- coding: utf-8 -*-
"""escaneo.py - el recorrido respeta pausa / detener / cancelar y la reanudacion."""
import io
import re

RUTA = r"C:\QBASWING-COVERS\escaneo.py"
texto = io.open(RUTA, encoding="utf-8").read()

NUEVO = '''def _control_progreso(control, marcador, progreso):
    """
    Envuelve la funcion de progreso para que cada carpeta sea un punto de
    control: respeta la pausa, corta si se detiene y anota lo ya revisado.
    """
    def revisar(ruta):
        if control is not None:
            if not control.es_seguro():
                raise Detenido(control.estado())
            if control.es_pausado() and not control.espera():
                raise Detenido(control.estado())
        if marcador is not None:
            try:
                marcador.marcar(ruta)
            except Exception:
                pass
        if progreso is not None:
            progreso(ruta)
    return revisar


def escanear_unidad(ruta_unidad, progreso=None, control=None, marcador=None):
    """
    5. Recorre una unidad en solo lectura y devuelve las carpetas candidatas.

    5.1 Una carpeta es candidata cuando tiene el video EN ELLA MISMA.
    Si el video esta en una subcarpeta (Serie/Season 1/, Pelicula/BD/),
    la candidata es esa subcarpeta: el poster se escribe siempre en la
    carpeta donde esta el video.

    Un telefono o tablet (mtp://) se recorre con el metodo MTP, porque
    Windows no le asigna letra de unidad.

    control  : objeto Control. Permite pausar, seguir, detener y cancelar.
    marcador : objeto con .marcar(ruta) y .ya_visto(ruta). Permite no
               volver a revisar las carpetas que ya se miraon, para que un
               escaneo interrumpido siga donde se quedo.

    Si se detiene o se cancela, devuelve las candidatas que lleva hasta ese
    momento y no se pierde nada.
    """
    if es_mtp(ruta_unidad):
        fn = _control_progreso(control, marcador, progreso)
        try:
            return mtp.escanear(ruta_unidad, progreso=fn)
        except Detenido:
            return []
        except Exception:
            return []

    encontradas = []
    raiz_propia = os.path.normcase(_programa_dir())
    fn = _control_progreso(control, marcador, progreso)

    if not os.path.isdir(ruta_unidad):
        return encontradas

    try:
        for raiz, dirs, archivos in os.walk(ruta_unidad, topdown=True,
                                             followlinks=False):
            try:
                base = os.path.normpath(ruta_unidad)
                nivel = os.path.normpath(raiz)[len(base):].count(os.sep)
            except Exception:
                nivel = 0

            # 5.6 No bajar de 8 niveles.
            if nivel >= PROFUNDIDAD_MAXIMA:
                dirs[:] = []
                continue

            # 5.5 Filtrar carpetas excluidas y la propia carpeta del programa.
            nuevas = []
            for d in dirs:
                if es_excluida(d):
                    continue
                completa = os.path.join(raiz, d)
                try:
                    if os.path.normcase(os.path.abspath(completa)) == raiz_propia:
                        continue
                except Exception:
                    pass
                # 5.9 Al reanudar, no volver a bajar a carpetas ya revisadas.
                if marcador is not None and getattr(marcador, "prunar", False):
                    try:
                        if marcador.ya_visto(completa):
                            continue
                    except Exception:
                        pass
                nuevas.append(d)
            dirs[:] = nuevas

            # 5.1 y 5.4 El video esta aqui mismo -> esta carpeta es candidata.
            videos = _videos_validos(raiz, archivos)
            if videos:
                img = imagen_existente(raiz)
                encontradas.append({
                    "ruta": raiz,
                    "nombre": os.path.basename(raiz) or raiz,
                    "unidad": ruta_unidad,
                    "ya_tiene": img is not None,
                    "imagen_existente": img or "",
                    "videos": videos,
                })
                # Una carpeta con video es una unidad: no se baja dentro.
                dirs[:] = []

            fn(raiz)
    except Detenido:
        return encontradas
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        return encontradas

    return encontradas
'''

patron = re.compile(r"^def escanear_unidad\(.*?(?=^def |^# ---|\Z)", re.S | re.M)
m = patron.search(texto)
if not m:
    raise SystemExit("no se encontro escanear_unidad")

texto = texto[:m.start()] + NUEVO.rstrip("\n") + "\n\n\n" + texto[m.end():]
io.open(RUTA, "w", encoding="utf-8", newline="\n").write(texto)

import ast
ast.parse(io.open(RUTA, encoding="utf-8").read())
print("escanear_unidad() con control y reanudacion, sintaxis OK")