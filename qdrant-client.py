from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

collection_name = "chai-aur-docs"

client.delete_collection(collection_name=collection_name)

print(f'Collection {collection_name} deleted successfully.')
