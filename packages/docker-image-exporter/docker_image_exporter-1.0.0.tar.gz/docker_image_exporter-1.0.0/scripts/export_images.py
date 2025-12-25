#!/usr/bin/env python3
"""
Script CLI para exportar imágenes Docker.
"""

import argparse
import logging
import sys
from pathlib import Path

# Añadir directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docker_exporter.export import export_all_images
from docker_exporter.utils import create_tar_gz


def setup_logging(verbose: bool = False):
    """Configura el logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    parser = argparse.ArgumentParser(
        description="Exporta todas las imágenes Docker a un directorio"
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="./docker_images",
        help="Directorio de salida para las imágenes",
    )
    parser.add_argument(
        "--create-archive",
        "-a",
        action="store_true",
        help="Crear archivo tar.gz comprimido",
    )
    parser.add_argument(
        "--archive-name",
        default="docker_images_backup.tar.gz",
        help="Nombre del archivo comprimido",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Mostrar información detallada"
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    print(f"🚢 Exportando imágenes Docker a: {args.output_dir}")

    # Exportar imágenes
    result = export_all_images(args.output_dir)

    # Crear archivo comprimido si se solicita
    if args.create_archive:
        print(f"📦 Creando archivo comprimido: {args.archive_name}")
        archive_path = create_tar_gz(args.output_dir, args.archive_name)
        print(f"✅ Archivo creado: {archive_path}")

    # Mostrar resumen
    print("\n📊 Resumen de exportación:")
    print(f"   Total de imágenes: {result['total']}")
    print(f"   Exportadas exitosamente: {result['successful']}")
    print(f"   Fallidas: {result.get('failed', 0)}")

    if result.get("failed", 0) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
