# -*- coding: utf-8 -*-
"""Sondea que devuelve el Shell en la raiz del telefono."""
import sys

sys.path.insert(0, r"C:\QBASWING-COVERS")
import mtp

SCRIPT = r'''
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ErrorActionPreference="SilentlyContinue"
$device = $env:QB_DEVICE
$shell = New-Object -ComObject Shell.Application
$pc = $shell.NameSpace(17)
$todos = @($pc.Items())
Write-Output ("TOTAL EN NameSpace(17): " + $todos.Count)
foreach($d in $todos){
    Write-Output ("  - '" + $d.Name + "' IsFileSystem=" + $d.IsFileSystem + " IsFolder=" + $d.IsFolder)
}
$dev = $todos | Where-Object { -not $_.IsFileSystem -and $_.Name -eq $device } | Select-Object -First 1
if(-not $dev){ Write-Output "NO SE ENCONTRO EL DISPOSITIVO"; exit }

Write-Output ""
Write-Output "--- Items() del dispositivo (directo) ---"
$dir = $dev.GetFolder
Write-Output ("  folder es null: " + ($dir -eq $null))
$items = @($dir.Items())
Write-Output ("  cantidad: " + $items.Count)
foreach($it in $items){
    Write-Output ("  - '" + $it.Name + "' IsFolder=" + $it.IsFolder + " IsFileSystem=" + $it.IsFileSystem)
}
'''

nombres = mtp.dispositivos()
print("dispositivos:", nombres)
salida = mtp._power_shell(SCRIPT, {"QB_DEVICE": nombres[0]}, timeout=90)
print(salida or "(sin salida)")