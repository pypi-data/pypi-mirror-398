# Roll-On 🎵

Roll-On es una herramienta CLI para descargar canciones, álbumes o discografías desde YouTube Music, ideal para servidores multimedia como Jellyfin o Plex.

## 🚀 Instalación con PIP

## 🔧 Requisitos del sistema

Antes de instalar Roll-On, asegúrate de tener estas herramientas instaladas:

> ffmpeg
> jp2a
> opus-tools
> opustags

Puedes instalarlos con el siguiente comando:
```bash
sudo apt update && sudo apt install -y ffmpeg jp2a opus-tools opustags
```

### 1. Instalacion
```bash
pip install rollon
```

Esto instalará Roll-On.

## 📂 Carpeta de descargas

Por defecto, **Roll-On** guarda la música descargada en la siguiente ruta:

```
<directorio actual>/Media/Music
```

> 💡 **Nota:**  
> Asegúrate de ejecutar Roll-On desde el directorio donde deseas que se cree la carpeta `Music`.  
> Esto te permitirá mantener tus archivos organizados y en la ubicación correcta.

## 👩‍💻 Uso
Ejecuta el comando:
```bash
rollon
```
Y sigue las instrucciones en pantalla para seleccionar qué deseas descargar:

1. Canción huérfana
2. Álbum completo
3. Discografía completa
4. Salir

## 📦 Integración con Jellyfin o Plex

Para que Roll-On funcione perfectamente con Jellyfin o Plex:
- Configura `<directorio pwd>/Media/Music` como una carpeta de música en tu servidor.
- Roll-On descargará automáticamente allí, manteniendo tu biblioteca actualizada.

## ⚙️ Requisitos
- Python 3.8+
- `yt-dlp`, `ffmpeg`, `jp2a`, `opus-tools` y `opustags`

## 📄 Licencia
Este proyecto está bajo la licencia MIT.
