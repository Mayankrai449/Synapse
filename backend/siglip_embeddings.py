"""
SigLIP Embeddings Wrapper for Manual Embedding Handling
Uses google/siglip-so400m-patch14-384 for both text and image embeddings
"""

import torch
from transformers import AutoModel, AutoProcessor
from PIL import Image
from typing import List, Union
import numpy as np


class SigLIPEmbeddings:
    """
    Wrapper for Google SigLIP model to generate embeddings for text and images.
    Compatible with manual embedding handling (returns list of floats).
    """

    def __init__(self, model_name: str = "google/siglip-so400m-patch14-384"):
        """
        Initialize SigLIP model and processor.

        Args:
            model_name: HuggingFace model identifier
        """
        print(f"Loading SigLIP model: {model_name}...")

        # Determine device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        # Load model and processor
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.processor = AutoProcessor.from_pretrained(model_name)

        # Set model to evaluation mode
        self.model.eval()

        print(f"SigLIP model loaded successfully!")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.

        Args:
            text: Input text string

        Returns:
            List of floats representing the embedding
        """
        # Process text
        inputs = self.processor(
            text=[text],
            return_tensors="pt",
            padding=True,
            truncation=True
        )

        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate embedding
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)

            # Normalize embeddings (important for similarity search)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        # Convert to list and return
        embedding = text_features.cpu().numpy()[0].tolist()
        return embedding

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple text strings (batch processing).

        Args:
            texts: List of text strings

        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        # Process texts in batch
        inputs = self.processor(
            text=texts,
            return_tensors="pt",
            padding=True,
            truncation=True
        )

        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate embeddings
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)

            # Normalize embeddings
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        # Convert to list and return
        embeddings = text_features.cpu().numpy().tolist()
        return embeddings

    def embed_image(self, image_path: str) -> List[float]:
        """
        Generate embedding for a single image.

        Args:
            image_path: Path to image file

        Returns:
            List of floats representing the embedding
        """
        # Load image
        image = Image.open(image_path).convert("RGB")

        # Process image
        inputs = self.processor(
            images=image,
            return_tensors="pt"
        )

        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate embedding
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)

            # Normalize embeddings
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

        # Convert to list and return
        embedding = image_features.cpu().numpy()[0].tolist()
        return embedding

    def embed_images(self, image_paths: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple images (batch processing).

        Args:
            image_paths: List of paths to image files

        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        # Load images
        images = [Image.open(path).convert("RGB") for path in image_paths]

        # Process images in batch
        inputs = self.processor(
            images=images,
            return_tensors="pt"
        )

        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate embeddings
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)

            # Normalize embeddings
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

        # Convert to list and return
        embeddings = image_features.cpu().numpy().tolist()
        return embeddings

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embeddings.

        Returns:
            Embedding dimension size
        """
        # For SigLIP models, the embedding dimension is in text_config
        # For siglip-so400m-patch14-384, dimension is typically 1152
        if hasattr(self.model.config, 'text_config'):
            return self.model.config.text_config.hidden_size
        elif hasattr(self.model.config, 'hidden_size'):
            return self.model.config.hidden_size
        else:
            # Fallback: generate a dummy embedding to get the dimension
            dummy_embedding = self.embed_text("test")
            return len(dummy_embedding)


# Singleton instance for global use
_siglip_instance = None

def get_siglip_embeddings() -> SigLIPEmbeddings:
    """
    Get or create singleton instance of SigLIP embeddings.
    This prevents loading the model multiple times.

    Returns:
        SigLIPEmbeddings instance
    """
    global _siglip_instance

    if _siglip_instance is None:
        _siglip_instance = SigLIPEmbeddings()

    return _siglip_instance


if __name__ == "__main__":
    # Test the embeddings
    print("Testing SigLIP embeddings...")

    siglip = SigLIPEmbeddings()

    # Test text embedding
    text = "A cat sitting on a mat"
    embedding = siglip.embed_text(text)
    print(f"\nText: {text}")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"Embedding preview: {embedding[:5]}...")

    # Test batch text embeddings
    texts = ["A dog running in the park", "A bird flying in the sky"]
    embeddings = siglip.embed_texts(texts)
    print(f"\nBatch embeddings shape: {len(embeddings)} x {len(embeddings[0])}")
