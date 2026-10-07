# -*- coding: utf-8 -*-
"""servidor.py - etapa 1: controles del escaneo + base local + progreso por unidad."""
import io
import re

RUTA = r"C:\QBASWING-COVERS\servidor.py"
texto = io.open(RUTA, encoding="utf-8").read()
hechos = []


def reemplazar(nombre, nuevo):
    global texto
    patron = re.compile(r"^def %s\(.*?(?=^def |^class |^# ---|\Z)" % nombre,
                        re.S | re.M)
    m = patron.search(texto)
    if not m:
        raise SystemExit("NO SE ENCONTRO: %s" % nombre)
    texto = texto[:m.start()] + nuevo.rstrip("\n") + "\n\n\n" + texto[m.end():]
    hechos.append("%s()" % nombre)


# ------------------------------------------------------------ 1) imports
if "\nimport base\n" not in texto:
    texto = texto.replace("import rutas\n", "import rutas\nimport base\nimport iconos\n", 1)
    hechos.append("imports base e iconos")

# ------------------------------------------------------------ 2) Estado
texto = texto.replace(
    "        self.progreso = {\"activo\": False, \"hechos\": 0, \"total\": 0,\n"
    "                         \"texto\": \"\", \"listo\": False}\n",
    "        self.progreso = {\"activo\": False, \"hechos\": 0, \"total\": 0,\n"
    "                         \"texto\": \"\", \"listo\": False}\n"
    "        self.detalle = []            # una linea de progreso por unidad\n"
    "        self.control = escaneo.Control()   # pausa / seguir / detener\n",
    1)
hechos.append("Estado: control y detalle")

# guardar_estado tambien en la base nueva
texto = texto.replace(
    "    def guardar_estado(self, ruta, **campos):\n"
    "        db = self.abrir_db()\n",
    "    def guardar_estado(self, ruta, **campos):\n"
    "        try:\n"
    "            base.actualizar(ruta, **{k: v for k, v in campos.items()\n"
    "                                 if k != 'marcada'})\n"
    "        except Exception:\n"
    "            pass\n"
    "        db = self.abrir_db()\n",
    1)
hechos.append("guardar_estado escribe tambien en la base nueva")

# ------------------------------------------------- 3) _hilo_escaneo completo
NUEVO_HILO = '''def _hilo_escaneo(reanudar=False):
    """
    Recorre las unidades elegidas y guarda las carpetas candidatas.

    Los botones de la pantalla (pausar, seguir, detener, cancelar) llegan
    por E.control. Lo que se encuentra se guarda en la base local, asi que
    un escaneo interrumpido se puede continuar donde se quedo.
    """
    control = E.control
    control.seguir()
    E.detalle = []
    E.progreso.update({"activo": True, "hechos": 0, "total": 0,
                       "texto": t("msg_preparando", E.lang), "listo": False})

    unidades = E.unidades_elegidas or [u["ruta"] for u in E.unidades]
    total = 0
    estado_final = "terminado"

    try:
        for pos, u in enumerate(unidades, 1):
            if not control.es_seguro():
                estado_final = control.estado()
                break

            _log("Escaneando %s" % u)
            linea = {"ruta": u, "hechas": 0, "candidatas": 0,
                     "terminada": False, "pos": pos, "total_unidades":
                     len(unidades), "texto": ""}
            E.detalle.append(linea)
            E.progreso["texto"] = t("msg_escaneando_ruta", E.lang) % u

            def avanzar(ruta, _l=linea):
                _l["hechas"] += 1
                _l["texto"] = ruta
                E.progreso["hechos"] = sum(x["hechas"] for x in E.detalle)
                E.progreso["texto"] = t("msg_escaneando_ruta", E.lang) % ruta

            marcador = None
            if base.conexion() is not None:
                try:
                    marcador = base.MarcadorRuta(u)
                    marcador.prunar = bool(reanudar)
                except Exception:
                    marcador = None

            try:
                encontradas = escaneo.escanear_unidad(
                    u, progreso=avanzar, control=control, marcador=marcador)
            except Exception as exc:
                _log("Fallo al escanear %s: %s" % (u, exc), "ERROR")
                encontradas = []
            finally:
                if marcador is not None:
                    try:
                        marcador.vaciar()
                    except Exception:
                        pass

            total += len(encontradas)
            linea["candidatas"] = len(encontradas)
            linea["terminada"] = control.es_seguro()

            for c in encontradas:
                c["anio"] = post.extraer_anio(c["nombre"])
                c["temporada"] = post.extraer_temporada(c["nombre"])
                c["titulo"] = post.quitar_anio_del_titulo(
                    post.limpiar_nombre(c["nombre"]), c["anio"])
                c["tipo"] = _tipo_de_carpeta(c["nombre"])
                c["descargado"] = _ya_descargada(c["ruta"])
                if c["descargado"]:
                    c["ya_tiene"] = True
                E.carpetas.append(c)

            # Se guarda en la base local: si se corta, no se pierde.
            try:
                base.guardar_carpetas(encontradas)
                base.guardar_escaneo(u, carpeta=linea["texto"],
                                     hechas=linea["hechas"],
                                     terminado=1 if linea["terminada"] else 0)
            except Exception:
                pass

            if not control.es_seguro():
                estado_final = control.estado()
                break

        if estado_final == "terminado" and control.estado() == "cancelado":
            estado_final = "cancelado"

    except Exception as exc:
        estado_final = "error"
        _log("Fallo en el escaneo: %s" % exc, "ERROR")
    finally:
        for linea in E.detalle:
            linea["terminada"] = True
        E.progreso.update({"activo": False, "listo": True,
                           "total": sum(x["hechas"] for x in E.detalle)})
        if estado_final == "pausado":
            E.progreso["texto"] = t("msg_escaneo_pausado", E.lang) % total
        elif estado_final in ("detenido", "cancelado"):
            E.progreso["texto"] = t("msg_escaneo_detenido", E.lang) % total
        elif estado_final == "error":
            E.progreso["texto"] = t("msg_escaneo_error", E.lang)
        else:
            E.progreso["texto"] = t("msg_escaneo_listo", E.lang) % total
        E.progreso["guardado"] = len(E.carpetas)
        E.progreso["reanudar"] = (
            estado_final in ("detenido", "pausado", "error"))
        _log("Escaneo terminado: %d carpetas con video (%s)"
             % (len(E.carpetas), estado_final))


def _ya_descargada(ruta):
    """True si esa carpeta ya tiene cover.jpg."""
    if escaneo.es_mtp(ruta):
        try:
            est = mtp.estado_carpeta(ruta) or {}
            return bool(est.get("cover"))
        except Exception:
            return False
    try:
        return os.path.isfile(os.path.join(ruta, COVER_NAME))
    except Exception:
        return False'''
reemplazar("_hilo_escaneo", NUEVO_HILO)

# ------------------------------------------------- 4) api progreso + control
texto = texto.replace(
    '''        if ruta == "/api/progreso":
            self._json({
                "activo": E.progreso["activo"],
                "hechos": E.progreso["hechos"],
                "total": E.progreso["total"],
                "texto": E.progreso["texto"],
                "listo": E.progreso["listo"],
            })
            return
''',
    '''        if ruta == "/api/progreso":
            self._json({
                "activo": E.progreso["activo"],
                "hechos": E.progreso["hechos"],
                "total": E.progreso["total"],
                "texto": E.progreso["texto"],
                "listo": E.progreso["listo"],
                "control": E.control.estado(),
                "detalle": E.detalle,
                "guardado": E.progreso.get("guardado", 0),
                "reanudar": E.progreso.get("reanudar", False),
            })
            return

        # --- Botones del escaneo: pausar / seguir / detener / cancelar ---
        if ruta == "/api/controlar":
            accion = (v("accion") or "").lower()
            if accion == "pausar":
                E.control.pausar()
            elif accion == "seguir":
                E.control.seguir()
            elif accion == "detener":
                E.control.detener()
            elif accion == "cancelar":
                E.control.cancelar()
            _log("Escaneo: %s" % accion)
            self._json({"ok": True, "control": E.control.estado()})
            return
''', 1)
hechos.append("/api/progreso con detalle y /api/controlar")

# ---------------------------------------------- 5) /api/cover con caratulas
texto = texto.replace(
    '''            imagen = escaneo.imagen_existente(ruta_carpeta)
            if not imagen:
                self._enviar(b"", "image/jpeg", 404)
                return''',
    '''            # Para la tarjeta sirve cualquier imagen buena de la carpeta,
            # aunque este en una subcarpeta tipo Posters/.
            imagen = escaneo.imagen_para_mostrar(ruta_carpeta)
            if not imagen:
                self._enviar(b"", "image/jpeg", 404)
                return''', 1)
hechos.append("/api/cover usa la mejor imagen de la carpeta")

# ------------------------------------------------------ 6) reanudar escaneo
texto = texto.replace(
    '''            if elegidas and (E.hilo is None or not E.hilo.is_alive()):
                E.hilo = threading.Thread(target=_hilo_escaneo, daemon=True)
                E.hilo.start()''',
    '''            reanudar = (q.get("reanudar") or ["0"])[0] in ("1", "si", "s")
            if elegidas and (E.hilo is None or not E.hilo.is_alive()):
                E.progreso["reanudado"] = reanudar
                E.hilo = threading.Thread(
                    target=_hilo_escaneo, kwargs={"reanudar": reanudar},
                    daemon=True)
                E.hilo.start()''', 1)
hechos.append("/paso3 acepta reanudar=1")

io.open(RUTA, "w", encoding="utf-8", newline="\n").write(texto)

import ast
ast.parse(io.open(RUTA, encoding="utf-8").read())
print("servidor.py etapa 1:")
for h in hechos:
    print("   -", h)
print("   sintaxis OK")