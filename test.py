from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-large"
)

vector_store = QdrantVectorStore.from_existing_collection(
    url= "http://localhost:6333",
    embedding=embedding_model,
    collection_name="chai-aur-docs"
)

query = input("> ")

results = vector_store.similarity_search(
    query=query
)

print(results)