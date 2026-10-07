# -*- coding: utf-8 -*-
"""
QBASWING COVERS - Soporte de telefonos y dispositivos portatiles (MTP).

Windows no le asigna letra de unidad a un telefono: aparece en "Este equipo"
como un dispositivo MTP y solo se puede recorrer por el Shell de Windows.
Este modulo usa PowerShell + Shell.Application (COM) para:

    - listar los dispositivos portatiles conectados,
    - recorrer sus carpetas buscando videos,
    - escribir cover.jpg en una carpeta del dispositivo (funcion que
      queda disponible, pero el flujo de descarga ya NO la usa: los
      posters se guardan en Descargas\\QBASWING COVERS).

Reglas de seguridad (igual que el resto del programa):
    - Solo lectura al escanear.
    - Nunca borra, mueve ni sobrescribe archivos.
    - Si alguien usa escribir_cover, solo en carpetas sin ninguna imagen.
"""

import os
import re
import json
import time
import base64
import random
import string
import subprocess
from urllib.parse import quote, unquote

PREFIJO = "mtp://"

# Presupuesto de tiempo (segundos) para recorrer un dispositivo, para que un
# telefono con muchisimas carpetas no deje la pantalla colgada.
TIEMPO_LIMITE = 240.0
PROFUNDIDAD_MTP = 5

VIDEO_EXT = {
    ".mkv", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
    ".mpg", ".mpeg", ".m2ts", ".ts", ".vob", ".rmvb", ".rm", ".3gp",
    ".divx", ".asf", ".ogv", ".f4v", ".mts", ".m2v", ".dat",
}
# Carpetas que nunca se escanean (no son coleccion).
CARPETAS_IGNORADAS = {
    "node_modules", "$recycle.bin", "system volume information",
    "windows", "program files", "program files (x86)", "programdata",
    "appdata", ".git", ".svn", "__pycache__", ".cache", ".vscode",
    "thumbs", "thumbnails", "sample", "samples", "screenshots",
    "windows.old", "$windows.~bt", "$windows.~ws", "recovery",
}

IMAGE_EXT = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif", ".jfif",
}

_CREATE_NO_WINDOW = 0x08000000


# --------------------------------------------------------------------------
# Utilidades de ruta  (mtp://<dispositivo>/<carpeta>/<subcarpeta>...)
# --------------------------------------------------------------------------

def es_ruta_mtp(ruta):
    return bool(ruta) and str(ruta).startswith(PREFIJO)


def unir(dispositivo, partes):
    """Construye una ruta MTP a partir del nombre del equipo y sus carpetas."""
    componentes = [quote(dispositivo, safe="")]
    componentes += [quote(p, safe="") for p in partes]
    return PREFIJO + "/".join(componentes)


def partir(ruta):
    """Devuelve (dispositivo, [carpetas...]) de una ruta MTP."""
    resto = str(ruta)[len(PREFIJO):]
    trozos = resto.split("/")
    dispositivo = unquote(trozos[0]) if trozos else ""
    partes = [unquote(t) for t in trozos[1:]]
    return dispositivo, partes


# --------------------------------------------------------------------------
# Puente con PowerShell
# --------------------------------------------------------------------------

def _power_shell(script, variables=None, timeout=120, control=None):
    """
    Ejecuta un script de PowerShell y devuelve su salida (texto) o None.
    El script se pasa codificado para no pelear con comillas ni acentos.

    Mientras el script corre se mira el control a intervalos cortos: si el
    usuario pulsa detener o cancelar, se mata el proceso y se devuelve None
    enseguida. Antes se esperaba en un bloqueo unico (hasta 330 segundos)
    y los botones de pausa, detener y cancelar no hacian efecto hasta que
    el escaneo del telefono terminaba solo.
    """
    if os.name != "nt":
        return None

    entorno = dict(os.environ)
    if variables:
        for clave, valor in variables.items():
            entorno[clave] = valor

    try:
        codificado = base64.b64encode(
            script.encode("utf-16-le")).decode("ascii")
    except Exception:
        return None

    orden = [
        "powershell", "-NoProfile", "-NonInteractive",
        "-ExecutionPolicy", "Bypass", "-EncodedCommand", codificado,
    ]

    try:
        proc = subprocess.Popen(orden, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                env=entorno, creationflags=_CREATE_NO_WINDOW)
    except Exception:
        return None

    # Se espera por trozos, mirando el control en cada vuelta.
    trozo = 0.25
    espera = 0.0
    while True:
        if proc.poll() is not None:
            break
        if control is not None:
            try:
                if control.terminado():
                    proc.kill()
                    proc.wait()
                    return None
                # En pausa el proceso se queda donde esta, sin consumir
                # la cuenta atras, hasta que digan seguir.
                if control.es_pausado():
                    if not control.esperar(trozo):
                        proc.kill()
                        proc.wait()
                        return None
                    continue
            except Exception:
                pass
        if timeout and espera >= timeout:
            try:
                proc.kill()
                proc.wait()
            except Exception:
                pass
            return None
        time.sleep(trozo)
        espera += trozo

    try:
        salida, _ = proc.communicate()
    except Exception:
        return None
    if not salida:
        return None
    return salida.decode("utf-8", "replace")


# --------------------------------------------------------------------------
# 1) Lista de dispositivos portatiles
# --------------------------------------------------------------------------

_PS_DISPOSITIVOS = r'''
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference="SilentlyContinue"
$shell = New-Object -ComObject Shell.Application
$pc = $shell.NameSpace(17)
$nombres = @(@($pc.Items()) | Where-Object { -not $_.IsFileSystem } |
             ForEach-Object { $_.Name } | Where-Object { $_ })
Write-Output ("__QB__" + (ConvertTo-Json -InputObject $nombres -Compress))
'''


def hay_soporte():
    """True si este Windows puede hablar con telefonos MTP."""
    return os.name == "nt"


def dispositivos():
    """Nombres de los dispositivos portatiles conectados (telefonos, etc.)."""
    salida = _power_shell(_PS_DISPOSITIVOS, timeout=40)
    if not salida:
        return []
    texto = ""
    for linea in salida.splitlines():
        if linea.startswith("__QB__"):
            texto = linea[len("__QB__"):].strip()
            break
    if not texto:
        return []
    try:
        datos = json.loads(texto)
    except ValueError:
        return []
    if isinstance(datos, str):
        datos = [datos]
    return [str(d).strip() for d in datos if str(d).strip()]


# --------------------------------------------------------------------------
# 2) Escaneo de un dispositivo  (solo lectura)
# --------------------------------------------------------------------------

_PS_ESCANEAR = r'''
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference="SilentlyContinue"
$device  = $env:QB_DEVICE
$depth   = [int]$env:QB_DEPTH
$budget  = [double]$env:QB_LIMITE
$extV    = @($env:QB_VIDEO.Split(","))
$extI    = @($env:QB_IMG.Split(","))
$excl    = @($env:QB_EXCLUIDAS.Split("|"))
$salida  = New-Object System.Collections.ArrayList
$reloj   = [System.Diagnostics.Stopwatch]::StartNew()

$shell = New-Object -ComObject Shell.Application
$pc = $shell.NameSpace(17)
$dev = @($pc.Items()) | Where-Object { -not $_.IsFileSystem -and $_.Name -eq $device } | Select-Object -First 1
if(-not $dev){ Write-Output "__QB__[]"; exit }

function Recorrer($folder, $partes, $nivel){
    if($reloj.Elapsed.TotalSeconds -gt $budget){ return }
    if($nivel -gt $depth){ return }
    $items = @($folder.Items())
    $videos = 0; $imgs = 0; $subs = @()
    foreach($it in $items){
        if($it.IsFolder){ $subs += $it; continue }
        $e = [System.IO.Path]::GetExtension($it.Name).ToLower()
        if($extV -contains $e){ $videos++ }
        elseif($extI -contains $e){ $imgs++ }
    }
    if($videos -gt 0){
        [void]$salida.Add([PSCustomObject]@{ partes=@($partes); videos=$videos; imagenes=$imgs })
    }
    foreach($s in $subs){
        if($reloj.Elapsed.TotalSeconds -gt $budget){ return }
        if($excl -contains $s.Name.ToLower()){ continue }
        $f = $s.GetFolder
        if($f -ne $null){ Recorrer $f (@($partes) + @($s.Name)) ($nivel+1) }
    }
}

$raiz = $dev.GetFolder
foreach($v in @($raiz.Items())){
    if($reloj.Elapsed.TotalSeconds -gt $budget){ break }
    if($excl -contains $v.Name.ToLower()){ continue }
    if($v.IsFolder){
        $f = $v.GetFolder
        if($f -ne $null){ Recorrer $f @($v.Name) 1 }
    }
}

if($salida.Count -eq 0){ Write-Output "__QB__[]" }
else { Write-Output ("__QB__" + (ConvertTo-Json -InputObject @($salida) -Compress -Depth 6)) }
'''


def escanear(ruta, profundidad=PROFUNDIDAD_MTP, limite=TIEMPO_LIMITE,
             progreso=None, control=None):
    """
    Recorre un dispositivo MTP y devuelve las carpetas candidatas.
    Misma forma de diccionario que escaneo.escanear_unidad().

    control : si el usuario detiene o cancela, se mata el proceso de
    PowerShell en cuanto se puede y se devuelve lo que lleve.
    """
    dispositivo, _ = partir(ruta)
    if not dispositivo:
        return []

    if progreso is not None:
        # Sin try/except: si el usuario ya detuvo o cancelo, la
        # excepcion tiene que subir y no quedarse aqui dentro.
        progreso(dispositivo)

    variables = {
        "QB_DEVICE": dispositivo,
        "QB_DEPTH": str(int(profundidad)),
        "QB_LIMITE": str(float(limite)),
        "QB_VIDEO": ",".join(sorted(VIDEO_EXT)),
        "QB_IMG": ",".join(sorted(IMAGE_EXT)),
    }
    salida = _power_shell(_PS_ESCANEAR, variables, timeout=limite + 90,
                          control=control)
    if not salida:
        return []

    texto = ""
    for linea in salida.splitlines():
        if linea.startswith("__QB__"):
            texto = linea[len("__QB__"):].strip()
    if not texto:
        return []
    try:
        datos = json.loads(texto)
    except ValueError:
        return []
    if isinstance(datos, dict):
        datos = [datos]

    encontradas = []
    for d in datos:
        partes = d.get("partes") or []
        if isinstance(partes, str):
            partes = [partes]
        if not partes:
            continue
        encontradas.append({
            "ruta": unir(dispositivo, partes),
            "nombre": partes[-1],
            "unidad": ruta,
            "ya_tiene": (int(d.get("imagenes") or 0) > 0),
            "imagen_existente": "",
            "videos": int(d.get("videos") or 0),
        })
    return encontradas


# --------------------------------------------------------------------------
# 3) Estado de una carpeta y escritura de cover.jpg
# --------------------------------------------------------------------------

_PS_ESTADO = r'''
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference="SilentlyContinue"
$device = $env:QB_DEVICE
$extI   = @($env:QB_IMG.Split(","))

function Bajar($folder, $partes){
    foreach($p in $partes){
        $it = @($folder.Items()) | Where-Object { $_.IsFolder -and $_.Name -eq $p } | Select-Object -First 1
        if(-not $it){ return $null }
        $folder = $it.GetFolder
        if($folder -eq $null){ return $null }
    }
    return $folder
}

$shell = New-Object -ComObject Shell.Application
$pc = $shell.NameSpace(17)
$dev = @($pc.Items()) | Where-Object { -not $_.IsFileSystem -and $_.Name -eq $device } | Select-Object -First 1
if(-not $dev){ Write-Output '__QB__{"carpeta":false}'; exit }

$partes = @()
$partes = @()
if($env:QB_PARTES){
    $crudo = $env:QB_PARTES.Trim()
    if($crudo -ne "" -and $crudo -ne "[]"){
        $tmp = ConvertFrom-Json $crudo
        $partes = @($tmp | Where-Object { $_ -ne $null -and "$_" -ne "" })
    }
}
$folder = $dev.GetFolder
$folder = Bajar $folder $partes
if($folder -eq $null){ Write-Output '__QB__{"carpeta":false}'; exit }

$tiene_cover = $false; $imagenes = 0
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
}
$obj = [PSCustomObject]@{ carpeta=$true; cover=$tiene_cover; imagenes=$imagenes }
Write-Output ("__QB__" + (ConvertTo-Json -InputObject $obj -Compress))
'''


def estado_carpeta(ruta):
    """{'carpeta': bool, 'cover': bool, 'imagenes': int} de una carpeta MTP."""
    dispositivo, partes = partir(ruta)
    if not dispositivo:
        return {"carpeta": False, "cover": False, "imagenes": 0}
    variables = {
        "QB_DEVICE": dispositivo,
        **({"QB_PARTES": json.dumps(partes, ensure_ascii=False)}
           if partes else {}),
        "QB_IMG": ",".join(sorted(IMAGE_EXT)),
    }
    salida = _power_shell(_PS_ESTADO, variables, timeout=90)
    if not salida:
        return {"carpeta": False, "cover": False, "imagenes": 0}
    for linea in salida.splitlines():
        if linea.startswith("__QB__"):
            try:
                datos = json.loads(linea[len("__QB__"):].strip())
            except ValueError:
                continue
            return {
                "carpeta": bool(datos.get("carpeta")),
                "cover": bool(datos.get("cover")),
                "imagenes": int(datos.get("imagenes") or 0),
            }
    return {"carpeta": False, "cover": False, "imagenes": 0}


def tiene_imagen(ruta):
    return estado_carpeta(ruta).get("imagenes", 0) > 0


_PS_ESCRIBIR = r'''
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference="SilentlyContinue"
$device  = $env:QB_DEVICE
$archivo = $env:QB_ARCHIVO
$base    = $env:QB_BASE

function Bajar($folder, $partes){
    foreach($p in $partes){
        $it = @($folder.Items()) | Where-Object { $_.IsFolder -and $_.Name -eq $p } | Select-Object -First 1
        if(-not $it){ return $null }
        $folder = $it.GetFolder
        if($folder -eq $null){ return $null }
    }
    return $folder
}

$shell = New-Object -ComObject Shell.Application
$pc = $shell.NameSpace(17)
$dev = @($pc.Items()) | Where-Object { -not $_.IsFileSystem -and $_.Name -eq $device } | Select-Object -First 1
if(-not $dev){ Write-Output "NO_DEVICE"; exit 1 }

$partes = @()
$partes = @()
if($env:QB_PARTES){
    $crudo = $env:QB_PARTES.Trim()
    if($crudo -ne "" -and $crudo -ne "[]"){
        $tmp = ConvertFrom-Json $crudo
        $partes = @($tmp | Where-Object { $_ -ne $null -and "$_" -ne "" })
    }
}
$folder = Bajar $dev.GetFolder $partes
if($folder -eq $null){ Write-Output "NO_FOLDER"; exit 2 }

# Nunca sobrescribir: si ya hay cover.jpg, se cancela.
foreach($it in @($folder.Items())){
    if(-not $it.IsFolder -and ($it.Name -ieq "cover.jpg" -or $it.Name -ieq "cover")){
        Write-Output "YA_EXISTE"; exit 3
    }
}

$dir = [System.IO.Path]::GetDirectoryName($archivo)
$nom = [System.IO.Path]::GetFileName($archivo)
$src = $shell.NameSpace($dir).ParseName($nom)
if($src -eq $null){ Write-Output "NO_LOCAL"; exit 4 }

$folder.CopyHere($src)

$item = $null
for($i=0; $i -lt 90; $i++){
    Start-Sleep -Seconds 1
    $item = @($folder.Items()) | Where-Object { $_.Name -ieq $base -or $_.Name -ieq ($base + ".jpg") } | Select-Object -First 1
    if($item){ break }
}
if($item -eq $null){ Write-Output "COPY_FAIL"; exit 5 }

try { $item.Name = "cover.jpg" } catch { Write-Output "RENAME_FAIL"; exit 6 }
Start-Sleep -Seconds 2

$ok = $null
for($i=0; $i -lt 10; $i++){
    $ok = @($folder.Items()) | Where-Object { $_.Name -ieq "cover.jpg" } | Select-Object -First 1
    if($ok){ break }
    Start-Sleep -Seconds 1
}
if($ok){ Write-Output "OK" } else { Write-Output "VERIFY_FAIL" }
'''


def escribir_cover(ruta, datos):
    """
    Copia 'datos' (bytes de la imagen) como cover.jpg en la carpeta MTP.
    No sobrescribe: si ya hay un cover, devuelve ('ya_existe', 0).
    Devuelve (estado, tamano) con el mismo vocabulario que la descarga local.
    """
    dispositivo, partes = partir(ruta)
    if not dispositivo or not partes:
        return "fallo", 0

    if not datos:
        return "fallo", 0

    # Archivo temporal local con nombre unico (Windows oculta la extension
    # al copiar por el Shell, por eso luego se renombra a cover.jpg).
    sufijo = "".join(random.choice(string.hexdigits.lower()) for _ in range(8))
    base = "qbc_%s" % sufijo
    temporal = os.path.join(os.environ.get("TEMP", "."), base + ".jpg")
    try:
        with open(temporal, "wb") as f:
            f.write(datos)
    except Exception:
        return "fallo", 0

    variables = {
        "QB_DEVICE": dispositivo,
        **({"QB_PARTES": json.dumps(partes, ensure_ascii=False)}
           if partes else {}),
        "QB_ARCHIVO": temporal,
        "QB_BASE": base,
    }
    try:
        salida = _power_shell(_PS_ESCRIBIR, variables, timeout=180) or ""
    finally:
        try:
            os.remove(temporal)
        except OSError:
            pass

    marca = salida.strip().splitlines()
    marca = marca[-1].strip() if marca else ""
    if marca == "OK":
        return "ok", len(datos)
    if marca == "YA_EXISTE":
        return "ya_existe", 0
    return "fallo", 0


# --------------------------------------------------------------------------
# 4) Listar carpetas de un dispositivo (para navegar en la galeria)
# --------------------------------------------------------------------------

_PS_LISTAR = r'''
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference="SilentlyContinue"
$device = $env:QB_DEVICE

function Bajar($folder, $partes){
    foreach($p in $partes){
        $it = @($folder.Items()) | Where-Object { $_.IsFolder -and $_.Name -eq $p } | Select-Object -First 1
        if(-not $it){ return $null }
        $folder = $it.GetFolder
        if($folder -eq $null){ return $null }
    }
    return $folder
}

$shell = New-Object -ComObject Shell.Application
$pc = $shell.NameSpace(17)
$dev = @($pc.Items()) | Where-Object { -not $_.IsFileSystem -and $_.Name -eq $device } | Select-Object -First 1
if(-not $dev){ Write-Output '__QB__[]'; exit }

$partes = @()
$partes = @()
if($env:QB_PARTES){
    $crudo = $env:QB_PARTES.Trim()
    if($crudo -ne "" -and $crudo -ne "[]"){
        $tmp = ConvertFrom-Json $crudo
        $partes = @($tmp | Where-Object { $_ -ne $null -and "$_" -ne "" })
    }
}
if($partes.Count -eq 0){ $folder = $dev.GetFolder }
else { $folder = Bajar $dev.GetFolder $partes }
if($folder -eq $null){ Write-Output '__QB__[]'; exit }

$salida = New-Object System.Collections.ArrayList
foreach($it in @($folder.Items())){
    if(-not $it.IsFolder){ continue }
    [void]$salida.Add([PSCustomObject]@{ nombre=$it.Name })
}
if($salida.Count -eq 0){ Write-Output '__QB__[]' }
else { Write-Output ("__QB__" + (ConvertTo-Json -InputObject @($salida) -Compress -Depth 5)) }
'''


def listar_subcarpetas(ruta):
    """
    Devuelve las carpetas que hay dentro de una ruta MTP.
    Si la ruta es solo el dispositivo, devuelve sus volumenes
    ("Memoria interna", "Tarjeta SD"...).
    """
    dispositivo, partes = partir(ruta)
    if not dispositivo:
        return []
    variables = {
        "QB_DEVICE": dispositivo,
        **({"QB_PARTES": json.dumps(partes, ensure_ascii=False)}
           if partes else {}),
    }
    salida = _power_shell(_PS_LISTAR, variables, timeout=150)
    if not salida:
        return []
    texto = ""
    for linea in salida.splitlines():
        if linea.startswith("__QB__"):
            texto = linea[len("__QB__"):].strip()
    if not texto:
        return []
    try:
        datos = json.loads(texto)
    except ValueError:
        return []
    if isinstance(datos, dict):
        datos = [datos]

    carpetas = []
    for d in datos:
        nombre = (d.get("nombre") or "").strip()
        if not nombre or nombre.startswith("."):
            continue
        carpetas.append({
            "nombre": nombre,
            "ruta": unir(dispositivo, partes + [nombre]),
            "hijos": 0,
        })
    carpetas.sort(key=lambda c: c["nombre"].lower())
    return carpetas
