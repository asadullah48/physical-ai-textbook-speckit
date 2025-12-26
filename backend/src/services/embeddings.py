"""Embedding generation service using Google Gemini text-embedding-004."""
from typing import List
from google import genai
from google.genai import types
from src.api.config import get_settings

class EmbeddingsService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model = "text-embedding-004"
        self.embedding_dimension = 768
    
    def embed(self, text: str) -> List[float]:
        """Embed a single text string."""
        result = self.client.models.embed_content(
            model=self.model,
            contents=text,  # Changed from 'content' to 'contents'
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT"
            )
        )
        return result.embeddings[0].values
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings."""
        embeddings = []
        for text in texts:
            result = self.client.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT"
                )
            )
            embeddings.append(result.embeddings[0].values)
        return embeddings

def get_embeddings_service() -> EmbeddingsService:
    """Get configured embeddings service."""
    settings = get_settings()
    return EmbeddingsService(api_key=settings.gemini_api_key)
