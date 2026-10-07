$ErrorActionPreference = "Stop"
function Info($m){ Write-Host $m }

$shell = New-Object -ComObject Shell.Application
$pc = $shell.NameSpace(17)
$dev = @($pc.Items()) | Where-Object { -not $_.IsFileSystem } | Select-Object -First 1
if(-not $dev){ Info "SIN DISPOSITIVO"; exit 1 }
$volFolder = (@($dev.GetFolder.Items()) | Where-Object { $_.IsFolder } | Select-Object -First 1).GetFolder

$nombre = "QBASWING_PRUEBA_BORRAR"
if(-not (@($volFolder.Items()) | Where-Object { $_.Name -eq $nombre })){ $volFolder.NewFolder($nombre); Start-Sleep -Seconds 2 }
$carpeta = @($volFolder.Items()) | Where-Object { $_.Name -eq $nombre } | Select-Object -First 1
$destFolder = $carpeta.GetFolder
Info ("Destino listo. Elementos actuales: " + @($destFolder.Items()).Count)

# Archivo local y su elemento Shell
$local = Join-Path $env:TEMP "prueba_cover.jpg"
[byte[]]$bytes = New-Object byte[] 40960
for($i=0; $i -lt $bytes.Length; $i++){ $bytes[$i] = 65 }
[System.IO.File]::WriteAllBytes($local, $bytes)
$srcNs = $shell.NameSpace($env:TEMP)
$srcItem = $srcNs.ParseName("prueba_cover.jpg")
Info ("Origen: " + $srcItem.Name + " / " + $srcItem.Size + " bytes")

Info "Variante A: CopyHere(elemento) ..."
$destFolder.CopyHere($srcItem)
$okA = $false
for($i=0; $i -lt 30; $i++){ Start-Sleep -Seconds 1; if(@($destFolder.Items()) | Where-Object { $_.Name -eq "prueba_cover.jpg" }){ $okA=$true; break } }
Info ("  A resultado: " + $okA)

if(-not $okA){
    Info "Variante B: CopyHere(elemento, 16) ..."
    $destFolder.CopyHere($srcItem, 16)
    for($i=0; $i -lt 30; $i++){ Start-Sleep -Seconds 1; if(@($destFolder.Items()) | Where-Object { $_.Name -eq "prueba_cover.jpg" }){ $okA=$true; break } }
    Info ("  B resultado: " + $okA)
}

Info ("Elementos finales: " + ((@($destFolder.Items()) | ForEach-Object { $_.Name }) -join ", "))

# Limpieza
$borrar = @($destFolder.Items()) | Where-Object { $_.Name -eq "prueba_cover.jpg" } | Select-Object -First 1
if($borrar){ $v = @($borrar.Verbs()) | Where-Object { $_.Name -match "liminar|elete" } | Select-Object -First 1; if($v){ $v.DoIt(); Start-Sleep -Seconds 2 } }
$v2 = @($carpeta.Verbs()) | Where-Object { $_.Name -match "liminar|elete" } | Select-Object -First 1
if($v2){ $v2.DoIt(); Start-Sleep -Seconds 2 }
Remove-Item $local -Force -ErrorAction SilentlyContinue
Info "FIN"
