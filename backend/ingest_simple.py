import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv()
from src.services import embeddings
from src.services.qdrant import QdrantService

def main():
    print("Starting content ingestion...")
    qdrant = QdrantService()
    contents = [
        {"text": "Physical AI refers to artificial intelligence systems that interact with and learn from the physical world through sensors, actuators, and embodied agents.", "source": "Module 1"},
        {"text": "Sensor systems include LiDAR for 3D mapping, cameras for visual perception, IMUs for motion tracking, and force/torque sensors.", "source": "Module 1"},
        {"text": "Embodied intelligence means AI that has a physical form and interacts with the environment.", "source": "Module 1"}
    ]
    from qdrant_client.models import PointStruct
    import uuid
    points = []
    for idx, content in enumerate(contents):
        print(f"Embedding chunk {idx+1}/{len(contents)}...")
        embedding = embeddings.generate_document_embedding(content["text"])
        points.append(PointStruct(id=str(uuid.uuid4()), vector=embedding, payload={"text": content["text"], "source": content["source"]}))
    print("Storing in Qdrant...")
    qdrant.client.upsert(collection_name="textbook_content", points=points)
    print("Done! Try asking: What is Physical AI?")

if __name__ == "__main__":
    main()
