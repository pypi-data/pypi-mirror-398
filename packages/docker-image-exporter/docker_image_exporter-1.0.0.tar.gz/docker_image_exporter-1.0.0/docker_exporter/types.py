"""
Type definitions for the docker-image-exporter package.
"""

from typing import Literal, TypedDict

# Tipo recursivo para valores JSON
JsonValue = dict[str, "JsonValue"] | list["JsonValue"] | str | int | float | bool | None


class ImageMetadata(TypedDict):
    """Metadata for a Docker image."""

    id: str
    tags: list[str]
    short_id: str
    labels: dict[str, str]
    created: str


class ImageMetadataExtended(ImageMetadata):
    """Extended metadata with export-specific fields."""

    primary_tag: str
    export_filename: str


class ExportSuccessResult(TypedDict):
    """Successful export result."""

    success: Literal[True]
    tag: str
    filename: str
    path: str


class ExportErrorResult(TypedDict):
    """Failed export result."""

    success: Literal[False]
    tag: str
    error: str


ExportResult = ExportSuccessResult | ExportErrorResult


class ImportSuccessResult(TypedDict):
    """Successful import result."""

    success: Literal[True]
    image_id: str
    tags: list[str]
    new_tags: list[str]
    tag: str


class ImportErrorResult(TypedDict):
    """Failed import result."""

    success: Literal[False]
    error: str
    tar_path: str
    tag: str


ImportResult = ImportSuccessResult | ImportErrorResult


class Manifest(TypedDict):
    """Manifest file structure."""

    export_date: str
    total_images: int
    images: list[ImageMetadataExtended]


class ExportSummary(TypedDict):
    """Summary of export operation."""

    total: int
    successful: int
    failed: int
    manifest_path: str
    export_dir: str


class ImportSummary(TypedDict):
    """Summary of import operation."""

    total: int
    successful: int
    failed: int
    results: list[ImportResult]
