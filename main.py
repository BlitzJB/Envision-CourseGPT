import json, fastapi, pydantic, uvicorn, base64, openai
from fastapi.middleware.cors import CORSMiddleware
# from providers.openai_legit import OpenAIGPT
from providers.freegpt import FreeGPT, RateLimiter
from providers.llamachat import LlamaChat
from coursegpt import CourseGPT
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# openai.api_key = "..."

MAX_RETRIES = 10

# openai_gpt = OpenAIGPT()
free_gpt_rate_limiter = RateLimiter(requests_per_minute=10)
free_gpt = FreeGPT(ratelimiter=free_gpt_rate_limiter)
# llama_chat = LlamaChat(version='70b')

            
def sse_format(data):
    """
    Format data for Server-Sent Events.
    """
    return f"data: {json.dumps(data)}\n\n"

app = fastapi.FastAPI()

class OutlineRequest(pydantic.BaseModel):
    topic: str

@app.post("/api/get_outline")
async def get_outline(request: OutlineRequest):
    outline = await CourseGPT.generate_outline(request.topic, free_gpt)
    return {"items": outline}

@app.get("/api/get_all_subtopics")
async def get_all_subtopics(outline: str, topic: str):
    decoded_outline = base64.b64decode(outline).decode('utf-8')
    outline_data = json.loads(decoded_outline)
    async def event_stream():
        async for subtopic_content in CourseGPT.generate_all_subtopics_generator_parallelized(outline_data.get("items"), topic, free_gpt):
            yield sse_format(subtopic_content)
    return fastapi.responses.StreamingResponse(event_stream(), media_type="text/event-stream")

import typing

class AskDoubtRequest(pydantic.BaseModel):
    content: str
    doubt: str
    outline: typing.Any
    
@app.post("/api/ask_doubt")
async def ask_doubt(request: AskDoubtRequest):
    answer = await CourseGPT.answer_doubt(request.content, request.doubt, request.outline.get("items"), free_gpt)
    return { "answer": answer }

app.mount("/", StaticFiles(directory="clientbuild", html=True), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://localhost:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)