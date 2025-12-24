from __future__ import annotations
import os

# -----------------------------------------------------------------------------
# Configuración (con soporte de variables de entorno en espanol e ingles)
# -----------------------------------------------------------------------------
# Preferimos nombres en español, pero aceptamos env vars en ambos idiomas para comodidad.

def _env_bool(*names: str, default: bool = False) -> bool:
    for n in names:
        v = os.getenv(n)
        if v is not None:
            return v not in ("0", "false", "False", "no", "No")
    return default

def _env_int(*names: str, default: int = 0) -> int:
    for n in names:
        v = os.getenv(n)
        if v:
            try:
                return int(v)
            except ValueError:
                pass
    return default

def _env_str(*names: str, default: str = "") -> str:
    for n in names:
        v = os.getenv(n)
        if v is not None:
            return v
    return default

# País por defecto para búsquedas de Apple (iTunes API).
PAIS_POR_DEFECTO = _env_str("ROLLON_PAIS", "ROLLON_COUNTRY", default="us")

# Si True, intenta primero el "truco" de 100000x100000-999 en la URL de Apple.
APPLE_TRUCO_MAXIMO = _env_bool("ROLLON_APPLE_TRUCO_MAXIMO", "ROLLON_APPLE_MAX_TRICK", default=True)

# Tamaño de arte de fallback si no se usa el truco máximo.
TAMANO_ARTE_POR_DEFECTO = _env_int("ROLLON_TAMANO_ARTE", "ROLLON_DEFAULT_ART_SIZE", default=3000)

# Depuración de elección de portada en consola.
DEPURAR_ARTE = _env_bool("ROLLON_DEPURAR_ARTE", "ROLLON_DEBUG_ART", default=False)

# UI
UI_BARRAS_UNICODE = _env_bool("ROLLON_UI_BARRAS_UNICODE", "ROLLON_UNICODE_BARS", default=True)
ANCHO_BARRA = _env_int("ROLLON_ANCHO_BARRA", "ROLLON_BAR_WIDTH", default=38)
