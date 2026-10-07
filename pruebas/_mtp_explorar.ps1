$ErrorActionPreference = "SilentlyContinue"
$shell = New-Object -ComObject Shell.Application
$pc = $shell.NameSpace(17)
$dev = @($pc.Items()) | Where-Object { -not $_.IsFileSystem } | Select-Object -First 1
if(-not $dev){ "SIN DISPOSITIVO"; exit }
"DISPOSITIVO: " + $dev.Name

$extVideo = @(".mp4",".mkv",".avi",".mov",".wmv",".flv",".webm",".m4v",".mpg",".mpeg",".m2ts",".ts",".vob",".rmvb",".rm",".3gp",".divx",".asf",".ogv",".f4v",".mts",".m2v",".dat")
$extImg = @(".jpg",".jpeg",".png",".webp",".bmp",".gif",".tiff",".tif",".jfif")
$script:resultado = @()
$script:tamMuestra = 0

function Recorrer($folder, $prefijo, $nivel){
    if($nivel -gt 3){ return }
    $items = @($folder.Items())
    $videos = 0; $imgs = 0; $subs = @()
    foreach($it in $items){
        if($it.IsFolder){ $subs += $it }
        else {
            $n = $it.Name.ToLower()
            $e = [System.IO.Path]::GetExtension($n)
            if($extVideo -contains $e){
                $videos++
                if($script:tamMuestra -eq 0){
                    try { $script:tamMuestra = [long]$it.ExtendedProperty("System.Size") } catch {}
                }
            }
            elseif($extImg -contains $e){ $imgs++ }
        }
    }
    if($videos -gt 0){
        $script:resultado += [PSCustomObject]@{ Ruta = $prefijo; Videos = $videos; Imagenes = $imgs }
    }
    foreach($s in $subs){
        $f = $s.GetFolder
        if($f -ne $null){ Recorrer $f ($prefijo + "|" + $s.Name) ($nivel+1) }
    }
}

$reloj = [System.Diagnostics.Stopwatch]::StartNew()
foreach($v in @($dev.GetFolder.Items())){
    if($v.IsFolder){ $f = $v.GetFolder; if($f -ne $null){ Recorrer $f $v.Name 1 } }
}
$reloj.Stop()

"TIEMPO: " + [math]::Round($reloj.Elapsed.TotalSeconds,1) + " s"
"CARPETAS CON VIDEO: " + $script:resultado.Count
"TAMANO DE EJEMPLO (System.Size): " + $script:tamMuestra
$script:resultado | Select-Object -First 25 | ForEach-Object { "  [" + $_.Videos + "v " + $_.Imagenes + "i] " + $_.Ruta }
