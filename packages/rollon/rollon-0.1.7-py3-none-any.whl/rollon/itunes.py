from __future__ import annotations
import json
import os
import re
import urllib.parse
import urllib.request
from typing import Optional

from .config import PAIS_POR_DEFECTO, DEPURAR_ARTE, APPLE_TRUCO_MAXIMO, TAMANO_ARTE_POR_DEFECTO
from .utils import normaliza, limpia_nombre_album

def http_get_json(url: str) -> dict:
    """GET sencillo que devuelve JSON (utf-8)."""
    with urllib.request.urlopen(url, timeout=12) as r:
        return json.loads(r.read().decode("utf-8"))

def itunes_search(term: str, country: str, entity: str = "album",
                  attribute: Optional[str] = None, limit: int = 25):
    """Búsqueda en iTunes Search API."""
    qs = {
        "term": term, "media": "music", "entity": entity,
        "limit": str(limit), "country": country or PAIS_POR_DEFECTO,
    }
    if attribute:
        qs["attribute"] = attribute
    url = "https://itunes.apple.com/search?" + urllib.parse.urlencode(qs)
    try:
        data = http_get_json(url)
        return data.get("results", []) or []
    except Exception:
        return []

def itunes_lookup(id_value: str, country: Optional[str] = None,
                  entity: Optional[str] = None, limit: int = 200):
    """Lookup por ID en iTunes; si entity='song' sobre un collectionId, regresa pistas."""
    qs = {"id": str(id_value), "country": (country or PAIS_POR_DEFECTO)}
    if entity:
        qs["entity"] = entity
    if limit:
        qs["limit"] = str(limit)
    url = "https://itunes.apple.com/lookup?" + urllib.parse.urlencode(qs)
    try:
        data = http_get_json(url)
        return data.get("results", []) or []
    except Exception:
        return []

def _norm_titulo_para_match(titulo: str) -> str:
    """Normaliza títulos quitando '(official video)', 'feat.', 'remastered 20xx', corchetes, etc."""
    t = titulo or ""
    t = re.sub(r"(?i)\s*\((official|official video|lyric video|audio|visualizer|remaster(?:ed)?\s*\d{0,4})\)\s*$", "", t)
    t = re.sub(r"(?i)\s*\[(official|official video|lyric video|audio|visualizer)\]\s*$", "", t)
    t = re.sub(r"(?i)\s*feat\.\s*.+$", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t.lower()

def elegir_mejor_cancion_estricta(artista: str, titulo: str, candidatos: list):
    """Entre resultados 'song' de iTunes, busca coincidencia estricta por artista y título."""
    na = normaliza(artista)
    nt = _norm_titulo_para_match(titulo)
    exactos = [c for c in candidatos if normaliza(c.get("artistName")) == na]
    if not exactos:
        return None

    def puntaje(item):
        s = 0
        n_t = _norm_titulo_para_match(item.get("trackName") or "")
        if n_t == nt:
            s += 100
        elif nt and nt in n_t:
            s += 40
        if nt and nt in normaliza(item.get("collectionName") or ""):
            s += 5
        return s

    mejor = max(exactos, key=puntaje)
    if DEPURAR_ARTE:
        print("[DEBUG_ARTE][cancion] ->", mejor.get("trackName")," artista:", mejor.get("artistName"),"coleccion:", mejor.get("collectionName"))
        return mejor

def elegir_mejor_album_estricto(artista: str, album: str, candidatos: list,
                                pistas_objetivo: Optional[int] = None,
                                anio_objetivo: Optional[int] = None):
    """Entre resultados 'album', elige el mejor por nombre, pistas y año cercanos."""
    na = normaliza(artista)
    nalbum = normaliza(album or "")
    nalbum_limpio = normaliza(limpia_nombre_album(album or "") or "")

    cand = [c for c in candidatos if normaliza(c.get("artistName")) == na]
    if not cand:
        return None

    def anio_de(item):
        rd = (item.get("releaseDate") or "")[:10]
        m = re.match(r"(\d{4})", rd)
        return int(m.group(1)) if m else None

    def puntaje(item):
        s = 0
        nombre = item.get("collectionName") or ""
        n_c = normaliza(nombre)
        tcount = item.get("trackCount") or 0
        if n_c == nalbum:
            s += 80
        if n_c == nalbum_limpio:
            s += 60
        ctype = (item.get("collectionType") or "")
        if "compilation" in ctype.lower() and "hits" not in n_c and "greatest" not in n_c:
            s -= 30
        if pistas_objetivo and tcount:
            s -= min(abs(tcount - pistas_objetivo), 10)
        cy = anio_de(item)
        if anio_objetivo and cy:
            s -= min(abs(cy - anio_objetivo), 10)
        return s

    mejor = max(cand, key=puntaje)
    if DEPURAR_ARTE:
        print("[DEBUG_ARTE][album] ->", mejor.get("collectionName"), "año:", (mejor.get("releaseDate") or "")[:4], "pistas:", mejor.get("trackCount"))
    return mejor

def _aplicar_truco_o_tamano(url100: str, preferir_max: bool, tam: int) -> list[tuple[str, str]]:
    """SOLO dos intentos: (1) truco 'max', (2) tamaño 3000 (o el indicado)."""
    intentos: list[tuple[str, str]] = []
    if preferir_max:
        intentos.append(("max", re.sub(r"/\d+x\d+bb(?:-\d+)?", "/100000x100000-999", url100)))
    s = tam or 3000
    intentos.append((str(s), re.sub(r"/\d+x\d+bb(?:-\d+)?", f"/{s}x{s}bb", url100)))
    return intentos

def descargar_portada_apple_precisa(artista_princ: str, album: str, titulo: str,
                                    country: Optional[str] = None, modo: str = "1",
                                    pistas_objetivo: Optional[int] = None, anio_objetivo: Optional[int] = None,
                                    preferir_max: bool = APPLE_TRUCO_MAXIMO, tamano: int = TAMANO_ARTE_POR_DEFECTO) -> Optional[str]:
    """
    Devuelve ruta local (temporal) de la portada descargada o None.
    """
    country = (country or PAIS_POR_DEFECTO) or "us"
    paises = [country] + (["us"] if country.lower() != "us" else [])

    def intenta(url100: str) -> Optional[str]:
        for etiqueta, u in _aplicar_truco_o_tamano(url100, preferir_max=preferir_max, tam=tamano):
            tmp = os.path.abspath("apple_cover_tmp.jpg")
            try:
                urllib.request.urlretrieve(u, tmp)
                return tmp
            except Exception:
                continue
        return None

    # 1) Buscar por canción primero (modo '1')
    if modo == '1' and titulo:
        for cc in paises:
            term = f"{artista_princ} {titulo}".strip()
            songs = itunes_search(term, cc, entity="song", attribute="songTerm", limit=25)
            mejor = elegir_mejor_cancion_estricta(artista_princ, titulo, songs)
            if mejor and mejor.get("artworkUrl100"):
                tmp = intenta(mejor["artworkUrl100"])
                if tmp:
                    return tmp

    # 2) Buscar por álbum (o fallback)
    if not artista_princ or artista_princ == "Desconocido" or not album or album == "Desconocido":
        print("⚠️ No hay datos suficientes para buscar portada en Apple (artista/álbum desconocidos).")
        return None

    terminos: list[str] = []
    album_limpio = limpia_nombre_album(album or "")
    terminos.append(f"{artista_princ} {album}".strip())
    if normaliza(album_limpio) != normaliza(album or ""):
        terminos.append(f"{artista_princ} {album_limpio}".strip())
    terminos += [album, album_limpio]

    for cc in paises:
        for t in terminos:
            cand = itunes_search(t, cc, entity="album", limit=25)
            mejor = elegir_mejor_album_estricto(artista_princ, album, cand,
                                                pistas_objetivo=pistas_objetivo, anio_objetivo=anio_objetivo)
            if mejor and mejor.get("artworkUrl100"):
                tmp = intenta(mejor["artworkUrl100"])
                if tmp:
                    return tmp

    #print("⚠️ No se pudo obtener portada desde Apple (sin coincidencias o descarga fallida).")
    return None

def resolver_track_album_apple(artista: str, titulo: str, album_hint: Optional[str],
                               country: Optional[str] = None):
    """
    Resuelve (número_de_pista, total_pistas, nombre_album) buscando en Apple.
    """
    country = country or PAIS_POR_DEFECTO
    if not artista or not titulo:
        return (None, None, None)

    term = f"{artista} {titulo}".strip()
    songs = itunes_search(term, country, entity="song", attribute="songTerm", limit=25)
    mejor = elegir_mejor_cancion_estricta(artista, titulo, songs)

    num_pista = None
    total_pistas = None
    nombre_album = None
    collection_id = None

    if mejor:
        num_pista = mejor.get("trackNumber") or None
        total_pistas = mejor.get("trackCount") or None
        nombre_album = mejor.get("collectionName") or None
        collection_id = mejor.get("collectionId") or None

    if (num_pista is None) and collection_id:
        res = itunes_lookup(str(collection_id), country=country, entity="song", limit=200)
        objetivo = _norm_titulo_para_match(titulo)
        for item in res:
            if (item.get("wrapperType") == "track") and _norm_titulo_para_match(item.get("trackName", "")) == objetivo:
                num_pista = item.get("trackNumber") or None
                total_pistas = total_pistas or item.get("trackCount") or None
                nombre_album = nombre_album or item.get("collectionName") or None
                break

    album_final = nombre_album if (not album_hint or album_hint == "Desconocido") else album_hint
    return (num_pista, total_pistas, album_final)
