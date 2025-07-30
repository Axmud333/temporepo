from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
import warnings
import psycopg2

warnings.filterwarnings("ignore", category=DeprecationWarning)


model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
qdrant_client = QdrantClient(url="http://localhost:6333")
collection_name = "uos"

def qdrant_search(question):
    results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=model.encode(question).tolist(),
        limit=1,
        with_payload=True,
    )

    conn = psycopg2.connect(
    host="POSTGRES_HOST",
    database="POSTGRES_DB",
    user="POSTGRES_USER",
    password="POSTGRES_PASSWORD",
    )

    psql = results[0].payload.get("command", "").strip()
    with conn.cursor() as cursor:
        cursor.execute(psql)
        database = cursor.fetchone()[0]
    return database

qdrant_search()