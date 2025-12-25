"""
Cliente Docker reutilizable y funciones de bajo nivel.
"""

import docker
from docker.models.images import Image


def get_docker_client() -> docker.DockerClient:
    """Obtiene cliente Docker."""
    return docker.from_env()


def get_all_images(client: docker.DockerClient) -> list[Image]:
    """Obtiene todas las imágenes del sistema."""
    return [
        img
        for img in client.images.list(all=True)
        if img.tags and img.tags[0] != "<none>:<none>"
    ]


def save_image_to_tar(
    client: docker.DockerClient, image_ref: str, output_path: str
) -> str:
    """Guarda una imagen en archivo tar."""
    image = client.images.get(image_ref)
    with open(output_path, "wb") as f:
        for chunk in image.save(named=True):
            f.write(chunk)
    return output_path


def load_image_from_tar(client: docker.DockerClient, tar_path: str) -> list[Image]:
    """Carga una imagen desde archivo tar."""
    with open(tar_path, "rb") as f:
        return client.images.load(f.read())


def tag_image(client: docker.DockerClient, image_id: str, tag: str) -> bool:
    """Aplica un tag a una imagen."""
    image = client.images.get(image_id)
    if ":" in tag:
        repo, tag_name = tag.split(":", 1)
    else:
        repo, tag_name = tag, "latest"
    image.tag(repository=repo, tag=tag_name)
    return True
