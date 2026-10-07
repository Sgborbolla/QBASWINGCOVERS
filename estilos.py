# -*- coding: utf-8 -*-
"""
QBASWING COVERS - Estilos.

La hoja de estilo vive aqui, aparte del servidor, para que se pueda
retocar sin tocar el programa.

El aspecto es el de casa: fondo casi negro, tipografia serif para los
titulos, detalles dorados y las perforaciones de la cinta de cine, igual
que QBASwing MyServer.

Las pantallas usan toda la anchura de la ventana: nada de columnas
pequenas con un monton de fondo vacio a los lados.
"""

# --------------------------------------------------------------------------
# La paleta
# --------------------------------------------------------------------------

CSS = """
:root{
  --bg:#0a0b12; --panel:#14161f; --panel-2:#1a1d29; --card:#171a25;
  --borde:#262a3a; --borde-claro:#333849;
  --gold:#e3bb6d; --gold-dim:#b08b4d; --gold-brillo:#f6d896;
  --rojo:#c1453a; --rojo-brillo:#e85c4d;
  --esmeralda:#4fd1a0; --zafiro:#6fb2ff;
  --texto:#f3efe6;
  /* Los textos chicos antes se perdian en el fondo oscuro. Ahora el
     apagado es gris claro y el tenue es gris medio: los dos se leen
     sobre el negro sin tener que pasar el raton por encima. */
  --apagado:#b3b9c5; --suave:#a6adba; --tenue:#8d94a3;
  --serif:Georgia,"Times New Roman","Noto Serif",serif;
  /* Letra de libro mas elegante para los titulos de Acerca de nosotros */
  --serif-ac:"Palatino Linotype","Book Antiqua",Palatino,Georgia,serif;
  --cuerpo:"Segoe UI",-apple-system,Roboto,"Helvetica Neue",Arial,sans-serif;
  /* Letra distinta y mas calida para los textos largos de Acerca */
  --cuerpo-ac:Candara,Corbel,"Segoe UI",-apple-system,"Helvetica Neue",
    Arial,sans-serif;
  --tinta-ac:#e8e2d4;
  --mono:"Consolas","SFMono-Regular",Menlo,monospace;
  --r:10px; --sombra:0 14px 34px rgba(0,0,0,.55);
  --oro:rgba(227,187,109,.16);
  --medida:82ch;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--bg);color:var(--texto);font-family:var(--cuerpo);
  line-height:1.55;min-height:100%;font-size:16px}
/* Los letras pequenos se ven mas limpios con el suavizado activado.
   Y el cuerpo es una columna de minimo una pantalla: asi el pie se
   queda pegado abajo aunque la pantalla tenga poco contenido. */
body{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;
  text-rendering:optimizeLegibility;overflow-x:hidden;
  display:flex;flex-direction:column;min-height:100vh}
h1,h2,h3,.serif{font-family:var(--serif)}
a{color:var(--gold);text-decoration:none}
a:hover{color:var(--gold-brillo)}
::selection{background:var(--gold);color:#14151a}

/* ---- la marca de agua: los tres brillos de QBASwing MyServer ----
   Dorado por arriba, zafiro en la esquina contraria y rojo en la otra.
   Va fija detras de todo y respira muy despacio, para que la pagina
   no parezca una foto quieta. */
.marca-agua{position:fixed;inset:0;z-index:0;pointer-events:none;
  background:
    radial-gradient(1200px 600px at 50% -10%,rgba(227,187,109,.13),transparent 60%),
    radial-gradient(900px 500px at 100% 100%,rgba(111,178,255,.09),transparent 60%),
    radial-gradient(800px 480px at 0% 100%,rgba(193,69,58,.10),transparent 60%),
    var(--bg);
  animation:aguaRespira 26s ease-in-out infinite alternate}
@keyframes aguaRespira{
  from{ filter:brightness(1)    saturate(1);   }
  to  { filter:brightness(1.14) saturate(1.2); }
}
@media (prefers-reduced-motion:reduce){
  .marca-agua{ animation:none; }
}

/* ---- las perforaciones de la cinta, la marca de la casa ---- */
.sprocket{height:14px;width:100%;
  background-image:radial-gradient(circle,var(--bg) 3.5px,transparent 3.6px);
  background-size:22px 14px;background-position:11px center;
  background-color:var(--gold-dim);opacity:.85;pointer-events:none}
.sprocket.fino{height:8px;background-size:16px 8px;background-position:8px center}

/* ---- cabecera ---- */
.barra{background:linear-gradient(180deg,#151824,#0e1017);
  border-bottom:1px solid var(--borde);padding:.55rem 1.2rem;
  display:flex;align-items:center;gap:1rem;flex-wrap:wrap;
  position:sticky;top:0;z-index:60;box-shadow:0 2px 16px rgba(0,0,0,.55)}
.barra .marca{display:flex;align-items:center;gap:.7rem}
.barra img{height:34px;max-height:34px;display:block}
.barra .tit{font-family:var(--serif);font-size:1.02rem;font-weight:700;
  letter-spacing:.2px;color:var(--gold-brillo)}
.barra .crece{margin-left:auto;display:flex;align-items:center;gap:.45rem;flex-wrap:wrap}
.idioma{background:transparent;border:1px solid rgba(227,187,109,.45);
  color:var(--gold);padding:.26rem .7rem;border-radius:20px;cursor:pointer;
  font-size:.82rem;transition:background .15s,color .15s}
.idioma.on{background:var(--gold);color:#1a1206;font-weight:700}
.idioma:hover:not(.on){background:var(--oro)}
.acerca,.cerrar{background:transparent;border:1px solid rgba(227,187,109,.4);
  color:var(--gold);padding:.28rem .7rem;border-radius:7px;cursor:pointer;
  font-size:.82rem;text-decoration:none;transition:background .15s,color .15s}
/* El boton de acerca lleva un degradado dorado para que resalte. */
.acerca{background:linear-gradient(135deg,rgba(227,187,109,.22),
  rgba(111,178,255,.18));border-color:rgba(227,187,109,.55);
  font-weight:600;letter-spacing:.2px}
.acerca:hover{background:linear-gradient(135deg,var(--gold),#cfa45a);
  color:#1a1206;border-color:var(--gold-brillo);
  box-shadow:0 0 14px rgba(227,187,109,.45)}
.cerrar{border-color:rgba(200,80,70,.5);color:#e08178}
.cerrar:hover{background:#c1453a;color:#fff;border-color:#c1453a}

/* ---- el cierre con su ruedita ---- */
.avisocerrar{display:none;position:fixed;inset:0;z-index:9999;
  background:rgba(10,11,18,.98)}
.avisocerrar .caja{text-align:center;margin-top:22vh}
.avisocerrar .ruedita{width:44px;height:44px;margin:0 auto 1.1rem;
  border:4px solid var(--borde);border-top-color:var(--gold);border-radius:50%;
  animation:giro .8s linear infinite}
@keyframes giro{ to{ transform:rotate(360deg); } }

/* ---- cajas: ocupa toda la pantalla, sin columnas estrechas ---- */
.envoltura{position:relative;z-index:1;width:100%;flex:1 0 auto;
  padding:1.1rem clamp(.9rem,2vw,2.2rem) 1.8rem}
.panel{background:var(--panel);border:1px solid var(--borde);border-radius:var(--r);
  padding:1.7rem;box-shadow:0 4px 18px rgba(0,0,0,.35)}
/* Lo que antes se quedaba en 900px centrados. Ahora coge el ancho
   completo del navegador, que es lo que se pidio. */
.ancho{width:100%;max-width:none;margin:0}
/* Los parrafos largos si se miden, para no quedar lineas de 200 letras.
   La caja es ancha; la lectura no. */
.panel p,.lead,.aviso,.info{max-width:var(--medida)}
.panel p+p{margin-top:.6rem}
.centrado{text-align:center}
.centrado p{margin-left:auto;margin-right:auto}
h1{font-size:clamp(1.5rem,2.4vw,2.2rem);margin-bottom:.6rem;letter-spacing:.2px}
h1::after{content:"";display:block;width:88px;height:3px;margin:.55rem auto 0;
  border-radius:2px;
  background:linear-gradient(90deg,var(--gold-dim),var(--gold-brillo),var(--gold-dim))}
.lead{color:var(--suave);font-size:1.02rem}
.slogan{font-family:var(--serif);color:var(--gold-dim);font-size:.95rem}

/* ---- botones y campos ---- */
.btn{background:var(--gold);color:#1a1206;border:1px solid var(--gold);
  padding:.6rem 1.25rem;border-radius:8px;font-size:.92rem;font-weight:700;
  cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;
  gap:.5rem;transition:transform .14s,box-shadow .14s,background .14s}
.btn:hover{background:var(--gold-brillo);border-color:var(--gold-brillo);
  color:#1a1206;transform:translateY(-2px);box-shadow:0 8px 20px rgba(0,0,0,.5)}
.btn.fantasma{background:transparent;color:var(--gold);border-color:rgba(227,187,109,.42)}
.btn.fantasma:hover{background:var(--oro);color:var(--gold-brillo)}
.btn.chico{padding:.36rem .75rem;font-size:.82rem}
.btn:disabled{opacity:.4;cursor:default;transform:none}
.fila-botones{display:flex;gap:.6rem;flex-wrap:wrap;margin-top:1.3rem;justify-content:center}
.campo{background:var(--panel-2);border:1px solid var(--borde);color:var(--texto);
  padding:.42rem .6rem;border-radius:7px;font-size:.88rem;font-family:var(--cuerpo)}
.campo:focus{outline:none;border-color:var(--gold-dim)}

/* ---- avisos ---- */
.aviso{background:rgba(193,69,58,.12);border-left:4px solid var(--rojo);
  border-radius:6px;padding:.7rem .9rem;color:#f0a49c;font-size:.88rem;margin:1rem 0}
.info{background:rgba(111,178,255,.10);border-left:4px solid var(--zafiro);
  border-radius:6px;padding:.7rem .9rem;color:var(--texto);font-size:.88rem;margin:1rem 0}
.aviso-fino{font-size:.86rem;color:var(--tenue);line-height:1.6}
.kbd{display:inline-block;border:1px solid var(--borde-claro);border-bottom-width:2px;
  border-radius:5px;padding:.05rem .4rem;font-family:var(--mono);font-size:.82rem;
  background:var(--panel-2);color:var(--gold)}
.oculto{display:none}

/* ---- el pie: calcado al del QBASwing Marketplace ----
   Franja de la bandera arriba, fondo azul marino, nombre con el
   degradado de la bandera y los creditos en dorado. Va al final de la
   pagina, a todo el ancho, en TODAS las pantallas, la portada incluida. */
.pie{position:relative;z-index:2;width:100%;margin-top:2.4rem;
  background:#213145;color:#e6ecf7;font-family:var(--cuerpo);
  box-shadow:0 -16px 36px rgba(0,0,0,.45)}
.pie-bandera{display:flex;width:100%;height:4px}
.pie-bandera .tira{flex:1;display:block}
.pie-bandera .azul{background:#002a8f}
.pie-bandera .blanca{background:#ffffff;flex:1.6}
.pie-bandera .rojo{background:#cf0a2c}
.pie-cuerpo{padding:1.5rem clamp(.9rem,2.2vw,2.2rem) 1.35rem}
.pie-nombre{display:flex;align-items:center;gap:.55rem;margin:0;
  font-family:var(--serif-ac);font-size:1.2rem;font-weight:700;
  letter-spacing:.05em}
.pie-nombre .icono-svg{width:22px;height:20px;flex:none}
.pie-nombre .estrella{color:#fcd116}
.pie-nombre .texto-bandera{
  background-image:linear-gradient(90deg,#8fb4ff 0%,#ffffff 33%,#cf0a2c 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}
.pie-creditos{display:flex;flex-wrap:wrap;gap:.35rem 1.7rem;margin-top:.8rem}
.pie-linea{display:flex;align-items:center;gap:.42rem;margin:0;
  font-size:.83rem;line-height:1.5;color:rgba(252,209,22,.78)}
.pie-linea .icono-svg{width:15px;height:14px;flex:none}
.pie-linea b{color:#fcd116;font-weight:600}
.pie-linea .anio{color:rgba(252,209,22,.55)}
.pie-legal{margin:.9rem 0 0;font-size:.8rem;line-height:1.5;
  color:rgba(252,209,22,.55)}
.pie-tmdb{margin:.35rem 0 0;font-size:.72rem;line-height:1.55;
  letter-spacing:.01em;color:rgba(230,236,247,.42);max-width:96ch}
.pie a{color:inherit}
@media (max-width:560px){
  .pie-nombre{font-size:1.02rem}
  .pie-linea{font-size:.78rem}
  .pie-creditos{gap:.3rem 1.05rem}
  .pie-cuerpo{padding:1.2rem clamp(.9rem,2.2vw,2.2rem) 1.15rem}
}

/* ---- barra de progreso y contadores ---- */
.barra-prog{height:14px;background:var(--panel-2);border:1px solid var(--borde);
  border-radius:8px;overflow:hidden;margin:1.4rem 0 .6rem}
.barra-prog span{display:block;height:100%;width:0;
  background:linear-gradient(90deg,var(--gold-dim),var(--gold-brillo));
  transition:width .4s ease}
.contador{font-family:var(--mono);font-size:1rem;color:var(--suave)}

/* ---- lineas del escaneo ---- */
.controles{display:flex;flex-wrap:wrap;gap:.5rem;justify-content:center;margin-top:1.3rem}
#lineas{margin:1rem auto 0;max-width:1100px;text-align:left}
.linea-unidad{display:flex;align-items:center;gap:.7rem;padding:.42rem .6rem;
  border-radius:7px;background:var(--panel-2);border:1px solid var(--borde);
  margin-bottom:.35rem;font-size:.95rem}
.linea-unidad .icono-unidad{min-width:2.3rem;text-align:center;font-weight:700;
  color:var(--gold);background:var(--oro);border-radius:5px;padding:.1rem .3rem}
.linea-unidad .ruta-unidad{flex:1;overflow:hidden;text-overflow:ellipsis;
  white-space:nowrap;color:var(--texto)}
.linea-unidad .estado-unidad{color:var(--suave);white-space:nowrap}

/* ======================================================================
   GALERIA: el explorador. Rejilla que ocupa toda la pantalla, con la
   caratula si la carpeta tiene una imagen y el icono de carpeta si no.
   ====================================================================== */
.migas{margin-bottom:.8rem;font-size:.9rem;display:flex;flex-wrap:wrap;
  align-items:center;gap:.2rem}
.migas a{background:var(--panel-2);border:1px solid var(--borde);border-radius:7px;
  padding:.2rem .6rem;color:var(--suave);transition:all .15s}
.migas a:hover{background:var(--oro);border-color:var(--gold-dim);color:var(--gold-brillo)}
.migas .sep{color:var(--tenue);padding:0 .15rem}

.pestanas{display:flex;gap:.4rem;overflow-x:auto;padding:.45rem;margin-bottom:1rem;
  background:var(--panel);border:1px solid var(--borde);border-radius:var(--r);
  box-shadow:0 3px 12px rgba(0,0,0,.3)}
.pestana{display:flex;align-items:center;gap:.5rem;padding:.4rem .8rem;border-radius:8px;
  color:var(--suave);text-decoration:none;white-space:nowrap;
  border:1px solid transparent;transition:all .15s}
.pestana:hover{background:var(--panel-2);color:var(--texto)}
.pestana.on{background:var(--oro);border-color:var(--gold-dim);color:var(--gold-brillo);
  font-weight:600}
.pestana .libre{font-family:var(--mono);font-size:.8rem;color:var(--tenue)}

.herramientas{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;
  margin-bottom:1rem;padding:.6rem .8rem;background:var(--panel);
  border:1px solid var(--borde);border-radius:var(--r);
  box-shadow:0 3px 12px rgba(0,0,0,.3)}
.herramientas input.campo,.herramientas select.campo{flex:1;min-width:150px}
.herramientas .crece2{margin-left:auto}
.cifras{font-family:var(--mono);font-size:.88rem;color:var(--apagado);white-space:nowrap}
.cifras b{color:var(--gold)}

/* La rejilla: se estira a todo el ancho del navegador, como el
   explorador de Windows. Cuanto mas pantalla, mas columnas. */
.fila{display:grid;grid-template-columns:repeat(auto-fill,minmax(186px,1fr));
  gap:18px;padding:.4rem 0 2rem}
@media (max-width:520px){ .fila{ grid-template-columns:repeat(auto-fill,minmax(138px,1fr));
  gap:12px; } }

/* La tarjeta */
.tarjeta{background:var(--card);border:1px solid var(--borde);border-radius:var(--r);
  overflow:hidden;cursor:pointer;position:relative;user-select:none;
  display:flex;flex-direction:column;
  transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease;
  animation:aparece .4s cubic-bezier(.2,.7,.3,1) both}
@keyframes aparece{ from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:none} }
.tarjeta:hover{transform:translateY(-6px) scale(1.02);border-color:var(--gold-dim);
  box-shadow:var(--sombra);z-index:4}
.tarjeta.marcada{border-color:var(--gold);box-shadow:0 0 0 2px var(--gold),var(--sombra)}

/* La caratula, o el icono de carpeta si todavia no hay poster */
.marco{width:100%;aspect-ratio:2/3;position:relative;overflow:hidden;
  background:linear-gradient(160deg,#21262f,#12141a);display:flex;
  align-items:center;justify-content:center}
.marco img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
  display:block;z-index:2;transition:transform .35s ease}
.tarjeta:hover .marco img{transform:scale(1.05)}
.portada-vacia{position:absolute;inset:0;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:.55rem;padding:.8rem;text-align:center;
  background:repeating-linear-gradient(45deg,rgba(227,187,109,.04) 0 2px,transparent 2px 10px),
             linear-gradient(160deg,#232832,#12141a)}
.portada-vacia::after{content:"";position:absolute;inset:0;
  background:radial-gradient(ellipse at 50% 35%,rgba(227,187,109,.10),transparent 70%)}
.portada-vacia svg{width:56%;max-width:84px;height:auto;opacity:.92;
  filter:drop-shadow(0 8px 14px rgba(0,0,0,.6));position:relative;z-index:1}
.portada-vacia span{position:relative;z-index:1;font-family:var(--serif);font-size:10.5px;
  letter-spacing:.18em;text-transform:uppercase;color:var(--gold);
  line-height:1.4;word-break:break-word}

/* El texto de abajo de la tarjeta */
.tarjeta .info{padding:10px 11px 12px;display:flex;flex-direction:column;gap:4px;
  flex:1;min-height:0}
.tarjeta .nombre{font-size:13.5px;color:var(--texto);white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.tarjeta:hover .nombre{color:var(--gold-brillo)}
.tarjeta .ruta{font-family:var(--mono);font-size:11px;color:var(--tenue);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tarjeta .estado{display:flex;align-items:center;gap:.4rem;font-size:11.5px;
  font-weight:600;color:var(--suave);letter-spacing:.2px}
.tarjeta .estado i{width:6px;height:6px;border-radius:50%;background:currentColor;
  flex:0 0 auto}
.estado.tiene{color:var(--esmeralda)}
.estado.falta{color:var(--rojo-brillo)}
.estado.rev{color:var(--rojo-brillo)}
.estado.pendiente,.estado.sin-escanear{color:var(--tenue)}

/* Las insignias */
.insignia{position:absolute;top:8px;right:8px;z-index:4;font-family:var(--mono);
  font-size:10.5px;background:rgba(0,0,0,.68);color:var(--gold);
  border:1px solid rgba(227,187,109,.36);padding:2px 7px;border-radius:5px}
.marca-check{position:absolute;top:8px;left:8px;z-index:4;width:20px;height:20px;
  border-radius:5px;border:2px solid rgba(237,234,227,.5);background:rgba(0,0,0,.4);
  display:flex;align-items:center;justify-content:center;font-size:12px;
  color:transparent;cursor:pointer;padding:0;transition:all .15s}
.marca-check:hover{border-color:var(--gold-brillo);transform:scale(1.1)}
.tarjeta.marcada .marca-check{background:var(--gold);border-color:var(--gold);
  color:#1a1206}
.tipo-icono{position:absolute;bottom:8px;left:8px;z-index:4;width:26px;height:26px;
  display:flex;align-items:center;justify-content:center;
  background:rgba(10,11,18,.78);border:1px solid rgba(227,187,109,.3);
  border-radius:7px;cursor:help}
.tipo-icono svg{width:100%;height:100%}

/* Las unidades se ven tumbadas, como los discos del explorador */
.tarjeta-unidad .marco{aspect-ratio:16/10}
.tarjeta-unidad .portada-vacia{background:linear-gradient(160deg,#232a36,#121620)}
.tarjeta-unidad .portada-vacia svg{width:38%}
.tarjeta-unidad .estado{color:var(--gold)}
.tarjeta-unidad .marca-check{display:none}
.vacio{grid-column:1/-1;color:var(--tenue);padding:3.5rem 1rem;text-align:center;
  font-size:1rem}

/* ---- revision uno por uno ---- */
.revision{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));
  gap:1.1rem}
.filtros{display:flex;gap:.45rem;flex-wrap:wrap;margin-bottom:1rem}
.filtros .marca{display:inline-flex;align-items:center;gap:.4rem;font-size:.88rem;
  color:var(--suave)}
.mini{max-width:100%}
.poster{display:block}
.det{font-size:.86rem;color:var(--tenue);margin-top:.35rem}

/* --- Acerca de nosotros: secciones con color --- */
.ac-hero{display:flex;flex-direction:column;align-items:center;
  text-align:center;margin-bottom:1.4rem}
.ac-logo{max-width:184px;max-height:108px;object-fit:contain;margin-bottom:.7rem;
  filter:drop-shadow(0 8px 22px rgba(0,0,0,.6))}
.ac-tit{font-family:var(--serif-ac);font-size:clamp(1.6rem,4vw,2.4rem);
  margin:.1rem 0 .45rem;letter-spacing:.6px;
  background:linear-gradient(92deg,var(--gold-brillo) 8%,var(--gold) 46%,var(--zafiro));
  -webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 2px 10px rgba(227,187,109,.28))}
.ac-lema{font-family:var(--serif-ac);font-style:italic;font-size:1.1rem;
  color:var(--gold);margin:.15rem 0 .5rem;letter-spacing:.3px}
.ac-hero .lead{max-width:78ch;color:var(--tinta-ac);font-size:1.05rem;
  line-height:1.8;font-family:var(--cuerpo-ac)}

.ac-rejilla{display:grid;gap:1.05rem;grid-template-columns:repeat(auto-fit,minmax(272px,1fr));
  margin:1.5rem 0 .4rem}
.ac-carta{position:relative;background:var(--card);border:1px solid var(--borde);
  border-radius:16px;padding:1.15rem 1.25rem 1.3rem;overflow:hidden}
.ac-carta::before{content:"";position:absolute;top:0;left:0;right:0;height:4px;
  background:linear-gradient(90deg,var(--ac),rgba(255,255,255,0))}
.ac-carta::after{content:"";position:absolute;width:170px;height:170px;right:-70px;
  top:-80px;border-radius:50%;background:var(--ac);opacity:.16;filter:blur(28px)}
.ac-carta h2{position:relative;font-family:var(--serif-ac);font-size:1.24rem;margin:0;
  color:var(--ac-txt);letter-spacing:.5px}
.ac-carta p{position:relative;color:var(--tinta-ac);font-family:var(--cuerpo-ac);
  font-size:1rem;line-height:1.85;margin:.65rem 0 0;letter-spacing:.15px}
.ac-carta p:first-of-type{margin-top:.75rem}
.ac-cara{position:relative;display:flex;align-items:center;gap:.65rem;margin-bottom:.7rem}
.ac-chip{flex:0 0 auto;width:50px;height:44px;border-radius:12px;display:grid;
  place-items:center;background:rgba(255,255,255,.07);
  border:1px solid rgba(255,255,255,.12)}
.ac-chip .icono-svg{width:100%;height:100%}
.ac-oro{--ac:var(--gold);--ac-txt:var(--gold-brillo);
  background:linear-gradient(155deg,rgba(227,187,109,.16),transparent 58%),var(--card);
  border-color:rgba(227,187,109,.42)}
.ac-zafiro{--ac:var(--zafiro);--ac-txt:#a8d1ff;
  background:linear-gradient(155deg,rgba(111,178,255,.16),transparent 58%),var(--card);
  border-color:rgba(111,178,255,.40)}
.ac-esmeralda{--ac:var(--esmeralda);--ac-txt:#8ce9c8;
  background:linear-gradient(155deg,rgba(79,209,160,.15),transparent 58%),var(--card);
  border-color:rgba(79,209,160,.38)}
.ac-rojo{--ac:var(--rojo);--ac-txt:#f0a49b;
  background:linear-gradient(155deg,rgba(193,69,58,.16),transparent 58%),var(--card);
  border-color:rgba(193,69,58,.40)}

/* Tira de datos sueltos, cada uno con su color */
.ac-datos{display:flex;flex-wrap:wrap;gap:.5rem;justify-content:center;margin:1.5rem 0 .2rem}
.ac-dato{font-size:.82rem;padding:.35rem .8rem;border-radius:30px;border:1px solid;
  background:rgba(255,255,255,.05)}
.ac-dato:nth-child(6n+1){color:var(--gold-brillo);border-color:rgba(227,187,109,.5)}
.ac-dato:nth-child(6n+2){color:#a8d1ff;border-color:rgba(111,178,255,.5)}
.ac-dato:nth-child(6n+3){color:#8ce9c8;border-color:rgba(79,209,160,.5)}
.ac-dato:nth-child(6n+4){color:#f0a49b;border-color:rgba(193,69,58,.5)}
.ac-dato:nth-child(6n+5){color:#e6c8ff;border-color:rgba(178,124,255,.45)}
.ac-dato:nth-child(6n+6){color:#ffe08a;border-color:rgba(255,196,64,.5)}

.ac-cierre{margin-top:1.4rem;text-align:center;font-family:var(--serif);
  font-style:italic;color:var(--gold);font-size:1.02rem}

@media (prefers-reduced-motion:reduce){
  *{animation-duration:.001ms !important;transition-duration:.001ms !important}
}
"""


# --------------------------------------------------------------------------
# La portada inicial
# --------------------------------------------------------------------------

CSS_PORTADA = """
.portada { position:relative; }

/* ---- el heroe: posters reales alrededor, como los vinilos ---- */
.esc-hero{position:relative;padding:clamp(2rem,5vh,4.4rem) clamp(1rem,4vw,3rem);
  min-height:min(94vh,900px);display:flex;flex-direction:column;
  align-items:center;justify-content:center;text-align:center;
  border-radius:16px;overflow:hidden;
  background:linear-gradient(160deg,#101320 0%,#0b0d16 52%,#0e1018 100%);
  border:1px solid var(--borde);box-shadow:0 20px 60px rgba(0,0,0,.6)}
.esc-capa{position:absolute;inset:0;opacity:.5;pointer-events:none}
.esc-capa img{position:absolute;width:150px;border-radius:8px;filter:blur(1px) saturate(1.05);
  box-shadow:0 14px 40px rgba(0,0,0,.75);will-change:transform}
.esc-capa img:nth-child(1){ left:-40px;  top:6%;   transform:rotate(-9deg); }
.esc-capa img:nth-child(2){ left:8%;    top:44%;  transform:rotate(-5deg) scale(.9); }
.esc-capa img:nth-child(3){ left:26%;   top:2%;   transform:rotate(3deg) scale(1.05); }
.esc-capa img:nth-child(4){ right:26%;  top:14%;  transform:rotate(6deg) scale(.95); }
.esc-capa img:nth-child(5){ right:6%;   top:52%;  transform:rotate(4deg) scale(1.05); }
.esc-capa img:nth-child(6){ right:-40px; top:4%;   transform:rotate(10deg); }
@media (max-width:900px){ .esc-capa{ opacity:.28; } }

/* el barrido de luz que pasa por encima */
.esc-brillo{position:absolute;top:-60%;left:-35%;width:45%;height:220%;
  background:linear-gradient(100deg,rgba(255,255,255,0) 0%,rgba(255,240,214,.14) 50%,rgba(255,255,255,0) 100%);
  transform:rotate(18deg);animation:escBarrido 4.6s ease-in-out infinite;pointer-events:none}
@keyframes escBarrido{ 0%{ left:-45%; } 55%,100%{ left:115%; } }

/* ==================================================================
   LA MARQUESINA DE MARCA
   Igual que la portada de QBASwing MyServer: logotipo, nombre en
   versalitas de serif doradas con brillo, empresa debajo con las
   letras muy separadas y el lema en cursiva.
   ================================================================== */
.marquesina{position:relative;margin-bottom:1.7rem}
.esc-logo{display:flex;justify-content:center;margin-bottom:14px}
.esc-logo img{width:clamp(74px,9vw,112px);height:auto;object-fit:contain;
  filter:drop-shadow(0 8px 20px rgba(0,0,0,.55))}
.esc-logo .logo-texto{font-family:var(--serif);font-weight:700;
  font-size:clamp(1.5rem,3vw,2.1rem);letter-spacing:.06em;color:var(--gold-brillo)}

.marca-nombre{font-family:var(--serif);font-weight:700;
  font-size:clamp(1.7rem,5vw,2.6rem);letter-spacing:.06em;
  text-transform:uppercase;color:var(--gold);margin:0;
  text-shadow:0 0 26px rgba(227,187,109,.35);line-height:1.12}

.marca-sub{font-size:12px;letter-spacing:.3em;text-transform:uppercase;
  color:var(--suave);margin-top:6px}

.marca-lema{font-family:var(--serif);font-style:italic;color:var(--gold-brillo);
  font-size:clamp(.95rem,1.7vw,1.15rem);margin-top:10px;
  text-shadow:0 0 18px rgba(227,187,109,.28)}

/* ==================================================================
   LA TIRA PROMOCIONAL que va cambiando sola, con sus puntitos
   ================================================================== */
.promo{position:relative;width:min(640px,100%);overflow:hidden;
  background:rgba(20,22,31,.72);border:1px solid var(--borde);
  border-radius:var(--radius);margin-bottom:1.9rem;
  box-shadow:0 6px 18px rgba(0,0,0,.35)}
.promo-pista{display:flex;transition:transform .45s ease}
.promo-lamina{min-width:100%;padding:15px 20px;text-align:center;
  font-size:13.5px;color:var(--suave);line-height:1.6}
.promo-lamina .icono{display:block;font-size:24px;margin-bottom:6px}
.promo-lamina b{display:block;font-family:var(--serif);font-size:15px;
  color:var(--gold-brillo);margin-bottom:2px;letter-spacing:.2px}
.promo-puntos{display:flex;justify-content:center;gap:6px;padding-bottom:12px}
.promo-puntos .puntito{width:6px;height:6px;border-radius:50%;
  background:var(--borde);transition:background .3s,transform .3s}
.promo-puntos .puntito.primero{background:var(--gold);transform:scale(1.3)}
.esc-boton{position:relative;display:inline-flex;align-items:center;gap:.7rem;
  padding:1.05rem 2.5rem;font-size:1.18rem;font-weight:800;letter-spacing:.6px;
  border:none;border-radius:11px;cursor:pointer;color:#1a1206;text-transform:uppercase;
  background:linear-gradient(135deg,var(--gold-dim),var(--gold-brillo));
  box-shadow:0 14px 34px rgba(0,0,0,.6),0 0 0 1px rgba(227,187,109,.4) inset;
  overflow:hidden;text-decoration:none;transition:transform .18s,box-shadow .18s}
.esc-boton:hover{transform:translateY(-3px);color:#1a1206;
  box-shadow:0 22px 48px rgba(0,0,0,.7),0 0 0 1px rgba(246,216,150,.7) inset}
.esc-boton::after{content:"";position:absolute;top:0;left:-120%;width:60%;height:100%;
  background:linear-gradient(100deg,rgba(255,255,255,0),rgba(255,255,255,.55),rgba(255,255,255,0));
  transform:skewX(-18deg);animation:escPasada 3.2s ease-in-out infinite}
@keyframes escPasada{ 0%{ left:-120%; } 45%,100%{ left:130%; } }
.esc-reanudar{display:inline-block;margin-left:.7rem}
.esc-reanudar a{color:var(--gold);font-weight:600}

/* ---- las tres tarjetas ---- */
.esc-tarjetas{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));
  gap:1.2rem;margin:2.6rem 0}
.esc-tarjeta{position:relative;padding:1.6rem 1.5rem;border-radius:12px;
  background:linear-gradient(160deg,var(--card),#12141c);
  border:1px solid var(--borde);box-shadow:0 8px 24px rgba(0,0,0,.4);
  transform-style:preserve-3d;transition:transform .18s ease,box-shadow .18s ease,
    border-color .18s ease}
.esc-tarjeta:hover{border-color:var(--gold-dim);box-shadow:0 20px 46px rgba(0,0,0,.6)}
.esc-tarjeta h3{font-family:var(--serif);margin:.6rem 0 .4rem;font-size:1.2rem;
  color:var(--gold-brillo)}
.esc-tarjeta p{margin:0;color:var(--suave);font-size:.94rem;line-height:1.55}
.esc-tarjeta .icono-svg{width:54px;height:47px}
.esc-tarjeta .icono-svg svg{width:100%;height:100%}

/* ---- la demo con posters ---- */
.esc-demo{display:grid;grid-template-columns:minmax(230px,300px) 2fr;gap:1.6rem;
  align-items:center;margin:2.6rem 0}
@media (max-width:820px){ .esc-demo{ grid-template-columns:1fr; } }
.esc-grande{position:relative;border-radius:12px;overflow:hidden;
  background:linear-gradient(160deg,#21262f,#12141a);aspect-ratio:2/3;
  box-shadow:0 20px 50px rgba(0,0,0,.65)}
.esc-grande img,.esc-mini img{width:100%;height:100%;object-fit:cover;display:block;
  animation:escKen 14s ease-in-out infinite alternate}
@keyframes escKen{ from{ transform:scale(1.02); } to{ transform:scale(1.12); } }
.esc-minis{display:grid;grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:.8rem}
.esc-mini{position:relative;border-radius:9px;overflow:hidden;aspect-ratio:2/3;
  background:linear-gradient(160deg,#21262f,#12141a);
  border:1px solid var(--borde);box-shadow:0 8px 20px rgba(0,0,0,.5);cursor:pointer;
  transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease}
.esc-mini:hover{transform:translateY(-6px) scale(1.05);border-color:var(--gold-dim);
  box-shadow:0 18px 38px rgba(0,0,0,.65);z-index:2}
.esc-mini::after{content:"";position:absolute;inset:0;
  background:linear-gradient(115deg,rgba(255,255,255,0) 40%,rgba(255,240,214,.35) 50%,rgba(255,255,255,0) 60%);
  transform:translateX(-120%);transition:transform .6s ease}
.esc-mini:hover::after{transform:translateX(120%)}
.esc-hueco{display:flex;align-items:center;justify-content:center;padding:1rem}

/* ---- los numeros ---- */
.esc-cifras{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
  gap:1rem;margin:2.4rem 0}
.esc-cifra{text-align:center;padding:1.5rem 1rem;border-radius:12px;
  background:var(--card);border:1px solid var(--borde)}
.esc-cifra b{display:block;font-family:var(--serif);font-size:2.4rem;
  color:var(--gold-brillo);line-height:1.1}
.esc-cifra span{font-size:.92rem;color:var(--suave)}
.esc-nota{font-size:.86rem;color:var(--tenue);text-align:center;margin-top:1.5rem;
  max-width:var(--medida);margin-left:auto;margin-right:auto;line-height:1.7}
.esc-titulo-seccion{font-family:var(--serif);font-size:1.7rem;margin:0 0 .3rem;
  color:var(--gold-brillo)}

/* sale al bajar, como los vinilos que pasan */
.revelar{opacity:0;transform:translateY(24px);transition:opacity .7s ease,transform .7s ease}
.revelar.visible{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){
  .esc-brillo,.esc-boton::after,.esc-grande img{animation:none}
  .revelar{opacity:1;transform:none}
}
"""