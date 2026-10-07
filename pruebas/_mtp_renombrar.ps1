$ErrorActionPreference = "Stop"
function Info($m){ Write-Host $m }
function Listar($f){ return ((@($f.Items()) | ForEach-Object { $_.Name }) -join " | ") }

$shell = New-Object -ComObject Shell.Application
$pc = $shell.NameSpace(17)
$dev = @($pc.Items()) | Where-Object { -not $_.IsFileSystem } | Select-Object -First 1
$volFolder = (@($dev.GetFolder.Items()) | Where-Object { $_.IsFolder } | Select-Object -First 1).GetFolder

$nombre = "QBASWING_PRUEBA_BORRAR"
if(-not (@($volFolder.Items()) | Where-Object { $_.Name -eq $nombre })){ $volFolder.NewFolder($nombre); Start-Sleep -Seconds 2 }
$carpeta = @($volFolder.Items()) | Where-Object { $_.Name -eq $nombre } | Select-Object -First 1
$destFolder = $carpeta.GetFolder

$local = Join-Path $env:TEMP "cover.jpg"
[byte[]]$bytes = New-Object byte[] 40960
for($i=0; $i -lt $bytes.Length; $i++){ $bytes[$i] = 65 }
[System.IO.File]::WriteAllBytes($local, $bytes)
$srcItem = $shell.NameSpace($env:TEMP).ParseName("cover.jpg")

Info "1) Copiando cover.jpg ..."
$destFolder.CopyHere($srcItem)
for($i=0; $i -lt 30; $i++){ Start-Sleep -Seconds 1; if(@($destFolder.Items()).Count -gt 0){ break } }
Info ("   Contenido tras copiar: " + (Listar $destFolder))

# Intentar renombrar el elemento a "cover.jpg"
$item = @($destFolder.Items()) | Select-Object -First 1
if($item){
    Info ("2) Intentando renombrar '" + $item.Name + "' a 'cover.jpg' ...")
    try { $item.Name = "cover.jpg"; Start-Sleep -Seconds 3; Info "   Renombrado sin error." }
    catch { Info ("   Error al renombrar: " + $_.Exception.Message) }
    Info ("   Contenido tras renombrar: " + (Listar $destFolder))
}

# Limpieza
foreach($it in @($destFolder.Items())){
    $v = @($it.Verbs()) | Where-Object { $_.Name -match "liminar|elete" } | Select-Object -First 1
    if($v){ $v.DoIt(); Start-Sleep -Seconds 2 }
}
$v2 = @($carpeta.Verbs()) | Where-Object { $_.Name -match "liminar|elete" } | Select-Object -First 1
if($v2){ $v2.DoIt(); Start-Sleep -Seconds 2 }
Remove-Item $local -Force -ErrorAction SilentlyContinue
Info "FIN"
