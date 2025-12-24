from __future__ import annotations
import glob
import os
import re
import subprocess
from typing import Optional

def sh(cmd, check=False, text=True):
    """Wrapper simple para ejecutar comandos y capturar stdout/stderr."""
    return subprocess.run(cmd, capture_output=True, text=text, check=check)

def obtener_metadata(url: str) -> tuple[str, str, str, str, int]:
    """
    Devuelve (artista, album, titulo, año, tracknum_hint) usando yt-dlp --print.
    """
    cmd = [
        "yt-dlp", "--skip-download",
        "--print", "%(artist,playlist_uploader,channel,uploader,creator)s",
        "--print", "%(album,playlist_title)s",
        "--print", "%(title)s",
        "--print", "%(release_year,release_date>%Y,upload_date>%Y)s",
        "--print", "%(track_number,playlist_index,0)d",
        url,
    ]
    res = sh(cmd)
    lines = (res.stdout or "").splitlines()
    artista = lines[0] if len(lines) > 0 and lines[0].strip() else "Desconocido"
    album = lines[1] if len(lines) > 1 and lines[1].strip() else "Desconocido"
    titulo = lines[2] if len(lines) > 2 and lines[2].strip() else "Desconocido"
    fecha = lines[3] if len(lines) > 3 and lines[3].strip() else "0000"
    try:
        tracknum = int(lines[4]) if len(lines) > 4 and lines[4].strip() else 0
    except ValueError:
        tracknum = 0
    return artista.strip(), album.strip(), titulo.strip(), fecha.strip(), tracknum

def obtener_conteo_playlist(url: str) -> Optional[int]:
    """Intenta n_entries y cae a playlist_count."""
    res = sh(["yt-dlp", "--skip-download", "--print", "%(n_entries,playlist_count)d", url])
    try:
        n = int((res.stdout or "0").strip() or "0")
        return n if n > 0 else None
    except ValueError:
        return None

def existe_opus_con_titulo(ruta: str, titulo: str) -> bool:
    """Verifica si ya existe algún .opus con el título en la carpeta."""
    patron = os.path.join(ruta, f"*{titulo}*.opus")
    archivos = glob.glob(patron)
    return len(archivos) > 0
