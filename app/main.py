import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from app.ha_client import start_entity_refresh
from app.router import classify
from app.agent import run

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(start_entity_refresh())
    yield
    
app = FastAPI(lifespan=lifespan)

class ConversationRequest(BaseModel):
    text: str
    conversation_id: str
    device_id: str
    language: str = "en"
    agent_id: str = ""
    
class ConversationResponse(BaseModel):
    message: str
    continue_conversation: bool = False
    finish_reason: str = "stop"
    
@app.post("/conversation", response_model=ConversationResponse)
async def conversation(request: ConversationRequest):
    intent = await classify(request.text)
    reply = await run(request.text, request.device_id, intent)
    return ConversationResponse(message=reply)