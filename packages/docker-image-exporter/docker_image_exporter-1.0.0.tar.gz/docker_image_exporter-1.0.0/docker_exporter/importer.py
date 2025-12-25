"""
Funciones específicas para importar imágenes Docker.
"""

import logging
from pathlib import Path
from typing import cast

import docker
from tqdm import tqdm

from .client import get_docker_client, load_image_from_tar, tag_image
from .types import ImportResult, ImportSummary, Manifest
from .utils import load_json

logger = logging.getLogger(__name__)


def load_manifest(import_dir: str) -> Manifest:
    """Carga y valida el manifest.json."""
    manifest_path = Path(import_dir) / "manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest no encontrado: {manifest_path}")

    return cast(Manifest, load_json(str(manifest_path)))


def import_single_image(
    client: docker.DockerClient,
    tar_path: str,
    original_tags: list[str],
    primary_tag: str,
) -> ImportResult:
    """Importa una imagen desde archivo tar."""
    try:
        # Cargar imagen
        response = load_image_from_tar(client, tar_path)
        image = response[0]

        if image.id is None:
            raise ValueError("Loaded image has no ID")

        # Aplicar todos los tags originales
        for tag in original_tags:
            if tag != "<none>:<none>":
                tag_image(client, image.id, tag)

        return {
            "success": True,
            "image_id": image.id,
            "tags": original_tags,
            "new_tags": image.tags,
            "tag": primary_tag,
        }

    except Exception as e:
        logger.error(f"Error importando {tar_path}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "tar_path": tar_path,
            "tag": primary_tag,
        }


def import_all_images(import_dir: str) -> ImportSummary:
    """
    Importa todas las imágenes desde directorio.

    Args:
        import_dir: Directorio con imágenes y manifest.json

    Returns:
        Dict con resultados de importación
    """
    client = get_docker_client()

    # Cargar manifest
    manifest = load_manifest(import_dir)
    images_dir = Path(import_dir) / "images"

    if not images_dir.exists():
        raise FileNotFoundError(f"Directorio de imágenes no encontrado: {images_dir}")

    results: list[ImportResult] = []
    successful = 0

    for img_info in tqdm(manifest["images"], desc="Importando imágenes"):
        tar_path = images_dir / img_info["export_filename"]

        if not tar_path.exists():
            logger.warning(f"Archivo no encontrado: {tar_path}")
            results.append(
                {
                    "success": False,
                    "tag": img_info.get("primary_tag", "unknown"),
                    "error": "Archivo no encontrado",
                    "tar_path": str(tar_path),
                }
            )
            continue

        # Importar imagen
        primary_tag = img_info.get("primary_tag", "unknown")
        result = import_single_image(
            client, str(tar_path), img_info["tags"], primary_tag
        )

        if result["success"] is True:
            successful += 1

        results.append(result)

    logger.info(
        f"Importación completada: {successful}/{len(manifest['images'])} exitosas"
    )

    return {
        "total": len(manifest["images"]),
        "successful": successful,
        "failed": len(manifest["images"]) - successful,
        "results": results,
    }
