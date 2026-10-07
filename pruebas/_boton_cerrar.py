# -*- coding: utf-8 -*-
"""
Boton CERRAR: cierra el programa completo desde el navegador.

Cierra el servidor web local y la ventana de Python de una vez, sin tener
que buscar la terminal. Pide confirmacion, avisa que se esta cerrando y
deja una pantalla de despedida en el navegador.
"""
import ast
import io

RUTA = r"C:\QBASWING-COVERS\servidor.py"
t = io.open(RUTA, encoding="utf-8").read()
hechos = []

# ------------------------------------------------------- 0) import sys
if "\nimport sys\n" not in t:
    t = t.replace("import threading\n", "import threading\nimport sys\n", 1)
    hechos.append("import sys")

# ------------------------------------------------------- 1) boton en la barra
VIEJO = '''        '    <a class="acerca" href="/acerca?volver=%s">%s</a>'
        '  </div>'
        '</div>'
        % (logo, esc(titulo), extra, es_on, en_on, esc_url(actual or "/"),
           esc(t("btn_acerca", lang)))
    )'''
NUEVO = '''        '    <a class="acerca" href="/acerca?volver=%s">%s</a>'
        '    <button class="cerrar" onclick="cerrarPrograma()"'
        ' title="%s">&#10005; %s</button>'
        '  </div>'
        '</div>'
        % (logo, esc(titulo), extra, es_on, en_on, esc_url(actual or "/"),
           esc(t("btn_acerca", lang)), esc(t("btn_cerrar_ayuda", lang)),
           esc(t("btn_cerrar", lang)))
    )'''
if VIEJO in t:
    t = t.replace(VIEJO, NUEVO, 1)
    hechos.append("barra: boton Cerrar en todas las pantallas")
else:
    raise SystemExit("no se encontro el final de barra_superior()")

# --------------------------------------- 2) SCRIPT_IR pasa a ser funcion
VIEJO_SCRIPT = 'SCRIPT_IR = """<script>\nfunction ir(url){window.location.href=url;}'
NUEVO_SCRIPT = 'def script_ir(lang):\n    """JS comun a todas las pantallas, en el idioma activo."""\n    return """<script>\nfunction ir(url){window.location.href=url;}'
if VIEJO_SCRIPT in t:
    t = t.replace(VIEJO_SCRIPT, NUEVO_SCRIPT, 1)
else:
    raise SystemExit("no se encontro SCRIPT_IR")

# Cierre de la cadena y de la funcion: estaba antes de "def pagina("
VIEJO_FIN = '''document.addEventListener('keydown',function(ev){
  if(ev.key==='F2'){
    ev.preventDefault();
    var actual=document.documentElement.getAttribute('lang')||'es';
    setLang(actual==='en'?'es':'en');
  }
});
</script>"""


def pagina('''
NUEVO_FIN = '''document.addEventListener('keydown',function(ev){
  if(ev.key==='F2'){
    ev.preventDefault();
    var actual=document.documentElement.getAttribute('lang')||'es';
    setLang(actual==='en'?'es':'en');
  }
});

/* --- Cerrar el programa entero: servidor web y ventana de Python --- */
var CERRAR_MSG  = "%(confirmar)s";
var CERRAR_FIN  = "%(fin)s";
var CERRAR_NOTA = "%(nota)s";
function cerrarPrograma(){
  if(!confirm(CERRAR_MSG)){ return; }
  var a=document.getElementById('avisocerrar');
  if(a){ a.style.display='block'; }
  fetch('/api/cerrar').catch(function(){});
  setTimeout(function(){
    document.body.innerHTML='<div class="envoltura"><div class="panel ancho '
      +'centrado"><div class="caja"><h1>'+CERRAR_FIN+'</h1><p class="lead">'
      +CERRAR_NOTA+'</p></div></div></div>';
  },1200);
}
</script>""" % {
        "confirmar": esc(t("msg_cerrar_confirmar", lang)),
        "fin": esc(t("titulo_cerrado", lang)),
        "nota": esc(t("msg_cerrado_nota", lang)),
    }


def pagina('''
if VIEJO_FIN in t:
    t = t.replace(VIEJO_FIN, NUEVO_FIN, 1)
    hechos.append("script_ir(lang) con el aviso de cierre")
else:
    raise SystemExit("no se encontro el final de SCRIPT_IR")

# --------------------------------------------------------- 3) usar la funcion
VIEJO_USO = "pie(lang) + SCRIPT_IR)"
NUEVO_USO = "pie(lang) + script_ir(lang))"
if VIEJO_USO in t:
    t = t.replace(VIEJO_USO, NUEVO_USO, 1)
    hechos.append("pagina() usa script_ir(lang)")
else:
    raise SystemExit("pagina() no usa SCRIPT_IR")

# --------------------------------------------- 4) pantalla de despedida
VIEJO_ENV = '"<body>%s%s%s%s%s</body></html>"'
NUEVO_ENV = ('"<body>%s%s%s%s%s"\n        \'<div class="avisocerrar" id="avisocerrar">\'\n'
             '        \'<div class="caja"><div class="ruedita"></div>\'\n'
             '        \'<h2>%s</h2></div></div>\'\n'
             '        "</body></html>"')
if VIEJO_ENV in t:
    t = t.replace(VIEJO_ENV, NUEVO_ENV, 1)
    t = t.replace("           barra_superior(lang, titulo, actual, extra_barra),",
                  "           barra_superior(lang, titulo, actual, extra_barra),", 1)
    t = t.replace("'<div class=\"envoltura\">', cuerpo, \"</div>\", pie(lang) + script_ir(lang))",
                  "'<div class=\"envoltura\">', cuerpo, \"</div>\", pie(lang) + script_ir(lang),\n"
                  "           esc(t(\"msg_cerrando\", lang)))", 1)
    hechos.append("pantalla de despedida al cerrar")
else:
    raise SystemExit("no se encontro el <body> de pagina()")

# ------------------------------------------------------- 5) endpoint
VIEJO_API = '        if ruta == "/api/controlar":'
NUEVO_API = '''        # --- Cerrar el programa entero desde el navegador ---
        if ruta == "/api/cerrar":
            self._json({"ok": True})
            # Se responde primero y luego se apaga, para que el navegador
            # reciba la respuesta y muestre la despedida.
            def _apagar():
                time.sleep(0.5)
                _log("Cerrado desde el navegador")
                try:
                    if E.hilo and E.hilo.is_alive():
                        E.control.cancelar()
                        E.parar.set()
                        time.sleep(1.2)
                except Exception:
                    pass
                try:
                    if SERVIDOR is not None:
                        SERVIDOR.parar()
                except Exception:
                    pass
                try:
                    base.cerrar()
                except Exception:
                    pass
                # Si quedara algun hilo vivo, se cierra igual.
                sys.exit(0)

            threading.Thread(target=_apagar, daemon=True).start()
            return

        if ruta == "/api/controlar":'''
if VIEJO_API in t:
    t = t.replace(VIEJO_API, NUEVO_API, 1)
    hechos.append("/api/cerrar apaga servidor y programa")
else:
    raise SystemExit("no se encontro /api/controlar")

# SERVIDOR global
t = t.replace("class ServidorGaleria(object):",
              "SERVIDOR = None\n\n\nclass ServidorGaleria(object):", 1)
t = t.replace('''        _log("Servidor local escuchando en 127.0.0.1:%d" % self.puerto)''',
              '''        global SERVIDOR
        SERVIDOR = self
        _log("Servidor local escuchando en 127.0.0.1:%d" % self.puerto)''', 1)
hechos.append("SERVIDOR apunta al servidor vivo")

# ------------------------------------------------------------ 6) estilos
t = t.replace(".pie{", '''.cerrar{ margin-left:.4rem; padding:.32rem .58rem; border-radius:7px; cursor:pointer;
  border:1px solid #E9B9BE; background:#FFF3F4; color:#D62B3A; font-size:.85rem;
  font-weight:600; white-space:nowrap;
  transition:background .15s ease, color .15s ease; }
.cerrar:hover{ background:#D62B3A; color:#fff; border-color:#D62B3A; }
.avisocerrar{ display:none; position:fixed; inset:0; z-index:9999;
  background:rgba(247,249,252,.97); }
.avisocerrar .caja{ text-align:center; margin-top:24vh; }
.avisocerrar .ruedita{ width:44px; height:44px; margin:0 auto 1.1rem;
  border:4px solid #DCE6F4; border-top-color:#2E6FD8; border-radius:50%;
  animation:giro .8s linear infinite; }
@keyframes giro{ to{ transform:rotate(360deg); } }
.pie{''', 1)
hechos.append("estilos del boton y del aviso de cierre")

io.open(RUTA, "w", encoding="utf-8", newline="\n").write(t)
ast.parse(t)

print("Boton de cerrar:")
for h in hechos:
    print("   -", h)
print("sintaxis OK")