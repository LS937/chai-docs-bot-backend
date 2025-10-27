from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_community.document_loaders import RecursiveUrlLoader
from bs4 import BeautifulSoup
import re
import sys

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

try:
    vector_store = QdrantVectorStore.from_documents(
        documents= docs,
        embedding=embedding_model,
        url="http://localhost:6333",
        collection_name="chai-aur-docs"
    )
    print("Indexing complete")
except Exception as e:
    print(f"Error connecting to Qdrant: {e}")
    print("Please ensure Qdrant is running on http://localhost:6333")
    print("You can start Qdrant using Docker: docker run -p 6333:6333 qdrant/qdrant")
    sys.exit(1)







