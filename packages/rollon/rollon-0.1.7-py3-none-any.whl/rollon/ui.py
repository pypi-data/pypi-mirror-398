from __future__ import annotations
import os
import re
import sys
import time
import shutil
import threading
import subprocess
from typing import Optional

from .config import UI_BARRAS_UNICODE, ANCHO_BARRA

# -----------------------------------------------------------------------------
# Colores y helpers de UI
# -----------------------------------------------------------------------------
COLOR_HABILITADO = sys.stdout.isatty() and (os.environ.get("NO_COLOR") is None)

class C:
    RESET = "\033[0m"; TENUE = "\033[2m"; NEGR = "\033[1m"
    CIAN = "\033[36m"; AMAR = "\033[33m"; VERD = "\033[32m"
    AZUL = "\033[34m"; MAG  = "\033[35m"; GRIS = "\033[90m"; BLAN = "\033[97m"

def c(s: str, color: str) -> str:
    if COLOR_HABILITADO:
        return f"{color}{s}{C.RESET}"
    return s

def _barra(pct: float, ancho: int = ANCHO_BARRA) -> str:
    pct = max(0.0, min(100.0, pct))
    llenos = int(round((pct / 100.0) * ancho))
    if UI_BARRAS_UNICODE:
        return c('█' * llenos, C.VERD) + c('░' * (ancho - llenos), C.GRIS)
    return c('#' * llenos, C.VERD) + c('.' * (ancho - llenos), C.GRIS)

def _regla():
    cols = shutil.get_terminal_size((100, 20)).columns
    print(c("─" * min(cols, 80), C.GRIS))

def _encabezado_pista(titulo: str, album: str, artista: str, idx: int | None = None, total: int | None = None):
    _regla()
    tline = f"Tema: {titulo}"
    if idx and total and total >= idx:
        tline += f" {c(f'({idx}/{total})', C.MAG)}"
    print(c(tline, C.NEGR))
    print(f"Álbum: {c(album or 'Desconocido', C.CIAN)}")
    print(f"Artista: {c(artista or 'Desconocido', C.CIAN)}")

# -----------------------------------------------------------------------------
# Spinner (rueda de carga) para tiempos de espera previos al progreso real
# -----------------------------------------------------------------------------
class Spinner:
    """
    Muestra una rueda de carga en una sola línea mientras no hay progreso real.
    - start(): comienza a animar
    - pause(): pausa y fija la línea con salto
    - resume(): reanuda la animación
    - stop(): detiene y limpia con salto de línea
    - bump(): notifica actividad (p. ej. al leer caracteres)
    - update_prefix(txt): cambia el prefijo (ej. 'Preparando…')
    """
    def __init__(self, prefix: str = "", interval: float = 0.10):
        self.frames = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']
        self.prefix = prefix
        self.interval = interval
        self._running = False
        self._paused = False
        self._th = None
        self._lock = threading.Lock()
        self._last_activity = time.time()

    def update_prefix(self, prefix: str):
        with self._lock:
            self.prefix = prefix

    def bump(self):
        """Llama cada vez que llega algún output para marcar actividad reciente."""
        with self._lock:
            self._last_activity = time.time()

    def start(self):
        if self._running:
            return
        self._running = True
        self._paused = False
        self._th = threading.Thread(target=self._run, daemon=True)
        self._th.start()

    def pause(self):
        with self._lock:
            if not self._running:
                return
            self._paused = True
        # fija la línea para no estorbar la siguiente impresión
        sys.stdout.write("\n"); sys.stdout.flush()

    def resume(self):
        with self._lock:
            if self._running:
                self._paused = False

    def stop(self):
        if not self._running:
            return
        with self._lock:
            self._running = False
        if self._th and self._th.is_alive():
            self._th.join(timeout=0.5)
        # limpia con salto final por si quedaba en la misma línea
        sys.stdout.write("\n"); sys.stdout.flush()

    def _run(self):
        i = 0
        while True:
            with self._lock:
                if not self._running:
                    break
                paused = self._paused
                prefix = self.prefix
                last = self._last_activity
            if paused:
                time.sleep(self.interval)
                continue
            cols = shutil.get_terminal_size((100, 20)).columns
            frame = self.frames[i % len(self.frames)]
            elapsed = int(time.time() - last)
            mins, secs = divmod(elapsed, 60)
            elapsed_s = f"{mins:02d}:{secs:02d}"
            line = f"{prefix} {frame} {elapsed_s}"
            sys.stdout.write("\r" + line[:max(1, cols - 1)])
            sys.stdout.flush()
            i += 1
            time.sleep(self.interval)

# -----------------------------------------------------------------------------
# Ejecución de yt-dlp con UI limpia (progreso/etapas) + spinner
# -----------------------------------------------------------------------------
def ejecutar_con_ui(cmd: list[str], artista: str, album_hint: str = "", mostrar_contador: bool = True) -> int:
    """
    Ejecuta yt-dlp y muestra:
      - Encabezado de tema/álbum/artista (+ (X/Y) si es playlist/álbum).
      - Barra de progreso con %/velocidad/ETA.
      - Mensajes compactos para ExtractAudio/Metadata.
      - Spinner de “Preparando…” antes de que haya progreso real.
    """
    term_cols = shutil.get_terminal_size((100, 20)).columns
    ancho_barra = min(ANCHO_BARRA, max(10, term_cols - 46))

    # Estado
    titulo_actual: str | None = None
    encabezados_impresos: set[tuple[str, Optional[int], Optional[int]]] = set()
    etapa_actual = ""
    item_idx: int | None = None
    item_total: int | None = None
    barra_activa = False

    def fijar_barra():
        nonlocal barra_activa
        if barra_activa:
            sys.stdout.write("\n")
            sys.stdout.flush()
            barra_activa = False

    # Spinner de preparación
    spinner = Spinner(prefix=c("⏳ Preparando…", C.AMAR))
    spinner.start()

    # Simulación de progreso para METADATA en hilo aparte
    lock_stdout = threading.Lock()
    meta_thread = None
    meta_done = threading.Event()
    meta_en_ejec = False
    meta_pct = 0.0
    META_TICK = 0.10
    META_CAP = 95.0
    meta_prefijo = ''

    def dibujar_meta(pct: float):
        nonlocal meta_prefijo
        pct = max(0.0, min(100.0, pct))
        b = _barra(pct, ancho_barra)
        pct_s = f"{pct:6.2f}%"
        linea = f"{meta_prefijo} [{b}] {c(pct_s, C.BLAN)}"
        with lock_stdout:
            sys.stdout.write("\r" + linea[:term_cols - 1])
            sys.stdout.flush()

    def iniciar_meta():
        nonlocal meta_thread, meta_en_ejec, meta_pct
        if meta_en_ejec:
            return
        meta_done.clear()
        meta_en_ejec = True
        meta_pct = 0.0

        def _worker():
            nonlocal meta_en_ejec, meta_pct
            if meta_pct < 3.0:
                meta_pct = 3.0
                dibujar_meta(meta_pct)
            while not meta_done.is_set():
                paso = 0.70 if meta_pct < 80 else 0.25
                meta_pct = min(META_CAP, meta_pct + paso)
                dibujar_meta(meta_pct)
                time.sleep(META_TICK)
            # Finalizar a 100%
            dibujar_meta(100.0)
            with lock_stdout:
                sys.stdout.write("\n")
                sys.stdout.flush()
            meta_en_ejec = False

        meta_thread = threading.Thread(target=_worker, daemon=True)
        meta_thread.start()

    def detener_meta():
        nonlocal meta_thread, meta_en_ejec
        if not meta_en_ejec:
            return
        meta_done.set()
        if meta_thread and meta_thread.is_alive():
            meta_thread.join(timeout=0.8)

    def dibuja_progreso(pct, total_str, vel_str, eta_str):
        nonlocal barra_activa
        b = _barra(pct, ancho_barra)
        pct_s = f"{pct:6.2f}%"
        vel = (vel_str or "").strip()
        eta = (eta_str or "").strip()
        total = (total_str or "").strip()
        partes = [f"[{b}] {c(pct_s, C.BLAN)}"]
        if vel:
            partes.append(c(f"{vel:>10}", C.CIAN))
        if eta:
            partes.append(c(f"ETA {eta:>7}", C.AMAR))
        if total:
            partes.append(c(f"Total {total:>9}", C.TENUE))
        linea = " ".join(partes)
        sys.stdout.write("\r" + linea[:term_cols - 1])
        sys.stdout.flush()
        barra_activa = True

    # Lanza yt-dlp
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, universal_newlines=True
    )
    buf = ""

    def procesa_linea(linea: str):
        nonlocal titulo_actual, etapa_actual, item_idx, item_total, barra_activa, meta_prefijo
        s = (linea or "").strip()

        # Opcional: mostrar mensajes [info] como prefijo del spinner
        m_info = re.match(r'^\[(?:info|debug)\]\s+(.*)$', s, re.I)
        if m_info:
            spinner.update_prefix(c(f"⏳ {m_info.group(1)}", C.AMAR))
            return

        # Contador "Downloading item X of Y"
        if mostrar_contador:
            m_item = re.search(r"Downloading item\s+(\d+)\s+of\s+(\d+)", s, re.I)
            if m_item:
                try:
                    item_idx = int(m_item.group(1))
                    item_total = int(m_item.group(2))
                except Exception:
                    item_idx = item_total = None
                return

        # Nueva pista por "Destination: ..."
        m_dest = re.search(r'(?:^\[.*?\]\s*)?Destination:\s+(.+)$', s)
        if m_dest:
            path = m_dest.group(1).strip()
            base = os.path.basename(path)
            titulo = re.sub(r'\.(webm|m4a|mp4|m4v|opus|mp3|flac)$', '', base, flags=re.I)
            clave = (titulo, item_idx, item_total)
            album_a_mostrar = album_hint
            padre = os.path.basename(os.path.dirname(path))
            if not album_a_mostrar and padre:
                album_a_mostrar = padre

            if s.startswith('[ExtractAudio]'):
                if clave not in encabezados_impresos:
                    encabezados_impresos.add(clave)
                    detener_meta()
                    fijar_barra()
                    spinner.stop()  # dejar de mostrar el spinner
                    titulo_actual = titulo
                    etapa_actual = "extract"
                    _encabezado_pista(titulo_actual, album_a_mostrar, artista, item_idx, item_total)
                else:
                    etapa_actual = "extract"
                return

            if clave in encabezados_impresos:
                return
            encabezados_impresos.add(clave)
            detener_meta()
            fijar_barra()
            spinner.stop()  # dejar de mostrar el spinner
            titulo_actual = titulo
            etapa_actual = "download"
            _encabezado_pista(titulo_actual, album_a_mostrar, artista, item_idx, item_total)
            return

        # Progreso de descarga
        m_prog = re.search(
            r'\[download\]\s+(\d+(?:\.\d+)?)%.*?of\s+([0-9.\s\w]+)'
            r'(?:.*?at\s+([0-9.\s\w]+/s))?(?:.*?ETA\s+([0-9:]+))?',
            s, re.I
        )
        if m_prog:
            try:
                pct = float(m_prog.group(1))
            except Exception:
                pct = 0.0
            total = m_prog.group(2)
            vel = m_prog.group(3)
            eta = m_prog.group(4)
            spinner.stop()  # detener spinner al mostrar barra real
            dibuja_progreso(pct, total, vel, eta)
            return

        # Etapas compactas
        if s.startswith('[ExtractAudio]'):
            spinner.stop()
            if etapa_actual != "extract":
                detener_meta()
                fijar_barra()
                print(c("🎧 Extrayendo audio…", C.AZUL))
                etapa_actual = "extract"
            return

        if s.startswith('[Metadata]'):
            spinner.stop()
            if etapa_actual != "metadata":
                fijar_barra()
                meta_prefijo = c("🏷️ Escribiendo metadatos…", C.MAG)
                iniciar_meta()
                etapa_actual = "metadata"
            return

        # Fin (100% de descarga)
        if ('[download]' in s) and ('100%' in s):
            spinner.stop()
            dibuja_progreso(100.0, None, None, None)
            sys.stdout.write("\n")
            sys.stdout.flush()
            barra_activa = False
            etapa_actual = ""
            return

    try:
        while True:
            ch = p.stdout.read(1)
            if not ch:
                if buf:
                    procesa_linea(buf)
                buf = ""
                break
            spinner.bump()  # notificar actividad al spinner
            if ch in ("\n", "\r"):
                if buf:
                    procesa_linea(buf)
                buf = ""
            else:
                buf += ch
        p.wait()
    finally:
        # Cierre ordenado
        try:
            if p.stdout:
                p.stdout.close()
        except Exception:
            pass
        try:
            detener_meta()
        except Exception:
            pass
        try:
            spinner.stop()
        except Exception:
            pass
        print()
    return p.returncode