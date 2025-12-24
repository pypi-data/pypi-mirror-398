"""
Safe retrieval interface for agents.
"""
from embeddings.embedding_provider import embed_text
from store.vector_store import query_embedding

def query_knowledge(query: str, actor_id: str):
    embedding = embed_text(query)
    results = query_embedding(embedding)
    return results
