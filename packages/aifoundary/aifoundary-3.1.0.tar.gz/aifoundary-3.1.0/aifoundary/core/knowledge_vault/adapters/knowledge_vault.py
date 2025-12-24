"""
Adapter for Knowledge Vault API.
"""
import requests

KNOWLEDGE_VAULT_URL = "http://localhost:8000"

def query_vault(query: str):
    response = requests.get(
        f"{KNOWLEDGE_VAULT_URL}/query",
        params={"q": query}
    )
    return response.json()
