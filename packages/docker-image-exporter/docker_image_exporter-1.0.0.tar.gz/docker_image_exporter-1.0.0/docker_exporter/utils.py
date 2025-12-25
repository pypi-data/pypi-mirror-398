"""
Funciones puras para manejo de archivos y datos.
"""

import json
import os
import tarfile
from pathlib import Path
from typing import cast

from docker.models.images import Image

from .types import ImageMetadata, JsonValue


def ensure_directory(path: str | Path) -> Path:
    """Crea directorio si no existe."""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def save_json(data: dict, path: str) -> None:
    """Guarda datos en archivo JSON."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(path: str) -> dict[str, JsonValue]:
    """Carga datos desde archivo JSON."""
    with open(path) as f:
        return cast(dict[str, JsonValue], json.load(f))


def create_tar_gz(source_dir: str, output_filename: str) -> str:
    """Crea archivo tar.gz comprimido."""
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
    return output_filename


def extract_tar_gz(archive_path: str, extract_dir: str) -> str:
    """Extrae archivo tar.gz."""
    ensure_directory(extract_dir)
    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=extract_dir)
    return extract_dir


def generate_filename_from_tag(tag: str) -> str:
    """Genera nombre de archivo seguro desde tag Docker."""
    safe_name = tag.replace("/", "_").replace(":", "_")
    return f"{safe_name}.tar"


def get_image_metadata(image_obj: Image) -> ImageMetadata:
    """Extrae metadatos de imagen Docker."""
    if image_obj.id is None:
        raise ValueError("Image has no ID")
    return {
        "id": image_obj.id,
        "tags": image_obj.tags,
        "short_id": image_obj.short_id,
        "labels": cast(dict[str, str], image_obj.labels),
        "created": cast(str, image_obj.attrs["Created"]),
    }
