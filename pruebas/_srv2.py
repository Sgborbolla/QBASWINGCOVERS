# -*- coding: utf-8 -*-
"""servidor.py - etapa 2: fuera la ventana de tipos, portada nueva con efectos."""
import io
import re

RUTA = r"C:\QBASWING-COVERS\servidor.py"
texto = io.open(RUTA, encoding="utf-8").read()
hechos = []

if "def ventana_portada(" in texto:
    print("ya aplicada")
    raise SystemExit(0)


PORTADA = '''CSS_PORTADA = """
.portada { position:relative; overflow:hidden; }
.esc-hero { position:relative; padding:3.2rem 1.6rem 3rem; text-align:center;
  border-radius:14px; overflow:hidden; background:linear-gradient(160deg,#F7F9FC 0%,#EAF2FD 55%,#DCEBFF 100%);
  border:1px solid #C8D6EA; }
.esc-capa { position:absolute; inset:0; opacity:.5; pointer-events:none; }
.esc-capa img { position:absolute; width:150px; border-radius:8px; filter:blur(1px) saturate(1.05);
  box-shadow:0 14px 34px rgba(30,64,120,.30); will-change:transform; }
.esc-capa img:nth-child(1){ left:-40px;  top:6%;   transform:rotate(-9deg); }
.esc-capa img:nth-child(2){ left:8%;    top:44%;  transform:rotate(-5deg) scale(.9); }
.esc-capa img:nth-child(3){ left:26%;   top:2%;   transform:rotate(3deg) scale(1.05); }
.esc-capa img:nth-child(4){ right:26%;  top:14%;  transform:rotate(6deg) scale(.95); }
.esc-capa img:nth-child(5){ right:6%;   top:52%;  transform:rotate(4deg) scale(1.05); }
.esc-capa img:nth-child(6){ right:-40px; top:4%;   transform:rotate(10deg); }
@media (max-width:900px){ .esc-capa{ display:none; } }
.esc-brillo { position:absolute; top:-60%; left:-35%; width:45%; height:220%;
  background:linear-gradient(100deg,rgba(255,255,255,0) 0%,rgba(255,255,255,.72) 50%,rgba(255,255,255,0) 100%);
  transform:rotate(18deg); animation:escBarrido 4.6s ease-in-out infinite; pointer-events:none; }
@keyframes escBarrido { 0%{ left:-45%; } 55%,100%{ left:115%; } }
.esc-titulo { font-family:var(--serif); font-size:2.9rem; line-height:1.06; margin:.2rem 0 .5rem;
  position:relative; }
.esc-titulo span { background:linear-gradient(90deg,#2E6FD8,#5B9BEB 60%,#7FB3F0);
  -webkit-background-clip:text; background-clip:text; color:transparent; }
.esc-sub { position:relative; max-width:640px; margin:0 auto 1.6rem; }
.esc-boton { position:relative; display:inline-flex; align-items:center; gap:.7rem;
  padding:1.05rem 2.4rem; font-size:1.18rem; font-weight:700; letter-spacing:.3px;
  border:none; border-radius:12px; cursor:pointer; color:#fff;
  background:linear-gradient(135deg,#2E6FD8,#5B9BEB);
  box-shadow:0 14px 30px rgba(46,111,216,.36); overflow:hidden;
  transition:transform .18s ease, box-shadow .18s ease; text-decoration:none; }
.esc-boton:hover { transform:translateY(-3px); box-shadow:0 20px 40px rgba(46,111,216,.44); color:#fff; }
.esc-boton::after { content:""; position:absolute; top:0; left:-120%; width:60%; height:100%;
  background:linear-gradient(100deg,rgba(255,255,255,0),rgba(255,255,255,.55),rgba(255,255,255,0));
  transform:skewX(-18deg); animation:escPasada 3.2s ease-in-out infinite; }
@keyframes escPasada { 0%{ left:-120%; } 45%,100%{ left:130%; } }
.esc-reanudar { display:inline-block; margin-left:.7rem; }
.esc-reanudar a { color:#2E6FD8; font-weight:600; }

.esc-tarjetas { display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:1.1rem;
  margin:2.4rem 0; }
.esc-tarjeta { position:relative; padding:1.5rem 1.4rem; border-radius:12px; background:#fff;
  border:1px solid #DCE6F4; box-shadow:0 6px 18px rgba(30,64,120,.08);
  transform-style:preserve-3d; transition:transform .18s ease, box-shadow .18s ease; }
.esc-tarjeta:hover { box-shadow:0 18px 40px rgba(30,64,120,.18); }
.esc-tarjeta h3 { font-family:var(--serif); margin:.5rem 0 .35rem; font-size:1.2rem; }
.esc-tarjeta p { margin:0; color:#6B7280; font-size:.95rem; line-height:1.5; }
.esc-tarjeta .icono-svg { width:56px; height:49px; }

.esc-demo { display:grid; grid-template-columns:minmax(240px,1.1fr) 2fr; gap:1.6rem;
  align-items:center; margin:2.4rem 0; }
@media (max-width:820px){ .esc-demo{ grid-template-columns:1fr; } }
.esc-grande { position:relative; border-radius:12px; overflow:hidden; background:#DCEBFF;
  aspect-ratio:2/3; box-shadow:0 18px 44px rgba(30,64,120,.24); }
.esc-grande img, .esc-mini img { width:100%; height:100%; object-fit:cover; display:block;
  animation:escKen 14s ease-in-out infinite alternate; }
@keyframes escKen { from{ transform:scale(1.02); } to{ transform:scale(1.12); } }
.esc-minis { display:grid; grid-template-columns:repeat(auto-fill,minmax(96px,1fr)); gap:.75rem; }
.esc-mini { position:relative; border-radius:9px; overflow:hidden; aspect-ratio:2/3;
  background:#DCEBFF; box-shadow:0 6px 16px rgba(30,64,120,.14); cursor:pointer;
  transition:transform .2s ease, box-shadow .2s ease; }
.esc-mini:hover { transform:translateY(-6px) scale(1.05); box-shadow:0 16px 32px rgba(30,64,120,.28); z-index:2; }
.esc-mini::after { content:""; position:absolute; inset:0;
  background:linear-gradient(115deg,rgba(255,255,255,0) 40%,rgba(255,255,255,.5) 50%,rgba(255,255,255,0) 60%);
  transform:translateX(-120%); transition:transform .6s ease; }
.esc-mini:hover::after { transform:translateX(120%); }
.esc-hueco { display:flex; align-items:center; justify-content:center; padding:1rem; }

.esc-cifras { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:1rem;
  margin:2.2rem 0; }
.esc-cifra { text-align:center; padding:1.4rem 1rem; border-radius:12px; background:#F7F9FC;
  border:1px solid #DCE6F4; }
.esc-cifra b { display:block; font-family:var(--serif); font-size:2.3rem; color:#2E6FD8;
  line-height:1.1; }
.esc-cifra span { font-size:.92rem; color:#6B7280; }
.esc-nota { font-size:.8rem; color:#9AA0A8; text-align:center; margin-top:1.4rem; line-height:1.6; }
.esc-titulo-seccion { font-family:var(--serif); font-size:1.7rem; margin:0 0 .3rem; }
.revelar { opacity:0; transform:translateY(22px); transition:opacity .7s ease, transform .7s ease; }
.revelar.visible { opacity:1; transform:none; }
@media (prefers-reduced-motion:reduce){ .esc-brillo,.esc-boton::after,.esc-grande img{ animation:none; }
  .revelar{ opacity:1; transform:none; } }
"""


JS_PORTADA = """<script>
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

    cuerpo = (
        '<div class="portada">'

        '  <section class="esc-hero">'
        '    <div class="esc-capa" id="esc-capa" aria-hidden="true">%s</div>'
        '    <div class="esc-brillo" aria-hidden="true"></div>'
        '    <h1 class="esc-titulo">%s<br><span>%s</span></h1>'
        '    <p class="lead esc-sub">%s</p>'
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
            esc(t("portada_titulo_1", lang)),
            esc(t("portada_titulo_2", lang)),
            esc(t("portada_sub", lang)),
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

    return pagina(lang, t("titulo_bienvenida", lang), cuerpo, "/",
                  head_extra="<style>%s</style>%s" % (CSS_PORTADA, JS_PORTADA))


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
'''

patron = re.compile(r"^def ventana_bienvenida\(.*?(?=^def |^class |^# ---|\Z)",
                    re.S | re.M)
m = patron.search(texto)
if not m:
    raise SystemExit("no se encontro ventana_bienvenida")
texto = texto[:m.start()] + PORTADA.rstrip("\n") + "\n\n\n" + texto[m.end():]
hechos.append("ventana_portada() reemplaza la ventana de tipos")

# borrar TIPOS_VISIBLES / TIPO_A_BOTON (ya no se usan)
texto = re.sub(r"^TIPOS_VISIBLES = \[.*?^\]\n\n^TIPO_A_BOTON = \{.*?^\}\n\n\n",
               "", texto, flags=re.S | re.M)
hechos.append("fuera TIPOS_VISIBLES y TIPO_A_BOTON")

# ------------------- endpoints de la portada + resumen
texto = texto.replace(
    '''        # --- logo ---''',
    '''        # --- portadas para la portada del programa ---
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

        # --- logo ---''', 1)
hechos.append("/api/portadas y /api/resumen")

# ------------------- router: la portada es la pantalla 1
texto = texto.replace(
    '''        if ruta == "/":
            E.paso = 1
            self._enviar(ventana_bienvenida(lang, E.tipos))
            return''',
    '''        if ruta == "/":
            E.paso = 1
            self._enviar(ventana_portada(lang))
            return''', 1)

# ------------------- /paso2: ya no hay tipos que elegir
texto = texto.replace(
    '''            tipos = q.get("tipo") or []
            E.tipos = [x for x in tipos if x] or ["todos"]
            E.cfg["tipos"] = E.tipos''',
    '''            # 5.0 El tipo se detecta solo: no hay nada que elegir.
            E.tipos = ["todos"]
            E.cfg["tipos"] = E.tipos''', 1)
hechos.append("ruta / usa la portada")

# ------------------- inclinacion 3D en las tarjetas
texto = texto.replace(
    'if (F2 pressed)', 'if (F2 pressed)')  # no-op de seguridad
JS_TILT = """<script>
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
texto = texto.replace('head_extra="<style>%s</style>%s" % (CSS_PORTADA, JS_PORTADA))',
                      'head_extra="<style>%s</style>%s%s" % (CSS_PORTADA, JS_PORTADA, TILT))', 1)
texto = texto.replace('JS_PORTADA = """<script>', 'TILT = """' + JS_TILT + '"""\n\nJS_PORTADA = """<script>', 1)
hechos.append("tarjetas con inclinacion 3D")

io.open(RUTA, "w", encoding="utf-8", newline="\n").write(texto)

import ast
ast.parse(io.open(RUTA, encoding="utf-8").read())
print("servidor.py etapa 2:")
for h in hechos:
    print("   -", h)
print("   sintaxis OK")