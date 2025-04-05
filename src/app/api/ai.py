from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.ai_service import AIService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
ai_service = AIService()

class MessageRequest(BaseModel):
    threadId: Optional[str] = None
    sessionId: Optional[str] = None
    message: str

@router.post("/openai/start")
async def start_conversation():
    """Start a new OpenAI conversation"""
    try:
        thread_id = await ai_service.create_conversation()
        return {"threadId": thread_id}
    except Exception as e:
        logger.error(f"Error starting OpenAI conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/openai/message")
async def send_message(request: MessageRequest):
    """Send a message to OpenAI assistant"""
    if not request.threadId or not request.message:
        raise HTTPException(status_code=400, detail="threadId and message are required")
    
    try:
        response = await ai_service.send_message(request.threadId, request.message)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error sending message to OpenAI: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bedrock/start")
async def start_bedrock_conversation():
    """Start a new Bedrock conversation"""
    try:
        session_id = await ai_service.create_bedrock_conversation()
        return {"sessionId": session_id}
    except Exception as e:
        logger.error(f"Error starting Bedrock conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bedrock/message")
async def send_bedrock_message(request: MessageRequest):
    """Send a message to Bedrock agent"""
    if not request.sessionId or not request.message:
        raise HTTPException(status_code=400, detail="sessionId and message are required")
    
    try:
        response = await ai_service.send_bedrock_message(request.sessionId, request.message)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error sending message to Bedrock: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 