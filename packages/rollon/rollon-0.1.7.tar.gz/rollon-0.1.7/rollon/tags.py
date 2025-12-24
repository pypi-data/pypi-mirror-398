from __future__ import annotations
import os
import shutil
import subprocess
from typing import List

def embeber_portada(ruta_portada: str | None, archivos_opus: List[str]) -> int:
    """
    Embebe una portada en archivos .opus usando 'opustags' (opus-tools).
    Devuelve la cantidad de archivos procesados con éxito.
    """
    if not ruta_portada or not os.path.exists(ruta_portada):
        print("⚠️ No hay portada para embeber (ruta inexistente).")
        return 0
    if not shutil.which("opustags"):
        print("❌ No se puede embeber portada: 'opustags' no está instalado."
              "Instala con: sudo apt update && sudo apt install -y opus-tools")
        return 0

    ok = 0
    for f in archivos_opus:
        if not os.path.exists(f):
            continue
        try:
            subprocess.run(["opustags", "--set-cover", ruta_portada, "-i", f], check=False)
            ok += 1
        except Exception as e:
            print(f"❌ Error al embeber portada en {os.path.basename(f)}: {e}")
    return ok

def poner_tags_opus(ruta_archivo: str, tags: dict):
    """Establece tags simples en un archivo .opus con opustags."""
    if not os.path.exists(ruta_archivo):
        return
    cmd = ["opustags", "-i", ruta_archivo]
    for k, v in tags.items():
        if v is None:
            continue
        cmd += ["--set", f"{k}={v}"]
    try:
        subprocess.run(cmd, check=False)
    except FileNotFoundError:
        print("ADVERTENCIA: 'opustags' no está instalado o no está en PATH.")
