from qdrant_client import QdrantClient
from dotenv import load_dotenv
import os


load_dotenv()


client = QdrantClient(url=os.getenv("QDRANT_URL"),
                      api_key=os.getenv("QDRANT_API_KEY"))

collection_name = "chai-aur-docs"

client.delete_collection(collection_name=collection_name)

print(f'Collection {collection_name} deleted successfully.')
