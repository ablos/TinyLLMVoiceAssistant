import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from app.ha_client import start_entity_refresh
from app.router import classify
from app.agent import run

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    import time
    t0 = time.monotonic()
    logger.info("[%s] '%s'", request.device_id, request.text)

    intent, query = await classify(request.text)
    t1 = time.monotonic()
    logger.info("[%s] intent: %s (%.2fs)", request.device_id, intent, t1 - t0)

    reply = await run(request.text, request.device_id, intent, query)
    t2 = time.monotonic()
    logger.info("[%s] reply: '%s' (%.2fs)", request.device_id, reply, t2 - t1)
    logger.info("[%s] total: %.2fs", request.device_id, t2 - t0)

    return ConversationResponse(message=reply, continue_conversation=reply.rstrip().endswith("?"))