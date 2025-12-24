from pathlib import Path
from setuptools import setup, find_packages

setup(
    name="rollon",
    version="0.1.7",
    packages=find_packages(),
    install_requires=[
        "ffmpeg-python",
        "jp2a-wrapper",
        "opuslib"
    ],
    entry_points={
        "console_scripts": [
            "rollon=rollon.cli:main"
        ]
    },
    author="Cesarx9",
    description="Roll-On es una herramienta CLI para descargar canciones, álbumes o discografías desde YouTube Music, ideal para servidores multimedia como Jellyfin o Plex.",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/Cesarx9/Roll-On",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
