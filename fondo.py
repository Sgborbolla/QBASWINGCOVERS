# -*- coding: utf-8 -*-
"""
QBASWING COVERS - Fondo de las pantallas.

Todas las ventanas llevan el fondo lleno de portada, como la pantalla
de inicio, pero con movimiento:

  - El mural: una pared de Posters repartidos por TODA la pantalla,
    abajo de todo, desenfocada para que se vea como una mancha de color
    y no estorbe para leer. La pared entera se desliza muy despacio.
  - La tira: Posters nitidos en los bordes, y cada uno se mueve por su
    cuenta, como los vinilos colgados de una pared.

Cada lienzo es un tipo distinto de contenido audiovisual: peliculas,
series, anime, novelas, manga, musica, documentales y clasicos.

Los Posters los dibuja el propio programa, asi que:

  - No hay ninguna imagen ajena dentro del .exe.
  - No hace falta internet para que el fondo se vea.
  - Se ven de inmediato: no hay nada que esperar a que cargue.

Si hay internet, el navegador cambia esos dibujos por Posters reales de
TMDB y AniList (los mismos de la portada). Si no hay internet, se queda
con los dibujos del programa y el fondo se ve igual de bonito.
"""

import re
import zlib

import iconos

# --------------------------------------------------------------------------
# Un color por cada tipo de contenido audiovisual
# --------------------------------------------------------------------------

COLORES = {
    "pelicula":   ("#1B3A8C", "#6B4BC4"),
    "serie":      ("#0B6F82", "#2E6FD8"),
    "anime":      ("#D6337E", "#7B3FD4"),
    "novela":     ("#A85C0C", "#6E3410"),
    "manga":      ("#B32B26", "#3A1C20"),
    "musica":     ("#5B22A8", "#D14FA0"),
    "documental": ("#176B3C", "#0F6C7A"),
    "clasico":    ("#7E5E1C", "#C79A3C"),
    "otro":       ("#3A4A63", "#7B8CA6"),
}

# El orden en que se reparten los lienzos. Los ocho tipos pasan siempre.
CICLO = ("pelicula", "serie", "anime", "novela",
         "manga", "musica", "documental", "clasico")

# El titulo que lleva cada lienzo, en los dos idiomas.
TITULOS = {
    "pelicula":   {"es": "Pel&iacute;culas", "en": "Movies"},
    "serie":      {"es": "Series", "en": "Series"},
    "anime":      {"es": "Anime", "en": "Anime"},
    "novela":     {"es": "Novelas", "en": "Novels"},
    "manga":      {"es": "Manga", "en": "Manga"},
    "musica":     {"es": "M&uacute;sica", "en": "Music"},
    "documental": {"es": "Documentales", "en": "Documentaries"},
    "clasico":    {"es": "Cl&aacute;sicos", "en": "Classics"},
    "otro":       {"es": "Otros", "en": "Others"},
}

ANCHO, ALTO = 66, 99


def esc(texto):
    """Escapa los cuatro caracteres que rompen el HTML."""
    return (str(texto or "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def titulo(tipo, lang="es"):
    d = TITULOS.get(tipo) or TITULOS["otro"]
    return d.get(lang) or d["es"]


# --------------------------------------------------------------------------
# El dibujo de cada lienzo
# --------------------------------------------------------------------------

def _dentro_de_icono(dibujo):
    """
    iconos.py devuelve un <svg> entero. Para meterlo dentro de otro
    <svg> solo hace falta quedarse con el dibujo de dentro.
    """
    d = dibujo.strip()
    d = re.sub(r"^<svg[^>]*>", "", d)
    d = re.sub(r"</svg>$", "", d)
    return d


def arte(tipo, semilla):
    """
    Un poster dibujado, del tipo pedido.

    El dibujo sale siempre igual: los numeros salen de una cuenta
    fija, no del azar, para que la pagina no cambie en cada recarga.
    """
    claro, oscuro = COLORES.get(tipo, COLORES["otro"])
    clave = "g%d" % semilla

    # El degradado va cambiando de angulo en cada lienzo.
    x1 = 10 + semilla % 55
    y1 = 4 + (semilla // 11) % 38
    x2 = 24 + (semilla // 17) % 52
    y2 = 58 + (semilla // 29) % 46

    # Tres manchas de luz, para que el degradado no quede plano.
    manchas = ""
    for k, opacidad in enumerate(("0.06", "0.09", "0.13")):
        cx = (semilla >> (k * 3 + 1)) % ANCHO
        cy = (semilla >> (k * 2 + 2)) % ALTO
        radio = 9 + ((semilla >> (k + 2)) % 24)
        manchas += ('<circle cx="%d" cy="%d" r="%d" fill="#FFFFFF" '
                    'opacity="%s"/>' % (cx, cy, radio, opacidad))

    # Las perforaciones de la tira de pelicula, en el canto izquierdo.
    hoyos = ""
    for k in range(6):
        hoyos += ('<rect x="2.4" y="%.1f" width="3.6" height="6.4" rx="1.6" '
                  'fill="#FFFFFF" opacity="0.22"/>' % (6 + k * 15.2))

    return (
        '<rect width="%d" height="%d" fill="url(#%s)"/>'
        '%s'
        '<path d="M0 26 L66 8 L66 34 L0 52 Z" fill="#FFFFFF" opacity="0.05"/>'
        '%s'
        '<rect x="0" y="74" width="66" height="25" fill="#0A1220" opacity="0.34"/>'
        '<rect x="6" y="80" width="36" height="4.2" rx="2.1" fill="#FFFFFF"'
        ' opacity="0.88"/>'
        '<rect x="6" y="88" width="21" height="3" rx="1.5" fill="#FFFFFF"'
        ' opacity="0.55"/>'
        '<g transform="translate(33,40) scale(0.46) translate(-48,-42)"'
        ' opacity="0.97">%s</g>'
        % (ANCHO, ALTO, clave, manchas, hoyos, _dentro_de_icono(iconos.por_tipo(tipo))))


def _simbolo(tipo):
    """Un <symbol> con el poster de ese tipo, para no repetirlo mil veces."""
    semilla = zlib.crc32(tipo.encode("utf-8")) % 65536
    return (
        '<symbol id="fa-%s" viewBox="0 0 %d %d">'
        '<defs><linearGradient id="g%d" gradientUnits="userSpaceOnUse"'
        ' x1="%d" y1="%d" x2="%d" y2="%d">'
        '<stop offset="0" stop-color="%s"/>'
        '<stop offset="1" stop-color="%s"/></linearGradient></defs>%s</symbol>'
        % (tipo, ANCHO, ALTO, semilla, 10 + semilla % 55, 4 + (semilla // 11) % 38,
           24 + (semilla // 17) % 52, 58 + (semilla // 29) % 46,
           COLORES.get(tipo, COLORES["otro"])[0],
           COLORES.get(tipo, COLORES["otro"])[1],
           arte(tipo, semilla)))


def _simbolos():
    return "".join(_simbolo(t) for t in CICLO)


# --------------------------------------------------------------------------
# El reparto de los Posters por la pantalla
# --------------------------------------------------------------------------

def _mural(semilla):
    """
    La pared de fondo: siete columnas por cinco filas, cada cartel
    con su sitio y su inclinacion. Se sale por los bordes a
    proposito, que luego el recorte y el desenfoque lo disimulan.

    La semilla mueve todo el reparto, para que ninguna pantalla se
    parezca a otra.
    """
    base = zlib.crc32(semilla.encode("utf-8")) if semilla else 0
    piezas = []
    n = 0
    for fila in range(5):
        for col in range(7):
            s = base + n * 101
            # Un reparto alterno, para que no salga en rejilla perfecta.
            x = col * 15.4 - 6 + ((s * 37) % 9) - 4
            y = fila * 24.5 - 10 + ((s * 53) % 11) - 5
            ancho = 21 + ((s * 29) % 7)
            giro = ((s * 47) % 21) - 10
            piezas.append((x, y, ancho, giro, n))
            n += 1
    return piezas


def _tira(semilla):
    """
    Los Posters nitidos: van por los bordes, que es donde no estorba
    para leer y donde se ven bien. La semilla tambien los reparte.
    """
    base = (zlib.crc32(("tira" + semilla).encode("utf-8")) % 7) if semilla else 0
    piezas = []
    n = 0
    # Columna izquierda y derecha, de arriba abajo, empezando por
    # un punto distinto en cada pantalla.
    for k in range(5):
        y = (k * 20 + base * 3) % 96 - 4
        s = base + n * 71
        piezas.append((-1.5, y, 10.5, ((s * 29) % 17) - 8, n)); n += 1
        piezas.append((91.0, y + 6, 11.0, ((s * 23) % 17) - 8, n)); n += 1
    # Y cuatro sueltos por arriba y por abajo, cruzados.
    for x, y, ancho in ((14, -4, 9.0), (48, -6, 10.0),
                        (78, -3, 9.5), (30, 92, 9.5)):
        s = base + n * 97
        piezas.append((x, y, ancho, ((s * 41) % 21) - 10, n)); n += 1
    return piezas


def _lienzo(tipo, numero, x, y, ancho, giro, clase):
    duracion = 7 + (numero * 13) % 11
    retraso = (numero * 29) % 9
    return (
        '<div class="f-lienzo %s" style="left:%s%%;top:%s%%;width:%svmax;'
        '--giro:%sdeg;--t:%ss;--d:%ss" data-tipo="%s" title="%s">'
        '<svg class="f-art" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid slice"'
        ' aria-hidden="true">'
        '<use href="#fa-%s" xlink:href="#fa-%s"/></svg>'
        '<span class="f-rotulo">%s</span></div>'
        % (clase, x, y, ancho, giro, duracion, retraso, tipo, titulo(tipo, "es"),
           ANCHO, ALTO, tipo, tipo, titulo(tipo, "es")))


def html(lang="es", semilla=""):
    """
    El fondo completo: mural, tira de los bordes, velo y el script.

    La semilla es el nombre de la pantalla. Con ella cambia el reparto
    de Posters, para que dos pantallas no se parezcan en nada.
    """
    mural = "".join(
        _lienzo(CICLO[n % len(CICLO)], n, x, y, ancho, giro, "f-mur")
        for (x, y, ancho, giro, n) in _mural(semilla))
    tira = "".join(
        _lienzo(CICLO[n % len(CICLO)], n, x, y, ancho, giro, "f-col")
        for (x, y, ancho, giro, n) in _tira(semilla))

    if lang != "es":
        for tipo in CICLO:
            viejo = titulo(tipo, "es")
            nuevo = titulo(tipo, lang)
            mural = mural.replace(">%s</span>" % viejo, ">%s</span>" % nuevo)
            tira = tira.replace(">%s</span>" % viejo, ">%s</span>" % nuevo)
            mural = mural.replace('title="%s"' % viejo, 'title="%s"' % nuevo)
            tira = tira.replace('title="%s"' % viejo, 'title="%s"' % nuevo)

    return ('<div class="fondo" data-semilla="%s" aria-hidden="true">'
            '<svg class="f-defs" width="0" height="0">%s</svg>'
            '<div class="f-capa f-mural">%s</div>'
            '<div class="f-capa f-tira">%s</div>'
            '<div class="f-velo"></div>'
            '</div>%s' % (esc(semilla), _simbolos(), mural, tira, _JS))


# --------------------------------------------------------------------------
# El navegador cambia los dibujos por Posters reales, si hay internet
# --------------------------------------------------------------------------

_JS = """<script>
/* El fondo ya se ve sin internet y ya se mueve. Si hay Posters de
   verdad de TMDB y AniList, se ponen encima, y cada pantalla con una
   mezcla distinta para que no se parezcan entre si. */
(function(){
  var raiz=document.querySelector('.fondo');
  if(!raiz){ return; }
  var semilla=raiz.getAttribute('data-semilla')||'';
  var guardada=null;
  try{ guardada=JSON.parse(sessionStorage.getItem('qc_fondo')||'null'); }catch(e){}
  if(guardada&&guardada.length){ poner(guardada); return; }
  fetch('/api/portadas?limite=30').then(function(r){return r.json();})
    .then(function(d){
      var p=(d&&d.portadas)||[];
      if(!p.length){ return; }
      var urls=p.map(function(x){ return {u:x.url, t:x.tipo||''}; });
      try{ sessionStorage.setItem('qc_fondo', JSON.stringify(urls)); }catch(e){}
      poner(urls);
    }).catch(function(){});

  /* Baraja fija a partir del nombre de la pantalla: la misma pantalla
     siempre sale igual, y dos pantallas nunca salen iguales. */
  function barajar(lista, clave){
    var s=2166136261, i;
    for(i=0;i<clave.length;i++){ s^=clave.charCodeAt(i); s=(s*16777619)>>>0; }
    for(i=lista.length-1;i>0;i--){
      s=(s*1664525+1013904223)>>>0;
      var j=s%(i+1), tmp=lista[i]; lista[i]=lista[j]; lista[j]=tmp;
    }
    return lista;
  }

  /* Cada cartel se lleva el Poster que sea de su mismo tipo. Si no
     queda ninguno de ese tipo, se va por orden, que tambien queda bien. */
  function poner(urls){
    var lienzos=raiz.querySelectorAll('.f-lienzo');
    var cola=barajar(urls.slice(), semilla);
    var primerTipo=raiz.querySelector('.f-lienzo');
    var giro=(primerTipo&&primerTipo.getAttribute('data-tipo')==='serie')?1:0;
    for(var i=0;i<lienzos.length;i++){
      var el=lienzos[i];
      var tipo=el.getAttribute('data-tipo')||'';
      var elegido=null;
      for(var j=0;j<cola.length;j++){
        if(familia(cola[j].t)===familia(tipo)){
          elegido=cola.splice(j,1)[0]; break;
        }
      }
      if(!elegido){ elegido=urls[(i*7+giro)%urls.length]; }
      if(!elegido||!elegido.u){ continue; }
      el.style.backgroundImage='url("'+elegido.u+'")';
      el.classList.add('con-foto');
    }
  }
  function familia(t){
    t=(t||'').toLowerCase();
    if(t==='pelicula'||t==='movie'||t==='peliculas'){ return 'pelicula'; }
    if(t==='serie'||t==='tv'||t==='series'){ return 'serie'; }
    if(t==='anime'){ return 'anime'; }
    return t||'otro';
  }

  /* Parallax: el raton mueve el mural y los Posters de los bordes. */
  var mural=raiz.querySelector('.f-mural'), tira=raiz.querySelector('.f-tira');
  if(mural&&tira&&!matchMedia('(prefers-reduced-motion:reduce)').matches){
    var x=0, y=0;
    document.addEventListener('mousemove',function(ev){
      var nx=(ev.clientX/window.innerWidth-.5)*2;
      var ny=(ev.clientY/window.innerHeight-.5)*2;
      x+= (nx-x)*.05; y+=(ny-y)*.05;
      mural.style.marginLeft=(-x*18)+'px';
      mural.style.marginTop=(-y*14)+'px';
      tira.style.marginLeft=(x*34)+'px';
      tira.style.marginTop=(y*26)+'px';
    });
  }
})();
</script>"""


# --------------------------------------------------------------------------
# Los estilos
# --------------------------------------------------------------------------

CSS = """
/* ---- fondo de portada en todas las pantallas ----
   La base (los tres brillos de MyServer) la pone .marca-agua en el
   servidor. Aqui solo van los Posters, por encima de ella. */
.fondo{position:fixed;inset:0;z-index:0;overflow:hidden;pointer-events:none;
  background:transparent}
.f-defs{position:absolute;width:0;height:0;overflow:hidden}
.f-capa{position:absolute;inset:-12%;will-change:transform}
/* El desenfoque se queda corto a proposito: si se pasa de largo los
   Posters dejan de leerse como Posters y solo queda una mancha de color. */
.f-mural{filter:blur(7px) saturate(1.4) brightness(.92);opacity:.78;
  animation:muralPaseo 64s ease-in-out infinite alternate}
@keyframes muralPaseo{
  0%  { transform:translate3d(-2.2%,-1.4%,0) scale(1.06) rotate(-.5deg); }
  50% { transform:translate3d( 1.8%, 1.6%,0) scale(1.12) rotate(.4deg); }
  100%{ transform:translate3d(-1.2%, 2.2%,0) scale(1.09) rotate(-.3deg); }
}
.f-tira{opacity:.96}

.f-lienzo{position:absolute;border-radius:12px;overflow:hidden;
  transform:rotate(var(--giro,0deg));
  animation:deriva var(--t,9s) ease-in-out var(--d,0s) infinite alternate}
@keyframes deriva{
  from{ translate:0 0; }
  to  { translate:0 -16px; }
}
@media (prefers-reduced-motion:reduce){
  .f-lienzo,.f-mural{ animation:none; }
}

.f-lienzo .f-art{display:block;width:100%;height:100%}
.f-lienzo .f-rotulo{position:absolute;left:0;right:0;bottom:0;z-index:2;
  padding:1.6em .6em .5em;font-size:clamp(7px,1.05vmax,15px);font-weight:800;
  letter-spacing:.13em;text-transform:uppercase;color:#fff;text-align:center;
  background:linear-gradient(180deg,rgba(10,18,32,0),rgba(10,18,32,.55))}

/* la tira de los bordes va enmarcada, como un poster puesto en la pared */
.f-col{box-shadow:0 18px 46px rgba(0,0,0,.75),0 0 0 1px rgba(227,187,109,.16);
  outline:1px solid rgba(227,187,109,.10)}
.f-col::after{content:"";position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(115deg,rgba(255,255,255,0) 42%,rgba(255,240,214,.16) 50%,rgba(255,255,255,0) 58%);
  transform:translateX(-120%);transition:transform .9s ease}
.f-col::before{content:"";position:absolute;inset:-14px;z-index:-1;border-radius:20px;
  background:radial-gradient(ellipse at 50% 50%,rgba(227,187,109,.20),transparent 70%);
  animation:resplandor 6s ease-in-out infinite alternate}
@keyframes resplandor{ from{opacity:.45} to{opacity:1} }

/* cuando hay Poster de verdad, el dibujo del programa se aparta */
.f-lienzo.con-foto{background-size:cover;background-position:center 20%;
  animation:none}
.f-lienzo.con-foto .f-art{display:none}
.f-lienzo.con-foto .f-rotulo{display:none}
.f-col.con-foto{box-shadow:0 22px 54px rgba(0,0,0,.85),0 0 0 1px rgba(227,187,109,.34)}

/* El velo: solo lo justo para que se lean los textos de encima. Los
   Posters tienen que seguir viéndose por los bordes. */
.f-velo{position:absolute;inset:0;
  background:radial-gradient(ellipse 74% 62% at 50% 42%,rgba(10,11,18,.34) 0,
    rgba(10,11,18,.58) 54%,rgba(10,11,18,.86) 100%),
    linear-gradient(180deg,rgba(10,11,18,.34),transparent 26%,transparent 74%,rgba(10,11,18,.44))}

/* el contenido va por encima del fondo. El pie NO entra aqui: el pie va
   fijo como en MyServer (position:fixed), y esta regla se lo cambiaba a
   relative, con lo que se iba al final del documento en vez de quedarse
   en la esquina inferior izquierda. Su z-index:5 ya lo deja por encima
   de los Posters. */
.envoltura{position:relative;z-index:1}
.barra{ z-index:60; }

@media (max-width:1000px){ .f-tira{ display:none; } }
@media (max-width:700px){
  .f-mural{ filter:blur(9px) saturate(1.15) brightness(.72); opacity:.5; }
}
"""