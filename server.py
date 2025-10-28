from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from fastapi.responses import StreamingResponse

from graph import graph, State

app = FastAPI()

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://chai-docs-bot.vercel.app",
        "https://chai-docs-bot.vercel.app/",  # With trailing slash
        "http://localhost:5173",  # Local development
        "http://localhost:3000",  # Alternative local dev port
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly include OPTIONS
    allow_headers=["*"],
    expose_headers=["*"],  # Expose headers to the browser
)

# Request schema
class Query(BaseModel):
    message: str

@app.post("/chat")
def chat(query : Query):
    _state : State = {"query" : query.message, "urls" : None, "sub_queries" : None, "llm_result" : None, "status" : None}

    response = graph.invoke(_state)
    return {"answer": response["llm_result"]}

    # def event_generator():
    #     for event in graph.stream(_state):
    #         for node_name, node_data in event.items():
    #             yield {"status": node_data.get("status"), "answer": node_data.get("llm_result")}

    # answer = "Krishna is revered as the Supreme Lord in Hinduism, known for his divine playfulness, wisdom, and compassion. He is the eighth avatar of Vishnu and is celebrated for his teachings in the Bhagavad Gita, where he guides Arjuna on duty, righteousness, and devotion. Krishna's childhood stories in Vrindavan, his miracles, and his role as a charioteer in the Mahabharata are central to his legacy. Devotees worship Krishna for his loving nature and his promise to protect the righteous."
    # return {"answer": answer}

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(
        "server:app",   # "server" = filename without .py, "app" = FastAPI instance
        host="0.0.0.0",
        port=8000,
        reload=True      # auto-reload on code changes (dev only)
    )


