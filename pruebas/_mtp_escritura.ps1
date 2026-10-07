$ErrorActionPreference = "Stop"
function Info($m){ Write-Host $m }

$shell = New-Object -ComObject Shell.Application
$pc = $shell.NameSpace(17)
$dev = @($pc.Items()) | Where-Object { -not $_.IsFileSystem } | Select-Object -First 1
if(-not $dev){ Info "SIN DISPOSITIVO"; exit 1 }
Info ("Dispositivo: " + $dev.Name)

$vol = @($dev.GetFolder.Items()) | Where-Object { $_.IsFolder } | Select-Object -First 1
Info ("Volumen: " + $vol.Name)
$volFolder = $vol.GetFolder

$nombre = "QBASWING_PRUEBA_BORRAR"
# Crear carpeta si no existe.
$ya = @($volFolder.Items()) | Where-Object { $_.Name -eq $nombre } | Select-Object -First 1
if(-not $ya){
    $volFolder.NewFolder($nombre)
    Start-Sleep -Seconds 2
}
$carpeta = @($volFolder.Items()) | Where-Object { $_.Name -eq $nombre } | Select-Object -First 1
if(-not $carpeta){ Info "NO SE PUDO CREAR LA CARPETA"; exit 1 }
Info "Carpeta de prueba creada."
$destFolder = $carpeta.GetFolder

# Archivo local de 40 KB.
$local = Join-Path $env:TEMP "prueba_cover.jpg"
[byte[]]$bytes = New-Object byte[] 40960
for($i=0; $i -lt $bytes.Length; $i++){ $bytes[$i] = 65 }
[System.IO.File]::WriteAllBytes($local, $bytes)
Info ("Archivo local: " + (Get-Item $local).Length + " bytes")

# Copiar al telefono.
$destFolder.CopyHere($local)
$ok = $false
for($i=0; $i -lt 20; $i++){
    Start-Sleep -Seconds 1
    $copia = @($destFolder.Items()) | Where-Object { $_.Name -eq "prueba_cover.jpg" } | Select-Object -First 1
    if($copia){ $ok = $true; break }
}
if($ok){
    Info "COPIA OK: el archivo llego al telefono."
} else {
    Info "COPIA FALLIDA: no aparece el archivo."
}

# Limpiar: borrar el archivo y la carpeta de prueba (solo lo que creamos).
$borrar = @($destFolder.Items()) | Where-Object { $_.Name -eq "prueba_cover.jpg" } | Select-Object -First 1
if($borrar){
    $v = @($borrar.Verbs()) | Where-Object { $_.Name -match "liminar|elete|Borrar" } | Select-Object -First 1
    if($v){ $v.DoIt(); Start-Sleep -Seconds 2; Info "Archivo de prueba borrado." }
}
$v2 = @($carpeta.Verbs()) | Where-Object { $_.Name -match "liminar|elete|Borrar" } | Select-Object -First 1
if($v2){ $v2.DoIt(); Start-Sleep -Seconds 2; Info "Carpeta de prueba borrada." }
Remove-Item $local -Force -ErrorAction SilentlyContinue
Info "FIN"
