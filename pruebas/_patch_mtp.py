# -*- coding: utf-8 -*-
"""
mtp.py - correcciones:
  1) QB_PARTES vacio rompia la navegacion (ConvertFrom-Json '[]' en PS 5.1)
  2) se excluyen carpetas basura (node_modules, thumbs...) al escanear
  3) estado_carpeta solo cuenta imagenes que pueden ser poster
"""
import io
import re

RUTA = r"C:\QBASWING-COVERS\mtp.py"
texto = io.open(RUTA, encoding="utf-8").read()
cambios = []


# ---------------------------------------------------------------- 1) QB_PARTES
VIEJO_PARTES = (
    'if($env:QB_PARTES){ $partes = @(ConvertFrom-Json $env:QB_PARTES) }')
NUEVO_PARTES = (
    '$partes = @()\n'
    'if($env:QB_PARTES){\n'
    '    $crudo = $env:QB_PARTES.Trim()\n'
    '    if($crudo -ne "" -and $crudo -ne "[]"){\n'
    '        $tmp = ConvertFrom-Json $crudo\n'
    '        $partes = @($tmp | Where-Object { $_ -ne $null -and "$_" -ne "" })\n'
    '    }\n'
    '}')

n = texto.count(VIEJO_PARTES)
texto = texto.replace(VIEJO_PARTES, NUEVO_PARTES)
cambios.append("QB_PARTES: %d scripts corregidos" % n)

# Python: no mandar QB_PARTES cuando esta vacio
n = texto.count('"QB_PARTES": json.dumps(partes, ensure_ascii=False),')
texto = texto.replace(
    '        "QB_PARTES": json.dumps(partes, ensure_ascii=False),\n',
    '        **({"QB_PARTES": json.dumps(partes, ensure_ascii=False)}\n'
    '           if partes else {}),\n')
cambios.append("QB_PARTES omitido cuando no hay carpetas: %d sitios" % n)

# ------------------------------------------------- 2) exclusiones al escanear
texto = texto.replace(
    'IMAGE_EXT = {',
    '''# Carpetas que nunca se escanean (no son coleccion).
CARPETAS_IGNORADAS = {
    "node_modules", "$recycle.bin", "system volume information",
    "windows", "program files", "program files (x86)", "programdata",
    "appdata", ".git", ".svn", "__pycache__", ".cache", ".vscode",
    "thumbs", "thumbnails", "sample", "samples", "screenshots",
    "windows.old", "$windows.~bt", "$windows.~ws", "recovery",
}

IMAGE_EXT = {''')

# pasar la lista por variable de entorno
texto = texto.replace(
    '$extI    = @($env:QB_IMG.Split(","))\n$salida  = New-Object',
    '$extI    = @($env:QB_IMG.Split(","))\n'
    '$excl    = @($env:QB_EXCLUIDAS.Split("|"))\n'
    '$salida  = New-Object')

# saltar carpetas ignoradas al bajar
texto = texto.replace(
    '''    foreach($s in $subs){
        if($reloj.Elapsed.TotalSeconds -gt $budget){ return }
        $f = $s.GetFolder
        if($f -ne $null){ Recorrer $f (@($partes) + @($s.Name)) ($nivel+1) }
    }''',
    '''    foreach($s in $subs){
        if($reloj.Elapsed.TotalSeconds -gt $budget){ return }
        if($excl -contains $s.Name.ToLower()){ continue }
        $f = $s.GetFolder
        if($f -ne $null){ Recorrer $f (@($partes) + @($s.Name)) ($nivel+1) }
    }''')

# saltar tambien en el primer nivel (volumenes)
texto = texto.replace(
    '''foreach($v in @($raiz.Items())){
    if($reloj.Elapsed.TotalSeconds -gt $budget){ break }
    if($v.IsFolder){''',
    '''foreach($v in @($raiz.Items())){
    if($reloj.Elapsed.TotalSeconds -gt $budget){ break }
    if($excl -contains $v.Name.ToLower()){ continue }
    if($v.IsFolder){''')

# anadir la variable al llamada de escanear
m = re.search(r'"QB_EXCLUIDAS"', texto)
if not m:
    texto = texto.replace(
        '        "QB_VIDEO": ",".join(VIDEO_EXT),',
        '        "QB_VIDEO": ",".join(VIDEO_EXT),\n'
        '        "QB_EXCLUIDAS": "|".join(CARPETAS_IGNORADAS),')
    cambios.append("QB_EXCLUIDAS agregado a la llamada de escanear")

# ------------------------------------------- 3) estado: solo poster de verdad
VIEJO_ESTADO = '''$tiene_cover = $false; $imagenes = 0
foreach($it in @($folder.Items())){
    if($it.IsFolder){ continue }
    if($it.Name -ieq "cover.jpg" -or $it.Name -ieq "cover"){ $tiene_cover = $true }
    $e = [System.IO.Path]::GetExtension($it.Name).ToLower()
    if($extI -contains $e){ $imagenes++ }
    if($it.Name -ieq "cover"){ $imagenes++ }
}'''
NUEVO_ESTADO = '''$tiene_cover = $false; $imagenes = 0
$buenos = @("cover","poster","folder","caratula","portada","front","movie","serie")
foreach($it in @($folder.Items())){
    if($it.IsFolder){ continue }
    $e = [System.IO.Path]::GetExtension($it.Name).ToLower()
    if($e -ne ".jpg" -and $e -ne ".jpeg" -and $e -ne ".png" -and
       $e -ne ".webp" -and $e -ne ".bmp"){ continue }
    $base = [System.IO.Path]::GetFileNameWithoutExtension($it.Name).ToLower()
    if($base -eq "thumbs" -or $base -eq "desktop"){ continue }
    if($buenos -contains $base){ $tiene_cover = $true; $imagenes++; continue }
    # MTP no da el tamano: una imagen suelta no se da por poster.
}'''
n = texto.count(VIEJO_ESTADO)
texto = texto.replace(VIEJO_ESTADO, NUEVO_ESTADO)
cambios.append("estado_carpeta: %d scripts (solo poster de verdad)" % n)

io.open(RUTA, "w", encoding="utf-8", newline="\n").write(texto)

import ast
ast.parse(io.open(RUTA, encoding="utf-8").read())
print("mtp.py parcheado:")
for c in cambios:
    print("   -", c)
print("   sintaxis OK")