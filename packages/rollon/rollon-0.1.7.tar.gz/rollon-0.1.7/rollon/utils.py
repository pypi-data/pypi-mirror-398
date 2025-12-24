from __future__ import annotations
import os
import re

def asegurar_directorio(path: str) -> None:
    """Crea el directorio si no existe (idempotente)."""
    os.makedirs(path, exist_ok=True)

def normaliza(s: str | None) -> str:
    """Espacios a uno solo, recorte y minúsculas."""
    return re.sub(r"\s+", " ", (s or "")).strip().lower()

def artista_principal(artista: str) -> str:
    """
    Elimina sufijos comunes ('- Topic', 'VEVO'), y si hay separadores (coma, &),
    devuelve solo el primer artista.
    """
    if not artista:
        return "Desconocido"
    a = artista.strip()
    a = re.sub(r"(?i)\s*-\s*topic$", "", a).strip()
    a = re.sub(r"(?i)(?:\s*-\s*)?vevo$", "", a).strip()
    a = re.split(r"[,&]", a)[0].strip()
    return a or "Desconocido"

def limpia_nombre_album(nombre: str | None) -> str | None:
    """Quita marcadores como (Deluxe), (Remastered 20xx), (Expanded), (Special Edition), (2020), etc."""
    if not nombre:
        return nombre
    a = nombre
    a = re.sub(
        r"\((?:[^\)]*(deluxe|remaster(?:ed)?|expanded|special(?:\s+edition)?|anniversary)[^\)]*)\)",
        "",
        a,
        flags=re.I,
    )
    a = re.sub(r"(deluxe|remaster(?:ed)?|expanded|special(?:\s+edition)?|anniversary)", "", a, flags=re.I)
    a = re.sub(r"\(\s*\d{4}\s*\)", "", a)  # (2020)
    a = re.sub(r"\s+", " ", a)
    return a.strip()

def tiene_bandera_edicion(nombre: str | None) -> bool:
    return bool(re.search(r"(deluxe|remaster|expanded|special|anniversary)", nombre or "", re.I))
