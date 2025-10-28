from dotenv import load_dotenv
from openai import OpenAI
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import models
from system_prompt import sub_queries_system_prompt, find_pages_system_prompt, context, give_answer_system_prompt
from qdrant_client import QdrantClient
import os
# from langfuse.langchain import CallbackHandler



load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# langfuse_handler = CallbackHandler()


class State(TypedDict):
    query : str
    sub_queries : list[str] | None
    urls : list[str] | None
    llm_result : str | None
    status: str | None

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

# Get Qdrant credentials from environment variables
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

# Connect to Qdrant (Cloud or Local)
if qdrant_api_key:
    # Production: Qdrant Cloud
    vector_store = QdrantVectorStore.from_existing_collection(
        url=qdrant_url,
        api_key=qdrant_api_key,
        embedding=embedding_model,
        collection_name="chai-aur-docs"
    )
else:
    # Local development: Docker Qdrant
    vector_store = QdrantVectorStore.from_existing_collection(
        url=qdrant_url,
        embedding=embedding_model,
        collection_name="chai-aur-docs"
    )

qdrant_client: QdrantClient = vector_store.client

class SubQueries(BaseModel):
    sub_queries : list[str]

class URLs(BaseModel):
    urls :list[str]

context = context

def generate_sub_queries(state: State):
    query = state["query"]

    SYSTEM_PROMPT = sub_queries_system_prompt

    response = client.beta.chat.completions.parse(
        model="gpt-2.5-flash",
        response_format=SubQueries,
        messages= [
            {"role": "system", "content" : SYSTEM_PROMPT},
            {"role": "user", "content" : query}
        ]
    )

    state["status"] = "searching"
    state["sub_queries"] = response.choices[0].message.parsed.sub_queries

    return state

def find_relevant_pages(state: State):
    user_query = state["query"]
    sub_queries = state["sub_queries"]

    SYSTEM_PROMPT = find_pages_system_prompt + f"""
        <context>
            Web Pages of Docs website by Chai Code: {context}
            User Query: {user_query}
            Sub-Queries: {sub_queries}
        </context>
    """

    response = client.beta.chat.completions.parse(
        model="gpt-2.5-flash",
        response_format=URLs,
        messages= [
            {"role": "system", "content" : SYSTEM_PROMPT},
            {"role": "user", "content" : user_query}
        ]
    )

    state["status"] = "thinking"
    state["urls"] = response.choices[0].message.parsed.urls

    return state


def give_answer(state: State):
    query = state["query"]
    urls = state["urls"]
    relevant_context = ""


    for url in urls:
        search_results = vector_store.similarity_search(
            query="",
            k=1,
            filter=models.Filter(
            should=[
                    models.FieldCondition(
                        key="metadata.source",
                        match=models.MatchValue(
                            value=url
                        ),
                    ),
                ]   
            ),
        )

        relevant_context += "\n\n\n".join([f"Web Page Content: {result.page_content} \n URL: {result.metadata['source']}" for result in search_results])


    SYSTEM_PROMPT = give_answer_system_prompt + f"""  
        <context>
            relevant_context:
                {relevant_context}
        </context>
    """


    response = client.chat.completions.create(
        model="gpt-2.5-pro",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ]
    )

    state["status"] = "streaming"
    state["llm_result"] = response.choices[0].message.content

    return state



graph_builder = StateGraph(State)

graph_builder.add_node("generate_sub_queries", generate_sub_queries)
graph_builder.add_node("find_relevant_pages", find_relevant_pages)
graph_builder.add_node("give_answer", give_answer)

graph_builder.add_edge(START, "generate_sub_queries")
graph_builder.add_edge("generate_sub_queries", "find_relevant_pages")
graph_builder.add_edge("find_relevant_pages", "give_answer")
graph_builder.add_edge("give_answer", END)

graph = graph_builder.compile()


# def main():
#     user_query = input("> ")

#     _state = State(
#         query=user_query,
#         llm_result= None,
#         sub_queries=[],
#         urls=[]
#     )

#     for event in graph.stream(_state):
#         print(event)

# main()



