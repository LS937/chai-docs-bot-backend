from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import RecursiveUrlLoader
from bs4 import BeautifulSoup
import re
import sys
import os

load_dotenv()


def bs4_extractor(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    return re.sub(r"\n\n+", "\n\n", soup.text).strip()


loader = RecursiveUrlLoader(
    "https://docs.chaicode.com/youtube/getting-started/",
    max_depth=2,
    extractor=bs4_extractor,
    timeout=60,
    prevent_outside=False
)

docs = loader.load()
print(f"Loaded {len(docs)} documents")

# Filter out any failed documents
docs = [doc for doc in docs if doc.page_content.strip()]
print(f"Valid documents after filtering: {len(docs)}")

if not docs:
    print("No documents were successfully loaded. Please check the URL and network connection.")
    exit(1)

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

# Get Qdrant credentials from environment variables
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

try:
    # If API key is provided, use Qdrant Cloud, otherwise use local Qdrant
    if qdrant_api_key:
        vector_store = QdrantVectorStore.from_documents(
            documents=docs,
            embedding=embedding_model,
            url=qdrant_url,
            api_key=qdrant_api_key,
            collection_name="chai-aur-docs"
        )
        print(f"Indexing complete on Qdrant Cloud: {qdrant_url}")
    else:
        vector_store = QdrantVectorStore.from_documents(
            documents=docs,
            embedding=embedding_model,
            url=qdrant_url,
            collection_name="chai-aur-docs"
        )
        print(f"Indexing complete on local Qdrant: {qdrant_url}")
    
    # Create payload index for metadata.source to enable filtering
    print("Creating payload index for metadata.source...")
    qdrant_client = vector_store.client
    qdrant_client.create_payload_index(
        collection_name="chai-aur-docs",
        field_name="metadata.source",
        field_schema="keyword"
    )
    print("Payload index created successfully!")
    
except Exception as e:
    print(f"Error connecting to Qdrant: {e}")
    print(f"Please ensure Qdrant is running on {qdrant_url}")
    print("You can start Qdrant using Docker: docker run -p 6333:6333 qdrant/qdrant")
    sys.exit(1)







