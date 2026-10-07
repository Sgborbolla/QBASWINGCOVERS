# -*- coding: utf-8 -*-
"""Botones de pausa / continuar / detener / cancelar en la pantalla de escaneo."""
import ast
import io

RUTA = r"C:\QBASWING-COVERS\servidor.py"
t = io.open(RUTA, encoding="utf-8").read()

VIEJO = '''def ventana_escaneo(lang, unidades_elegidas):
    rutas_js = ",".join('"%s"' % esc_url(u) for u in unidades_elegidas)
    cuerpo = (
        '<div class="panel ancho centrado">'
        '  <h1>%s</h1>'
        '  <p class="lead">%s</p>'
        '  <div class="barra-prog"><span id="barra"></span></div>'
        '  <p class="contador" id="txt">%s</p>'
        '  <p class="contador" id="det"></p>'
        '  <div style="margin-top:1.4rem" class="lead">%s</div>'
        '</div>'
        '<script>const RUTAS=[%s];</script>'
        % (esc(t("titulo_escaneo", lang)),
           esc(t("msg_escaneando", lang)),
           esc(t("msg_preparando", lang)),
           esc(t("msg_escaneo_tiempo", lang)),
           rutas_js)
    )

    js = """<script>
var timer=setInterval(function(){
  fetch('/api/progreso').then(function(r){return r.json();}).then(function(d){
    var barra=document.getElementById('barra');
    var pct = d.total>0 ? Math.round(d.hechos*100/d.total) : 0;
    barra.classList.toggle('indeterminada',d.activo && d.total===0);
    barra.style.width = d.total>0 ? pct+'%' : '';
    document.getElementById('txt').textContent = d.texto||'';
    document.getElementById('det').innerHTML =
        (d.total>0 ? d.hechos+' / '+d.total : '');
    if(d.listo){ clearInterval(timer); window.location.href='/paso4'; }
  }).catch(function(){});
},600);
</script>"""

    return pagina(lang, t("titulo_escaneo", lang), cuerpo, "/", head_extra=js)'''

NUEVO = '''def ventana_escaneo(lang, unidades_elegidas):
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
        '    <button id="bpausa" class="btn chico" onclick="ctl(\\'pausar\\')">%s</button>'
        '    <button id="bseguir" class="btn chico fantasma" '
        'onclick="ctl(\\'seguir\\')" hidden>%s</button>'
        '    <button id="bdetener" class="btn chico fantasma" '
        'onclick="ctl(\\'detener\\')">%s</button>'
        '    <button class="btn chico fantasma" onclick="ctl(\\'cancelar\\')">%s</button>'
        '  </div>'
        '  <p class="lead" style="margin-top:1.4rem">%s</p>'
        '  <p class="lead aviso-fino">%s</p>'
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
           esc(t("aviso_telefono_lento", lang)),
           rutas_js)
    )

    js = """<script>
function ctl(accion){
  fetch('/api/controlar?accion='+accion).catch(function(){});
}
/* Una linea de progreso por unidad: asi se ve C: y el telefono a la vez. */
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
        window.location.href = seguir ? '/paso4' : '/paso4';
      },700);
    }
  }).catch(function(){});
},600);
</script>"""

    return pagina(lang, t("titulo_escaneo", lang), cuerpo, "/", head_extra=js)'''

if VIEJO not in t:
    raise SystemExit("no se encontro ventana_escaneo()")
t = t.replace(VIEJO, NUEVO, 1)

# Estilos de los controles y de las lineas por unidad.
t = t.replace(".pie{", """.controles{ display:flex; flex-wrap:wrap; gap:.5rem;
  justify-content:center; margin-top:1.3rem; }
#lineas{ margin:1rem auto 0; max-width:620px; text-align:left; }
.linea-unidad{ display:flex; align-items:center; gap:.55rem; padding:.3rem .5rem;
  border-radius:7px; background:#F7F9FC; border:1px solid #E3EBF6; margin-bottom:.3rem;
  font-size:.85rem; }
.linea-unidad .icono-unidad{ min-width:2.1rem; text-align:center; font-weight:700;
  color:#2E6FD8; background:#EAF2FD; border-radius:5px; padding:.1rem .3rem; }
.linea-unidad .ruta-unidad{ flex:1; overflow:hidden; text-overflow:ellipsis;
  white-space:nowrap; color:#1A1D23; }
.linea-unidad .estado-unidad{ color:#6B7280; white-space:nowrap; }
.aviso-fino{ font-size:.8rem; color:#9AA0A8; }
.pie{""", 1)

io.open(RUTA, "w", encoding="utf-8", newline="\n").write(t)
ast.parse(t)
print("ventana_escaneo(): botones de control y detalle por unidad")
print("sintaxis OK")