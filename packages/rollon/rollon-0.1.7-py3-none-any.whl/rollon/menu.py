from __future__ import annotations
from .config import PAIS_POR_DEFECTO, APPLE_TRUCO_MAXIMO, TAMANO_ARTE_POR_DEFECTO
from .core import descargar_contenido

def main():
    while True:
        print("¿Qué vamos a descargar hoy?")
        print("1. Canción huérfana")
        print("2. Álbum completo")
        print("3. Discografía completa")
        print("4. Salir")
        opcion = input("Selecciona una opción (1, 2, 3 o 4): ").strip()

        if opcion == '4':
            print("Saliendo del programa.")
            break

        if opcion in ['1', '2', '3']:
            url = input("Introduce la URL: ").strip()
            if not url.startswith("http"):
                print("ERROR: La URL ingresada no es válida.")
                continue

            # Mantener comportamiento original: sin rango por defecto.
            rango = None
            descargar_contenido(
                url, opcion, rango_playlist=rango,
                usar_apple_art=True, art_size=TAMANO_ARTE_POR_DEFECTO,
                prefer_max=APPLE_TRUCO_MAXIMO, country=PAIS_POR_DEFECTO
            )
        else:
            print("Opción no válida. Intenta de nuevo.")
