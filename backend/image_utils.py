"""
Image storage and management utilities
"""

import os
import uuid
import httpx
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image
import io


# Image storage configuration
IMAGE_STORAGE_DIR = "./chroma_db/images"


def ensure_image_directory():
    """Create base image storage directory if it doesn't exist"""
    Path(IMAGE_STORAGE_DIR).mkdir(parents=True, exist_ok=True)


def get_document_image_dir(document_id: str) -> str:
    """
    Get or create directory for a document's images

    Args:
        document_id: Unique document identifier

    Returns:
        Path to document's image directory
    """
    doc_dir = Path(IMAGE_STORAGE_DIR) / document_id
    doc_dir.mkdir(parents=True, exist_ok=True)
    return str(doc_dir)


async def download_image_from_url(url: str, save_path: str, timeout: int = 30) -> bool:
    """
    Download image from URL and save to filesystem

    Args:
        url: Image URL
        save_path: Path to save the image
        timeout: Request timeout in seconds

    Returns:
        True if successful, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            response.raise_for_status()

            # Validate it's an image
            image = Image.open(io.BytesIO(response.content))

            # Save image
            image.save(save_path)
            return True

    except Exception as e:
        print(f"Failed to download image from {url}: {e}")
        return False


def save_uploaded_image(file_content: bytes, save_path: str) -> bool:
    """
    Save uploaded image file to filesystem

    Args:
        file_content: Image file bytes
        save_path: Path to save the image

    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate it's an image
        image = Image.open(io.BytesIO(file_content))

        # Save image
        image.save(save_path)
        return True

    except Exception as e:
        print(f"Failed to save uploaded image: {e}")
        return False


def get_image_dimensions(file_path: str) -> Optional[Dict[str, int]]:
    """
    Get image dimensions

    Args:
        file_path: Path to image file

    Returns:
        Dict with width and height, or None if failed
    """
    try:
        image = Image.open(file_path)
        return {"width": image.width, "height": image.height}
    except Exception as e:
        print(f"Failed to get image dimensions: {e}")
        return None


def delete_document_images(document_id: str) -> bool:
    """
    Delete all images for a document

    Args:
        document_id: Document identifier

    Returns:
        True if successful
    """
    try:
        doc_dir = Path(IMAGE_STORAGE_DIR) / document_id
        if doc_dir.exists():
            import shutil
            shutil.rmtree(doc_dir)
        return True
    except Exception as e:
        print(f"Failed to delete images for document {document_id}: {e}")
        return False


def cleanup_orphaned_images():
    """
    Cleanup image directories that don't have corresponding ChromaDB entries
    This should be called periodically or on startup
    """
    # TODO: Implement cleanup logic by checking against ChromaDB
    pass


# Initialize image directory on module import
ensure_image_directory()
