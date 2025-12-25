#!/usr/bin/env python3
"""
Script CLI para importar imágenes Docker.
"""

import argparse
import logging
import sys
from pathlib import Path

# Añadir directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docker_exporter.importer import import_all_images
from docker_exporter.utils import extract_tar_gz


def setup_logging(verbose: bool = False):
    """Configura el logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    parser = argparse.ArgumentParser(
        description="Importa imágenes Docker desde un directorio"
    )
    parser.add_argument(
        "--input-dir",
        "-i",
        default="./docker_images",
        help="Directorio con las imágenes exportadas",
    )
    parser.add_argument("--archive", help="Archivo tar.gz a extraer e importar")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Mostrar información detallada"
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    # Extraer archivo comprimido si se proporciona
    if args.archive:
        print(f"📦 Extrayendo archivo: {args.archive}")

        # Crear directorio de extracción
        extract_dir = Path(args.archive).stem
        if extract_dir.endswith(".tar"):
            extract_dir = extract_dir[:-4]

        args.input_dir = extract_tar_gz(args.archive, extract_dir)
        print(f"✅ Extraído en: {args.input_dir}")

    print(f"🚢 Importando imágenes desde: {args.input_dir}")

    try:
        # Importar imágenes
        result = import_all_images(args.input_dir)

        # Mostrar resumen
        print("\n📊 Resumen de importación:")
        print(f"   Total de imágenes: {result['total']}")
        print(f"   Importadas exitosamente: {result['successful']}")
        print(f"   Fallidas: {result['failed']}")

        # Mostrar errores si los hay
        if result["failed"] > 0:
            print("\n❌ Errores encontrados:")
            for res in result["results"]:
                if not res["success"]:
                    print(
                        f"   - {res.get('tag', 'unknown')}: {res.get('error', 'Error desconocido')}"
                    )
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
