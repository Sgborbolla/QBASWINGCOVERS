# -*- coding: utf-8 -*-
"""
QBASWING COVERS v1.0 - Servidor web local y toda la interfaz.

Cada pantalla es una ventana del navegador (seccion 0.2):
    Ventana 1  Bienvenida
    Ventana 2  Discos
    Ventana 3  Escaneo
    Ventana 4  Galeria

Solo escucha en 127.0.0.1. Nadie en la red puede conectarse (9.1).
"""

import os
import re
import csv
import json
import time
import shutil
import sqlite3
import threading
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import escaneo

import fuentes
import posters as post
import rutas
import base
import iconos
import fondo
import estilos
from i18n import t

BASE_DIR = rutas.base_dir()
LOGO = BASE_DIR / "logo-qbaswing.png"
if not LOGO.exists():
    LOGO = rutas.recurso("logo-qbaswing.png")
INVENTARIO = BASE_DIR / "inventario.csv"
DB_FILE = BASE_DIR / "qbawing_covers.db"
HISTORIA = BASE_DIR / "ACERCA_DE_NOSOTROS.txt"

MIN_POSTER_SIZE = 15 * 1024          # 9.8 - menos de 15 KB es fallo
COVER_NAME = "cover.jpg"             # imagen previa de la carpeta origen (5.4)
NOMBRE_DESCARGAS = "QBASWING COVERS"  # subcarpeta dentro de Descargas

YA_TIENE = "ya_tiene"
SIN_POSTER = "sin_poster"
DESCARGADO = "descargado"
REVISION = "revision"
PENDIENTE = "pendiente"

# --------------------------------------------------------------------------
# Estado de la sesion
# --------------------------------------------------------------------------

class Estado(object):
    def __init__(self, cfg):
        self.cfg = cfg
        self.lang = cfg.get("idioma") or "es"
        if self.lang not in ("es", "en"):
            self.lang = "es"

        self.paso = 1
        self.tipos = cfg.get("tipos") or ["todos"]

        self.unidades = []
        self.unidades_elegidas = []

        self.carpetas = []            # candidatos encontrados por el escaneo
        self.resultados = {}          # ruta -> {poster_url, titulo, ...}
        self.marcadas = set()
        self.historial = []

        self.progreso = {"activo": False, "hechos": 0, "total": 0,
                         "texto": "", "listo": False}
        self.detalle = []            # una linea de progreso por unidad
        self.control = escaneo.Control()   # pausa / seguir / detener
        self.detalle = []            # una linea de progreso por unidad
        self.control = escaneo.Control()   # pausa / seguir / detener
        self.resumen = None

        # 10.1 punto 2: las rutas viajan como id numerico.
        self.ids = {}
        self.rutas = {}
        self.siguiente_id = 1
        self.indice = None

        self.hilo = None
        self.parar = threading.Event()
        self.cerrado = False

        self._db = None

    # --- ids <-> rutas ---
    def id_de(self, ruta):
        if ruta not in self.ids:
            self.ids[ruta] = self.siguiente_id
            self.rutas[self.siguiente_id] = ruta
            self.siguiente_id += 1
        return self.ids[ruta]

    def ruta_de(self, cid):
        return self.rutas.get(cid)

    # --- base de datos de sesion (10.1 punto 6) ---
    def abrir_db(self):
        if self._db is not None:
            return self._db
        try:
            self._db = sqlite3.connect(str(DB_FILE), check_same_thread=False)
            self._db.execute("""CREATE TABLE IF NOT EXISTS estado (
                ruta TEXT PRIMARY KEY,
                estado TEXT,
                marcada INTEGER DEFAULT 0,
                fuente TEXT,
                titulo TEXT,
                url_poster TEXT,
                puntuacion INTEGER
            )""")
            self._db.commit()
        except Exception:
            self._db = None
        return self._db

    def guardar_estado(self, ruta, **campos):
        try:
            base.actualizar(ruta, **{k: v for k, v in campos.items()
                                 if k != 'marcada'})
        except Exception:
            pass
        db = self.abrir_db()
        if db is None:
            return
        try:
            claves = ", ".join("%s=?" % k for k in campos)
            valores = list(campos.values())
            sql = ("INSERT OR REPLACE INTO estado (ruta, %s) VALUES (?, %s)"
                   % (", ".join(campos.keys()), ", ".join("?" * len(campos))))
            db.execute(sql, [ruta] + valores)
            db.commit()
        except Exception:
            pass


E = None


# --------------------------------------------------------------------------
# Utilidades de texto
# --------------------------------------------------------------------------

def esc(texto):
    """5 - HTML escapado para evitar inyeccion de codigo."""
    if texto is None:
        return ""
    return (str(texto)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;"))


def esc_url(texto):
    from urllib.parse import quote
    return quote(str(texto or ""), safe="")


# --------------------------------------------------------------------------
# 0.4 Estilo visual
# --------------------------------------------------------------------------

CSS = estilos.CSS + fondo.CSS


def marca_agua():
    """
    La marca de agua de QBASwing MyServer: tres brillos (oro, zafiro y
    rojo) sobre el fondo negro. Va detras de todo y respira muy despacio.
    Sale en todas las pantallas, incluida la portada.
    """
    return '<div class="marca-agua" aria-hidden="true"></div>'


def pie(lang):
    """
    0.4 Pie de marca, calcado al del QBASwing Marketplace: franja de la
    bandera arriba, fondo azul marino, nombre con el degradado de la
    bandera y los creditos en dorado. Va al final de la pagina, a todo el
    ancho, en TODAS las pantallas, la portada incluida.

    Todo el texto viene de i18n y el aviso de TMDB solo se pinta cuando
    hay clave de la API (sin clave no hay Posters de TMDB que avisar).
    """
    anio = time.strftime("%Y")
    nombre = "QBASWING COVERS"
    estrella = iconos.estrella('class="icono-svg estrella"')
    marca_ok = iconos.verificado('class="icono-svg tick"')
    marca_arte = iconos.paleta('class="icono-svg tick"')
    patrocinio = ('<p class="pie-linea">%s %s <b>Freeman</b></p>'
                  % (marca_ok, esc(t("pie_patrocinado", lang))))
    autor = ('<p class="pie-linea">%s %s <b>QBASwing Designer y Freeman '
             'y Diseños</b> <span class="anio">&copy; %s</span></p>'
             % (marca_arte, esc(t("pie_disenado", lang)), esc(anio)))
    legal = ('<p class="pie-legal">&copy; %s %s. %s</p>'
             % (esc(anio), esc(nombre), esc(t("pie_reserva", lang))))
    # Aviso obligatorio de TMDB: en el fondo hay Posters suyos.
    aviso = ('<p class="pie-tmdb">%s</p>' % esc(t("aviso_tmdb", lang))) if E else ""
    return ('<footer class="pie">'
            '<div class="pie-bandera" aria-hidden="true">'
            '<span class="tira azul"></span><span class="tira blanca"></span>'
            '<span class="tira roja"></span></div>'
            '<div class="pie-cuerpo">'
            '<p class="pie-nombre">%s<span class="texto-bandera">%s</span></p>'
            '<div class="pie-creditos">%s%s</div>'
            "%s%s"
            "</div></footer>"
            % (estrella, esc(nombre), patrocinio, autor, legal, aviso))


def barra_superior(lang, titulo, actual="", extra=""):
    """Cabecera con logo, selector ES|EN y Acerca de nosotros."""
    logo = ('<img src="/logo.png" alt="QBASwing">' if LOGO.exists()
            else '<span style="font-family:Georgia,serif;font-size:1.1rem">'
                 'QBASwing</span>')
    es_on = " on" if lang == "es" else ""
    en_on = " on" if lang == "en" else ""
    return (
        '<div class="barra">'
        '  <div class="marca">%s<span class="tit">%s</span></div>'
        '  <div class="crece">%s'
        '    <button class="idioma%s" onclick="setLang(\'es\')">ES</button>'
        '    <button class="idioma%s" onclick="setLang(\'en\')">EN</button>'
        '    <a class="acerca" href="/acerca?volver=%s">%s</a>'
        '    <button class="cerrar" onclick="cerrarPrograma()"'
        ' title="%s">&#10005; %s</button>'
        '  </div>'
        '</div>'
        % (logo, esc(titulo), extra, es_on, en_on,
           esc_url(actual or "/"),
           esc(t("btn_acerca", lang)), esc(t("btn_cerrar_ayuda", lang)),
           esc(t("btn_cerrar", lang)))
    )


def script_ir(lang):
    """JS comun a todas las pantallas, en el idioma activo."""
    return """<script>
/* 0.2 La pantalla siguiente sustituye a esta: no se apilan. */
function ir(url){window.location.replace(url);}
function setLang(l){
  var u=new URL(window.location.href);
  u.searchParams.delete('lang'); u.searchParams.delete('volver');
  var volver=u.pathname+u.search;
  u.searchParams.set('lang',l);
  u.searchParams.set('volver',volver);
  window.location.href=u.toString();
}
/* Atajo F2: cambia el idioma en cualquier pantalla. */
document.addEventListener('keydown',function(ev){
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
    document.body.innerHTML='<div class="marca-agua"></div><div class="envoltura">'
      +'<div class="panel ancho centrado"><div class="caja"><h1>'+CERRAR_FIN
      +'</h1><p class="lead">'+CERRAR_NOTA+'</p></div></div></div>';
  },1200);
}
</script>""" % {
        "confirmar": esc(t("msg_cerrar_confirmar", lang)),
        "fin": esc(t("titulo_cerrado", lang)),
        "nota": esc(t("msg_cerrado_nota", lang)),
    }


def pagina(lang, titulo, cuerpo, actual="", extra_barra="", head_extra="",
            con_fondo=True):
    """
    Una sola pagina para todas las ventanas.

    Todas las pantallas llevan la marca de agua de MyServer y los Posters
    de fondo, incluida la portada. El fondo usa de semilla el nombre de
    la ventana que lo pide, para que cada pantalla salga con Posters
    distintos de las demas.
    """
    if con_fondo:
        try:
            semilla = sys._getframe(1).f_code.co_name
        except Exception:
            semilla = actual or "inicio"
    else:
        semilla = ""
    decorado = fondo.html(lang, semilla) if con_fondo else ""
    return (
        "<!DOCTYPE html><html lang=\"%s\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>%s</title><link rel=\"icon\" href=\"data:,\"><style>%s</style>%s</head>"
        "<body>%s%s%s%s%s%s%s"
        '<div class="avisocerrar" id="avisocerrar">'
        '<div class="caja"><div class="ruedita"></div>'
        '<h2>%s</h2></div></div>'
        "</body></html>"
        % (lang, esc("%s · QBASWING COVERS" % titulo), CSS, head_extra,
           marca_agua(), barra_superior(lang, titulo, actual, extra_barra),
           decorado,
           '<div class="envoltura">', cuerpo, "</div>", pie(lang) + script_ir(lang),
           esc(t("msg_cerrando", lang)))
    )


# --------------------------------------------------------------------------
# Ventana 1 - Bienvenida
# --------------------------------------------------------------------------

CSS_PORTADA = estilos.CSS_PORTADA


TILT = """<script>
(function(){
  document.querySelectorAll('[data-inclinacion]').forEach(function(el){
    el.addEventListener('mousemove',function(ev){
      var r=el.getBoundingClientRect();
      var x=(ev.clientX-r.left)/r.width-.5, y=(ev.clientY-r.top)/r.height-.5;
      el.style.transform='perspective(700px) rotateX('+(-y*7)+'deg) rotateY('+(x*9)+'deg) translateY(-4px)';
    });
    el.addEventListener('mouseleave',function(){ el.style.transform=''; });
  });
})();
</script>"""

JS_PORTADA = """<script>
  /* La tira promocional va cambiando sola, con sus puntitos,
     al ritmo del login de QBASwing MyServer. */
  (function(){
    var pista=document.getElementById('promo-pista');
    if(pista){
      var total=pista.children.length, k=0;
      var puntos=document.querySelectorAll('.promo-puntos .puntito');
      setInterval(function(){
        if(document.hidden || total<2 || !pista.isConnected){ return; }
        k=(k+1)%total;
        pista.style.transform='translateX(-'+(k*100)+'%)';
        for(var i=0;i<puntos.length;i++){
          puntos[i].classList.toggle('primero', i===k);
        }
      },4200);
    }
  })();

  (function(){
  var c=document.getElementById('esc-capa');
  if(c){ document.addEventListener('mousemove',function(ev){
    var x=(ev.clientX/window.innerWidth-.5), y=(ev.clientY/window.innerHeight-.5);
    var imgs=c.querySelectorAll('img');
    for(var i=0;i<imgs.length;i++){
      var f=(i%3)+1;
      imgs[i].style.marginLeft=(x*26*f)+'px';
      imgs[i].style.marginTop=(y*20*f)+'px';
    }
  }); }

  var ob=new IntersectionObserver(function(es){
    es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('visible');
      if(e.target.dataset.n){ cuenta(e.target); e.target.removeAttribute('data-n'); }
      ob.unobserve(e.target); }});
  },{threshold:.18});
  document.querySelectorAll('.revelar').forEach(function(el){ ob.observe(el); });

  function cuenta(el){
    var fin=parseInt(el.dataset.n,10)||0; var t0=null;
    function paso(ts){
      if(!t0) t0=ts;
      var p=Math.min((ts-t0)/1100,1);
      var v=Math.round(fin*(1-Math.pow(1-p,3)));
      el.textContent=v.toLocaleString('es');
      if(p<1) requestAnimationFrame(paso);
    }
    requestAnimationFrame(paso);
  }

  var grande=document.getElementById('esc-grande');
  fetch('/api/portadas?limite=13').then(function(r){return r.json();}).then(function(d){
    var lista=(d&&d.portadas)||[]; if(!lista.length){ return; }
    document.querySelectorAll('#esc-capa img').forEach(function(im){ im.remove(); });
    var capa=document.getElementById('esc-capa');
    lista.slice(0,6).forEach(function(p){
      var im=document.createElement('img'); im.src=p.url; im.alt=''; im.loading='lazy';
      capa.appendChild(im);
    });
    grande.innerHTML='';
    var a=document.createElement('img'); a.src=lista[0].url; a.alt=lista[0].titulo||'';
    grande.appendChild(a); grande.setAttribute('title', lista[0].titulo||'');
    var caja=document.getElementById('esc-minis'); caja.innerHTML='';
    lista.slice(1,13).forEach(function(p){
      var d2=document.createElement('div'); d2.className='esc-mini';
      d2.title=p.titulo||'';
      var b=document.createElement('img'); b.src=p.url; b.alt=p.titulo||''; b.loading='lazy';
      d2.appendChild(b); caja.appendChild(d2);
    });
  }).catch(function(){});

  fetch('/api/resumen').then(function(r){return r.json();}).then(function(d){
    if(!d) return;
    var c=document.querySelector('[data-n="'+d.total+'"]');
    if(c) return;
    document.querySelectorAll('.esc-cifra b').forEach(function(b){
      var k=b.dataset.clave;
      if(k && d[k]!=null){ b.setAttribute('data-n', d[k]); b.textContent='0'; }
    });
  }).catch(function(){});
})();
</script>"""


def ventana_portada(lang):
    """Pantalla de inicio: un solo boton para escanear. Sin elegir tipos."""
    n = base.resumen()
    cifras = [
        (n.get("total", 0), "portada_cifra_carpetas"),
        (n.get("con_poster", 0), "portada_cifra_posters"),
        (n.get("descargados", 0), "portada_cifra_descargados"),
    ]
    bloque_cifras = "".join(
        '<div class="esc-cifra"><b data-n="%d" data-clave="">%s</b><span>%s</span></div>'
        % (v, esc("{:,}".format(v).replace(",", ".")), esc(t(clave, lang)))
        for v, clave in cifras)

    tarjetas = "".join(
        '<div class="esc-tarjeta revelar" data-inclinacion="1">'
        '  %s<h3>%s</h3><p>%s</p></div>'
        % (dibujo, esc(t(titulo, lang)), esc(t(texto, lang)))
        for dibujo, titulo, texto in (
            (iconos.carpeta(), "portada_t1_titulo", "portada_t1_texto"),
            (iconos.por_tipo("pelicula"), "portada_t2_titulo", "portada_t2_texto"),
            (iconos.disco_extraible(), "portada_t3_titulo", "portada_t3_texto"),
        ))

    huecos = "".join(
        '<div class="esc-mini esc-hueco">%s</div>' % iconos.por_tipo("serie")
        for _ in range(6))

    hay_pendientes = _escaneos_pendientes()

    # La marquesina de marca, tal cual la pone la portada de
    # QBASwing MyServer: logotipo, nombre, empresa y lema.
    cuerpo = (
        '<div class="portada">'

        '  <section class="esc-hero">'
        '    <div class="esc-capa" id="esc-capa" aria-hidden="true">%s</div>'
        '    <div class="esc-brillo" aria-hidden="true"></div>'
        '    <div class="marquesina">'
        '      <div class="esc-logo">%s</div>'
        '      <p class="marca-nombre">%s</p>'
        '      <p class="marca-sub">QBASwing Designer</p>'
        '      <p class="marca-lema">%s</p>'
        '    </div>'
        '    <a class="esc-boton" href="/paso2">%s</a>'
        '    %s'
        '  </section>'

        '  <section class="esc-tarjetas">%s</section>'

        '  <section class="esc-demo revelar">'
        '    <div><h2 class="esc-titulo-seccion">%s</h2>'
        '      <p class="lead">%s</p></div>'
        '    <div class="esc-grande" id="esc-grande"></div>'
        '  </section>'

        '  <section class="esc-minis revelar" id="esc-minis">%s</section>'

        '  <section class="esc-cifras revelar">%s</section>'

        '  <p class="esc-nota">%s<br>%s</p>'
        '</div>'
        % (
            "".join('<img src="" alt="">' for _ in range(6)),
            ('<img src="/logo.png" alt="QBASwing">' if LOGO.exists()
             else '<span class="logo-texto">QBASwing</span>'),
            esc(t("portada_titulo_1", lang)),
            '&ldquo;%s&rdquo;' % esc(t("portada_titulo_2", lang)),
            esc(t("btn_escanear_ya", lang)),
            ('<span class="esc-reanudar"><a href="/paso2?reanudar=1">%s</a></span>'
             % esc(t("btn_seguir_escaneo", lang))) if hay_pendientes else "",
            tarjetas,
            esc(t("portada_demo_titulo", lang)),
            esc(t("portada_demo_texto", lang)),
            huecos,
            bloque_cifras,
            esc(t("aviso_tmdb", lang)),
            esc(t("portada_pie", lang)),
        ))

    # La portada tambien lleva los Posters de fondo, con su propia semilla,
# para que no se repita ninguna de las demas pantallas.
    return pagina(lang, t("titulo_bienvenida", lang), cuerpo, "/",
                  head_extra="<style>%s</style>%s%s" % (CSS_PORTADA, JS_PORTADA, TILT),
                  con_fondo=True)


def _escaneos_pendientes():
    """True si hay escaneos a medias que se pueden continuar."""
    try:
        for fila in base.leer_escaneos():
            if not fila.get("terminado"):
                return True
    except Exception:
        pass
    return False


def ventana_bienvenida(lang, tipos_actual=None):
    """Se mantiene el nombre viejo por compatibilidad. Ahora es la portada."""
    return ventana_portada(lang)


# --------------------------------------------------------------------------
# Ventana 2 - Discos
# --------------------------------------------------------------------------

def ventana_discos(lang, unidades):
    if not unidades:
        cuerpo = ('<div class="panel ancho centrado"><h1>%s</h1>'
                  '<div class="aviso">%s</div>'
                  '<a class="btn fantasma" href="/">%s</a></div>'
                  % (esc(t("titulo_discos", lang)),
                     esc(t("err_no_discos", lang)),
                     esc(t("btn_atras", lang))))
        return pagina(lang, t("titulo_discos", lang), cuerpo, "/")

    filas = []
    for i, u in enumerate(unidades, 1):
        interna = escaneo.es_interna(u)
        # Todas las unidades se ofrecen: internas, USB y externas.
        marcado = " checked"
        filas.append(
            "<tr>"
            '<td><input type="checkbox" name="unidad" value="%s"%s '
            'style="width:1.05rem;height:1.05rem;accent-color:#2E6FD8"></td>'
            "<td><b>%s</b>%s</td>"
            "<td>%s</td>"
            "<td>%s</td>"
            '<td class="%s">%s</td>'
            "</tr>"
            % (esc(u["ruta"]), marcado,
               esc(u["ruta"]),
               (" <span style='color:#9AA0A8'>%s</span>" % esc(u["etiqueta"]))
               if u.get("etiqueta") else "",
               esc(escaneo.formatear_bytes(u.get("libre"))) + " / "
               + esc(escaneo.formatear_bytes(u.get("total"))),
               esc(u.get("descripcion", "")),
               "etiqueta-si" if interna else "etiqueta-no",
               esc(t("disco_si", lang) if interna else t("disco_no", lang)))
        )

    cuerpo = (
        '<div class="panel">'
        '  <h1>%s</h1>'
        '  <p class="lead" style="margin-bottom:1.2rem">%s</p>'
        '  <form method="get" action="/paso3">'
        '  <table><thead><tr>'
        '    <th></th><th>%s</th><th>%s</th><th>%s</th><th>%s</th>'
        '  </tr></thead><tbody>%s</tbody></table>'
        '  <div class="fila-botones" style="justify-content:flex-start">'
        '    <button class="btn" type="submit">%s</button>'
        '    <a class="btn fantasma" href="/">%s</a>'
        '  </div>'
        '  </form>'
        '</div>'
        '<div class="info">%s</div>'
        % (esc(t("titulo_discos", lang)),
           esc(t("msg_elige_discos", lang)),
           esc(t("col_unidad", lang)),
           esc(t("col_espacio", lang)),
           esc(t("col_tipo", lang)),
           esc(t("col_interna", lang)),
           "".join(filas),
           esc(t("btn_escanear", lang)),
           esc(t("btn_atras", lang)),
           esc(t("aviso_lee_solo", lang)))
    )
    return pagina(lang, t("titulo_discos", lang), cuerpo, "/")


# --------------------------------------------------------------------------
# Ventana 3 - Escaneo
# --------------------------------------------------------------------------

def ventana_escaneo(lang, unidades_elegidas):
    rutas_js = ",".join('"%s"' % esc_url(u) for u in unidades_elegidas)
    cuerpo = (
        '<div class="panel ancho centrado">'
        '  <h1>%s</h1>'
        '  <p class="lead">%s</p>'
        '  <div class="barra-prog"><span id="barra"></span></div>'
        '  <p class="contador" id="txt">%s</p>'
        '  <p class="contador" id="det"></p>'
        '  <div id="lineas"></div>'
        '  <div class="controles">'
        '    <button id="bpausa" class="btn chico" onclick="ctl(\'pausar\')">%s</button>'
        '    <button id="bseguir" class="btn chico fantasma" '
        'onclick="ctl(\'seguir\')" hidden>%s</button>'
        '    <button id="bdetener" class="btn chico fantasma" '
        'onclick="ctl(\'detener\')">%s</button>'
        '    <button class="btn chico fantasma" onclick="ctl(\'cancelar\')">%s</button>'
        '  </div>'
        '  <p class="lead" style="margin-top:1.4rem">%s</p>'
        '</div>'
        '<script>const RUTAS=[%s];</script>'
        % (esc(t("titulo_escaneo", lang)),
           esc(t("msg_escaneando", lang)),
           esc(t("msg_preparando", lang)),
           esc(t("btn_pausar", lang)),
           esc(t("btn_seguir", lang)),
           esc(t("btn_detener", lang)),
           esc(t("btn_cancelar", lang)),
           esc(t("msg_escaneo_tiempo", lang)),
           rutas_js)
    )

    js = """<script>
function ctl(accion){
  fetch('/api/controlar?accion='+accion).catch(function(){});
}
/* Una linea de progreso por unidad: asi se ve cada disco por separado. */
function pintarDetalle(d){
  var caja=document.getElementById('lineas');
  if(!d.detalle || !d.detalle.length){ caja.innerHTML=''; return; }
  var h='';
  for(var i=0;i<d.detalle.length;i++){
    var u=d.detalle[i];
    h+='<div class="linea-unidad">'
      +'<span class="icono-unidad">'+u.hechas+'</span>'
      +'<span class="ruta-unidad" title="'+u.ruta+'">'+u.ruta+'</span>'
      +'<span class="estado-unidad">'
      +(u.terminada ? (u.candidatas+' ✓') : '…')+'</span></div>';
  }
  caja.innerHTML=h;
}
var timer=setInterval(function(){
  fetch('/api/progreso').then(function(r){return r.json();}).then(function(d){
    var barra=document.getElementById('barra');
    var pct = d.total>0 ? Math.round(d.hechos*100/d.total) : 0;
    barra.classList.toggle('indeterminada',d.activo && d.total===0);
    barra.style.width = d.total>0 ? pct+'%' : '';
    document.getElementById('txt').textContent = d.texto||'';
    document.getElementById('det').innerHTML =
        (d.total>0 ? d.hechos+' / '+d.total : '');
    pintarDetalle(d);

    /* El boton de pausa se vuelve "continuar" mientras esta pausado. */
    var pau=(d.control==='pausado');
    var bp=document.getElementById('bpausa');
    var bs=document.getElementById('bseguir');
    if(bp){ bp.style.display = pau ? 'none' : ''; }
    if(bs){ bs.hidden = !pau; }

    if(d.listo){
      clearInterval(timer);
      var seguir=d.reanudar;
      setTimeout(function(){
        window.location.replace('/paso4');
      },700);
    }
  }).catch(function(){});
},600);
</script>"""

    return pagina(lang, t("titulo_escaneo", lang), cuerpo, "/", head_extra=js)


# --------------------------------------------------------------------------
# Ventana 4 - Pregunta de busqueda
# --------------------------------------------------------------------------

def ventana_pregunta(lang, con_faltantes):
    if con_faltantes <= 0:
        cuerpo = (
            '<div class="panel ancho centrado">'
            '  <h1>%s</h1>'
            '  <div class="info">%s</div>'
            '  <div class="fila-botones">'
            '    <a class="btn" href="/galeria">%s</a>'
            '  </div>'
            '</div>'
            % (esc(t("titulo_resultado", lang)),
               esc(t("msg_todo_ya_tiene", lang)),
               esc(t("btn_abrir_galeria", lang)))
        )
        return pagina(lang, t("titulo_resultado", lang), cuerpo, "/")

    cuerpo = (
        '<div class="panel ancho centrado">'
        '  <h1>%s</h1>'
        '  <p class="lead" style="margin-bottom:1.4rem">%s</p>'
        '  <div class="fila-botones">'
        '    <form method="get" action="/buscar" style="display:inline">'
        '      <input type="hidden" name="q" value="s">'
        '      <button class="btn" type="submit">%s</button>'
        '    </form>'
        '    <form method="get" action="/galeria" style="display:inline">'
        '      <button class="btn fantasma" type="submit">%s</button>'
        '    </form>'
        '  </div>'
        '  <p class="lead" style="margin-top:1.4rem;font-size:.85rem">%s</p>'
        '</div>'
        % (esc(t("titulo_resultado", lang)),
           esc(t("msg_pregunta_buscar", lang)) % con_faltantes,
           esc(t("btn_si", lang)),
           esc(t("btn_no", lang)),
           esc(t("msg_busqueda_tarda", lang)))
    )
    return pagina(lang, t("titulo_resultado", lang), cuerpo, "/")


def ventana_buscando(lang):
    cuerpo = (
        '<div class="panel ancho centrado">'
        '  <h1>%s</h1>'
        '  <p class="lead">%s</p>'
        '  <div class="barra-prog"><span id="barra"></span></div>'
        '  <p class="contador" id="txt">%s</p>'
        '</div>'
        % (esc(t("titulo_busqueda", lang)),
           esc(t("msg_buscando", lang)),
           esc(t("msg_preparando", lang)))
    )
    js = """<script>
var timer=setInterval(function(){
  fetch('/api/progreso').then(function(r){return r.json();}).then(function(d){
    var pct = d.total>0 ? Math.round(d.hechos*100/d.total) : 0;
    document.getElementById('barra').style.width = pct+'%';
    document.getElementById('txt').textContent = d.texto||'';
    if(d.listo){ clearInterval(timer); window.location.replace('/galeria'); }
  }).catch(function(){});
},600);
</script>"""
    return pagina(lang, t("titulo_busqueda", lang), cuerpo, "/", head_extra=js)


# --------------------------------------------------------------------------
# Ventana 4 - Galeria
# --------------------------------------------------------------------------

def _indice_carpetas():
    """Indice ruta -> carpeta, para no recorrer la lista en cada tarjeta."""
    if E.indice is None or len(E.indice) != len(E.carpetas):
        E.indice = {}
        for c in E.carpetas:
            E.indice[c["ruta"]] = c
            c["id"] = E.id_de(c["ruta"])
    return E.indice


def _estado_de_carpeta(ruta):
    """Devuelve el estado visible de una carpeta."""
    c = _indice_carpetas().get(ruta)
    if c is None:
        return None

    # Descargado manda sobre ya_tiene: una carpeta con poster descargado
    # tiene las dos marcas, y el inventario debe mostrar DESCARGADO.
    if c.get("descargado"):
        return DESCARGADO
    if c.get("ya_tiene"):
        return YA_TIENE
    info = E.resultados.get(ruta)
    if info and info.get("poster_url"):
        return SIN_POSTER
    if info is not None:
        return REVISION
    return PENDIENTE


def _mirar_subcarpeta(ruta):
    """
    Una sola pasada por la carpeta: cuantas subcarpetas tiene y si hay
    alguna imagen utilizable como poster. Devuelve (hijos, imagen).

    La imagen se busca aqui mismo, sin una lectura mas, porque para
    contar los hijos ya hubo que abrir la carpeta.
    """
    hijos = 0
    imagen = False
    try:
        with os.scandir(ruta) as entradas:
            for e in entradas:
                try:
                    if e.is_dir(follow_symlinks=False):
                        hijos += 1
                        continue
                except OSError:
                    continue
                if imagen:
                    continue
                try:
                    tamano = e.stat(follow_symlinks=False).st_size
                except OSError:
                    tamano = 0
                # Solo cuenta una imagen de verdad: nada de thumbs.db,
                # nada de iconos del sistema, nada por debajo del minimo.
                if escaneo._imagen_util(e.name, tamano):
                    imagen = True
    except OSError:
        return 0, False
    return hijos, imagen


def listar_subdirectorios(ruta_actual):
    """Lee la carpeta y devuelve las subcarpetas reales de la ruta."""
    try:
        entradas = sorted(os.scandir(ruta_actual), key=lambda e: e.name.lower())
    except Exception:
        return []

    indice = _indice_carpetas()
    salida = []
    for e in entradas:
        try:
            if not e.is_dir(follow_symlinks=False):
                continue
        except OSError:
            continue
        nombre = e.name
        if escaneo.es_excluida(nombre):
            continue
        hijos, imagen = _mirar_subcarpeta(e.path)
        escaneada = indice.get(e.path) or {}
        salida.append({
            "ruta": e.path,
            "nombre": nombre,
            "hijos": hijos,
            "id": E.id_de(e.path),
            "estado": _estado_de_carpeta(e.path),
            "tipo": escaneada.get("tipo"),
            "tiene_imagen": bool(imagen or escaneada.get("ya_tiene")
                                 or escaneada.get("descargado")),
        })
    return salida


def _unidad_de_ruta(ruta, unidades):
    if not ruta:
        return None

    try:
        candidata = os.path.normcase(os.path.abspath(ruta))
    except (OSError, ValueError):
        return None
    coincidentes = []
    for unidad in unidades or []:
        try:
            raiz = os.path.normcase(os.path.abspath(unidad))
            if os.path.commonpath((raiz, candidata)) == raiz:
                coincidentes.append(unidad)
        except (OSError, ValueError, TypeError):
            continue
    return max(coincidentes, key=len) if coincidentes else None


def _contadores(items):
    con = sum(1 for i in items if i["estado"] in (YA_TIENE, DESCARGADO))
    sin = sum(1 for i in items if i["estado"] in
              (SIN_POSTER, PENDIENTE, REVISION))
    rev = sum(1 for i in items if i["estado"] == REVISION)
    return con, sin, rev


def _filtrar(items, lang, filtro, orden, texto):
    if filtro == "con":
        items = [i for i in items if i["estado"] in (YA_TIENE, DESCARGADO)]
    elif filtro == "sin":
        items = [i for i in items if i["estado"] in (SIN_POSTER, PENDIENTE)]
    elif filtro == "revision":
        items = [i for i in items if i["estado"] == REVISION]

    if texto:
        q = texto.strip().lower()
        items = [i for i in items if q in post.quitar_acentos(i["nombre"]).lower()]

    if orden == "za":
        items.sort(key=lambda i: post.quitar_acentos(i["nombre"]).lower(), reverse=True)
    elif orden == "hijos":
        items.sort(key=lambda i: (-i["hijos"], post.quitar_acentos(i["nombre"]).lower()))
    else:
        items.sort(key=lambda i: post.quitar_acentos(i["nombre"]).lower())
    return items


def _dispositivo_de(ruta):
    """Clave que iconos.py entiende para cada unidad."""
    try:
        tipo = (escaneo._unidades_wmi().get(
            os.path.abspath(ruta), {}) or {}).get("tipo") or ""
    except Exception:
        tipo = ""
    n = post.quitar_acentos(tipo).lower()
    if "red" in n:
        return "red"
    if "extra" in n or "usb" in n or "remov" in n:
        return "extraible"
    if "cd" in n or "optical" in n:
        return "cd"
    return "local"


def _ruta_corta(ruta, limite=46):
    """
    9.5 Ruta completa pero reducida si es larga:
    C:\\Users\\1\\Videos\\...\\Rosario Tijeras
    """
    if not ruta:
        return ""
    if len(ruta) <= limite:
        return ruta
    partes = [p for p in ruta.replace("/", "\\").split("\\") if p]
    if len(partes) <= 2:
        return "...\\" + partes[-1] if partes else ruta
    mitad = len(partes) // 2
    izq = "/".join(partes[:mitad])
    der = "/".join(partes[mitad:])
    return "%s/.../%s" % (izq, der)


def _icono_de_carpeta(item):
    """
    Icono grande de la tarjeta: de disco si es una unidad, y de carpeta
    con su tipo de contenido si es una carpeta.
    """
    if item.get("es_unidad"):
        return iconos.por_dispositivo(
            item.get("tipo_dispositivo") or "local")
    tipo = item.get("tipo") or _tipo_de_carpeta(item.get("nombre") or "")
    return iconos.por_tipo(tipo)


def _icono_tipo(tipo):
    """Chiquito de la esquina con el tipo de contenido."""
    if not tipo:
        return ""
    return ('<span class="tipo-icono" title="%s">%s</span>'
            % (esc(tipo), iconos.por_tipo(tipo, 'class="mini"')))


def _tarjeta(item, lang, orden=0):
    est = item["estado"]
    es_unidad = item.get("es_unidad", False)

    if es_unidad:
        clase, texto = "", t("msg_unidad", lang)
    elif est is None:
        clase, texto = "sin-escanear", t("msg_carpeta_sin_escanear", lang)
    elif est == PENDIENTE:
        clase, texto = "pendiente", t("msg_pendiente_busqueda", lang)
    elif est == YA_TIENE:
        clase, texto = "tiene", t("msg_ya_tiene", lang)
    elif est == DESCARGADO:
        clase, texto = "tiene", t("msg_descargado", lang)
    elif est == REVISION:
        clase, texto = "rev", t("msg_sin_coincidencia", lang)
    else:
        clase, texto = "falta", t("msg_sin_poster", lang)

    tipo = item.get("tipo") or ("" if es_unidad
                                else _tipo_de_carpeta(item.get("nombre") or ""))

    # --- La caratula: la de la carpeta si la tiene, y si no la de
    #     internet. El orden importa: primero lo que ya esta en disco.
    caratula = None
    if not es_unidad:
        if item.get("tiene_imagen") or est in (YA_TIENE, DESCARGADO):
            caratula = "/api/cover?id=%d" % item["id"]
        else:
            info = E.resultados.get(item["ruta"]) or {}
            caratula = info.get("poster_url")

    if caratula:
        # Detras va el icono: si la imagen no carga, se ve la carpeta.
        marco = ('<div class="portada-vacia">%s<span>%s</span></div>'
                 % (_icono_de_carpeta(item),
                    esc(t("msg_carpeta_sin_escanear", lang))))
        marco += ('<img src="%s" alt="" loading="lazy" class="caratula"'
                  ' onerror="this.remove()">' % esc(caratula))
    else:
        marco = ('<div class="portada-vacia">%s<span>%s</span></div>'
                 % (_icono_de_carpeta(item),
                    esc(t("msg_unidad", lang) if es_unidad
                        else t("msg_sin_poster", lang))))

    insignia = ('<span class="insignia" title="%s">%d</span>'
                % (esc(t("msg_subcarpetas", lang)), item["hijos"])
                if item.get("hijos") else "")

    # --- Marca para descargar ---
    carpeta_escaneada = _indice_carpetas().get(item["ruta"])
    seleccionable = bool(
        not es_unidad and carpeta_escaneada and
        not carpeta_escaneada.get("ya_tiene"))
    marca = "" if not seleccionable else (
        '<button type="button" class="marca-check"'
        ' onclick="marcarClick(event,%d)" aria-label="%s"'
        ' aria-pressed="%s">&#10003;</button>'
        % (item["id"], esc(t("msg_marca_clic", lang)),
           "true" if item["ruta"] in E.marcadas else "false"))

    eventos = 'ondblclick="entrar(%d)"' % item["id"]
    if not es_unidad:
        eventos += ' oncontextmenu="marcar(event,%d)"' % item["id"]

    retraso = min(orden * 26, 420)

    return (
        '<div class="tarjeta%s%s" data-ruta="%d" data-nombre="%s" %s'
        ' title="%s" style="animation-delay:%dms">'
        '  <div class="marco">%s%s%s</div>'
        '  <div class="info">'
        '    <div class="nombre">%s</div>'
        '    <div class="ruta">%s</div>'
        '    <div class="estado %s"><i></i>%s</div>'
        '  </div>'
        '</div>'
        % (" marcada" if item["ruta"] in E.marcadas else "",
           " tarjeta-unidad" if es_unidad else "",
           item["id"], esc(post.quitar_acentos(item["nombre"]).lower()),
           eventos, esc(t("msg_marca_derecha", lang)), retraso,
           marco, insignia, marca + _icono_tipo("" if es_unidad else tipo),
           esc(item["nombre"]),
           esc(_ruta_corta(item["ruta"])),
           clase, esc(texto)))


def ventana_galeria(lang, ruta_actual, filtro="todas", orden="az", texto=""):
    unidades = E.unidades_elegidas or [u["ruta"] for u in E.unidades]
    vista_unidades = ruta_actual is None

    # --- pestanas de unidad ---
    pestanas = []
    for u in E.unidades:
        if u["ruta"] not in unidades:
            continue
        activa = " on" if ruta_actual and os.path.normcase(
            os.path.abspath(u["ruta"])) == os.path.normcase(
                os.path.abspath(ruta_actual)) else ""
        cid = E.id_de(u["ruta"])
        pestanas.append(
            '<a class="pestana%s" href="/galeria?ruta=%d">%s'
            '<span class="libre">%s</span></a>'
            % (activa, cid, esc(u["ruta"]),
               esc(escaneo.formatear_bytes(u.get("libre"))))
        )

    # --- migas de pan ---
    migas = []
    unidad_actual = _unidad_de_ruta(ruta_actual, unidades)
    if not vista_unidades and unidad_actual:
        cid = E.id_de(unidad_actual)
        migas.append('<a onclick="ir(\'/galeria?ruta=%d\')">%s</a>'
                     % (cid, esc(unidad_actual)))
        try:
            rel = os.path.relpath(ruta_actual, unidad_actual)
        except (OSError, ValueError):
            rel = ""
        if rel and rel != ".":
            acumulado = unidad_actual
            for parte in rel.split(os.sep):
                acumulado = os.path.join(acumulado, parte)
                cid = E.id_de(acumulado)
                migas.append('<a onclick="ir(\'/galeria?ruta=%d\')">%s</a>'
                             % (cid, esc(parte)))
    ruta_html = ('<span class="sep">&#9656;</span>'.join(migas)
                 if migas else "")

    # --- volver al padre o salir a la seleccion de unidades ---
    padre = os.path.dirname(os.path.normpath(ruta_actual)) if ruta_actual else ""
    dentro_de_subcarpeta = bool(
        unidad_actual and os.path.normcase(os.path.abspath(ruta_actual)) !=
        os.path.normcase(os.path.abspath(unidad_actual)) and
        _unidad_de_ruta(padre, [unidad_actual]))
    if dentro_de_subcarpeta:
        cid_padre = E.id_de(padre)
        boton_subir = ('<button class="btn chico fantasma" '
                       'onclick="ir(\'/galeria?ruta=%d\')">%s</button>'
                       % (cid_padre, esc(t("btn_subir", lang))))
    else:
        boton_subir = ""

    # --- items ---
    if vista_unidades:
        items = []
        for unidad in E.unidades:
            if unidad["ruta"] not in unidades:
                continue
            items.append({
                "ruta": unidad["ruta"],
                "nombre": unidad["ruta"],
                "hijos": 0,
                "id": E.id_de(unidad["ruta"]),
                "estado": None,
                "es_unidad": True,
                "tipo_dispositivo": unidad.get("tipo_icono")
                or _dispositivo_de(unidad["ruta"]),
                "tiene_imagen": False,
            })
    else:
        items = listar_subdirectorios(ruta_actual)
    con, sin, rev = _contadores(items)
    visibles = _filtrar(list(items), lang,
                        "todas" if vista_unidades else filtro,
                        orden, "" if vista_unidades else texto)
    cid_actual = E.id_de(ruta_actual) if ruta_actual else 0

    tarjetas = "".join(_tarjeta(i, lang, k) for k, i in enumerate(visibles))
    if not tarjetas:
        tarjetas = '<div class="vacio">%s</div>' % esc(t("msg_sin_carpetas", lang))

    # --- filtros ---
    def clase_f(f):
        return " on" if filtro == f else ""

    filtros = (
        '<div class="filtros">'
        '<button class="filtro%s" onclick="setFiltro(\'todas\')">%s</button>'
        '<button class="filtro%s" onclick="setFiltro(\'con\')">%s</button>'
        '<button class="filtro%s" onclick="setFiltro(\'sin\')">%s</button>'
        '<button class="filtro%s" onclick="setFiltro(\'revision\')">%s</button>'
        '</div>'
        % (clase_f("todas"), esc(t("filtro_todas", lang)),
           clase_f("con"), esc(t("filtro_con_poster", lang)),
           clase_f("sin"), esc(t("filtro_sin_poster", lang)),
           clase_f("revision"), esc(t("filtro_sin_coincidencia", lang)))
    )

    barra = (
        '<div class="migas">%s</div>'
        '<div class="herramientas">%s'
        '  <a class="btn chico fantasma" href="/galeria?vista=unidades">%s</a>'
        '  <input class="campo" id="q" placeholder="%s" value="%s" oninput="buscar()">'
        '  <select class="campo" onchange="ir(this.value)">'
        '    <option value="/galeria?ruta=%d&filtro=%s&orden=az"%s>%s</option>'
        '    <option value="/galeria?ruta=%d&filtro=%s&orden=za"%s>%s</option>'
        '    <option value="/galeria?ruta=%d&filtro=%s&orden=hijos"%s>%s</option>'
        '  </select>'
        '  <span class="cifras"><b>%d</b> %s &middot; <b>%d</b> %s &middot; <b>%d</b> %s</span>'
        '</div>'
        '<div class="herramientas" style="margin-top:-.4rem">'
        '  %s'
        '  <button class="btn chico" onclick="descargar(\'lote\')">%s</button>'
        '  <a class="btn chico fantasma" href="/revision">%s</a>'
        '  <button class="btn chico fantasma" onclick="descargar(\'seleccion\')">%s</button>'
        '  <button class="btn chico fantasma" onclick="selFaltan()">%s</button>'
        '  <button class="btn chico fantasma" onclick="limpiar()">%s</button>'
        '  <span class="cifras"><b id="nmarc">%d</b> %s</span>'
        '</div>'
        '<div class="fila">%s</div>'
        % (ruta_html, filtros, esc(t("btn_unidades", lang)),
           esc(t("buscar_placeholder", lang)), esc(texto),
           cid_actual, filtro, " selected" if orden == "az" else "",
           esc(t("orden_az", lang)),
           cid_actual, filtro, " selected" if orden == "za" else "",
           esc(t("orden_za", lang)),
           cid_actual, filtro, " selected" if orden == "hijos" else "",
           esc(t("orden_subcarpetas", lang)),
           len(items), esc(t("msg_carpetas", lang)),
           con, esc(t("msg_con_poster", lang)),
           sin, esc(t("msg_sin_poster_plural", lang)),
           boton_subir,
           esc(t("btn_descargar_todo", lang)),
           esc(t("btn_revisar_uno", lang)),
           esc(t("btn_descargar_seleccion", lang)),
           esc(t("btn_seleccionar_faltan", lang)),
           esc(t("btn_limpiar_seleccion", lang)),
           len(E.marcadas), esc(t("msg_marcadas", lang)),
           tarjetas)
    )

    if vista_unidades:
        barra = (
            '<div class="panel ancho"><h1>%s</h1><p class="lead">%s</p></div>'
            '<div class="fila">%s</div>'
            % (esc(t("titulo_galeria_unidades", lang)),
               esc(t("msg_galeria_unidades", lang)), tarjetas)
        )

    cuerpo = ('<div class="pestanas">%s</div>%s' % ("".join(pestanas), barra))

    js = """<script>
var filtro=%s, orden=%s, texto=%s, RID=%d;

function entrar(id){ ir('/galeria?ruta='+id+'&filtro='+filtro+'&orden='+orden+'&q='+encodeURIComponent(texto)); }
function marcarClick(ev,id){ ev.stopPropagation(); marcar(ev,id); }
function marcar(ev,id){
  ev.preventDefault();
  fetch('/api/marcar',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id:id})})
    .then(function(r){return r.json();})
    .then(function(d){
      if(!d.ok){ throw new Error('No se pudo marcar la carpeta'); }
      var c=document.querySelector('.tarjeta[data-ruta="'+id+'"]');
      if(c){
        c.classList.toggle('marcada',!!d.seleccionada);
        var boton=c.querySelector('.marca-check');
        if(boton){ boton.setAttribute('aria-pressed',d.seleccionada?'true':'false'); }
      }
      document.getElementById('nmarc').textContent=d.marcadas;
    }).catch(function(){ alert('No se pudo cambiar la selección de la carpeta.'); });
}
function setFiltro(f){
  ir('/galeria?ruta='+RID+'&filtro='+f+'&orden='+orden+'&q='+encodeURIComponent(texto));
}
function ordenar(v){
  ir('/galeria?ruta='+RID+'&filtro='+filtro+'&orden='+v+'&q='+encodeURIComponent(texto));
}
function buscar(){
  texto=document.getElementById('q').value;
  var t=setTimeout(aplicar,220);
  if(t){clearTimeout(window.__t);} window.__t=t;
}
function aplicar(){
  var q=texto.trim().toLowerCase();
  var n=0;
  var tarjetas=document.querySelectorAll('.tarjeta');
  for(var i=0;i<tarjetas.length;i++){
    var c=tarjetas[i];
    var nombre=(c.getAttribute('data-nombre')||'');
    var visible = q==='' || nombre.indexOf(q)>=0;
    if(visible){
      c.style.display='';
      if(orden==='za'){ c.style.order = (-1*i)+''; }
      else if(orden==='hijos'){ c.style.order = (i)+''; }
      else { c.style.order = i+''; }
      n++;
    } else { c.style.display='none'; }
  }
  var cv=document.getElementById('cifraV');
  if(cv){ cv.textContent=n; }
}
function selFaltan(){
  fetch('/api/seleccionar-faltantes',{method:'POST'})
    .then(function(r){return r.json();})
    .then(function(d){ window.location.reload(); });
}
function limpiar(){
  fetch('/api/limpiar',{method:'POST'})
    .then(function(){ window.location.reload(); });
}
function descargar(modo){
  fetch('/api/descargar',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({modo:modo})})
    .then(function(r){return r.json();})
    .then(function(d){
      if(d && d.ok){ window.location.replace(d.url); }
      else { alert('No hay nada pendiente para descargar con esa opcion.'); }
    })
    .catch(function(){ alert('No se pudo iniciar la descarga.'); });
}
</script>""" % (json.dumps(filtro), json.dumps(orden), json.dumps(texto),
                 E.id_de(ruta_actual) if ruta_actual else 0)

    return pagina(lang, t("titulo_galeria", lang), cuerpo, "/galeria",
                  head_extra=js)


# --------------------------------------------------------------------------
# Resumen final
# --------------------------------------------------------------------------

def ventana_resumen(lang, resumen):
    filas = [
        (t("res_descargados", lang), resumen["descargados"], "tiene"),
        (t("res_ya_tenian", lang), resumen["ya_tenian"], "tiene"),
        (t("res_sin_coincidencia", lang), resumen["sin_coincidencia"], "rev"),
        (t("res_fallos", lang), resumen["fallos"], "rev"),
    ]
    cuerpo = (
        '<div class="panel ancho centrado">'
        '  <h1>%s</h1>'
        '  <p class="lead" style="margin-bottom:1.6rem">%s</p>'
        '  %s'
        '  <div class="fila-botones">'
        '    <a class="btn" href="/galeria">%s</a>'
        '    <a class="btn fantasma" href="/inventario">%s</a>'
        '  </div>'
        '</div>'
        % (esc(t("titulo_resumen", lang)),
           esc(t("msg_trabajo_listo", lang)),
           "".join('<p style="font-size:1.05rem;margin:.35rem 0">%s: '
                   '<b class="estado %s" style="font-size:1.15rem">%d</b></p>'
                   % (esc(nombre), clase, n) for nombre, n, clase in filas),
           esc(t("btn_abrir_galeria", lang)),
           esc(t("btn_ver_inventario", lang)))
    )
    return pagina(lang, t("titulo_resumen", lang), cuerpo, "/galeria")

# --------------------------------------------------------------------------
# Acerca de nosotros  (0.3)
# --------------------------------------------------------------------------

def bloques(texto):
    """Parte un texto largo en parrafos."""
    partes = [p.strip() for p in (texto or "").split("\n\n")]
    return [p for p in partes if p]


def ventana_acerca(lang, volver):
    """
    0.3 Acerca de nosotros. Los textos son los mismos de siempre; lo que
    cambia es la presentacion: cada trozo va en su tarjeta de color y los
    titulos se ponen en letra de libro (serif) con degradado dorado.
    """
    historia = "".join("<p>%s</p>" % esc(p)
                       for p in bloques(t("historia_texto", lang)))
    porque = "".join("<p>%s</p>" % esc(p)
                     for p in bloques(t("porque_texto", lang)))

    cuerpo = (
        '<div class="panel ancho">'

        '  <div class="ac-hero">'
        '    <img class="ac-logo" src="/logo.png" alt="QBASwing">'
        '    <h1 class="ac-tit">%s</h1>'
        '    <p class="ac-lema">&ldquo;%s&rdquo;</p>'
        '    <p class="lead">%s</p>'
        '  </div>'

        '  <div class="ac-rejilla">'
        '    <section class="ac-carta ac-oro">'
        '      <div class="ac-cara"><span class="ac-chip">%s</span>'
        '        <h2>%s</h2></div>'
        '      %s'
        '    </section>'
        '    <section class="ac-carta ac-zafiro">'
        '      <div class="ac-cara"><span class="ac-chip">%s</span>'
        '        <h2>%s</h2></div>'
        '      %s'
        '    </section>'
        '    <section class="ac-carta ac-esmeralda">'
        '      <div class="ac-cara"><span class="ac-chip">%s</span>'
        '        <h2>%s</h2></div>'
        '      %s'
        '    </section>'
        '  </div>'

        '  <div class="fila-botones">'
        '    <a class="btn" href="/%s">%s</a>'
        '  </div>'
        '</div>'
        % (esc(t("titulo_bienvenida", lang)),
           esc(t("slogan", lang)),
           esc(t("msg_bienvenida", lang)),

           iconos.carpeta(),
           esc(t("historia_titulo", lang)),
           historia,

           iconos.pelicula(),
           esc(t("porque_titulo", lang)),
           porque,

           iconos.disco_local(),
           esc(t("creditos_titulo", lang)),
           "<p>%s</p>" % esc(t("creditos_texto", lang)),

           esc_url(volver or "/"),
           esc(t("btn_volver", lang)))
    )
    return pagina(lang, t("acerca_de", lang), cuerpo, "/acerca")


def escribir_historia_archivo():
    """Genera ACERCA_DE_NOSOTROS.txt junto al programa."""
    try:
        partes = []
        partes.append("QBASWING COVERS v1.0")
        partes.append("QBASwing Designer")
        partes.append("")
        partes.append(t("historia_texto", "es"))
        partes.append("")
        partes.append(t("porque_texto", "es"))
        partes.append("")
        partes.append(t("creditos_texto", "es"))
        HISTORIA.write_text("\n".join(partes), encoding="utf-8")
    except Exception:
        pass


# --------------------------------------------------------------------------
# 11.1 inventario.csv
# --------------------------------------------------------------------------

COLUMNAS = ["RutaCarpeta", "NombreCarpeta", "Unidad", "Tipo", "Temporada",
            "AnioCarpeta", "Estado", "Fuente", "TituloEncontrado",
            "AnioEncontrado", "TemporadaEncontrada", "Puntuacion",
            "UrlPoster", "RutaPoster", "TamanoBytes", "Notas"]


def escribir_inventario():
    """Guarda la tabla completa de la coleccion en utf-8-sig."""
    filas = []
    for c in sorted(E.carpetas, key=lambda x: post.quitar_acentos(
            x["nombre"]).lower()):
        ruta = c["ruta"]
        info = E.resultados.get(ruta) or {}
        estado = _estado_de_carpeta(ruta) or ""
        # Donde esta realmente el poster: en Descargas o, si era de la
        # version antigua, cover.jpg de la propia carpeta.
        destino = ""
        archivo_desc = base.descarga_de(ruta)
        carpeta_desc = _carpeta_descargas(crear=False)
        if archivo_desc:
            posible = os.path.join(carpeta_desc, archivo_desc)
            if os.path.isfile(posible):
                destino = posible
        if not destino and os.path.isfile(os.path.join(ruta, COVER_NAME)):
            destino = os.path.join(ruta, COVER_NAME)
        tam = 0
        nota = ""
        if destino:
            try:
                tam = os.path.getsize(destino)
            except OSError:
                tam = 0
        if estado == YA_TIENE:
            nota = "Carpeta con imagen previa, no se toco"
        elif estado == REVISION:
            nota = "Sin coincidencia por revision manual"
        elif estado == SIN_POSTER:
            nota = "Sin poster en las bases consultadas"
        filas.append([
            ruta,
            c.get("nombre", ""),
            c.get("unidad", ""),
            c.get("tipo", ""),
            str(c.get("temporada") or ""),
            str(c.get("anio") or ""),
            estado,
            info.get("fuente", ""),
            info.get("titulo", ""),
            str(info.get("ano") or ""),
            str(info.get("temporada_encontrada") or ""),
            str(info.get("puntuacion") or ""),
            info.get("poster_url", ""),
            destino if estado == DESCARGADO else "",
            str(tam),
            nota,
        ])

    try:
        with open(INVENTARIO, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(COLUMNAS)
            for fila in filas:
                w.writerow(fila)
        return len(filas)
    except Exception as exc:
        _log("No se pudo escribir inventario.csv: %s" % exc, "ERROR")
        return 0


def _log(mensaje, nivel="INFO"):
    try:
        from qbaswing_covers import log
        log(mensaje, nivel)
    except Exception:
        pass


# --------------------------------------------------------------------------
# Hilos de trabajo
# --------------------------------------------------------------------------

def _hilo_escaneo(reanudar=False):
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
    """
    True si el poster de esa carpeta ya esta resuelto:
    - se descargo antes y el archivo sigue en Descargas\\QBASWING COVERS
    - o la carpeta origen ya tiene su cover.jpg (versiones antiguas)
    """
    archivo = base.descarga_de(ruta)
    if archivo:
        carpeta = _carpeta_descargas(crear=False)
        if os.path.isfile(os.path.join(carpeta, archivo)):
            return True
    try:
        return os.path.isfile(os.path.join(ruta, COVER_NAME))
    except Exception:
        return False


def _tipo_de_carpeta(nombre):
    """Clase aproximada para el inventario."""
    n = post.quitar_acentos(nombre or "").lower()
    if post.es_pelicula_de_serie(nombre):
        return "serie"
    if re.search(r"\b(documental|doc)\b", n):
        return "documental"
    if re.search(r"\b(anime|cartoon)\b", n):
        return "anime"
    if re.search(r"\b(novela|telenovela|soap opera)\b", n):
        return "serie"
    # Un marcador de temporada (T1, S01, 1x2, "Temporada 3") = serie.
    if post.extraer_temporada(nombre) is not None:
        return "serie"
    # Deportes (peleas, partidos, ligas): van como pelicula o como
    # especial de TV; la clase documental consulta las dos.
    if re.search(r"\b(deportes?|deportivos?|vs|versus|jornada|liga|"
                 r"partido|derbis?|combate|boxeo|mma|ufc|wwe|nba|"
                 r"futbol|baloncesto|voleibol|tenis|olimpiadas?|"
                 r"mundial|copa|maraton)\b", n):
        return "documental"
    return "pelicula"


_FAMILIAS_TIPO = {"pelicula": "peliculas", "serie": "series",
                  "anime": "animes", "documental": "documentales"}


def _tipos_de_carpeta(c):
    """5.0 El tipo se detecta solo: la carpeta consulta SUS APIs primero."""
    familia = _FAMILIAS_TIPO.get(c.get("tipo"))
    if familia in fuentes.TIPOS_APIS:
        return [familia]
    return None


def _unir_candidatos(a, b):
    """Junta dos busquedas sin repetir candidatos."""
    def clave(x):
        return "%s|%s" % (x.get("fuente") or "",
                          x.get("id") or x.get("url") or "")
    unidos = list(a)
    vistos = set(clave(x) for x in unidos)
    for x in b:
        k = clave(x)
        if k not in vistos:
            vistos.add(k)
            unidos.append(x)
    return unidos


def _buscar_carpeta(c):
    """
    6 Consulta las APIs para UNA carpeta y guarda el resultado en
    E.resultados. Nunca lanza excepcion: si algo revienta, la carpeta
    queda con error y el hilo sigue adelante.
    """
    ruta = c["ruta"]
    titulo = c.get("titulo") or post.limpiar_nombre(c["nombre"])
    tipos = _tipos_de_carpeta(c)
    try:
        candidatos = fuentes.buscar(E.cfg, titulo, c.get("anio"),
                                    c.get("temporada"), tipos or E.tipos)

        # 6.3 El poster de temporada es distinto al general.
        mejor, motivo, puntuados = post.elegir_mejor(
            candidatos, titulo, c.get("anio"), c.get("temporada"))

        # Si el tipo detectado no dio respuesta clara, se consulta el
        # resto de APIs; la cache hace gratis lo que ya se pregunto.
        if tipos and (mejor is None or motivo == "empate"):
            extras = fuentes.buscar(E.cfg, titulo, c.get("anio"),
                                    c.get("temporada"), ["todos"])
            if extras:
                mejor, motivo, puntuados = post.elegir_mejor(
                    _unir_candidatos(candidatos, extras),
                    titulo, c.get("anio"), c.get("temporada"))

        if mejor is None:
            if motivo == "empate":
                E.resultados[ruta] = {"empate": True, "poster_url": None,
                                      "candidatos": puntuados}
            else:
                E.resultados[ruta] = {"poster_url": None,
                                      "candidatos": puntuados}
            return

        url_temporada = fuentes.poster_de_temporada(
            E.cfg, mejor.get("tipo"), mejor.get("id"), c.get("temporada"))
        E.resultados[ruta] = {
            "titulo": mejor.get("titulo"),
            "ano": mejor.get("ano"),
            "tipo": mejor.get("tipo"),
            "fuente": mejor.get("fuente"),
            "poster_url": url_temporada or mejor.get("poster_url"),
            "id": mejor.get("id"),
            "puntuacion": mejor.get("puntuacion"),
            "temporada_encontrada": c.get("temporada"),
            "candidatos": puntuados,
        }
    except Exception as exc:
        _log("Fallo al buscar %s: %s" % (titulo, exc), "ERROR")
        E.resultados[ruta] = {"error": True, "poster_url": None}


def _hilo_busqueda():
    """Consulta las APIs para cada carpeta que todavia no tiene poster."""
    pendientes = [c for c in E.carpetas if not c.get("ya_tiene")]
    total = len(pendientes)
    E.progreso.update({"activo": True, "hechos": 0, "total": total,
                       "texto": t("msg_preparando", E.lang), "listo": False})
    try:
        for i, c in enumerate(pendientes, 1):
            if E.parar.is_set():
                break
            titulo = c.get("titulo") or post.limpiar_nombre(c["nombre"])
            E.progreso["hechos"] = i - 1
            E.progreso["texto"] = t("msg_buscando_de", E.lang) % titulo
            _buscar_carpeta(c)
            E.progreso["hechos"] = i
    except Exception as exc:
        # Si esto se escapa, la pantalla de "Buscando..." se queda clavada
        # para siempre: el usuario lo ve como "no funcionan las APIs".
        _log("Fallo en la busqueda: %s" % exc, "ERROR")
    finally:
        # Pase lo que pase, el progreso termina en "listo" y la pantalla
        # avanza a la galeria.
        E.progreso.update({"activo": False, "listo": True,
                           "texto": t("msg_busqueda_lista", E.lang) % total})
        _log("Busqueda terminada: %d carpetas consultadas" % total)


# --------------------------------------------------------------------------
# 9.8 Descarga de posters
#
# El poster NO se escribe en la carpeta del video: se guarda en
#   Descargas\QBASWING COVERS\<nombre de la carpeta>.jpg
# con -2, -3... si dos carpetas se llaman igual. En el origen
# no se escribe NADA.
# --------------------------------------------------------------------------

_GENERICO_DESCARGA = re.compile(
    r"^(t\s?\d{1,3}|temporada\s?\d{1,3}|season\s?\d{1,3}|"
    r"cap\w*\s?\d{1,3}|ep\w*\s?\d{1,3}|"
    r"temporada|season|capitulo|capitulos|episodio|episodios|"
    r"especiales|specials|extras?|bonus|ovas?|"
    r"peliculas|pelis|series|anime|documentales)$")


def _raiz_descargas():
    """
    Carpeta Descargas del usuario. La busca en el registro de Windows,
    asi que aguanta carpetas renombradas ("Descargas") o en otro disco.
    Si no, usa ~/Downloads y, en ultimo caso, la carpeta del usuario.
    """
    try:
        import winreg
        k = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
        valor, _tipo = winreg.QueryValueEx(
            k, "{374DE290-123F-4565-9164-39C4925E4678}")
        winreg.CloseKey(k)
        if isinstance(valor, str) and valor and os.path.isdir(valor):
            return valor
    except Exception:
        pass
    casa = os.path.expanduser("~")
    descargas = os.path.join(casa, "Downloads")
    if os.path.isdir(descargas):
        return descargas
    return casa


def _carpeta_descargas(crear=True):
    """Descargas\\QBASWING COVERS. Con crear=False solo calcula la ruta."""
    carpeta = os.path.join(_raiz_descargas(), NOMBRE_DESCARGAS)
    if not crear:
        return carpeta
    try:
        os.makedirs(carpeta, exist_ok=True)
        return carpeta
    except OSError:
        _log("No se pudo crear la carpeta de descargas: %s" % carpeta, "ERROR")
        return None


def _padre_de(ruta):
    """Nombre de la carpeta padre, para nombrar carpetas genericas."""
    try:
        return os.path.basename(os.path.dirname(ruta))
    except Exception:
        return ""


def _nombre_descarga(ruta, nombre):
    """
    Nombre base del archivo en Descargas: el mismo de la carpeta.
    Si el nombre es generico (T1, Temporada 1, Episodios...) se le
    anade la carpeta padre, para que se vea de que serie es.
    """
    texto = (nombre or "").strip() or "poster"
    if _GENERICO_DESCARGA.match(post.quitar_acentos(texto).lower()):
        padre = (_padre_de(ruta) or "").strip()
        if padre:
            texto = "%s %s" % (padre, texto)
    # Windows prohibe estos signos en los nombres de archivo; una carpeta
    # de Windows no los puede tener, pero aqui se limpian por si acaso.
    for signo in '\\/:*?"<>|':
        texto = texto.replace(signo, "_")
    texto = texto.strip().rstrip(". ")
    if len(texto) > 200:
        texto = texto[:200].rstrip(". ")
    return texto or "poster"


def _destino_descarga(ruta, nombre):
    """
    Ruta final del poster de ESTA carpeta. Reutiliza el nombre que ya
    le toco y, si esta libre, busca el primero libre: base.jpg,
    base-2.jpg, base-3.jpg... Devuelve None si Descargas no funciona.
    """
    carpeta = _carpeta_descargas()
    if not carpeta:
        return None
    previo = base.descarga_de(ruta)
    if previo:
        anterior = os.path.join(carpeta, previo)
        if os.path.isfile(anterior):
            return anterior
    nombre_base = _nombre_descarga(ruta, nombre)
    archivo = nombre_base + ".jpg"
    contador = 2
    while os.path.exists(os.path.join(carpeta, archivo)):
        archivo = "%s-%d.jpg" % (nombre_base, contador)
        contador += 1
    return os.path.join(carpeta, archivo)


def _descargar_una(c):
    """
    Descarga el poster de UNA carpeta en Descargas\\QBASWING COVERS,
    con el nombre de la carpeta. El origen no se toca nunca.
    Devuelve (estado, tamano). Nunca sobrescribe ni borra nada.
    """
    ruta = c["ruta"]

    # 5.4 Si el origen ya tiene imagen, se respeta: no se descarga nada.
    if escaneo.tiene_imagen(ruta):
        return "ya_tiene_imagen", 0

    destino = _destino_descarga(ruta, c.get("nombre") or "")
    if not destino:
        return "fallo", 0

    # Si ya estaba descargada: se reporta y se salta.
    if os.path.isfile(destino):
        try:
            return "ya_existe", os.path.getsize(destino)
        except OSError:
            return "ya_existe", 0

    info = E.resultados.get(ruta) or {}
    url = info.get("poster_url")
    if not url:
        return "sin_poster", 0

    datos = fuentes.descargar_binario(url)
    if not datos:
        return "fallo", 0

    # 9.8 Menos de 15 KB se considera fallo y se borra el parcial.
    if len(datos) < MIN_POSTER_SIZE:
        return "fallo_pequeno", len(datos)

    temporal = destino + ".qbawing-parcial"
    try:
        with open(temporal, "wb") as f:
            f.write(datos)
        if os.path.isfile(destino):
            try:
                os.remove(temporal)
            except OSError:
                pass
            return "ya_existe", 0
        os.replace(temporal, destino)
    except Exception as exc:
        _log("No se pudo escribir en %s: %s" % (destino, exc), "ERROR")
        try:
            if os.path.isfile(temporal):
                os.remove(temporal)
        except OSError:
            pass
        return "fallo", 0

    base.registrar_descarga(ruta, os.path.basename(destino))
    c["descargado"] = True
    c["ya_tiene"] = True
    E.guardar_estado(ruta, estado=DESCARGADO, marcada=0,
                     fuente=info.get("fuente", ""),
                     titulo=info.get("titulo", ""),
                     url_poster=url,
                     puntuacion=info.get("puntuacion", 0))
    _log("Descargado: %s" % destino, "OK")
    return "ok", len(datos)


def _hilo_descarga(lista, motivo):
    """Descarga en segundo plano una lista de carpetas."""
    E.progreso.update({"activo": True, "hechos": 0, "total": len(lista),
                       "texto": t("msg_preparando", E.lang), "listo": False})
    resumen = {"descargados": 0, "ya_tenian": 0, "sin_coincidencia": 0,
               "fallos": 0}
    primera = None

    try:
        # Si nadie consulto las APIs todavia (el usuario fue directo a
        # "descargar" o dijo que no a la busqueda), se consultan aqui:
        # sin una URL de poster no hay nada que bajar.
        for c in lista:
            if E.parar.is_set():
                break
            info = E.resultados.get(c["ruta"])
            if info is not None and not info.get("error"):
                continue
            titulo = c.get("titulo") or post.limpiar_nombre(c["nombre"])
            E.progreso["texto"] = t("msg_buscando_de", E.lang) % titulo
            _buscar_carpeta(c)

        for i, c in enumerate(lista, 1):
            if E.parar.is_set():
                break
            E.progreso["hechos"] = i - 1
            E.progreso["texto"] = t("msg_descargando_de", E.lang) % c["nombre"]

            estado, tam = _descargar_una(c)
            if estado == "ok":
                resumen["descargados"] += 1
                if primera is None:
                    primera = c["ruta"]
            elif estado in ("ya_existe", "ya_tiene_imagen"):
                resumen["ya_tenian"] += 1
            elif estado == "sin_poster":
                resumen["sin_coincidencia"] += 1
            else:
                resumen["fallos"] += 1
                _log("Fallo al descargar %s" % c["ruta"], "ERROR")
            E.progreso["hechos"] = i

        E.resumen = resumen
        escribir_inventario()
        _log("Descarga terminada (%s): %d descargados, %d ya tenian, "
             "%d sin coincidencia, %d fallos"
             % (motivo, resumen["descargados"], resumen["ya_tenian"],
                resumen["sin_coincidencia"], resumen["fallos"]))

        # 11.3 Abrir la carpeta de Descargas, donde estan los posters.
        if primera:
            _abrir_carpeta(_carpeta_descargas() or primera)
    except Exception as exc:
        # Un fallo sin registrar dejaba la pantalla de descarga clavada
        # sin resumen: el usuario lo ve como "no descarga nada".
        _log("Fallo en la descarga: %s" % exc, "ERROR")
    finally:
        E.resumen = resumen
        E.progreso.update({"activo": False, "listo": True,
                           "texto": t("msg_descarga_lista", E.lang)
                           % resumen["descargados"]})


def _abrir_carpeta(ruta):
    """Abre la carpeta en el explorador de Windows. Si no puede, no pasa nada."""
    try:
        os.startfile(ruta)          # noqa: F821  (solo Windows)
    except Exception:
        try:
            import subprocess
            subprocess.Popen(["explorer", ruta])
        except Exception:
            pass


def _abrir_archivo(ruta):
    """
    Abre un archivo con el programa que tenga asignado Windows
    (inventario.csv sale en Excel o en el bloc de notas).
    Si no hay con que abrirlo, se abre la carpeta que lo contiene.
    """
    if not ruta or not os.path.isfile(ruta):
        _abrir_carpeta(os.path.dirname(ruta or "") or ".")
        return
    try:
        os.startfile(ruta)          # noqa: F821  (solo Windows)
        return
    except Exception:
        pass
    try:
        import subprocess
        subprocess.Popen(["notepad.exe", ruta])
    except Exception:
        _abrir_carpeta(os.path.dirname(ruta))


def carpeta_por_id(cid):
    ruta = E.ruta_de(cid)
    if not ruta:
        return None
    return _indice_carpetas().get(ruta)


# --------------------------------------------------------------------------
# Revisar uno por uno  (9.8)
# --------------------------------------------------------------------------

def _pendientes_de_revision():
    lista = []
    for c in E.carpetas:
        if c.get("ya_tiene"):
            continue
        info = E.resultados.get(c["ruta"]) or {}
        if info.get("poster_url"):
            lista.append(c)
    return lista


def _revisar_alternativas(cid, lang):
    """Poster del resultado elegido + hasta 5 alternativas de la misma busqueda."""
    info = E.resultados.get(cid) or {}
    principal = info.get("poster_url")
    otros = []
    vistos = {principal}
    for cand in info.get("candidatos") or []:
        url = cand.get("poster_url")
        if not url or url in vistos:
            continue
        vistos.add(url)
        otros.append(cand)
        if len(otros) >= 5:
            break
    return principal, otros


def ventana_revision(lang, cid):
    if cid is None:
        lista = _pendientes_de_revision()
        if not lista:
            cuerpo = ('<div class="panel ancho centrado"><h1>%s</h1>'
                      '<div class="info">%s</div>'
                      '<div class="fila-botones"><a class="btn" href="/galeria">%s</a>'
                      '</div></div>'
                      % (esc(t("titulo_revision", lang)),
                         esc(t("msg_revision_vacia", lang)),
                         esc(t("btn_abrir_galeria", lang))))
            return pagina(lang, t("titulo_revision", lang), cuerpo, "/galeria")
        cid = E.id_de(lista[0]["ruta"])
        return _redir("/revision?carpeta=%d" % cid)

    ruta = E.ruta_de(cid)
    c = carpeta_por_id(cid)
    if not ruta or c is None:
        return _redir("/revision")

    info = E.resultados.get(ruta) or {}
    principal, otros = _revisar_alternativas(ruta, lang)

    galeria = []
    if principal:
        galeria.append('<img class="poster" src="%s" alt="">' % esc(principal))
    else:
        galeria.append('<div class="panel centrado" style="width:250px;'
                       'height:360px;display:flex;align-items:center;'
                       'justify-content:center;color:#9AA0A8">%s</div>'
                       % esc(t("msg_sin_poster", lang)))

    if otros:
        galeria.append('<div style="width:110px">')
        galeria.append('<div style="font-size:.78rem;color:#6B7280;'
                       'margin-bottom:.35rem">%s</div>'
                       % esc(t("msg_otras_opciones", lang)))
        for o in otros:
            galeria.append(
                '<a href="/revision?carpeta=%d&usar=%s" title="%s" '
                'style="display:block;margin-bottom:.4rem">'
                '<img src="%s" style="width:110px;border-radius:8px;'
                'border:2px solid #e2e8f2" alt=""></a>'
                % (cid, esc_url(o.get("poster_url") or ""),
                   esc(o.get("titulo", "")), esc(o.get("poster_url") or "")))
        galeria.append('</div>')

    cuerpo = (
        '<div class="panel">'
        '  <h1>%s</h1>'
        '  <p class="lead" style="margin-bottom:1.2rem">'
        '    <b>%s</b><br><span style="color:#9AA0A8;font-size:.86rem">%s</span></p>'
        '  <div class="revision">%s<div class="det">'
        '    <p><b>%s:</b> %s</p>'
        '    <p><b>%s:</b> %s</p>'
        '    <p><b>%s:</b> %s</p>'
        '    <p><b>%s:</b> %s</p>'
        '    <div class="fila-botones" style="justify-content:flex-start">'
        '      <button class="btn" onclick="ir(\'/revision?accion=aceptar&amp;carpeta=%d\')">%s</button>'
        '      <button class="btn fantasma" onclick="ir(\'/revision?accion=saltar&amp;carpeta=%d\')">%s</button>'
        '      <a class="btn fantasma" href="/galeria">%s</a>'
        '    </div>'
        '    <p style="margin-top:1rem;font-size:.86rem">%s <span class="kbd">%s</span> '
        '<span class="kbd">%s</span> <span class="kbd">%s</span></p>'
        '  </div></div>'
        '</div>'
        '<script>document.addEventListener("keydown",function(e){'
        ' var k=e.key.toLowerCase();'
        ' if(k=="a"){ir("/revision?accion=aceptar&carpeta=%d");}'
        ' if(k=="s"){ir("/revision?accion=saltar&carpeta=%d");}'
        ' if(k=="n"){ir("/revision?accion=siguiente&carpeta=%d");}'
        '});</script>'
        % (esc(t("titulo_revision", lang)),
           esc(c.get("nombre", "")),
           esc(ruta),
           "".join(galeria),
           esc(t("msg_carpeta_original", lang)),
           esc(c.get("nombre", "")),
           esc(t("msg_titulo_encontrado", lang)),
           esc(info.get("titulo", "") or "-"),
           esc(t("msg_fuente", lang)),
           esc(info.get("fuente", "") or "-"),
           esc(t("msg_puntuacion", lang)),
           str(info.get("puntuacion", "-")),
           cid, esc(t("btn_aceptar", lang)),
           cid, esc(t("btn_saltar", lang)),
           esc(t("btn_abrir_galeria", lang)),
           esc(t("msg_atajos_revision", lang)),
           esc(t("kbd_aceptar", lang)),
           esc(t("kbd_saltar", lang)),
           esc(t("kbd_siguiente", lang)),
           cid, cid, cid)
    )
    return pagina(lang, t("titulo_revision", lang), cuerpo, "/galeria")


def _redir(destino):
    """Redireccion interna. La ruta NO se codifica: solo se escapan los signos."""
    seguro = (destino or "/")
    seguro = (seguro.replace("&", "&amp;").replace("<", "&lt;")
              .replace(">", "&gt;").replace('"', "&quot;"))
    return ('<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<meta http-equiv="refresh" content="0;url=%s"></head>'
            '<body><a href="%s">Continuar</a></body></html>'
            % (seguro, seguro))


def _revision_accion(lang, accion, cid):
    """Aceptar, saltar o pasar a la siguiente en la revision uno por uno."""
    ruta = E.ruta_de(cid)
    c = carpeta_por_id(cid)

    if accion == "aceptar" and ruta and c is not None:
        info = E.resultados.get(ruta) or {}
        estado, _tam = _descargar_una(c)
        if estado in ("fallo", "fallo_pequeno"):
            _log("Fallo al aceptar %s" % ruta, "ERROR")

    # Saltar significa: descartar este resultado y buscar el siguiente candidato.
    if accion in ("saltar", "aceptar") and ruta:
        info = E.resultados.get(ruta)
        if info and info.get("candidatos"):
            restantes = [c2 for c2 in info["candidatos"]
                         if c2.get("poster_url") != info.get("poster_url")]
            if restantes:
                elegido, motivo, _p = post.elegir_mejor(
                    [dict(x, tipo_pedido=info.get("tipo")) for x in restantes],
                    c.get("titulo") or "", c.get("anio"), c.get("temporada"))
                if elegido and elegido.get("poster_url"):
                    info["poster_url"] = elegido["poster_url"]
                    info["titulo"] = elegido.get("titulo")
                    info["fuente"] = elegido.get("fuente")
                    info["puntuacion"] = elegido.get("puntuacion")
                    E.guardar_estado(ruta, estado=SIN_POSTER, marcada=0,
                                     fuente=info.get("fuente", ""),
                                     titulo=info.get("titulo", ""),
                                     url_poster=info.get("poster_url", ""),
                                     puntuacion=info.get("puntuacion", 0))
                    return _redir("/revision?carpeta=%d" % cid)
        info["poster_url"] = None

    # Siguiente: avanzar en la lista de pendientes.
    lista = _pendientes_de_revision()
    for i, c2 in enumerate(lista):
        if c2["ruta"] == ruta:
            if i + 1 < len(lista):
                return _redir("/revision?carpeta=%d" % E.id_de(lista[i + 1]["ruta"]))
            return _redir("/fin")
    if lista:
        return _redir("/revision?carpeta=%d" % E.id_de(lista[0]["ruta"]))
    return _redir("/fin")


# --------------------------------------------------------------------------
# Paginas de estado
# --------------------------------------------------------------------------

def ventana_descargando(lang):
    cuerpo = (
        '<div class="panel ancho centrado">'
        '  <h1>%s</h1>'
        '  <p class="lead">%s</p>'
        '  <div class="barra-prog"><span id="barra"></span></div>'
        '  <p class="contador" id="txt">%s</p>'
        '</div>'
        % (esc(t("titulo_descargando", lang)),
           esc(t("msg_descargando", lang)),
           esc(t("msg_preparando", lang)))
    )
    js = """<script>
var timer=setInterval(function(){
  fetch('/api/progreso').then(function(r){return r.json();}).then(function(d){
    var pct = d.total>0 ? Math.round(d.hechos*100/d.total) : 0;
    document.getElementById('barra').style.width = pct+'%';
    document.getElementById('txt').textContent = d.texto||'';
    if(d.listo){ clearInterval(timer); window.location.href='/fin'; }
  }).catch(function(){});
},500);
</script>"""
    return pagina(lang, t("titulo_descargando", lang), cuerpo, "/galeria",
                  head_extra=js)


def ventana_inventario(lang):
    if not INVENTARIO.exists():
        cuerpo = ('<div class="panel ancho centrado"><h1>%s</h1>'
                  '<div class="info">%s</div>'
                  '<div class="fila-botones"><a class="btn" href="/galeria">%s</a>'
                  '</div></div>'
                  % (esc(t("titulo_inventario", lang)),
                     esc(t("msg_sin_inventario", lang)),
                     esc(t("btn_abrir_galeria", lang))))
        return pagina(lang, t("titulo_inventario", lang), cuerpo, "/galeria")

    cuerpo = (
        '<div class="panel">'
        '  <h1>%s</h1>'
        '  <p class="lead" style="margin-bottom:1rem">%s</p>'
        '  <div class="fila-botones" style="justify-content:flex-start">'
        '    <button class="btn" onclick="ir(\'/api/abrir-inventario\')">%s</button>'
        '    <a class="btn fantasma" href="/galeria">%s</a>'
        '  </div>'
        '  <div class="info" style="margin-top:1.4rem">%s</div>'
        '</div>'
        % (esc(t("titulo_inventario", lang)),
           esc(str(INVENTARIO)),
           esc(t("btn_abrir_csv", lang)),
           esc(t("btn_abrir_galeria", lang)),
           esc(t("msg_csv_excel", lang)))
    )
    return pagina(lang, t("titulo_inventario", lang), cuerpo, "/galeria")


# --------------------------------------------------------------------------
# Manejador HTTP
# --------------------------------------------------------------------------

class Manejador(BaseHTTPRequestHandler):
    server_version = "QBASWINGCovers/1.0"
    sys_version = ""

    # --- silencio en la terminal, el log lo lleva qbaswing_covers.log ---
    def log_message(self, formato, *args):
        return

    # --- utilidades ---
    def _enviar(self, cuerpo, tipo="text/html; charset=utf-8", codigo=200):
        if isinstance(cuerpo, str):
            cuerpo = cuerpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        try:
            self.end_headers()
            self.wfile.write(cuerpo)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError,
                ConnectionError, OSError):
            # El navegador se fue a otra pantalla a media respuesta. Es
            # normal: 0.2 dice que la siguiente sustituye a la anterior.
            pass

    def _json(self, datos, codigo=200):
        self._enviar(json.dumps(datos, ensure_ascii=False),
                     "application/json; charset=utf-8", codigo)

    def _leer_json(self):
        try:
            largo = int(self.headers.get("Content-Length") or 0)
            if largo <= 0 or largo > 1_000_000:
                return {}
            return json.loads(self.rfile.read(largo).decode("utf-8", "replace"))
        except Exception:
            return {}

    # --- GET ---
    def do_GET(self):
        parsed = urlparse(self.path)
        ruta = parsed.path.rstrip("/") or "/"
        q = parse_qs(parsed.query)

        def v(clave, defecto=""):
            return (q.get(clave) or [defecto])[0]

        try:
            self._get(ruta, q, v)
        except Exception as exc:
            _log("Error en GET %s: %s" % (ruta, exc), "ERROR")
            # Si la pagina de error tampoco sale, se manda un texto pelado:
            # el programa nunca puede dejar al usuario sin respuesta.
            try:
                html = self._error_html()
            except Exception:
                html = ("<!DOCTYPE html><html lang=\"es\"><head>"
                        "<meta charset=\"utf-8\"><title>QBASWING COVERS</title>"
                        "</head><body style=\"font-family:Segoe UI,sans-serif;"
                        "padding:3rem;background:#F7F9FC\">"
                        "<h1 style=\"font-family:Georgia,serif;color:#2E6FD8\">"
                        "QBASWING COVERS</h1>"
                        "<p style=\"color:#6B7280\">Vuelve al inicio.</p>"
                        "<p><a href=\"/\" style=\"color:#2E6FD8\">QBASWING COVERS</a>"
                        "</p></body></html>")
            self._enviar(html, "text/html; charset=utf-8", 500)

    def _error_html(self):
        lang = E.lang if E else "es"
        cuerpo = ('<div class="panel ancho centrado"><h1>%s</h1>'
                  '<div class="aviso">%s</div>'
                  '<div class="fila-botones"><a class="btn" href="/">%s</a>'
                  '</div></div>'
                  % (esc(t("err_titulo", lang)), esc(t("err_cuerpo", lang)),
                     esc(t("btn_volver_inicio", lang))))
        return pagina(lang, t("err_titulo", lang), cuerpo, "/")

    def _get(self, ruta, q, v):
        global E
        lang = E.lang

        # --- cambio de idioma (0.2) ---
        if "lang" in q:
            nuevo = v("lang", "es")
            if nuevo in ("es", "en"):
                E.lang = nuevo
                E.cfg["idioma"] = nuevo
                try:
                    import qbaswing_covers
                    qbaswing_covers.guardar_config(E.cfg)
                except Exception:
                    pass
            destino = v("volver", "/") or "/"
            self._enviar(_redir(destino))
            return

        # --- portadas para la portada del programa ---
        if ruta == "/api/portadas":
            limite = self._entero(v("limite")) or 12
            lista = []
            try:
                lista = fuentes.portadas_destacadas(E.cfg, max(1, min(limite, 24)))
            except Exception:
                lista = []
            self._json({"portadas": lista})
            return

        # --- cifras de tu coleccion ---
        if ruta == "/api/resumen":
            try:
                self._json(base.resumen())
            except Exception:
                self._json({})
            return

        # --- logo ---
        if ruta == "/logo.png":
            self._enviar_archivo(LOGO, "image/png")
            return

        # --- API de progreso ---
        if ruta == "/api/progreso":
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
        # --- Cerrar el programa entero desde el navegador ---
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

        # --- cover local para las tarjetas ---
        if ruta == "/api/cover":
            cid = self._entero(v("id"))
            ruta_carpeta = E.ruta_de(cid) if cid else None
            if not ruta_carpeta:
                self._enviar(b"", "image/jpeg", 404)
                return
            # Primero: lo que se descargo a Descargas\QBASWING COVERS.
            archivo = base.descarga_de(ruta_carpeta)
            if archivo:
                posible = os.path.join(
                    _carpeta_descargas(crear=False), archivo)
                if os.path.isfile(posible):
                    self._enviar_archivo(posible)
                    return
            if not os.path.isdir(ruta_carpeta):
                self._enviar(b"", "image/jpeg", 404)
                return
            # Para la tarjeta sirve cualquier imagen buena de la carpeta,
            # aunque este en una subcarpeta tipo Posters/.
            imagen = escaneo.imagen_para_mostrar(ruta_carpeta)
            if not imagen:
                self._enviar(b"", "image/jpeg", 404)
                return
            self._enviar_archivo(imagen)
            return

        # --- abrir inventario.csv ---
        if ruta == "/api/abrir-inventario":
            if not INVENTARIO.exists():
                escribir_inventario()
            # El archivo, no la carpeta: es lo que pide el boton.
            _abrir_archivo(str(INVENTARIO))
            self._enviar(_redir("/inventario"))
            return

        # --- Ventana 1 ---
        if ruta == "/":
            E.paso = 1
            self._enviar(ventana_portada(lang))
            return

        # --- Ventana 2 ---
        if ruta == "/paso2":
            # 5.0 El tipo se detecta solo: no hay nada que elegir.
            E.tipos = ["todos"]
            E.cfg["tipos"] = E.tipos
            try:
                import qbaswing_covers
                qbaswing_covers.guardar_config(E.cfg)
            except Exception:
                pass
            if not E.unidades:
                _log("Detectando unidades del sistema")
                E.unidades = escaneo.detectar_unidades()
            self._enviar(ventana_discos(lang, E.unidades))
            return

        # --- Ventana 3 ---
        if ruta == "/paso3":
            elegidas = [x for x in (q.get("unidad") or []) if x]
            if not elegidas:
                cuerpo = (
                    '<div class="panel ancho centrado">'
                    '<h1>%s</h1><div class="aviso">%s</div>'
                    '<div class="fila-botones"><a class="btn" href="/paso2">%s</a>'
                    '</div></div>'
                    % (esc(t("titulo_discos", lang)),
                       esc(t("err_elige_unidad", lang)),
                       esc(t("btn_volver", lang)))
                )
                self._enviar(pagina(lang, t("titulo_discos", lang),
                                    cuerpo, "/paso2"))
                return
            E.unidades_elegidas = elegidas
            E.cfg["unidades"] = elegidas
            try:
                import qbaswing_covers
                qbaswing_covers.guardar_config(E.cfg)
            except Exception:
                pass
            E.carpetas = []
            E.resultados = {}
            E.marcadas = set()
            E.indice = None
            E.progreso.update({"activo": False, "hechos": 0, "total": 0,
                               "texto": t("msg_preparando", lang),
                               "listo": False})
            self._enviar(ventana_escaneo(lang, elegidas))
            # Arrancar despues de enviar la pagina: el hilo va aparte.
            reanudar = (q.get("reanudar") or ["0"])[0] in ("1", "si", "s")
            if elegidas and (E.hilo is None or not E.hilo.is_alive()):
                E.progreso["reanudado"] = reanudar
                E.hilo = threading.Thread(
                    target=_hilo_escaneo, kwargs={"reanudar": reanudar},
                    daemon=True)
                E.hilo.start()
            return

        # --- Ventana 4, pregunta ---
        if ruta == "/paso4":
            E.paso = 4
            faltan = sum(1 for c in E.carpetas if not c.get("ya_tiene"))
            self._enviar(ventana_pregunta(lang, faltan))
            return

        # --- Ventana 4, busqueda ---
        if ruta == "/buscar":
            if v("q") != "s":
                self._enviar(_redir("/paso4"))
                return
            E.progreso["listo"] = False
            self._enviar(ventana_buscando(lang))
            if E.hilo is None or not E.hilo.is_alive():
                E.hilo = threading.Thread(target=_hilo_busqueda, daemon=True)
                E.hilo.start()
            return

        # --- Ventana 4, galeria ---
        if ruta == "/galeria":
            self._enviar(self._galeria(q, v))
            return

        # --- Revisar uno por uno ---
        if ruta == "/revision":
            accion = v("accion")
            cid = self._entero(v("carpeta"))
            if accion:
                self._enviar(_revision_accion(lang, accion, cid))
                return
            usar = v("usar")
            if usar and cid:
                ruta_c = E.ruta_de(cid)
                if ruta_c:
                    info = E.resultados.setdefault(ruta_c, {})
                    info["poster_url"] = usar
            self._enviar(ventana_revision(lang, cid))
            return

        # --- Descargando ---
        if ruta == "/descargando":
            self._enviar(ventana_descargando(lang))
            return

        # --- Fin ---
        if ruta == "/fin":
            self._enviar(ventana_resumen(lang, E.resumen or {
                "descargados": 0, "ya_tenian": 0,
                "sin_coincidencia": 0, "fallos": 0}))
            return

        # --- Inventario ---
        if ruta == "/inventario":
            if not INVENTARIO.exists():
                escribir_inventario()
            self._enviar(ventana_inventario(lang))
            return

        # --- Acerca de nosotros ---
        if ruta == "/acerca":
            self._enviar(ventana_acerca(lang, v("volver", "/")))
            return

        self._enviar(self._error_html(), "text/html; charset=utf-8", 404)

    # --- POST ---
    def do_POST(self):
        parsed = urlparse(self.path)
        ruta = parsed.path.rstrip("/") or "/"
        datos = self._leer_json()

        try:
            if ruta == "/api/marcar":
                cid = self._entero(datos.get("id"))
                ruta_c = E.ruta_de(cid)
                c = carpeta_por_id(cid) if ruta_c else None
                if not ruta_c or c is None or c.get("ya_tiene"):
                    return self._json({"ok": False})
                if ruta_c in E.marcadas:
                    E.marcadas.discard(ruta_c)
                    if c:
                        c["marcada"] = False
                        E.guardar_estado(ruta_c, marcada=0)
                else:
                    E.marcadas.add(ruta_c)
                    if c:
                        c["marcada"] = True
                        E.guardar_estado(ruta_c, marcada=1)
                return self._json({"ok": True, "marcadas": len(E.marcadas),
                                   "seleccionada": ruta_c in E.marcadas})

            if ruta == "/api/seleccionar-faltantes":
                for c in E.carpetas:
                    info = E.resultados.get(c["ruta"]) or {}
                    if not c.get("ya_tiene") and info.get("poster_url"):
                        E.marcadas.add(c["ruta"])
                        c["marcada"] = True
                        E.guardar_estado(c["ruta"], marcada=1)
                return self._json({"ok": True, "marcadas": len(E.marcadas)})

            if ruta == "/api/limpiar":
                for ruta_c in E.marcadas:
                    c = carpeta_por_id(E.ids.get(ruta_c))
                    if c:
                        c["marcada"] = False
                    E.guardar_estado(ruta_c, marcada=0)
                E.marcadas.clear()
                return self._json({"ok": True, "marcadas": 0})

            if ruta == "/api/descargar":
                modo = datos.get("modo") or "lote"
                lista = self._lista_a_descargar(modo)
                if not lista:
                    return self._json({"ok": False, "motivo": "vacio"})
                E.progreso["listo"] = False
                self._json({"ok": True, "url": "/descargando"})
                E.hilo = threading.Thread(target=_hilo_descarga,
                                          args=(lista, modo), daemon=True)
                E.hilo.start()
                return

            self._json({"ok": False}, 404)
        except Exception as exc:
            _log("Error en POST %s: %s" % (ruta, exc), "ERROR")
            self._json({"ok": False}, 500)

    # --- apoyo ---
    @staticmethod
    def _entero(valor):
        try:
            return int(valor)
        except (TypeError, ValueError):
            return None

    def _enviar_archivo(self, ruta, tipo=None):
        try:
            with open(ruta, "rb") as f:
                datos = f.read()
        except Exception:
            self._enviar(b"", "application/octet-stream", 404)
            return
        if tipo is None:
            ext = os.path.splitext(ruta)[1].lower()
            tipo = {
                ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
            }.get(ext, "application/octet-stream")
        self._enviar(datos, tipo)

    def _lista_a_descargar(self, modo):
        if modo == "seleccion":
            return [c for c in E.carpetas if c["ruta"] in E.marcadas]
        return [c for c in E.carpetas if not c.get("ya_tiene")]

    def _galeria(self, q, v):
        lang = E.lang

        # Idioma si viene en la URL.
        if "lang" in q:
            nuevo = v("lang", "es")
            if nuevo in ("es", "en"):
                E.lang = nuevo
                lang = nuevo

        unidades = E.unidades_elegidas or [u["ruta"] for u in E.unidades]
        cid = self._entero(v("ruta"))
        ruta_actual = E.ruta_de(cid) if cid else None

        if not unidades:
            unidades = [u["ruta"] for u in E.unidades]
        if not unidades:
            cuerpo = ('<div class="panel ancho centrado"><h1>%s</h1>'
                      '<div class="aviso">%s</div>'
                      '<div class="fila-botones"><a class="btn" href="/">%s</a>'
                      '</div></div>'
                      % (esc(t("titulo_galeria", lang)),
                         esc(t("err_no_discos", lang)),
                         esc(t("btn_volver_inicio", lang))))
            return pagina(lang, t("titulo_galeria", lang), cuerpo, "/galeria")

        vista_unidades = v("vista") == "unidades" or not v("ruta")
        if not vista_unidades and (
                not ruta_actual or not os.path.isdir(ruta_actual) or
                not _unidad_de_ruta(ruta_actual, unidades)):
            vista_unidades = True
        if vista_unidades:
            ruta_actual = None

        # Dar id numerico a cada carpeta ya escaneada.
        for c in E.carpetas:
            c["id"] = E.id_de(c["ruta"])

        filtro = v("filtro", "todas")
        if filtro not in ("todas", "con", "sin", "revision"):
            filtro = "todas"
        orden = v("orden", "az")
        if orden not in ("az", "za", "hijos"):
            orden = "az"
        texto = v("q", "")[:80]

        return ventana_galeria(lang, ruta_actual, filtro, orden, texto)


# --------------------------------------------------------------------------
# 9.1 Servidor local
# --------------------------------------------------------------------------

SERVIDOR = None


class ServidorGaleria(object):
    """
    Servidor web local. Escucha solo en 127.0.0.1, nunca en la red.
    """

    def __init__(self, cfg, puerto):
        global E
        self.cfg = cfg
        self.puerto = puerto
        E = Estado(cfg)
        self.httpd = None

    def arrancar(self):
        escribir_historia_archivo()
        E.abrir_db()

        # Recargar lo marcado de la sesion anterior (10.1 punto 6).
        try:
            db = E.abrir_db()
            filas = db.execute(
                "SELECT ruta FROM estado WHERE marcada=1 AND estado<>?",
                (DESCARGADO,)).fetchall()
            for (ruta,) in filas:
                if os.path.isdir(ruta):
                    E.marcadas.add(ruta)
        except Exception:
            pass

        for intento in range(30):
            try:
                self.httpd = ThreadingHTTPServer(("127.0.0.1", self.puerto),
                                                Manejador)
                self.httpd.daemon_threads = True
                break
            except OSError:
                time.sleep(0.2)
        else:
            raise OSError("No se pudo abrir el puerto %d" % self.puerto)

        self.hilo = threading.Thread(target=self.httpd.serve_forever,
                                     kwargs={"poll_interval": 0.4}, daemon=True)
        self.hilo.start()
        global SERVIDOR
        SERVIDOR = self
        _log("Servidor local escuchando en 127.0.0.1:%d" % self.puerto)
        return self.httpd

    def esperar(self):
        try:
            while True:
                time.sleep(0.5)
                if self.cerrado:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            self.parar()

    cerrado = False

    def parar(self):
        self.cerrado = True
        E.parar.set()
        try:
            if self.httpd:
                self.httpd.shutdown()
                self.httpd.server_close()
        except Exception:
            pass
        _log("Servidor detenido")
