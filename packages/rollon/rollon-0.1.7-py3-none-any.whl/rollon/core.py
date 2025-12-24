from __future__ import annotations
import glob
import os
import re
import shutil
import subprocess
import sys
from typing import Optional

from .config import PAIS_POR_DEFECTO, APPLE_TRUCO_MAXIMO, TAMANO_ARTE_POR_DEFECTO
from .utils import asegurar_directorio, artista_principal, limpia_nombre_album
from .downloader import obtener_metadata, obtener_conteo_playlist
from .itunes import (
    descargar_portada_apple_precisa,
    resolver_track_album_apple,
    itunes_search,
    elegir_mejor_album_estricto,
    elegir_mejor_cancion_estricta,
)
from .tags import embeber_portada, poner_tags_opus
from .ui import ejecutar_con_ui


# ---------------------------------------------------------------------
# Herramientas de portada (solo ffmpeg/ffprobe)
# ---------------------------------------------------------------------
def _recortar_portada_1x1(path: str, max_dim: int | None = None) -> bool:
    """
    Recorta la imagen a 1:1 centrado usando ffmpeg.
    - Si max_dim se define, escala a min(max_dim, lado_menor_original) con Lanczos.
    - Si max_dim es None, solo recorta (sin escalar).
    Sobrescribe el archivo original si todo sale bien.
    """
    if not path or not os.path.exists(path):
        print("⚠️ _recortar_portada_1x1: ruta inválida o inexistente:", path)
        return False

    if not shutil.which("ffmpeg"):
        print("❌ _recortar_portada_1x1: 'ffmpeg' no está en PATH. Instálalo (p. ej., 'sudo apt install ffmpeg').")
        return False
    if not shutil.which("ffprobe"):
        print("❌ _recortar_portada_1x1: 'ffprobe' no está en PATH. Instálalo (p. ej., 'sudo apt install ffmpeg').")
        return False

    # 1) Dimensiones originales
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "csv=s=x:p=0", path],
        capture_output=True, text=True
    )
    if probe.returncode != 0 or not probe.stdout.strip():
        lado_objetivo = None
    else:
        try:
            w_s, h_s = probe.stdout.strip().split("x")
            w, h = int(w_s), int(h_s)
            lado_menor = min(w, h)
            lado_objetivo = None
            if max_dim and max_dim > 0:
                lado_objetivo = min(max_dim, lado_menor)  # evita upscaling
        except Exception:
            lado_objetivo = max_dim if (max_dim and max_dim > 0) else None

    # 2) Filtro de recorte/escala
    crop = "crop=min(iw\\,ih):min(iw\\,ih)"
    vf = crop if not lado_objetivo else f"{crop},scale={lado_objetivo}:{lado_objetivo}:flags=lanczos"

    tmp_out = path + ".sq.jpg"
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", path,
        "-vf", vf,
        "-q:v", "2",
        tmp_out
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        if res.stderr:
            print("❌ ffmpeg falló recortando portada:", res.stderr.strip())
        return False

    if not os.path.exists(tmp_out):
        print("❌ ffmpeg no produjo archivo de salida:", tmp_out)
        return False

    os.replace(tmp_out, path)
    return True


def _descargar_portada_ytdlp(url: str, out_dir: str, modo: str) -> str | None:
    """
    Descarga UNA miniatura de YouTube (u origen) y la convierte a JPG.
    - modo='single' -> --no-playlist
    - modo='first'  -> --yes-playlist -I 1 (solo primer item)
    Devuelve ruta del JPG o None.
    """
    os.makedirs(out_dir, exist_ok=True)

    # Limpia restos previos
    for p in glob.glob(os.path.join(out_dir, "yt_cover.*")):
        try:
            os.remove(p)
        except Exception:
            pass

    cmd = [
        "yt-dlp", "--skip-download",
        "--write-thumbnail",
        "--convert-thumbnails", "jpg",
        "-P", out_dir,
        "--output-na-placeholder", "",
        "-o", "yt_cover.%(ext)s",
        url, "--cookies", cookies_path
    ]
    if modo == "single":
        cmd += ["--no-playlist"]
    elif modo == "first":
        cmd += ["--yes-playlist", "-I", "1"]

    try:
        subprocess.run(cmd, check=False, capture_output=True, text=True)
    except Exception:
        return None

    for cand in ("yt_cover.jpg", "yt_cover.jpeg"):
        p = os.path.join(out_dir, cand)
        if os.path.exists(p):
            return p

    jpgs = sorted(glob.glob(os.path.join(out_dir, "yt_cover.*")), key=os.path.getmtime)
    return jpgs[-1] if jpgs else None


def _extraer_frame_alta(url: str, out_dir: str, t="00:00:10",
                        min_h: int = 1080, playlist_modo: str | None = None) -> str | None:
    """
    Usa yt-dlp para obtener la mejor URL de video (>=min_h si es posible) y ffmpeg para extraer un frame.
    - t: timestamp (hh:mm:ss) del frame
    - playlist_modo: None | 'single' (no-playlist) | 'first' (primer ítem)
    Devuelve la ruta al JPG cuadrado recortado/reescalado (cover.jpg) o None si falla.
    """
    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(out_dir, "frame_raw.jpg")
    out = os.path.join(out_dir, "cover.jpg")

    # 1) Construir comando para obtener URL directa del mejor *video-only*
    base_cmd = ["yt-dlp", "-g", "-f", f"bestvideo[height>={min_h}]/bestvideo"]
    if playlist_modo == "single":
        base_cmd += ["--no-playlist"]
    elif playlist_modo == "first":
        base_cmd += ["--yes-playlist", "-I", "1"]
    base_cmd.append(url)

    # Intento con filtro por altura; cae a bestvideo
    try:
        vid_url = subprocess.check_output(base_cmd, text=True).strip()
    except subprocess.CalledProcessError:
        try:
            fallback_cmd = ["yt-dlp", "-g", "-f", "bestvideo"]
            if playlist_modo == "single":
                fallback_cmd += ["--no-playlist"]
            elif playlist_modo == "first":
                fallback_cmd += ["--yes-playlist", "-I", "1"]
            fallback_cmd.append(url)
            vid_url = subprocess.check_output(fallback_cmd, text=True).strip()
        except Exception:
            return None

    if not vid_url:
        return None

    # 2) Extraer un frame al tiempo t
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", t, "-i", vid_url, "-frames:v", "1",
        tmp
    ]
    if subprocess.run(cmd).returncode != 0 or not os.path.exists(tmp):
        return None

    # 3) Recortar a 1:1 y escalar como máximo (sin upscaling real por _recortar_portada_1x1)
    try:
        os.replace(tmp, out)
    except Exception:
        out = tmp

    _recortar_portada_1x1(out, max_dim=TAMANO_ARTE_POR_DEFECTO)  # 3000 por defecto
    return out if os.path.exists(out) else None


# ---------------------------------------------------------------------
# Deducción opcional de número de pista desde el título (modo 1)
# ---------------------------------------------------------------------
def _numero_desde_titulo(titulo: str) -> int | None:
    """
    Intenta deducir el número de pista a partir de un título como:
    '01 - ...', '1. ...', '07 ...' (máx 2 dígitos).
    Devuelve int o None si no hay patrón claro.
    """
    if not titulo:
        return None
    m = re.match(r"^\s*(\d{1,2})\s*[-.\)]?\s+", titulo.strip())
    if not m:
        return None
    try:
        n = int(m.group(1))
        return n if 1 <= n <= 99 else None
    except Exception:
        return None


# ---------------------------------------------------------------------
# Metadatos extra: género (Apple/YT) y bitrate (ffprobe)
# ---------------------------------------------------------------------
def _resolver_genero_apple(artista: str, album: str | None, titulo: str | None, country: str, modo: str) -> str | None:
    """
    Intenta obtener GENRE desde Apple:
      - modo '1': buscar canción (entity=song)
      - modo '2': buscar álbum  (entity=album)
    Devuelve primaryGenreName o None.
    """
    try:
        if modo == '1' and titulo:
            cand = itunes_search(f"{artista} {titulo}".strip(), country, entity="song", attribute="songTerm", limit=25)
            mejor = elegir_mejor_cancion_estricta(artista, titulo, cand)
            if mejor:
                return (mejor.get("primaryGenreName") or None)
        if (modo == '2') and album:
            cand = itunes_search(f"{artista} {album}".strip(), country, entity="album", limit=25)
            mejor = elegir_mejor_album_estricto(artista, album, cand)
            if mejor:
                return (mejor.get("primaryGenreName") or None)
    except Exception:
        pass
    return None


def _resolver_genero_ytdlp(url: str) -> str | None:
    """
    Fallback: intenta obtener categorías/genre desde el extractor de yt-dlp (YouTube: 'Music', etc.).
    Toma el primer elemento si viene una lista.
    """
    try:
        res = subprocess.run(
            ["yt-dlp", "--skip-download", "--print", "%(genre,categories)s", url],
            capture_output=True, text=True, check=False
        )
        raw = (res.stdout or "").strip()
        if not raw:
            return None
        # Si es lista: ['Music'] o [Music]
        m = re.search(r"\['([^']+)'\]", raw)
        if m:
            return m.group(1)
        # Si viene como texto plano
        return raw.split(",")[0].strip()
    except Exception:
        return None


def _bitrate_kbps(path: str) -> int | None:
    """
    Lee el bitrate del stream de audio con ffprobe y devuelve kbps (entero).
    """
    if not shutil.which("ffprobe") or not os.path.exists(path):
        return None
    try:
        res = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=bit_rate", "-of", "default=nw=1:nk=1", path],
            capture_output=True, text=True, check=False
        )
        bps = res.stdout.strip()
        if bps.isdigit():
            return max(1, round(int(bps) / 1000))
    except Exception:
        pass
    return None


def _poner_tags_completos(
    fpath: str,
    titulo: str | None,
    artista: str | None,
    album: str | None,
    year: str | None,
    tracknum: int | None,
    tracktotal: int | None,
    genre: str | None,
    bitrate_kbps: int | None,
    albumartist: str | None,
):
    """
    Aplica tags “completos” en un .opus (Vorbis comments) usando opustags.
    Nota: 'TITLE','ARTIST','ALBUM','DATE','YEAR','TRACKNUMBER','TRACKTOTAL','GENRE','ALBUMARTIST','COMMENT'
    """
    tags = {}
    if titulo:       tags["TITLE"] = titulo
    if artista:      tags["ARTIST"] = artista
    if album:        tags["ALBUM"] = album
    if albumartist:  tags["ALBUMARTIST"] = albumartist
    if year and year.isdigit():
        tags["DATE"] = year
        tags["YEAR"] = year
    if tracknum is not None:
        tags["TRACKNUMBER"] = str(tracknum)
    if tracktotal is not None and int(tracktotal) > 0:
        tags["TRACKTOTAL"] = str(int(tracktotal))
    if genre:
        tags["GENRE"] = genre
    if bitrate_kbps:
        tags["BITRATE"] = f"{bitrate_kbps} kbps"

    if tags:
        poner_tags_opus(fpath, tags)

# ---------------------------------------------------------------------
# Display cover
# ---------------------------------------------------------------------

def _mostrar_cover_con_jp2a(cover_path: str):
    """
    Muestra la imagen de portada como ASCII a color con jp2a, ajustada
    al tamaño de la terminal menos 2 filas para dejar visible:
      - la línea del mensaje "✅ Portada embebida en ..."
      - el prompt del shell al final.
    Se omite si no hay jp2a o no estamos en una TTY.
    """
    try:
        if not cover_path or not os.path.exists(cover_path):
            return
        if not sys.stdout.isatty():
            return
        if not shutil.which("jp2a"):
            print("ℹ️ Sugerencia: instala 'jp2a' para ver la portada en ASCII (sudo apt install jp2a).")
            return

        cols, rows = shutil.get_terminal_size((100, 30))
        # Reservar 2 líneas: 1 arriba (mensaje) y 1 abajo (prompt)
        height = max(4, rows - 2)
        width = max(20, cols)

        # Mostramos sin limpiar la pantalla (no usar --clear)
        cmd = [
            "jp2a",
            "--colors",          # usar colores ANSI
            "--term-fit",
            cover_path
        ]
        subprocess.run(cmd, check=False)
    except Exception as e:
        print(f"⚠️ No se pudo renderizar la portada con jp2a: {e}")

# ---------------------------------------------------------------------
# Flujo principal
# ---------------------------------------------------------------------
def descargar_contenido(
    url: str,
    modo: str,
    rango_playlist: Optional[str] = None,
    usar_apple_art: bool = True,
    art_size: int = TAMANO_ARTE_POR_DEFECTO,
    prefer_max: bool = APPLE_TRUCO_MAXIMO,
    country: str = PAIS_POR_DEFECTO,
    cookies_path: Optional[str] = "../cookies.txt",
):
    """
    Descarga y post-procesa contenido:
      '1' -> Canción huérfana
      '2' -> Álbum completo
      '3' -> Discografía completa (por subcarpetas)
    """
    artista, album, titulo, fecha, tracknum_hint = obtener_metadata(url)
    artista_p = artista_principal(artista)

    # Carpeta base por artista (bajo Music/)
    artista_dir = artista_p or "Desconocido"
    base_path = os.path.join("Music", artista_dir)
    asegurar_directorio(base_path)

    # Variables para modo == '1'
    res_tn = None
    res_total = None
    res_album = None

    # Rutas/plantillas por modo
    if modo == '2':
        album_dir = limpia_nombre_album(album) if album and album != "Desconocido" else "Unknown Album"
        out_base = os.path.join(base_path, album_dir)
        asegurar_directorio(out_base)
        salida = "%(track_number)02d - %(title).170B.%(ext)s"
    elif modo == '3':
        salida = "%(album,playlist_title,channel,Unknown Album)s/%(track_number)02d - %(title).170B.%(ext)s"
        out_base = base_path
    else:  # '1' - Canción huérfana
        res_tn, res_total, res_album = resolver_track_album_apple(artista_p, titulo, album, country=country)
        album_dir_source = res_album or album
        album_dir = limpia_nombre_album(album_dir_source) if album_dir_source and album_dir_source != "Desconocido" else "Unknown Album"
        out_base = os.path.join(base_path, album_dir)
        asegurar_directorio(out_base)
        salida = "%(title).170B.%(ext)s"

    fields_clean = "uploader,channel,artist,album_artist,playlist_uploader"
    cmd = [
        "yt-dlp", url,
        "--newline", "-N", "3",
        "--trim-filenames", "183",
        "--no-mtime",
        # SponsorBlock en modo "marcar" (no recortar)
        "--sponsorblock-mark", "sponsor,selfpromo,interaction",
        "-f", "ba/b", "-x", "--audio-format", "opus",
        "-S", "aext:opus,br,asr,filesize",
        "-P", out_base,
        "-o", salida,
        "--output-na-placeholder", "",
        "--embed-metadata",  # embebe metadatos básicos via ffmpeg/yt-dlp
        "--replace-in-metadata", fields_clean, r"(?i)\s*-\s*Topic$", "",
        "--replace-in-metadata", fields_clean, r"(?i)(?:\s*-\s*)?VEVO$", "",
        "--replace-in-metadata", fields_clean, r"\s{2,}", " ",
        "--replace-in-metadata", fields_clean, r"^\s+|\s+$", "",
        "--parse-metadata", "artist:%(artist)s",
        "--parse-metadata", "album:%(album)s",
        "--parse-metadata", "%(artist)s:%(album_artist)s",
        "--parse-metadata", "%(track_number,playlist_index)s:%(track_number)s",
        # Sugerencia: si quieres fijar bitrate de salida, agrega por ejemplo:
        # "--audio-quality", "192K",
    ]
    if modo == '1':
        cmd += ["--no-playlist"]
    elif modo in ('2', '3'):
        cmd += ["--yes-playlist"]
    else:
        print("Modo no reconocido. Saliendo.")
        return
    if rango_playlist and modo == '2':
        cmd += ["-I", rango_playlist]

    print(f"\nDescargando en: {out_base}")
    if modo == '1':
        album_label = (res_album or album or "Desconocido")
    elif modo == '2':
        album_label = (album or "Desconocido")
    else:
        album_label = ""

    _ = ejecutar_con_ui(cmd, artista_p, album_label, mostrar_contador=True)

    # ===========================================================
    #   Portada (Apple -> frame -> miniatura) + METADATA COMPLETA
    # ===========================================================
    if usar_apple_art:
        genero: str | None = None

        if modo == '1':
            # 1) Determinar número de pista si REALMENTE lo tenemos
            tracknum: int | None = None
            candidatos = []

            # a) Apple
            if res_tn and str(res_tn).isdigit() and int(res_tn) > 0:
                candidatos.append(int(res_tn))
            # b) Hint de yt-dlp (track_number/playlist_index)
            if tracknum_hint and int(tracknum_hint) > 0:
                candidatos.append(int(tracknum_hint))
            # c) Deducir del título visible (opcional)
            n_titulo = _numero_desde_titulo(titulo)
            if n_titulo:
                candidatos.append(n_titulo)

            if candidatos:
                tracknum = candidatos[0]

            # 2) Localiza el archivo .opus recién generado
            opus_files = sorted(glob.glob(os.path.join(out_base, "*.opus")), key=os.path.getmtime)
            target_path = None
            if opus_files:
                ultimo = opus_files[-1]
                target_path = ultimo  # por defecto NO renombramos

                # 3) Renombrar SOLO si tenemos tracknum y el nombre aún no lo trae
                if tracknum is not None:
                    base_titulo = os.path.splitext(os.path.basename(ultimo))[0].strip()
                    if not re.match(r"^\d{2}\s-\s", base_titulo):
                        nuevo_nombre = f"{tracknum:02d} - {base_titulo}.opus"
                        nuevo_path = os.path.join(out_base, nuevo_nombre)
                        if os.path.abspath(ultimo) != os.path.abspath(nuevo_path):
                            if os.path.exists(nuevo_path):
                                i = 1
                                raiz, ext = os.path.splitext(nuevo_path)
                                while os.path.exists(f"{raiz} ({i}){ext}"):
                                    i += 1
                                nuevo_path = f"{raiz} ({i}){ext}"
                            os.replace(ultimo, nuevo_path)
                            target_path = nuevo_path

            # 4) Portada Apple
            tmp = descargar_portada_apple_precisa(
                artista_p, res_album or album, titulo,
                country=country, modo='1',
                pistas_objetivo=(res_total or 1),
                anio_objetivo=int(fecha) if (fecha and fecha.isdigit()) else None,
                preferir_max=prefer_max, tamano=art_size
            )
            portada_path = None
            if tmp:
                portada_path = os.path.join(out_base, "cover.jpg")
                try:
                    if os.path.exists(portada_path):
                        os.remove(portada_path)
                    os.replace(tmp, portada_path)
                except Exception:
                    portada_path = tmp

            # 5) Frame HD/4K del video (si Apple falló)
            if not portada_path:
                frame = _extraer_frame_alta(url, out_base, t="00:00:10", min_h=1080, playlist_modo="single")
                if frame and os.path.exists(frame):
                    portada_path = frame

            # 6) Miniatura YT como último recurso
            if not portada_path:
                yt_thumb = _descargar_portada_ytdlp(url, out_base, modo="single")
                if yt_thumb and os.path.exists(yt_thumb):
                    portada_path = os.path.join(out_base, "cover.jpg")
                    try:
                        if os.path.exists(portada_path):
                            os.remove(portada_path)
                        os.replace(yt_thumb, portada_path)
                    except Exception:
                        portada_path = yt_thumb

            # 7) Recortar 1:1 antes de embeber
            if portada_path and os.path.exists(portada_path):
                _recortar_portada_1x1(portada_path, max_dim=art_size)

            # 8) Resolver género (Apple -> YT)
            genero = _resolver_genero_apple(artista_p, res_album or album, titulo, country, modo='1') or \
                     _resolver_genero_ytdlp(url)

            # 9) Embebido + tags
            if target_path:
                if portada_path and os.path.exists(portada_path):
                    n = embeber_portada(portada_path, [target_path])
                    if n > 0:
                        print(f"✅ Portada embebida en 1 pista: {os.path.basename(target_path)}")
                        _mostrar_cover_con_jp2a(portada_path)
                        print("Descarga finalizada; disfruta tu cancion.")
                else:
                    print("⚠️ No se obtuvo portada (Apple / frame / miniatura).")

                # Bitrate real del archivo final
                br = _bitrate_kbps(target_path)

                # Tags completos
                _poner_tags_completos(
                    fpath=target_path,
                    titulo=titulo,
                    artista=artista_p or artista or None,
                    album=res_album or album or None,
                    year=fecha if (fecha and fecha.isdigit()) else None,
                    tracknum=tracknum,
                    tracktotal=(int(res_total) if (res_total and str(res_total).isdigit()) else None),
                    genre=genero,
                    bitrate_kbps=br,
                    albumartist=artista_p or artista or None,
                )
                print("✅ Metadata completa aplicada (TITLE, ARTIST, ALBUM, DATE/YEAR, TRACKNUMBER, TRACKTOTAL, GENRE, BITRATE).")
            else:
                print("❌ No se encontró el archivo descargado para renombrar/incrustar portada.")

        elif modo == '2':
            pistas_obj = obtener_conteo_playlist(url)

            # Portada Apple
            tmp = descargar_portada_apple_precisa(
                artista_p, album, titulo,
                country=country, modo='2',
                pistas_objetivo=pistas_obj,
                anio_objetivo=int(fecha) if (fecha and fecha.isdigit()) else None,
                preferir_max=prefer_max, tamano=art_size
            )
            portada_path = None
            if tmp:
                portada_path = os.path.join(out_base, "cover.jpg")
                try:
                    if os.path.exists(portada_path):
                        os.remove(portada_path)
                    os.replace(tmp, portada_path)
                except Exception:
                    portada_path = tmp

            # Frame del PRIMER ítem
            if not portada_path:
                frame = _extraer_frame_alta(url, out_base, t="00:00:10", min_h=1080, playlist_modo="first")
                if frame and os.path.exists(frame):
                    portada_path = frame

            # Miniatura del PRIMER ítem
            if not portada_path:
                yt_thumb = _descargar_portada_ytdlp(url, out_base, modo="first")
                if yt_thumb and os.path.exists(yt_thumb):
                    portada_path = os.path.join(out_base, "cover.jpg")
                    try:
                        if os.path.exists(portada_path):
                            os.remove(portada_path)
                        os.replace(yt_thumb, portada_path)
                    except Exception:
                        portada_path = yt_thumb

            # Recortar 1:1 antes de embeber
            if portada_path and os.path.exists(portada_path):
                _recortar_portada_1x1(portada_path, max_dim=art_size)

            # Resolver género (Apple -> YT)
            genero = _resolver_genero_apple(artista_p, album, None, country, modo='2') or \
                     _resolver_genero_ytdlp(url)

            # Embebido de portada a todas las pistas
            opus_files = sorted(glob.glob(os.path.join(out_base, "*.opus")))
            if portada_path and os.path.exists(portada_path):
                count = embeber_portada(portada_path, opus_files)
                print(f"✅ Portada embebida en {count} pista(s) del álbum.")
                _mostrar_cover_con_jp2a(portada_path)
                print("Descarga finalizada; disfruta tu album.")
            else:
                print("⚠️ No se obtuvo ninguna portada (Apple / frame / miniatura).")

            # Asegurar TRACKNUMBER, nombre "NN - Título" y aplicar metadata extra (album-level)
            opus_files = sorted(glob.glob(os.path.join(out_base, "*.opus")))
            total = len(opus_files) if opus_files else None
            for i, fpath in enumerate(opus_files, start=1):
                # TRACKNUMBER secuencial
                poner_tags_opus(fpath, {"TRACKNUMBER": f"{i}"})

                # Renombrar si hace falta
                base = os.path.basename(fpath)
                if not re.match(r"^\d{2}\s-\s", base):
                    titulo_simple = os.path.splitext(base)[0]
                    nuevo = os.path.join(out_base, f"{i:02d} - {titulo_simple}.opus")
                    if os.path.abspath(fpath) != os.path.abspath(nuevo):
                        if os.path.exists(nuevo):
                            os.remove(nuevo)
                        os.replace(fpath, nuevo)
                        fpath = nuevo  # actualizar referencia

                # Bitrate real
                br = _bitrate_kbps(fpath)

                # Metadata “completa” (para TITLE usamos la que ya embebió yt-dlp;
                # aquí reforzamos album/artist/year/genre/tracktotal/albumartist/bitrate)
                _poner_tags_completos(
                    fpath=fpath,
                    titulo=None,  # dejar el TITLE original embebido por yt-dlp
                    artista=artista_p or artista or None,
                    album=album or None,
                    year=fecha if (fecha and fecha.isdigit()) else None,
                    tracknum=i,
                    tracktotal=total,
                    genre=genero,
                    bitrate_kbps=br,
                    albumartist=artista_p or artista or None,
                )

        elif modo == '3':
            # Procesa cada subcarpeta de álbum bajo el artista (no tenemos URL por álbum para extraer frame)
            artista_root = base_path
            if os.path.isdir(artista_root):
                subfolders = [d for d in glob.glob(os.path.join(artista_root, "*")) if os.path.isdir(d)]
                total_albums = 0
                total_files = 0
                for album_dir in subfolders:
                    album_name = os.path.basename(album_dir)
                    opus_files = sorted(glob.glob(os.path.join(album_dir, "*.opus")))
                    if not opus_files:
                        continue
                    pistas_objetivo = len(opus_files)

                    # Portada Apple por nombre de carpeta
                    tmp = descargar_portada_apple_precisa(
                        artista_p, album_name, "",
                        country=country, modo='3',
                        pistas_objetivo=pistas_objetivo, anio_objetivo=None,
                        preferir_max=prefer_max, tamano=art_size
                    )
                    portada_path = None
                    if tmp:
                        portada_path = os.path.join(album_dir, "cover.jpg")
                        try:
                            if os.path.exists(portada_path):
                                os.remove(portada_path)
                            os.replace(tmp, portada_path)
                        except Exception:
                            portada_path = tmp

                    # Recortar 1:1 antes de embeber
                    if portada_path and os.path.exists(portada_path):
                        _recortar_portada_1x1(portada_path, max_dim=art_size)

                    if portada_path and os.path.exists(portada_path):
                        count = embeber_portada(portada_path, opus_files)
                        print(f"✅ [{album_name}] Portada embebida en {count} pista(s).")
                        print("")
                    else:
                        print(f"⚠️ [{album_name}] No se obtuvo portada (Apple).")
                        print("")

                    # Resolver género álbum (Apple)
                    genero_album = _resolver_genero_apple(artista_p, album_name, None, country, modo='2')

                    # TRACKNUMBER + renombrado + metadata extra
                    for i, fpath in enumerate(opus_files, start=1):
                        poner_tags_opus(fpath, {"TRACKNUMBER": f"{i}"})
                        base = os.path.basename(fpath)
                        if not re.match(r"^\d{2}\s-\s", base):
                            titulo_simple = os.path.splitext(base)[0]
                            nuevo = os.path.join(album_dir, f"{i:02d} - {titulo_simple}.opus")
                            if os.path.abspath(fpath) != os.path.abspath(nuevo):
                                if os.path.exists(nuevo):
                                    os.remove(nuevo)
                                os.replace(fpath, nuevo)
                                fpath = nuevo

                        # Bitrate real
                        br = _bitrate_kbps(fpath)

                        _poner_tags_completos(
                            fpath=fpath,
                            titulo=None,  # conservar TITLE original
                            artista=artista_p or artista or None,
                            album=album_name or None,
                            year=None,  # año desconocido a nivel carpeta
                            tracknum=i,
                            tracktotal=len(opus_files),
                            genre=genero_album,
                            bitrate_kbps=br,
                            albumartist=artista_p or artista or None,
                        )
                    total_albums += 1
                    total_files += len(opus_files)
                    print(f"[{album_name}] listo: {len(opus_files)} pista(s) con portada y metadata.")
                print(f"Discografía: {total_albums} álbum(es) procesado(s), {total_files} pistas con portada.")
                print("")
