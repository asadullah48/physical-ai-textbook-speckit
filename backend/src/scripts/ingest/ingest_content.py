"""Content ingestion script for the Physical AI Textbook.

This script:
1. Parses all MDX files from the frontend docs directory
2. Generates embeddings for content chunks
3. Stores embeddings in Qdrant vector database
4. Updates content metadata in PostgreSQL

Usage:
    python -m src.scripts.ingest.ingest_content --docs-path ../frontend/docs
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List
from uuid import uuid4

from src.api.config import get_settings
from src.scripts.ingest.mdx_parser import ParsedMDX, parse_mdx_directory
from src.services.embeddings import EmbeddingsService
from src.services.qdrant import get_qdrant_client


async def ingest_content(
    docs_path: Path,
    collection_name: str = "textbook_content",
    batch_size: int = 100,
    dry_run: bool = False,
) -> dict:
    """Ingest MDX content into vector database.

    Args:
        docs_path: Path to the docs directory.
        collection_name: Qdrant collection name.
        batch_size: Number of embeddings to process at once.
        dry_run: If True, parse content but don't store.

    Returns:
        Statistics about the ingestion process.
    """
    settings = get_settings()
    stats = {
        "files_parsed": 0,
        "chunks_created": 0,
        "embeddings_generated": 0,
        "errors": [],
    }

    print(f"Parsing MDX files from: {docs_path}")

    # Parse all MDX files
    parsed_docs: List[ParsedMDX] = parse_mdx_directory(docs_path)
    stats["files_parsed"] = len(parsed_docs)

    print(f"Parsed {len(parsed_docs)} MDX files")

    # Collect all chunks
    all_chunks = []
    for doc in parsed_docs:
        for chunk in doc.chunks:
            all_chunks.append({
                "id": str(uuid4()),
                "text": chunk.text,
                "metadata": {
                    "module_id": doc.module_id,
                    "chapter_id": doc.chapter_id,
                    "title": doc.title,
                    "section": chunk.section,
                    "chunk_index": chunk.chunk_index,
                    "week": doc.week,
                    "difficulty": doc.difficulty,
                },
            })

    stats["chunks_created"] = len(all_chunks)
    print(f"Created {len(all_chunks)} content chunks")

    if dry_run:
        print("Dry run - skipping embedding generation and storage")
        return stats

    # Initialize services
    settings = get_settings()
    embeddings_service = EmbeddingsService(settings.google_api_key)
    qdrant_client = get_qdrant_client()

    # Ensure collection exists
    try:
        from qdrant_client.models import Distance, VectorParams

        await qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=embeddings_service.embedding_dimension,
                distance=Distance.COSINE,
            ),
        )
        print(f"Created collection: {collection_name}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"Collection {collection_name} already exists")
        else:
            stats["errors"].append(f"Collection creation error: {e}")
            print(f"Warning: {e}")

    # Process in batches
    from qdrant_client.models import PointStruct

    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        texts = [chunk["text"] for chunk in batch]

        try:
            # Generate embeddings
            embeddings = await embeddings_service.embed_texts(texts)

            # Create points
            points = [
                PointStruct(
                    id=chunk["id"],
                    vector=embedding,
                    payload=chunk["metadata"],
                )
                for chunk, embedding in zip(batch, embeddings)
            ]

            # Upsert to Qdrant
            await qdrant_client.upsert(
                collection_name=collection_name,
                points=points,
            )

            stats["embeddings_generated"] += len(embeddings)
            print(f"Processed batch {i // batch_size + 1}/{(len(all_chunks) + batch_size - 1) // batch_size}")

        except Exception as e:
            stats["errors"].append(f"Batch {i // batch_size + 1} error: {e}")
            print(f"Error processing batch: {e}")

    print(f"\nIngestion complete!")
    print(f"  Files parsed: {stats['files_parsed']}")
    print(f"  Chunks created: {stats['chunks_created']}")
    print(f"  Embeddings generated: {stats['embeddings_generated']}")
    if stats["errors"]:
        print(f"  Errors: {len(stats['errors'])}")
        for error in stats["errors"]:
            print(f"    - {error}")

    return stats


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest MDX content into vector database"
    )
    parser.add_argument(
        "--docs-path",
        type=Path,
        required=True,
        help="Path to the docs directory containing MDX files",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="textbook_content",
        help="Qdrant collection name",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of embeddings to process at once",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse content without storing",
    )

    args = parser.parse_args()

    if not args.docs_path.exists():
        print(f"Error: Path does not exist: {args.docs_path}")
        sys.exit(1)

    asyncio.run(
        ingest_content(
            docs_path=args.docs_path,
            collection_name=args.collection,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )
    )


if __name__ == "__main__":
    main()
