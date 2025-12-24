import chromadb
from chromadb.config import Settings

client = chromadb.Client(
    Settings(
        persist_directory="./data/chroma",
        anonymized_telemetry=False
    )
)

collection = client.get_or_create_collection("knowledge_vault")

def upsert_embedding(doc_id: str, embedding: list, metadata: dict):
    collection.upsert(
        ids=[doc_id],
        embeddings=[embedding],
        metadatas=[metadata]
    )
    client.persist()

def query_embedding(query_embedding: list, top_k: int = 5):
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
