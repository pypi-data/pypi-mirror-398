"""
Funciones específicas para exportar imágenes Docker.
"""

import logging
from datetime import datetime
from pathlib import Path

import docker
from docker.models.images import Image
from tqdm import tqdm

from .client import get_all_images, get_docker_client, save_image_to_tar
from .types import ExportResult, ExportSummary, ImageMetadataExtended
from .utils import (
    ensure_directory,
    generate_filename_from_tag,
    get_image_metadata,
    save_json,
)

logger = logging.getLogger(__name__)


def export_single_image(
    client: docker.DockerClient, image_tag: str, output_dir: Path
) -> ExportResult:
    """Exporta una sola imagen Docker."""
    try:
        filename = generate_filename_from_tag(image_tag)
        filepath = output_dir / filename

        logger.debug(f"Exportando {image_tag} a {filename}")
        save_image_to_tar(client, image_tag, str(filepath))

        return {
            "success": True,
            "tag": image_tag,
            "filename": filename,
            "path": str(filepath),
        }

    except Exception as e:
        logger.error(f"Error exportando {image_tag}: {str(e)}")
        return {"success": False, "tag": image_tag, "error": str(e)}


def collect_image_info(images: list[Image]) -> list[ImageMetadataExtended]:
    """Recopila información de todas las imágenes."""
    image_info: list[ImageMetadataExtended] = []
    for img in images:
        if img.tags:
            for tag in img.tags:
                if tag != "<none>:<none>":
                    metadata = get_image_metadata(img)
                    image_info.append(
                        {
                            **metadata,
                            "primary_tag": tag,
                            "export_filename": "",
                        }
                    )
                    break  # Solo necesitamos un tag por imagen
    return image_info


def create_manifest(image_info: list[ImageMetadataExtended], export_dir: str) -> str:
    """Crea archivo manifest.json con metadatos."""
    manifest = {
        "export_date": datetime.now().isoformat(),
        "total_images": len(image_info),
        "images": image_info,
    }

    manifest_path = Path(export_dir) / "manifest.json"
    save_json(manifest, str(manifest_path))

    return str(manifest_path)


def export_all_images(output_dir: str = "./docker_images") -> ExportSummary:
    """
    Exporta todas las imágenes Docker.

    Returns:
        Dict con resultados y estadísticas
    """
    client = get_docker_client()
    images = get_all_images(client)

    # Crear estructura de directorios
    export_dir = ensure_directory(output_dir)
    images_dir = ensure_directory(export_dir / "images")

    # Recopilar información
    image_info = collect_image_info(images)

    # Exportar cada imagen
    results = []
    successful = 0

    for info in tqdm(image_info, desc="Exportando imágenes"):
        result = export_single_image(client, info["primary_tag"], images_dir)

        if result["success"] is True:
            successful += 1
            # Añadir nombre de archivo al metadata
            info["export_filename"] = result["filename"]

        results.append(result)

    # Crear manifest
    manifest_path = create_manifest(image_info, str(export_dir))

    logger.info(f"Exportación completada: {successful}/{len(images)} imágenes")
    logger.info(f"Manifest creado en: {manifest_path}")

    return {
        "total": len(images),
        "successful": successful,
        "failed": len(images) - successful,
        "manifest_path": manifest_path,
        "export_dir": str(export_dir),
    }
