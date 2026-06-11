"""Smoke test: Azure AI Search connectivity."""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential

QUERY = "malaria"

def test_search():
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    index_name = os.getenv("AZURE_KB_NAME", "medorarx-kb")
    key = os.getenv("AZURE_SEARCH_KEY") or os.getenv("AZURE_OPENAI_KEY")

    if not endpoint or not key:
        print("FAIL: AZURE_SEARCH_ENDPOINT or search key not set in .env")
        sys.exit(1)

    credential = AzureKeyCredential(key)

    # List available indexes so the correct name is visible if the configured one is wrong
    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
    available = [idx.name for idx in index_client.list_indexes()]
    print(f"INFO: Indexes found on service: {available}")

    if index_name not in available:
        print(f"FAIL: Index '{index_name}' not found. Update AZURE_KB_NAME in .env to one of: {available}")
        sys.exit(1)

    try:
        client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential,
        )
        results = list(client.search(QUERY, top=1))
        if results:
            print(f"SUCCESS: First result: {results[0]}")
        else:
            print(f"SUCCESS: Search returned no results for '{QUERY}' (index may be empty)")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_search()
