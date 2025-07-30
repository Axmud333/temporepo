from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct
from qdrant_client.http.models import VectorParams, Distance
import uuid

model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

qdrant_client = QdrantClient(url="http://localhost:6333")

my_collection = "uos"

def qdrant_builder(data: list[dict]) -> None:
    if my_collection not in [col.name for col in qdrant_client.get_collections().collections]:
        qdrant_client.recreate_collection(
            collection_name=my_collection,
            vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE),
        )

    for item in data:
        question= item.get("questions", "").strip()
        command= item.get("command", "").strip()
        lang = item.get("lang", "").strip()

        if not question or not command:
            continue
        
        # Yohohohoho!!! Here is the fanci trick!!
        qdrant_id = str(uuid.uuid4())

        qdrant_client.upsert(
            collection_name=my_collection,
            points=[
                models.PointStruct(
                    id=qdrant_id,
                    vector=model.encode(question).tolist(),
                    payload={"command": command,"lang": lang, "questions": question}
                )
            ]
        )