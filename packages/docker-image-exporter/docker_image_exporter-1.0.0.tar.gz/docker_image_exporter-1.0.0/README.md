# Docker Image Exporter/Importer

Herramienta modular para exportar e importar imágenes Docker entre máquinas sin
internet.

## Características

- 🚢 Exporta todas las imágenes Docker manteniendo tags
- 📦 Crea archivos comprimidos para transferencia fácil
- 🔄 Importa imágenes conservando nombres y tags originales
- 📊 Logging detallado y barras de progreso
- 🧩 Diseño modular con funciones puras

## Instalación

```bash
# Clonar e instalar
git clone <repo>
cd docker-image-exporter

# Instalar con uv
uv pip install -e .

# Para desarrollo (opcional)
just setup  # Instala dependencias de desarrollo
```

## Uso

### Scripts de Línea de Comandos

```bash
# Exportar todas las imágenes
export-docker-images --output-dir ./mis_imagenes

# Exportar y crear archivo comprimido
export-docker-images --output-dir ./mis_imagenes --create-archive

# Importar imágenes
import-docker-images --input-dir ./mis_imagenes

# Importar desde archivo comprimido
import-docker-images --archive docker_images_backup.tar.gz
```

### Como Biblioteca

```python
from docker_exporter import export_all_images, import_all_images

# Exportar imágenes
result = export_all_images("./output_dir")
print(f"Exportadas {result['successful']}/{result['total']} imágenes")

# Importar imágenes
result = import_all_images("./input_dir")
print(f"Importadas {result['successful']}/{result['total']} imágenes")
```

## Desarrollo

### Comandos de Desarrollo (usando Justfile)

```bash
# Instalar dependencias de desarrollo
just setup

# Ejecutar pruebas
just test           # Todas las pruebas
just test-cov        # Con cobertura (100% ✅)
just test-utils      # Pruebas de módulo específico

# Calidad de código
just lint            # Verificar estilo
just format          # Formatear código
just type            # Verificar tipos (solo código principal)
just check           # Lint + Type checking

# Workflow de desarrollo
just dev            # test + lint-fix + format
just ci              # Pipeline completo (test + lint + type + build)
```

### Construcción y Publicación

```bash
# Construir paquete
just build          # Wheel + sdist
just build-wheel     # Solo wheel
just build-sdist     # Solo sdist

# Validar lanzamiento
just release-check   # Pruebas + lint + type + build + validación de paquete

# Publicar
just publish-test    # A Test PyPI
just publish-prod    # A PyPI de producción
just release         # Lanzamiento completo
```

### Herramientas Utilizadas

- **Just**: Automatización de tareas de desarrollo
- **Ruff**: Formateo y linting (archivos de código + tests)
- **MyPy**: Verificación de tipos (solo código principal)
- **Pytest**: Suite de pruebas con 100% de cobertura
- **Twine**: Validación de paquetes antes de publicación
